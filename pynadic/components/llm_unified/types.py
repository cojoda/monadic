from typing import Any, Dict, Optional
from pydantic import BaseModel


class LLMOutput(BaseModel):
    """A minimal base schema for LLM structured outputs.

    Tests can subclass with their own fields as needed.
    """
    data: Optional[Dict[str, Any]] = None
    text: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
