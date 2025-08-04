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

    def _construct_branch_prompt_input(self, goal, file_path, content):
        return [
            {"role": "system", "content": self.BRANCH_SYSTEM_PROMPT},
            {"role": "user", "content": f"""
**Goal:** {goal}

**File to improve:** `{file_path}`

**Current content:**
```python
{content}
```
"""},
        ]

    def _construct_integrator_prompt_input(self, goal, proposals):
        combined = f"**Original Goal:** {goal}\n---" + ''.join(
            f"\n\n**Branch ID: {p['id']}**\n**Reasoning:**\n{p['plan']}\n\n**Code:**\n```python\n{p['code']}\n```\n---" for p in proposals)
        return [
            {"role": "system", "content": self.INTEGRATOR_SYSTEM_PROMPT},
            {"role": "user", "content": combined},
        ]

    async def _run_branch(self, branch_id, goal, file_path, content, iterations=1):
        print(f"Branch-{branch_id}: Starting {iterations} iteration(s)...")
        for i in range(iterations):
            print(f"Branch-{branch_id} Iteration-{i+1}: Improving...")
            resp = await get_structured_completion(self._construct_branch_prompt_input(goal, file_path, content), PlanAndCode)
            parsed = resp.get("parsed_content") if resp else None
            if not isinstance(parsed, PlanAndCode):
                print(f"Branch-{branch_id} Iteration-{i+1}: Invalid LLM response.")
                return None
            try:
                ast.parse(parsed.code)
            except SyntaxError as e:
                print(f"Branch-{branch_id} Iteration-{i+1}: SyntaxError, discarding:\n{e}")
                return None
            print(f"Branch-{branch_id} Iteration-{i+1}: Syntax check passed. Tokens used: {resp['tokens']}")
            content = parsed.code
        print(f"Branch-{branch_id}: Completed all iterations.")
        return parsed

    async def run(self, goal, file_path, num_branches=3, iterations_per_branch=3):
        print(f"\n--- Starting improvement for '{file_path}' ---\nGoal: {goal}")
        try:
            original = self.safe_io.read(file_path)
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return

        results = await asyncio.gather(*[self._run_branch(i + 1, goal, file_path, original, iterations_per_branch) for i in range(num_branches)])

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
