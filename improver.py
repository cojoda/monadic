import asyncio
import ast
from pydantic import BaseModel

from safe_io import SafeIO
from llm_provider import get_structured_completion

class PlanAndCode(BaseModel):
    reasoning: str
    code: str

class Improver:
    BRANCH_SYSTEM_PROMPT = '''
You are an expert Python programmer. Your task is to rewrite a given file to achieve a specific goal.
You must follow a "Plan-and-Execute" strategy.
First, create a concise, step-by-step plan in the 'reasoning' field.
Second, provide the new, complete source code for the file in the 'code' field, based on your plan.
'''

    INTEGRATOR_SYSTEM_PROMPT = '''
You are a senior software architect expert in Python code improvement.
Your task is to carefully review multiple proposed code revisions for the same goal.
Each proposal includes reasoning and resulting code.
Your objective is to integrate the best improvements into a final version.
Provide reasoning explaining your choices and return the final code.
'''

    def __init__(self, safe_io: SafeIO):
        self.safe_io = safe_io

    def _construct_branch_prompt_input(self, goal, file_path, content, syntax_error=None):
        base_content = f"""
**Goal:** {goal}

**File to improve:** `{file_path}`

**Current content:**
```python
{content}
```
"""
        if syntax_error:
            # Add detailed feedback about the syntax error including line and offset info
            base_content += f"""

The previous attempt resulted in a SyntaxError:
```
{syntax_error}
```
Please fix the mistake and provide a corrected version following the same "Plan-and-Execute" strategy.
"""

        return [
            {"role": "system", "content": self.BRANCH_SYSTEM_PROMPT},
            {"role": "user", "content": base_content},
        ]

    def _construct_integrator_prompt_input(self, goal, proposals):
        combined = f"**Original Goal:** {goal}\n---" + ''.join(
            f"\n\n**Branch ID: {p['id']}**\n**Reasoning:**\n{p['plan']}\n\n**Code:**\n```python\n{p['code']}\n```\n---" for p in proposals)
        return [
            {"role": "system", "content": self.INTEGRATOR_SYSTEM_PROMPT},
            {"role": "user", "content": combined},
        ]

    async def _run_branch(self, branch_id, goal, file_path, content, iterations=3, max_corrections_per_iteration=3):
        print(f"Branch-{branch_id}: Starting {iterations} iteration(s)...")
        current_content = content
        syntax_error = None
        parsed = None
        for i in range(iterations):
            print(f"Branch-{branch_id} Iteration-{i+1}: Improving...")
            correction_attempt = 0
            while correction_attempt < max_corrections_per_iteration:
                correction_attempt += 1

                # Construct prompt including syntax error if any to enable self-correction
                prompt_input = self._construct_branch_prompt_input(goal, file_path, current_content, syntax_error)
                resp = await get_structured_completion(prompt_input, PlanAndCode)
                parsed = resp.get("parsed_content") if resp else None

                if not isinstance(parsed, PlanAndCode):
                    print(f"Branch-{branch_id} Iteration-{i+1} Correction-{correction_attempt}: Invalid LLM response.")
                    # Break correction loop; do not discard attempt
                    break

                try:
                    ast.parse(parsed.code)
                except SyntaxError as e:
                    # Compose a detailed syntax error message including line, offset, and context
                    syntax_error_msg = f"{e.msg} at line {e.lineno}, offset {e.offset}: {e.text.strip() if e.text else ''}".strip()
                    print(f"Branch-{branch_id} Iteration-{i+1} Correction-{correction_attempt}: SyntaxError detected:\n{syntax_error_msg}")
                    # Keep the syntax error to feed back for correction
                    syntax_error = syntax_error_msg
                    # Retain the latest code even if it has a syntax error
                    current_content = parsed.code
                    if correction_attempt == max_corrections_per_iteration:
                        print(f"Branch-{branch_id} Iteration-{i+1}: Max corrections reached, moving to next iteration with latest code and error.")
                        break  # Proceed to next iteration
                    else:
                        print(f"Branch-{branch_id} Iteration-{i+1}: Retrying to fix syntax error (attempt {correction_attempt + 1})...")
                        continue  # Retry correction loop feeding syntax error back
                else:
                    # Successfully parsed code: clear syntax error state and update code
                    print(f"Branch-{branch_id} Iteration-{i+1} Correction-{correction_attempt}: Syntax check passed. Tokens used: {resp.get('tokens', 'unknown')}")
                    current_content = parsed.code
                    syntax_error = None
                    break  # Success, move to next iteration

        print(f"Branch-{branch_id}: Completed all iterations.")
        if syntax_error is not None:
            print(f"Branch-{branch_id}: Finished with unresolved syntax errors, but returning latest result.")
        return PlanAndCode(reasoning=parsed.reasoning if parsed else "", code=current_content)

    async def run(self, goal, file_path, num_branches=3, iterations_per_branch=3):
        print(f"\n--- Starting improvement for '{file_path}' ---\nGoal: {goal}")
        try:
            original = self.safe_io.read(file_path)
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return

        tasks = [self._run_branch(i + 1, goal, file_path, original, iterations_per_branch) for i in range(num_branches)]
        results = await asyncio.gather(*tasks)

        successes = [
            {"id": i + 1, "plan": r.reasoning, "code": r.code}
            for i, r in enumerate(results) if r
        ]

        if not successes:
            print("\nResult: No successful proposals.")
            return

        if len(successes) == 1:
            print("\nSingle successful branch. Using its result.")
            final_reasoning, final_code = successes[0]["plan"], successes[0]["code"]
        else:
            print("Multiple successful branches, integrating...")
            resp = await get_structured_completion(self._construct_integrator_prompt_input(goal, successes), PlanAndCode)
            integration = resp.get("parsed_content") if resp else None
            if not isinstance(integration, PlanAndCode):
                print("Integrator LLM failed. Aborting.")
                return
            try:
                ast.parse(integration.code)
            except SyntaxError as e:
                print(f"Integrated code SyntaxError, discarding result:\n{e}")
                return
            print(f"\nIntegration reasoning:\n{integration.reasoning}")
            final_reasoning, final_code = integration.reasoning, integration.code

        if original == final_code:
            print("\nResult: No changes detected after integration.")
            return

        print("\nApplying integrated changes...")
        try:
            self.safe_io.write(file_path, final_code)
        except PermissionError as e:
            print(f"Failed to write changes: {e}")
            return

        print(f"--- Finished improvement for '{file_path}' ---")
