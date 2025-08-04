import asyncio
import difflib
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
            f"\n\n**Branch ID: {p['id']}**\n**Reasoning:**\n{p['plan']}\n\n**Code:**\n```python\n{p['code']}\n```\n---" for p in proposals
        )
        return [
            {"role": "system", "content": self.INTEGRATOR_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

    async def _run_branch(self, branch_id: int, goal: str, file_path: str, original_content: str) -> PlanAndCode | None:
        print(f"Branch-{branch_id}: Starting...")
        prompt_input = self._construct_branch_prompt_input(goal, file_path, original_content)
        response = await get_structured_completion(prompt_input, PlanAndCode)
        if parsed := response.get("parsed_content") if response else None:
            if isinstance(parsed, PlanAndCode):
                print(f"Branch-{branch_id}: Finished. Tokens used: {response['tokens']}")
                return parsed
        print(f"Branch-{branch_id}: Failed to get a valid structured response from LLM.")
        return None

    async def run(self, goal: str, file_path: str, num_branches: int = 3):
        print(f"\n--- Starting improvement run for '{file_path}' ---\nGoal: {goal}")
        try:
            original_content = self.safe_io.read(file_path)
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return

        results = await asyncio.gather(*(self._run_branch(i + 1, goal, file_path, original_content) for i in range(num_branches)))
        successful = [
            {"id": i + 1, "plan": r.reasoning, "code": r.code}
            for i, r in enumerate(results) if r
        ]

        if not successful:
            print("\nResult: No successful proposals to integrate.")
            return

        if len(successful) == 1:
            print("\nOnly one successful branch. Applying its changes directly.")
            final_reasoning, final_code = successful[0]["plan"], successful[0]["code"]
        else:
            print("Multiple successful branches detected. Integrating proposals...")
            response = await get_structured_completion(
                self._construct_integrator_prompt_input(goal, successful), PlanAndCode
            )
            integration = response.get("parsed_content") if response else None
            if not isinstance(integration, PlanAndCode):
                print("Integrator LLM failed to produce a valid integrated solution. Aborting.")
                return
            print(f"\nIntegration reasoning:\n{integration.reasoning}")
            final_reasoning, final_code = integration.reasoning, integration.code

        if not list(difflib.unified_diff(original_content.splitlines(), final_code.splitlines())):
            print("\nResult: Integrated proposal resulted in no changes to the code.")
            return

        print("\nApplying integrated changes...")
        try:
            self.safe_io.write(file_path, final_code)
        except PermissionError as e:
            print(f"Integration failed: {e}")
            return

        print(f"--- Improvement run for '{file_path}' finished ---")
