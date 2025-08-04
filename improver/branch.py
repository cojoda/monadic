import os
import ast
from functools import cached_property
from typing import List, Dict

from .core import LLMTask
from .models import PlanAndCode, FileEdit
from safe_io import SafeIO

class BranchTask(LLMTask):
    system_prompt = """
You are an expert Python programmer. Your task is to use the provided files as context to achieve a specific goal.
You can freely edit existing files and also invent and create completely new files as needed to fulfill the goal.
You must follow a "Plan-and-Execute" strategy.
First, create a concise, step-by-step plan in the "reasoning" field.
Second, provide the new, complete source codes for the files in the "edits" list, each with "file_path" and its updated "code", based on your plan.
"""
    response_model = PlanAndCode

    def construct_prompt(self, files_contents: List, syntax_errors: Dict[str, str] = None, api_docs: str = '', protected_files: List[str] = []) -> List[Dict[str, str]]:
        file_paths = {fp for fp, _ in files_contents}
        msg = [f'**Goal:** {self.goal}']
        if 'llm_provider.py' in file_paths and 'llm_provider.py' not in protected_files and api_docs.strip():
            msg.append(f'\n**Context:**\n\n{api_docs}')
        for fp, content in files_contents:
            msg.extend([f'\n**File to improve:** `{fp}`\n', '```python', content, '```'])
            if syntax_errors and syntax_errors.get(fp):
                err = syntax_errors[fp].replace('```', '` ` `')
                msg.extend([f'\nThe previous attempt for `{fp}` resulted in a SyntaxError:', '```', err, '```'])
        return [{"role": "system", "content": self.system_prompt}, {"role": "user", "content": "\n".join(msg)}]

class BranchRunner:
    def __init__(self, goal: str, safe_io: SafeIO, protected_files: List[str], branch_id: int, iterations: int = 3, max_corrections: int = 3):
        self.branch_id = branch_id
        self.goal = goal
        self.safe_io = safe_io
        self.protected_files = set(protected_files)
        self.iterations = iterations
        self.max_corrections = max_corrections
        self.branch_task = BranchTask(goal)

    @cached_property
    def _api_docs_text(self) -> str:
        if not os.path.isdir('docs'):
            return ''
        return '\n\n'.join(
            f"# Documentation file: {os.path.join(root, f)}\n" + self.safe_io.read(os.path.join(root, f))
            for root, _, files in os.walk('docs') for f in sorted(files)
        )

    async def run(self, selected_files: List[str]) -> PlanAndCode:
        filtered = [fp for fp in selected_files if fp not in self.protected_files]
        codes = {}
        for fp in filtered:
            try:
                codes[fp] = self.safe_io.read(fp)
            except Exception as e:
                print(f"Branch-{self.branch_id}: Failed to read {fp}: {e}")
        if not codes:
            print(f"Branch-{self.branch_id}: No files to process after reading.")
            return PlanAndCode(reasoning="No readable files.", edits=[])

        syntax_errors = {}
        parsed = None
        api_docs = self._api_docs_text
        print(f"Branch-{self.branch_id}: Starting {self.iterations} iteration(s) for {len(codes)} files...")

        for i in range(self.iterations):
            print(f"Branch-{self.branch_id} Iteration-{i + 1}: Improving...")
            for attempt in range(1, self.max_corrections + 1):
                resp = await self.branch_task.execute(
                    files_contents=list(codes.items()),
                    syntax_errors={k: v for k, v in syntax_errors.items() if v} or None,
                    api_docs=api_docs,
                    protected_files=list(self.protected_files)
                )
                if not isinstance(resp, PlanAndCode):
                    print(f"Branch-{self.branch_id} Iteration-{i + 1} Correction-{attempt}: Invalid LLM response.")
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
                        msg = f"{se.msg} at line {se.lineno}, offset {se.offset}: {(se.text or '').strip()}"
                        syntax_errors[e.file_path] = msg
                        all_ok = False
                        print(f"Branch-{self.branch_id} Iteration-{i + 1} Correction-{attempt}: SyntaxError in `{e.file_path}`: {msg}")
                codes.update({e.file_path: e.code for e in filtered_edits})
                if all_ok:
                    print(f"Branch-{self.branch_id} Iteration-{i + 1} Correction-{attempt}: Syntax check passed.")
                    break
                if attempt == self.max_corrections:
                    print(f"Branch-{self.branch_id} Iteration-{i + 1}: Max corrections reached, moving to next iteration.")
                    break
                print(f"Branch-{self.branch_id} Iteration-{i + 1}: Retrying syntax fix (attempt {attempt + 1})...")

        print(f"Branch-{self.branch_id}: Completed all iterations.")
        unresolved = [fp for fp, err in syntax_errors.items() if err]
        if unresolved:
            print(f"Branch-{self.branch_id}: Finished with unresolved syntax errors in files: {unresolved}")
        return PlanAndCode(
            reasoning=parsed.reasoning if parsed else "",
            edits=[FileEdit(file_path=fp, code=code) for fp, code in codes.items()]
        )
