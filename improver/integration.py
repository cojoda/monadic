# improver/integration.py
import ast
from typing import List, Dict, Any

from .core import LLMTask
from .models import PlanAndCode, FileEdit
from safe_io import SafeIO

class IntegratorTask(LLMTask):
    system_prompt = (
        'You are a senior software architect expert in Python code improvement.'
        ' Your task is to carefully review multiple proposed code revisions for the same goal.'
        ' Each proposal may have different file structures and may include newly created files.'
        ' Your objective is to choose the best architectural approach among these proposals and integrate the best improvements into a final version.'
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
            # The 'edits' here are FileEdit objects
            for edit in p['edits']:
                lines.extend([f"\nFile: `{edit.file_path}`", '```python', edit.code, '```'])
        return [{"role": "system", "content": self.system_prompt}, {"role": "user", "content": "\n".join(lines)}]

class IntegrationRunner:
    def __init__(self, goal: str, safe_io: SafeIO):
        self.goal = goal
        self.safe_io = safe_io # Note: This parameter is unused.
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

        # Validate only Python files (.py). Use a helper that accepts file_path and code
        for e in integration.edits:
            # Support both attribute-style FileEdit objects and dict-like edits
            file_path = getattr(e, 'file_path', None)
            if file_path is None and isinstance(e, dict):
                file_path = e.get('file_path')
            code = getattr(e, 'code', None)
            if code is None and isinstance(e, dict):
                code = e.get('code', '')

            err = self._try_parse_code(file_path, code)
            if err:
                print(f"Integrated code SyntaxError detected in {file_path or '<unknown>'}: {err}")
                return None

        print(f"\nIntegration reasoning:\n{integration.reasoning}")
        return integration

    @staticmethod
    def _try_parse_code(file_path: Any, code: Any):
        """
        Attempt to parse code only if the file path indicates a Python file (.py).
        Returns the SyntaxError instance if parsing fails, otherwise None. Non-.py files
        are skipped and treated as having no syntax errors.
        """
        # Normalize types and guard against None
        if not isinstance(file_path, str) or not file_path.lower().endswith('.py'):
            # Skip syntax checking for non-python files
            return None

        try:
            # Provide the filename to ast.parse for clearer error locations
            ast.parse(code or '', filename=file_path)
        except SyntaxError as e:
            return e
        return None
