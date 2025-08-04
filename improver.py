import asyncio
import os
from functools import cached_property
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
        ' First, create a concise, step-by-step plan in the "reasoning" field.'
        ' Second, provide the new, complete source codes for the files in the "edits" list, each with "file_path" and its updated "code", based on your plan.'
    )

    response_model = PlanAndCode

    def construct_prompt(self, files_contents: List, syntax_errors: Dict[str, str]=None, api_docs: str='', protected_files: List[str]=[]) -> List[Dict[str, str]]:
        file_paths = {fp for fp, _ in files_contents}
        msg = [f'**Goal:** {self.goal}']
        if 'llm_provider.py' in file_paths - set(protected_files) and api_docs.strip():
            msg.append(f'\n**Context:**\n\n{api_docs}')
        for fp, content in files_contents:
            msg.extend([f'\n**File to improve:** `{fp}`\n', '```python', content, '```'])
            if syntax_errors and syntax_errors.get(fp):
                err = syntax_errors[fp].replace('```', '` ` `') if syntax_errors[fp] else ''
                msg.extend([f'\nThe previous attempt for `{fp}` resulted in a SyntaxError:', '```', err, '```'])
        return [{"role": "system", "content": self.system_prompt}, {"role": "user", "content": "\n".join(msg)}]

class FileSelectionResponse(BaseModel):
    selected_files: List[str]

class FileSelectionTask(LLMTask):
    system_prompt = (
        'You are an expert Python programmer tasked with selecting files relevant to a specified goal from a provided file tree.'
        ' You must strictly NOT select any protected files listed.'
        ' Respond with a JSON object with key "selected_files" containing an array of file paths.'
        ' Respond ONLY with the JSON object, no extra text.'
    )

    response_model = FileSelectionResponse

    def construct_prompt(self, file_tree: List[str], protected_files: List[str]) -> List[Dict[str, str]]:
        prompt_lines = [
            f'**Goal:** {self.goal}',
            '\nYou have the following project file tree (one file path per line):',
            *file_tree,
            '\nThe following files are PROTECTED and must NOT be selected:',
            *protected_files,
            '\nBased on the goal, select only relevant files not listed as protected.'
            ' Respond ONLY with a JSON object with key ' + "'selected_files'" + ' listing file paths.'
        ]
        return [{"role": "system", "content": self.system_prompt}, {"role": "user", "content": "\n".join(prompt_lines)}]

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
        lines = [f'**Original Goal:** {self.goal}\n---']
        for p in proposals:
            lines.extend(["---",
                          f"\n**Branch ID: {p['id']}**",
                          f"**Reasoning:**\n{p['plan']}",
                          "\n**Code Edits:**"])
            for edit in p['edits']:
                lines.extend([f"\nFile: `{edit.file_path}`", '```python', edit.code, '```'])
        return [{"role": "system", "content": self.system_prompt}, {"role": "user", "content": "\n".join(lines)}]

class BranchRunner:
    def __init__(self, goal: str, safe_io: SafeIO, protected_files: List[str], branch_id: int, iterations: int=3, max_corrections: int=3):
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
        parts = []
        for root, _, files in os.walk('docs'):
            for f in sorted(files):
                path = os.path.join(root, f)
                parts.append(f"# Documentation file: {path}\n" + self.safe_io.read(path))
        return '\n\n'.join(parts)

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
            print(f"Branch-{self.branch_id} Iteration-{i+1}: Improving...")
            for attempt in range(1, self.max_corrections + 1):
                resp = await self.branch_task.execute(
                    files_contents=list(codes.items()),
                    syntax_errors={k: v for k, v in syntax_errors.items() if v} or None,
                    api_docs=api_docs,
                    protected_files=list(self.protected_files)
                )
                if not isinstance(resp, PlanAndCode):
                    print(f"Branch-{self.branch_id} Iteration-{i+1} Correction-{attempt}: Invalid LLM response.")
                    break
                parsed = resp
                syntax_errors.clear()
                filtered_edits = [e for e in parsed.edits if e.file_path not in self.protected_files]
                all_ok = True
                import ast
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

        import ast
        if any(self._try_parse_code(e.code) for e in integration.edits):
            print("Integrated code SyntaxError detected, discarding result.")
            return None

        print(f"\nIntegration reasoning:\n{integration.reasoning}")
        return integration

    @staticmethod
    def _try_parse_code(code: str):
        try:
            import ast
            ast.parse(code)
        except SyntaxError as e:
            return e
        return None

class Improver:
    def __init__(self, safe_io: SafeIO):
        self.safe_io = safe_io
        self._protected_files = set()
        try:
            content = safe_io.read('protected.yaml')
            if content:
                import yaml
                loaded = yaml.safe_load(content)
                if isinstance(loaded, list):
                    self._protected_files = set(loaded)
        except Exception:
            pass

    def _scan_project_files(self) -> List[str]:
        files = [os.path.join(root if root != '.' else '', f)
                 for root, _, fnames in os.walk('.')
                 if not any(p.startswith('.') for p in os.path.relpath(root, '.').split(os.sep))
                 for f in fnames if not f.startswith('.')]
        files.sort()
        return files

    async def run(self, goal, num_branches=3, iterations_per_branch=3):
        print(f"\nStarting workspace-aware improvement with goal: {goal}")

        file_tree = self._scan_project_files()
        if not file_tree:
            print("No files found in project directory.")
            return

        selected_resp = await FileSelectionTask(goal).execute(file_tree=file_tree, protected_files=sorted(self._protected_files))
        selected_files = [f for f in (getattr(selected_resp, 'selected_files', []) or []) if f not in self._protected_files]

        if not selected_files:
            print("No files to improve after filtering protected files.")
            return

        print(f"Selected files for improvement (excluding protected): {selected_files}")
        print(f"\n--- Starting multi-file improvement for files: {selected_files} ---\nGoal: {goal}")

        runners = [BranchRunner(goal, self.safe_io, list(self._protected_files), i+1, iterations_per_branch).run(selected_files) for i in range(num_branches)]
        results = await asyncio.gather(*runners)

        proposals = [dict(id=i+1, plan=r.reasoning, edits=r.edits) for i, r in enumerate(results) if r]
        if not proposals:
            print("\nResult: No successful proposals.")
            return

        integration = await IntegrationRunner(goal, self.safe_io).run(proposals)
        if not integration:
            print("\nResult: No integration result available.")
            return

        try:
            original = {fp: self.safe_io.read(fp) for fp in selected_files}
        except Exception as e:
            print(f"Failed to read original files before applying changes: {e}")
            return

        if not any(original.get(e.file_path) != e.code for e in integration.edits if e.file_path not in self._protected_files):
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

        print(f"--- Finished multi-file improvement for files: {selected_files} ---")
