import asyncio
import difflib
import ast
from typing import List
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
Each proposal includes a detailed reasoning (plan) and the resulting code.
Your objective is to identify, extract, and integrate the best improvements, innovations, and ideas from all proposals into a single, final improved code.
Provide a comprehensive reasoning explaining how you combined the proposals, explaining which parts you selected and why.
Return the full, final integrated code that best achieves the original goal.
'''

    def __init__(self, safe_io: SafeIO):
        self.safe_io = safe_io

    def _construct_branch_prompt_input(self, goal: str, file_path: str, file_content: str) -> List[dict]:
        return [
            {"role": "system", "content": self.BRANCH_SYSTEM_PROMPT},
            {"role": "user", "content": f"""
**Goal:** {goal}

**File to improve:** `{file_path}`

**Current content of `{file_path}`:**
```python
{file_content}
```
"""},
        ]

    def _construct_integrator_prompt_input(self, goal: str, proposals: List[dict]) -> List[dict]:
        user_content = f"**Original Goal:** {goal}\n---" + ''.join(
            f"\n\n**Branch ID: {p['id']}**\n**Reasoning:**\n{p['plan']}\n\n**Code:**\n```python\n{p['code']}\n```\n---" for p in proposals)
        return [
            {"role": "system", "content": self.INTEGRATOR_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

    async def _run_branch(self, branch_id: int, goal: str, file_path: str, content: str, iterations: int = 1) -> PlanAndCode | None:
        print(f"Branch-{branch_id}: Starting {iterations} iteration(s)...")
        plan_and_code = None
        for i in range(iterations):
            print(f"Branch-{branch_id} Iteration-{i+1}: Improving...")
            resp = await get_structured_completion(self._construct_branch_prompt_input(goal, file_path, content), PlanAndCode)
            parsed = resp and resp.get("parsed_content")
            if not isinstance(parsed, PlanAndCode):
                print(f"Branch-{branch_id} Iteration-{i+1}: Invalid LLM response.")
                return None

            # Stage 1 Syntax Validation: Validate generated code after each iteration and fail fast if syntax error
            try:
                ast.parse(parsed.code)
            except SyntaxError as e:
                print(f"Branch-{branch_id} Iteration-{i+1}: SyntaxError detected during stage 1 validation, discarding this attempt:\n{e}")
                return None

            print(f"Branch-{branch_id} Iteration-{i+1}: Syntax check passed.")
            print(f"Branch-{branch_id} Iteration-{i+1}: Done. Tokens used: {resp['tokens']}")
            content, plan_and_code = parsed.code, parsed
        print(f"Branch-{branch_id}: Completed all iterations.")
        return plan_and_code

    async def run(self, goal: str, file_path: str, num_branches: int = 3, iterations_per_branch: int = 3):
        print(f"\n--- Starting improvement for '{file_path}' ---\nGoal: {goal}")
        try:
            original = self.safe_io.read(file_path)
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return

        results = await asyncio.gather(*(
            self._run_branch(i + 1, goal, file_path, original, iterations_per_branch) for i in range(num_branches)
        ))

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
            integration = resp and resp.get("parsed_content")
            if not isinstance(integration, PlanAndCode):
                print("Integrator LLM failed. Aborting.")
                return

            # Stage 2 Syntax Validation: Validate integrated code before writing to disk
            try:
                ast.parse(integration.code)
            except SyntaxError as e:
                print(f"Integrated code SyntaxError detected during stage 2 validation, discarding integration result:\n{e}")
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
