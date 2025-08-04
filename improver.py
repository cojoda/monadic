import asyncio
import difflib
from typing import List, Dict, Optional
from pydantic import BaseModel

from safe_io import SafeIO
from llm_provider import get_structured_completion


class PlanAndCode(BaseModel):
    '''A Pydantic model to structure the LLM's output for code generation.'''
    reasoning: str
    code: str

class IntegratorChoice(BaseModel):
    '''A Pydantic model to structure the LLM's decision for integration.'''
    best_branch_id: int
    justification: str


class Improver:
    '''
    The core engine for iterative code improvement. It manages parallel branches
    of thought, evaluates their proposals, and integrates the best one.
    '''
    def __init__(self, safe_io: SafeIO):
        self.safe_io = safe_io

    def _construct_branch_prompt_input(self, goal: str, file_path: str, file_content: str) -> List[Dict[str, str]]:
        """Builds the prompt input for the new Responses API."""
        system_prompt = """
You are an expert Python programmer. Your task is to rewrite a given file to achieve a specific goal.
You must follow a "Plan-and-Execute" strategy.
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
        '''Builds the prompt for the integrator LLM call.'''
        system_prompt = '''
    You are a senior software architect. Your task is to review several proposed code changes and select the best one.
    Analyze the provided goal and the different proposals from each branch. Each proposal includes the reasoning (plan) and the resulting code.
    Choose the proposal that most effectively and correctly achieves the goal.
    You must provide the ID of the winning branch and a justification for your choice.
    '''

        user_prompt = f"**Original Goal:** {goal}\n\n---"
        
        for p in proposals:
            user_prompt += f"\n\n**Branch ID: {p['id']}**\n"
            user_prompt += f"**Reasoning:**\n{p['plan']}\n\n"
            user_prompt += f"**Code:**\n```python\n{p['code']}\n```\n---"

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

    async def _run_branch(self, branch_id: int, goal: str, file_path: str, original_content: str) -> Optional[PlanAndCode]:
        '''Runs a single improvement branch using structured outputs.'''
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
        '''Orchestrates the improvement process for a single file.'''
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

        # --- New Integrator Logic ---
        print("\n--- Integration Phase ---")
        
        successful_proposals = []
        for i, result in enumerate(branch_results):
            if result:
                successful_proposals.append({
                    "id": i + 1,
                    "plan": result.reasoning,
                    "code": result.code
                })
        
        if not successful_proposals:
            print("\nResult: No successful proposals to integrate.")
            return

        if len(successful_proposals) == 1:
            print("\nOnly one successful branch. Applying its changes directly.")
            best_proposal_code = successful_proposals[0]['code']
        else:
            print("Multiple successful branches. Asking LLM architect to choose the best...")
            integrator_prompt = self._construct_integrator_prompt_input(goal, successful_proposals)
            integrator_response = await get_structured_completion(integrator_prompt, IntegratorChoice)
            
            choice = integrator_response.get("parsed_content")
            if not isinstance(choice, IntegratorChoice):
                print("Integrator LLM failed to make a valid choice. Aborting.")
                return

            print(f"\nIntegrator Choice: Branch {choice.best_branch_id}")
            print(f"Justification: {choice.justification}")
            
            winner_id = choice.best_branch_id
            try:
                # Find the winning proposal dict by its id
                winning_proposal_dict = next(p for p in successful_proposals if p['id'] == winner_id)
                best_proposal_code = winning_proposal_dict['code']
            except StopIteration:
                print(f"Error: Integrator chose a non-existent branch ID {winner_id}. Aborting.")
                return
        
        # Check if the chosen code is actually different
        diff_score = len(list(difflib.unified_diff(original_content.splitlines(), best_proposal_code.splitlines())))
        if diff_score == 0:
            print("\nResult: Winning proposal resulted in no changes to the code.")
            return

        print("\nApplying changes from the winning branch...")
        try:
            self.safe_io.write(file_path, best_proposal_code)
        except PermissionError as e:
            print(f"Integration failed: {e}")

        print(f"--- Improvement run for '{file_path}' finished ---")
