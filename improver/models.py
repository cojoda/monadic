from typing import List, Optional
from pydantic import BaseModel, validator, Field

class FileEdit(BaseModel):
    file_path: str
    code: str

class PlanAndCode(BaseModel):
    reasoning: str
    edits: List[FileEdit]

    @validator('edits')
    def edits_not_empty(cls, v):
        if not v:
            raise ValueError('edits must not be empty')
        return v

class FileSelectionResponse(BaseModel):
    selected_files: List[str]

class ScaffoldingPlan(BaseModel):
    # Use a mutable-default-safe field for steps
    steps: List[str] = Field(default_factory=list)

class WorkflowContext(BaseModel):
    # Centralized state for the workflow
    goal: str
    file_tree: List[str]
    # Initialize with an empty scaffolding plan by default to represent an empty scaffold
    scaffolding_plan: Optional[ScaffoldingPlan] = Field(default_factory=lambda: ScaffoldingPlan())
