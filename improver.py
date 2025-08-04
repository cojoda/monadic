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
        msg = f"**Goal:** {goal}\n\n**File to improve:** `{file_path}`\n\n**Current content:**\n```python\n{content}\n```"
        if syntax_error:
            msg += f"\n\nThe previous attempt resulted in a SyntaxError:\n```\n{syntax_error}\n```\nPlease fix the mistake and provide a corrected version following the same \"Plan-and-Execute\" strategy."
        return [{"role": "system", "content": self.BRANCH_SYSTEM_PROMPT}, {"role": "user", "content": msg}]

    def _construct_integrator_prompt_input(self, goal, proposals):
        combined = (
            f"**Original Goal:** {goal}\n---" +
            ''.join(f"\n\n**Branch ID: {p['id']}**\n**Reasoning:**\n{p['plan']}\n\n**Code:**\n```python\n{p['code']}\n```\n---" for p in proposals)
        )
        return [{"role": "system", "content": self.INTEGRATOR_SYSTEM_PROMPT}, {"role": "user", "content": combined}]

    async def _run_branch(self, branch_id, goal, file_path, content, iterations=3, max_corrections=3):
        print(f"Branch-{branch_id}: Starting {iterations} iteration(s)...")
        code, syntax_err, parsed = content, None, None

        for i in range(iterations):
            print(f"Branch-{branch_id} Iteration-{i+1}: Improving...")
            for attempt in range(1, max_corrections + 1):
                prompt = self._construct_branch_prompt_input(goal, file_path, code, syntax_err)
                resp = await get_structured_completion(prompt, PlanAndCode)
                parsed = resp.get("parsed_content") if resp else None
                if not isinstance(parsed, PlanAndCode):
                    print(f"Branch-{branch_id} Iteration-{i+1} Correction-{attempt}: Invalid LLM response.")
                    break
                try:
                    ast.parse(parsed.code)
                except SyntaxError as e:
                    syntax_err = f"{e.msg} at line {e.lineno}, offset {e.offset}: {(e.text.strip() if e.text else '')}".strip()
                    print(f"Branch-{branch_id} Iteration-{i+1} Correction-{attempt}: SyntaxError detected:\n{syntax_err}")
                    code = parsed.code
                    if attempt == max_corrections:
                        print(f"Branch-{branch_id} Iteration-{i+1}: Max corrections reached, moving to next iteration.")
                        break
                    print(f"Branch-{branch_id} Iteration-{i+1}: Retrying syntax fix (attempt {attempt + 1})...")
                else:
                    print(f"Branch-{branch_id} Iteration-{i+1} Correction-{attempt}: Syntax check passed. Tokens used: {resp.get('tokens', 'unknown')}")
                    code, syntax_err = parsed.code, None
                    break
        print(f"Branch-{branch_id}: Completed all iterations.")
        if syntax_err:
            print(f"Branch-{branch_id}: Finished with unresolved syntax errors, returning latest result.")
        return PlanAndCode(reasoning=(parsed.reasoning if parsed else ""), code=code)

    async def run(self, goal, file_path, num_branches=3, iterations_per_branch=3):
        print(f"\n--- Starting improvement for '{file_path}' ---\nGoal: {goal}")
        try:
            original = self.safe_io.read(file_path)
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return

        tasks = [self._run_branch(i + 1, goal, file_path, original, iterations_per_branch) for i in range(num_branches)]
        results = await asyncio.gather(*tasks)

        proposals = [{"id": i + 1, "plan": r.reasoning, "code": r.code} for i, r in enumerate(results) if r]
        if not proposals:
            print("\nResult: No successful proposals.")
            return

        if len(proposals) == 1:
            print("\nSingle successful branch. Using its result.")
            final_reasoning, final_code = proposals[0]["plan"], proposals[0]["code"]
        else:
            print("Multiple successful branches, integrating...")
            resp = await get_structured_completion(self._construct_integrator_prompt_input(goal, proposals), PlanAndCode)
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
