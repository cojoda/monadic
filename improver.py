import asyncio
import ast
from pydantic import BaseModel, validator
from typing import List

from safe_io import SafeIO
from llm_provider import get_structured_completion

class FileEdit(BaseModel):
    file_path: str
    code: str

class PlanAndCode(BaseModel):  # Renamed for clarity
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

    def _construct_branch_prompt_input(self, goal, files_contents, syntax_errors=None):
        # files_contents is List of (file_path, content)
        # syntax_errors is dict file_path->error string or None
        msg_lines = [f"**Goal:** {goal}"]
        for file_path, content in files_contents:
            msg_lines.append(f"\n**File to improve:** `{file_path}`\n\n**Current content:**")
            msg_lines.append("```python")
            msg_lines.append(content)
            msg_lines.append("```")
            if syntax_errors and syntax_errors.get(file_path):
                # Safely escape triple backticks to avoid null byte issues
                escaped_err = syntax_errors[file_path].replace("```", "` ` `")
                msg_lines.append(f"\nThe previous attempt for `{file_path}` resulted in a SyntaxError:")
                msg_lines.append("```")
                msg_lines.append(escaped_err)
                msg_lines.append("```")
        msg = "\n".join(msg_lines)
        return [
            {"role": "system", "content": self.BRANCH_SYSTEM_PROMPT},
            {"role": "user", "content": msg}
        ]

    def _construct_integrator_prompt_input(self, goal, proposals):
        # proposals: list of dict with 'id', 'plan', 'edits' (list of FileEdits)
        combined_lines = [f"**Original Goal:** {goal}\n---"]
        for p in proposals:
            combined_lines.append(f"---\n\n**Branch ID: {p['id']}**")
            combined_lines.append(f"**Reasoning:**\n{p['plan']}")
            combined_lines.append(f"\n**Code Edits:**")
            for edit in p['edits']:
                combined_lines.append(f"\nFile: `{edit.file_path}`")
                combined_lines.append("```python")
                combined_lines.append(edit.code)
                combined_lines.append("```")
        combined = "\n".join(combined_lines)
        return [
            {"role": "system", "content": self.INTEGRATOR_SYSTEM_PROMPT},
            {"role": "user", "content": combined}
        ]

    async def _run_branch(self, branch_id, goal, files_contents, iterations=3, max_corrections=3):
        print(f"Branch-{branch_id}: Starting {iterations} iteration(s) for {len(files_contents)} files...")
        # files_contents: List[(file_path, code)] representing current code states
        current_codes = {fp: content for fp, content in files_contents}
        syntax_errors = {fp: None for fp, _ in files_contents}
        parsed = None

        for i in range(iterations):
            print(f"Branch-{branch_id} Iteration-{i+1}: Improving...")
            for attempt in range(1, max_corrections + 1):
                prompt = self._construct_branch_prompt_input(goal, list(current_codes.items()), syntax_errors)
                resp = await get_structured_completion(prompt, PlanAndCode)
                parsed = resp.get("parsed_content") if resp else None
                if not isinstance(parsed, PlanAndCode):
                    print(f"Branch-{branch_id} Iteration-{i+1} Correction-{attempt}: Invalid LLM response.")
                    break

                # Validate syntax for each file
                all_passed = True
                new_errors = {}

                for edit in parsed.edits:
                    try:
                        ast.parse(edit.code)
                        new_errors[edit.file_path] = None
                    except SyntaxError as e:
                        err_msg = f"{e.msg} at line {e.lineno}, offset {e.offset}: {(e.text.strip() if e.text else '')}".strip()
                        new_errors[edit.file_path] = err_msg
                        all_passed = False
                        print(f"Branch-{branch_id} Iteration-{i+1} Correction-{attempt}: SyntaxError in `{edit.file_path}`:\n{err_msg}")

                current_codes.update({edit.file_path: edit.code for edit in parsed.edits})
                syntax_errors = new_errors

                if all_passed:
                    print(f"Branch-{branch_id} Iteration-{i+1} Correction-{attempt}: Syntax check passed. Tokens used: {resp.get('tokens', 'unknown')}")
                    break
                else:
                    if attempt == max_corrections:
                        print(f"Branch-{branch_id} Iteration-{i+1}: Max corrections reached, moving to next iteration.")
                        break
                    print(f"Branch-{branch_id} Iteration-{i+1}: Retrying syntax fix (attempt {attempt + 1})...")
        print(f"Branch-{branch_id}: Completed all iterations.")

        if any(syntax_errors.values()):
            print(f"Branch-{branch_id}: Finished with unresolved syntax errors in files: {[fp for fp, err in syntax_errors.items() if err]}")

        final_edits = [FileEdit(file_path=fp, code=code) for fp, code in current_codes.items()]
        return PlanAndCode(reasoning=(parsed.reasoning if parsed else ""), edits=final_edits)

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
            print("\nSingle successful branch. Using its result.")
            final_reasoning = proposals[0]["plan"]
            final_edits = proposals[0]["edits"]
        else:
            print("Multiple successful branches, integrating...")
            resp = await get_structured_completion(self._construct_integrator_prompt_input(goal, proposals), PlanAndCode)
            integration = resp.get("parsed_content") if resp else None

            if not isinstance(integration, PlanAndCode):
                print("Integrator LLM failed. Aborting.")
                return

            # Validate all integrated edits
            for edit in integration.edits:
                try:
                    ast.parse(edit.code)
                except SyntaxError as e:
                    print(f"Integrated code SyntaxError in `{edit.file_path}`, discarding result:\n{e}")
                    return

            print(f"\nIntegration reasoning:\n{integration.reasoning}")
            final_reasoning = integration.reasoning
            final_edits = integration.edits

        # Check if any changes compared to originals
        changes_detected = False
        original_dict = dict(originals)
        for edit in final_edits:
            original_code = original_dict.get(edit.file_path)
            if original_code != edit.code:
                changes_detected = True
                break

        if not changes_detected:
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
