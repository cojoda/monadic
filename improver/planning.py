from pydantic import BaseModel
from typing import List, Dict, Any

from .core import LLMTask


class ScaffoldingPlan(BaseModel):
    reasoning: str
    existing_files_to_edit: List[str]
    new_files_to_create: List[str]


class PlanningAndScaffoldingTask(LLMTask):
    response_model = ScaffoldingPlan

    system_prompt = (
        "You are an expert software architect tasked with analyzing the user's goal and the project's file tree. "
        "Your output must be a JSON object matching the ScaffoldingPlan schema. "
        "First, provide a clear, step-by-step reasoning plan in the 'reasoning' field describing how to accomplish the user's goal. "
        "Second, identify and list all existing project files that will need to be read or edited in 'existing_files_to_edit'. "
        "Third, crucially list all new files (new modules, test files, scaffolding files) that must be created from scratch in 'new_files_to_create' to fulfill the goal."
    )

    # THIS IS THE MISSING METHOD THAT NEEDS TO BE ADDED
    def construct_prompt(self, file_tree: List[str], **kwargs: Any) -> List[Dict[str, str]]:
        """Constructs the prompt for the planning and scaffolding task."""
        prompt_lines = [
            "Based on the following user goal and project file tree, create a ScaffoldingPlan.",
            f"\n**Goal:**\n{self.goal}",
            "\n**Project File Tree:**",
            *file_tree,
            "\nYour response must be a single JSON object matching the ScaffoldingPlan schema with no extra commentary."
        ]
        
        user_prompt = "\n".join(prompt_lines)
        
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt}
        ]