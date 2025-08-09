# improver/integration.py
import ast
from typing import List, Dict, Any, Optional

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

    def construct_prompt(self, proposals: List[Dict], error_context: Optional[str] = None) -> List[Dict[str, str]]:
        """Construct the prompt for the integration task.

        Args:
            proposals: List of proposals, each containing an 'id', 'plan', and 'edits'.
            error_context: Optional string describing errors from a previous attempt. If provided,
                           it should guide the LLM to fix the noted issues in the next integration.
        """
        lines = [f'**Original Goal:** {self.goal}\n---']
        for p in proposals:
            lines.extend(["---",
                          f"\n**Branch ID: {p['id'] }**",
                          f"**Reasoning:**\n{p['plan']}",
                          "\n**Code Edits:"])
            # The 'edits' here are FileEdit objects or dicts with file_path/code.
            for edit in p['edits']:
                if isinstance(edit, dict):
                    file_path = edit.get('file_path')
                    code = edit.get('code', '')
                else:
                    file_path = getattr(edit, 'file_path', None)
                    code = getattr(edit, 'code', '')
                lines.extend([f"\nFile: `{file_path}`", '```python', code, '```'])
        if error_context:
            lines.extend([
                "",
                "**Error Context / Previous Attempt Issues:**",
                error_context,
                "",
                "Please fix the syntax error in the next integration attempt."
            ])
        return [{"role": "system", "content": self.system_prompt}, {"role": "user", "content": "\n".join(lines)}]

class IntegrationRunner:
    def __init__(self, goal: str, safe_io: SafeIO):
        self.goal = goal
        self.safe_io = safe_io  # Note: This parameter is unused.
        self.integrator_task = IntegratorTask(goal)

    async def run(self, proposals: List[Dict]) -> Any:
        if not proposals:
            print("\nResult: No successful proposals.")
            return None
        if len(proposals) == 1:
            print("\nSingle successful branch. Using its result.")
            return PlanAndCode(reasoning=proposals[0]['plan'], edits=proposals[0]['edits'])

        print("Multiple successful branches, integrating...")

        max_retries = 2
        error_context: Optional[str] = None

        for attempt in range(max_retries + 1):
            if attempt == 0:
                print("Integrator attempt 1 with no prior error context.")
            else:
                print(f"Integrator attempt {attempt + 1} with error_context provided.")

            integration = await self.integrator_task.execute(proposals=proposals, error_context=error_context)
            if not isinstance(integration, PlanAndCode):
                print("Integrator LLM failed. Aborting." if attempt == max_retries else "Integrator LLM failed. Will retry with error context if available.")
                if attempt < max_retries:
                    continue
                else:
                    return None

            # Validate only Python files (.py). Skip syntax checking for non-.py files.
            syntax_error_found = False
            detected_err: Optional[SyntaxError] = None
            detected_file: Optional[str] = None
            for e in integration.edits:
                # Support both attribute-style FileEdit objects and dict-like edits
                file_path = getattr(e, 'file_path', None)
                if isinstance(e, dict):
                    file_path = e.get('file_path', file_path)
                code = getattr(e, 'code', None)
                if isinstance(e, dict):
                    code = e.get('code', code)

                # Only attempt to parse files that have a string file_path ending with .py
                if not (isinstance(file_path, str) and file_path.lower().endswith('.py')):
                    continue

                err = self._try_parse_code(file_path, code)
                if err:
                    syntax_error_found = True
                    detected_err = err
                    detected_file = file_path
                    break

            if syntax_error_found and detected_err is not None:
                # Build error context from the SyntaxError
                err = detected_err
                err_desc = getattr(err, 'msg', str(err))
                lineno = getattr(err, 'lineno', None)
                if lineno is not None:
                    err_desc = f"{err_desc} (line {lineno})"
                error_context = f"SyntaxError in {detected_file}: {err_desc}"
                print(f"Integrated code SyntaxError detected in {detected_file}: {err_desc}")
                if attempt < max_retries:
                    # Retry with updated error_context
                    continue
                else:
                    print("Maximum retries reached. Aborting.")
                    return None

            # No syntax errors detected; integration successful
            print(f"\nIntegration reasoning:\n{integration.reasoning}")
            return integration

        # If somehow the loop exits without returning, abort safely
        return None

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
