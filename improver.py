import asyncio
import os
import ast
from functools import cache
from typing import List, Dict, Any, Type
from pydantic import BaseModel, validator
from abc import ABC, abstractmethod

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

class LLMTask(ABC):
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        pass

    @property
    @abstractmethod
    def response_model(self) -> Type[BaseModel]:
        pass

    def __init__(self, goal: str):
        self.goal = goal

    @abstractmethod
    def construct_prompt(self, **kwargs: Any) -> List[Dict[str, str]]:
        pass

    async def execute(self, **kwargs: Any) -> Any:
        prompt = self.construct_prompt(**kwargs)
        resp = await get_structured_completion(prompt, self.response_model)
        return resp.get('parsed_content') if resp else None

class BranchTask(LLMTask):
    system_prompt = (
        'You are an expert Python programmer. Your task is to rewrite given files to achieve a specific goal.'
        ' You must follow a "Plan-and-Execute" strategy.'
        " First, create a concise, step-by-step plan in the 'reasoning' field."
        " Second, provide the new, complete source codes for the files in the 'edits' list, each with 'file_path' and its updated 'code', based on your plan."
    )

    response_model = PlanAndCode

    def construct_prompt(self, files_contents: List, syntax_errors: Dict[str, str] = None, api_docs: str = '', protected_files: List[str] = []) -> List[Dict[str, str]]:
        msg = [f"**Goal:** {self.goal}"]
        file_paths = {fp for fp, _ in files_contents}
        if 'llm_provider.py' in file_paths and 'llm_provider.py' not in protected_files and api_docs.strip():
            msg.extend(["\n**Context:**", f"\n{api_docs}"])
        for fp, content in files_contents:
            msg.extend([f"\n**File to improve:** `{fp}`\n", '```python', content, '```'])
            if syntax_errors and syntax_errors.get(fp):
                err = syntax_errors[fp].replace('```', '` ` `') if syntax_errors[fp] else ''
                msg.extend([f"\nThe previous attempt for `{fp}` resulted in a SyntaxError:", '```', err, '```'])
        return [{"role": "system", "content": self.system_prompt}, {"role": "user", "content": "\n".join(msg)}]

class IntegratorTask(LLMTask):
    system_prompt = (
        'You are a senior software architect expert in Python code improvement.'
        ' Your task is to carefully review multiple proposed code revisions for the same goal.'
        ' Each proposal includes reasoning and resulting code edits for files.'
        ' Your objective is to integrate the best improvements into a final version.'
        ' Provide reasoning explaining your choices and return the final code edits.'
    )

    response_model = PlanAndCode

    def construct_prompt(self, proposals: List[Dict]) -> List[Dict[str, str]]:
        lines = [f"**Original Goal:** {self.goal}\n---"]
        for p in proposals:
            lines.extend(["---",
                          f"\n**Branch ID: {p['id']}**",
                          f"**Reasoning:**\n{p['plan']}",
                          "\n**Code Edits:**"])
            for edit in p['edits']:
                lines.extend([f"\nFile: `{edit.file_path}`", '```python', edit.code, '```'])
        return [{"role": "system", "content": self.system_prompt}, {"role": "user", "content": "\n".join(lines)}]

class BranchRunner:
    def __init__(self, goal: str, safe_io: SafeIO, protected_files: List[str], branch_id: int, iterations: int = 3, max_corrections: int = 3):
        self.branch_id = branch_id
        self.goal = goal
        self.safe_io = safe_io
        self.protected_files = set(protected_files)
        self.iterations = iterations
        self.max_corrections = max_corrections
        self.branch_task = BranchTask(goal)

    @cache
    def _get_api_docs_text(self) -> str:
        if not os.path.isdir('docs'):
            return ''
        return '\n\n'.join(
            f"# Documentation file: {os.path.join(root, f)}\n" + self.safe_io.read(os.path.join(root, f))
            for root, _, files in os.walk('docs') for f in sorted(files)
        )

    async def run(self, files_contents: List[tuple]) -> PlanAndCode:
        filtered = [(fp, c) for fp, c in files_contents if fp not in self.protected_files]
        print(f"Branch-{self.branch_id}: Starting {self.iterations} iteration(s) for {len(filtered)} files...")
        codes = {fp: c for fp, c in filtered}
        syntax_errors = {fp: None for fp, _ in filtered}
        parsed = None
        api_docs = self._get_api_docs_text()

        for i in range(self.iterations):
            print(f"Branch-{self.branch_id} Iteration-{i+1}: Improving...")
            for attempt in range(1, self.max_corrections + 1):
                resp = await self.branch_task.execute(files_contents=list(codes.items()),
                                                      syntax_errors=syntax_errors,
                                                      api_docs=api_docs,
                                                      protected_files=list(self.protected_files))
                if not isinstance(resp, PlanAndCode):
                    print(f"Branch-{self.branch_id} Iteration-{i+1} Correction-{attempt}: Invalid LLM response.")
                    break
                parsed = resp
                syntax_errors.clear()

                filtered_edits = [e for e in parsed.edits if e.file_path not in self.protected_files]
                all_ok = True

                for e in filtered_edits:
                    try:
                        ast.parse(e.code)
                        syntax_errors[e.file_path] = None
                    except SyntaxError as se:
                        msg = f"{se.msg} at line {se.lineno}, offset {se.offset}: {(se.text.strip() if se.text else '')}".strip()
                        syntax_errors[e.file_path] = msg
                        all_ok = False
                        print(f"Branch-{self.branch_id} Iteration-{i+1} Correction-{attempt}: SyntaxError in `{e.file_path}`:\n{msg}")

                codes.update({e.file_path: e.code for e in filtered_edits})

                if all_ok:
                    print(f"Branch-{self.branch_id} Iteration-{i+1} Correction-{attempt}: Syntax check passed.")
                    break

                if attempt == self.max_corrections:
                    print(f"Branch-{self.branch_id} Iteration-{i+1}: Max corrections reached, moving to next iteration.")
                    break

                print(f"Branch-{self.branch_id} Iteration-{i+1}: Retrying syntax fix (attempt {attempt + 1})...")

        print(f"Branch-{self.branch_id}: Completed all iterations.")
        unresolved = [fp for fp, err in syntax_errors.items() if err]
        if unresolved:
            print(f"Branch-{self.branch_id}: Finished with unresolved syntax errors in files: {unresolved}")

        return PlanAndCode(reasoning=parsed.reasoning if parsed else "", edits=[FileEdit(file_path=fp, code=code) for fp, code in codes.items()])

class IntegrationRunner:
    def __init__(self, goal: str, safe_io: SafeIO):
        self.goal = goal
        self.safe_io = safe_io
        self.integrator_task = IntegratorTask(goal)

    async def run(self, proposals: List[Dict]) -> Any:
        if not proposals:
            print("\nResult: No successful proposals.")
            return None
        if len(proposals) == 1:
            print("\nSingle successful branch. Using its result.")
            return PlanAndCode(reasoning=proposals[0]['plan'], edits=proposals[0]['edits'])

        print("Multiple successful branches, integrating...")
        integration = await self.integrator_task.execute(proposals=proposals)
        if not isinstance(integration, PlanAndCode):
            print("Integrator LLM failed. Aborting.")
            return None

        if any(self._try_parse_code(e.code) for e in integration.edits):
            print("Integrated code SyntaxError detected, discarding result.")
            return None

        print(f"\nIntegration reasoning:\n{integration.reasoning}")
        return integration

    @staticmethod
    def _try_parse_code(code: str):
        try:
            ast.parse(code)
        except SyntaxError as e:
            return e
        return None

class Improver:
    def __init__(self, safe_io: SafeIO):
        self.safe_io = safe_io
        try:
            parsed = safe_io.read('protected.yaml')
        except Exception:
            parsed = None
        try:
            import yaml
            loaded = yaml.safe_load(parsed) if parsed else None
            self._protected_files = set(loaded) if isinstance(loaded, list) else set()
        except Exception:
            self._protected_files = set()

    async def run(self, goal, file_paths: List[str], num_branches=3, iterations_per_branch=3):
        filtered = [fp for fp in file_paths if fp not in self._protected_files]
        if not filtered:
            print(f"No files to improve after filtering protected files: {file_paths}")
            return

        print(f"\n--- Starting multi-file improvement for files: {filtered} ---\nGoal: {goal}")

        try:
            originals = [(fp, self.safe_io.read(fp)) for fp in filtered]
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return

        tasks = [BranchRunner(goal, self.safe_io, list(self._protected_files), i + 1, iterations_per_branch).run(originals) for i in range(num_branches)]
        results = await asyncio.gather(*tasks)

        proposals = [dict(id=i + 1, plan=r.reasoning, edits=r.edits) for i, r in enumerate(results) if r]
        if not proposals:
            print("\nResult: No successful proposals.")
            return

        integration = await IntegrationRunner(goal, self.safe_io).run(proposals)
        if not integration:
            print("\nResult: No integration result available.")
            return

        original_dict = dict(originals)
        changed = any(original_dict.get(e.file_path) != e.code for e in integration.edits if e.file_path not in self._protected_files)
        if not changed:
            print("\nResult: No changes detected after integration.")
            return

        print("\nApplying integrated changes...")
        try:
            for edit in integration.edits:
                if edit.file_path in self._protected_files:
                    print(f"Skipping write for protected file: {edit.file_path}")
                    continue
                self.safe_io.write(edit.file_path, edit.code)
        except PermissionError as e:
            print(f"Failed to write changes: {e}")
            return

        print(f"--- Finished multi-file improvement for files: {filtered} ---")
