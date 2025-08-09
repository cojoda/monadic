from typing import List, Optional, Any, Dict
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
    steps: List[str] = Field(default_factory=list)

class WorkflowContext(BaseModel):
    # Centralized state for the workflow
    goal: str
    file_tree: List[str]
    # Relax the type to allow storing arbitrary planning results (PlanningScaffoldingPlan, etc.)
    scaffolding_plan: Optional[Any] = None
    # New field: store per-branch proposals/results as a list of dictionaries
    branch_proposals: List[Dict[str, Any]] = Field(default_factory=list)
