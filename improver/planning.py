from pydantic import BaseModel
from typing import List

from llm_provider import LLMTask


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
