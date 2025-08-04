import asyncio
import difflib
from typing import List, Dict, Optional
from pydantic import BaseModel

from safe_io import SafeIO
from llm_provider import get_structured_completion


class PlanAndCode(BaseModel):
    """A Pydantic model to structure the LLM's output for code generation."""
    reasoning: str
    code: str


class IntegrationResult(BaseModel):
    """A Pydantic model to structure the integrator's combined solution."""
    reasoning: str  # explanation of integration decision
    code: str       # the final integrated code


class Improver:
    """
    The core engine for iterative code improvement. It manages parallel branches
    of thought, evaluates their proposals, and integrates the best parts into a final solution.
    """

    def __init__(self, safe_io: SafeIO):
        self.safe_io = safe_io

    def _construct_branch_prompt_input(self, goal: str, file_path: str, file_content: str) -> List[Dict[str, str]]:
        """Builds the prompt input for the new Responses API."""
        system_prompt = """
You are an expert Python programmer. Your task is to rewrite a given file to achieve a specific goal.
You must follow a \"Plan-and-Execute\" strategy.
First, create a concise, step-by-step plan in the 'reasoning' field.
Second, provide the new, complete source code for the file in the 'code' field, based on your plan.
"""
        user_prompt = f"""
**Goal:** {goal}

**File to improve:** `{file_path}`

**Current content of `{file_path}`:**
```python
{file_content}
```

"""
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

    def _construct_integrator_prompt_input(self, goal: str, proposals: List[Dict]) -> List[Dict[str, str]]:
        """Builds the prompt for the integrator LLM call to integrate best parts from proposals."""
        system_prompt = '''
You are a senior software architect expert in Python code improvement.
Your task is to carefully review multiple proposed code revisions for the same goal.
Each proposal includes a detailed reasoning (plan) and the resulting code.

Your objective is to identify, extract, and integrate the best improvements, innovations, and ideas from all proposals into a single, final improved code.
Provide a comprehensive reasoning explaining how you combined the proposals,
explaining which parts you selected and why.

Return the full, final integrated code that best achieves the original goal.
'''

        user_prompt = f"""**Original Goal:** {goal}

---"""
        for p in proposals:
            user_prompt += f"\n\n**Branch ID: {p['id']}**\n"
            user_prompt += f"**Reasoning:**\n{p['plan']}\n\n"
            user_prompt += f"**Code:**\n```python\n{p['code']}\n```\n---"

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

    async def _run_branch(self, branch_id: int, goal: str, file_path: str, original_content: str) -> Optional[PlanAndCode]:
        """Runs a single improvement branch using structured outputs."""
        print(f"Branch-{branch_id}: Starting...")
        prompt_input = self._construct_branch_prompt_input(goal, file_path, original_content)
        response = await get_structured_completion(prompt_input, PlanAndCode)

        if response and isinstance(response.get("parsed_content"), PlanAndCode):
            print(f"Branch-{branch_id}: Finished. Tokens used: {response['tokens']}")
            return response["parsed_content"]
        else:
            print(f"Branch-{branch_id}: Failed to get a valid structured response from LLM.")
            return None

    async def run(self, goal: str, file_path: str, num_branches: int = 3):
        """Orchestrates the improvement process for a single file."""
        print(f"\n--- Starting improvement run for '{file_path}' ---")
        print(f"Goal: {goal}")

        try:
            original_content = self.safe_io.read(file_path)
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return

        tasks = [
            self._run_branch(i + 1, goal, file_path, original_content)
            for i in range(num_branches)
        ]
        branch_results: List[Optional[PlanAndCode]] = await asyncio.gather(*tasks)

        # --- Integration Phase ---
        print("\n--- Integration Phase ---")

        successful_proposals = [{
            "id": i + 1,
            "plan": result.reasoning,
            "code": result.code
        } for i, result in enumerate(branch_results) if result]

        if not successful_proposals:
            print("\nResult: No successful proposals to integrate.")
            return
        elif len(successful_proposals) == 1:
            final_reasoning = successful_proposals[0]['plan']
            final_code = successful_proposals[0]['code']
            print("\nOnly one successful branch. Applying its changes directly.")
        else:
            print("Multiple successful branches detected.")
            print("Integrating the best parts from all proposals to form the final solution...")
            integrator_prompt = self._construct_integrator_prompt_input(goal, successful_proposals)
            integrator_response = await get_structured_completion(integrator_prompt, IntegrationResult)

            integration_result = integrator_response.get("parsed_content") if integrator_response else None
            if not isinstance(integration_result, IntegrationResult):
                print("Integrator LLM failed to produce a valid integrated solution. Aborting.")
                return

            print(f"\nIntegration reasoning:\n{integration_result.reasoning}")
            final_reasoning = integration_result.reasoning
            final_code = integration_result.code

        # Check if the final integrated code is different from original
        diff = list(difflib.unified_diff(original_content.splitlines(), final_code.splitlines()))
        if not diff:
            print("\nResult: Integrated proposal resulted in no changes to the code.")
            return

        print("\nApplying integrated changes...")
        try:
            self.safe_io.write(file_path, final_code)
        except PermissionError as e:
            print(f"Integration failed: {e}")
            return

        print(f"--- Improvement run for '{file_path}' finished ---")
