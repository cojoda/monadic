import asyncio
import ast
import os
import yaml
from functools import lru_cache
from pydantic import BaseModel, validator
from typing import List, Optional

from safe_io import SafeIO
from llm_provider import get_structured_completion

class FileEdit(BaseModel):
    file_path: str
    code: str

class PlanAndCode(BaseModel):
    reasoning: str
    edits: List[FileEdit]

    @validator('edits')
    def edits_not_empty(cls, v):
        if not v:
            raise ValueError('edits must not be empty')
        return v

class Improver:
    BRANCH_SYSTEM_PROMPT = '''
You are an expert Python programmer. Your task is to rewrite given files to achieve a specific goal.
You must follow a "Plan-and-Execute" strategy.
First, create a concise, step-by-step plan in the 'reasoning' field.
Second, provide the new, complete source codes for the files in the 'edits' list, each with 'file_path' and its updated 'code', based on your plan.
'''

    INTEGRATOR_SYSTEM_PROMPT = '''
You are a senior software architect expert in Python code improvement.
Your task is to carefully review multiple proposed code revisions for the same goal.
Each proposal includes reasoning and resulting code edits for files.
Your objective is to integrate the best improvements into a final version.
Provide reasoning explaining your choices and return the final code edits.
'''

    def __init__(self, safe_io: SafeIO):
        self.safe_io = safe_io
        self._protected_files = self._load_protected_files()

    def _load_protected_files(self) -> List[str]:
        try:
            data = yaml.safe_load(self.safe_io.read('protected.yaml'))
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def _is_protected(self, file_path: str) -> bool:
        return file_path in self._protected_files

    @lru_cache(maxsize=1)
    def _get_api_docs_text(self) -> str:
        if not os.path.isdir('docs'):
            return ''
        texts = []
        for root, _, files in os.walk('docs'):
            for f in sorted(files):
                path = os.path.join(root, f)
                try:
                    content = self.safe_io.read(path)
                    texts.append(f"# Documentation file: {path}\n" + content)
                except Exception:
                    continue
        return "\n\n".join(texts)

    def _construct_branch_prompt_input(self, goal, files_contents, syntax_errors=None):
        files_set = {fp for fp, _ in files_contents}
        include_docs = 'llm_provider.py' in files_set and not self._is_protected('llm_provider.py')
        msg = [f"**Goal:** {goal}"]
        if include_docs:
            docs = self._get_api_docs_text()
            if docs:
                msg.append("\n**Context: API Documentation from docs/ directory:**")
                msg.extend(["```python", docs, "```"])

        for fp, content in files_contents:
            msg.extend([f"\n**File to improve:** `{fp}`\n\n**Current content:**", "```python", content, "```"])
            if syntax_errors and syntax_errors.get(fp):
                err = syntax_errors[fp].replace("```", "` ` `")
                msg.extend([f"\nThe previous attempt for `{fp}` resulted in a SyntaxError:", "```", err, "```"])
        return [
            {"role": "system", "content": self.BRANCH_SYSTEM_PROMPT},
            {"role": "user", "content": "\n".join(msg)}
        ]

    def _construct_integrator_prompt_input(self, goal, proposals):
        lines = [f"**Original Goal:** {goal}\n---"]
        for p in proposals:
            lines.extend(["---", f"\n**Branch ID: {p['id']}**", f"**Reasoning:**\n{p['plan']}", "\n**Code Edits:**"])
            for edit in p['edits']:
                lines.extend([f"\nFile: `{edit.file_path}`", "```python", edit.code, "```"])
        return [
            {"role": "system", "content": self.INTEGRATOR_SYSTEM_PROMPT},
            {"role": "user", "content": "\n".join(lines)}
        ]

    async def _run_branch(self, branch_id, goal, files_contents, iterations=3, max_corrections=3):
        print(f"Branch-{branch_id}: Starting {iterations} iteration(s) for {len(files_contents)} files...")
        codes = {fp: content for fp, content in files_contents}
        syntax_errors = {fp: None for fp, _ in files_contents}
        parsed = None

        for i in range(iterations):
            print(f"Branch-{branch_id} Iteration-{i+1}: Improving...")
            for attempt in range(1, max_corrections + 1):
                prompt = self._construct_branch_prompt_input(goal, list(codes.items()), syntax_errors)
                resp = await get_structured_completion(prompt, PlanAndCode)
                parsed = resp.get("parsed_content") if resp else None
                if not isinstance(parsed, PlanAndCode):
                    print(f"Branch-{branch_id} Iteration-{i+1} Correction-{attempt}: Invalid LLM response.")
                    break

                new_errors = {}
                all_ok = True
                for edit in parsed.edits:
                    try:
                        ast.parse(edit.code)
                        new_errors[edit.file_path] = None
                    except SyntaxError as e:
                        msg = f"{e.msg} at line {e.lineno}, offset {e.offset}: {(e.text.strip() if e.text else '')}".strip()
                        new_errors[edit.file_path] = msg
                        all_ok = False
                        print(f"Branch-{branch_id} Iteration-{i+1} Correction-{attempt}: SyntaxError in `{edit.file_path}`:\n{msg}")
                codes.update({edit.file_path: edit.code for edit in parsed.edits})
                syntax_errors = new_errors

                if all_ok:
                    print(f"Branch-{branch_id} Iteration-{i+1} Correction-{attempt}: Syntax check passed. Tokens used: {resp.get('tokens', 'unknown')}")
                    break

                if attempt == max_corrections:
                    print(f"Branch-{branch_id} Iteration-{i+1}: Max corrections reached, moving to next iteration.")
                    break

                print(f"Branch-{branch_id} Iteration-{i+1}: Retrying syntax fix (attempt {attempt + 1})...")
        print(f"Branch-{branch_id}: Completed all iterations.")

        if any(syntax_errors.values()):
            unresolved = [fp for fp, err in syntax_errors.items() if err]
            print(f"Branch-{branch_id}: Finished with unresolved syntax errors in files: {unresolved}")

        final_edits = [FileEdit(file_path=fp, code=code) for fp, code in codes.items()]
        return PlanAndCode(reasoning=parsed.reasoning if parsed else "", edits=final_edits)

    async def run(self, goal, file_paths: List[str], num_branches=3, iterations_per_branch=3):
        print(f"\n--- Starting multi-file improvement for files: {file_paths} ---\nGoal: {goal}")
        try:
            originals = [(fp, self.safe_io.read(fp)) for fp in file_paths]
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return

        tasks = [self._run_branch(i + 1, goal, originals, iterations_per_branch) for i in range(num_branches)]
        results = await asyncio.gather(*tasks)

        proposals = [
            {"id": i + 1, "plan": r.reasoning, "edits": r.edits}
            for i, r in enumerate(results) if r
        ]

        if not proposals:
            print("\nResult: No successful proposals.")
            return

        if len(proposals) == 1:
            final_reasoning, final_edits = proposals[0]["plan"], proposals[0]["edits"]
            print("\nSingle successful branch. Using its result.")
        else:
            print("Multiple successful branches, integrating...")
            resp = await get_structured_completion(self._construct_integrator_prompt_input(goal, proposals), PlanAndCode)
            integration = resp.get("parsed_content") if resp else None

            if not isinstance(integration, PlanAndCode):
                print("Integrator LLM failed. Aborting.")
                return

            for edit in integration.edits:
                try:
                    ast.parse(edit.code)
                except SyntaxError as e:
                    print(f"Integrated code SyntaxError in `{edit.file_path}`, discarding result:\n{e}")
                    return

            print(f"\nIntegration reasoning:\n{integration.reasoning}")
            final_reasoning, final_edits = integration.reasoning, integration.edits

        original_dict = dict(originals)
        if not any(original_dict.get(edit.file_path) != edit.code for edit in final_edits):
            print("\nResult: No changes detected after integration.")
            return

        print("\nApplying integrated changes...")
        try:
            for edit in final_edits:
                self.safe_io.write(edit.file_path, edit.code)
        except PermissionError as e:
            print(f"Failed to write changes: {e}")
            return

        print(f"--- Finished multi-file improvement for files: {file_paths} ---")
