# improver/models.py
from typing import List
from pydantic import BaseModel, validator

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