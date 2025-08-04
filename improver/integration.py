# improver/integration.py
import ast
from typing import List, Dict, Any

from .core import LLMTask
from .models import PlanAndCode, FileEdit  # CORRECTED: Added FileEdit import
from safe_io import SafeIO

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