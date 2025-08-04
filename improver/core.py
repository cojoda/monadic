# improver/core.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Type
from pydantic import BaseModel

from llm_provider import get_structured_completion

class LLMTask(ABC):
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        pass

    @property
    @abstractmethod
    def response_model(self) -> Type[BaseModel]:
        pass

    def __init__(self, goal: str):
        self.goal = goal

    @abstractmethod
    def construct_prompt(self, **kwargs: Any) -> List[Dict[str, str]]:
        pass

    async def execute(self, **kwargs: Any) -> Any:
        prompt = self.construct_prompt(**kwargs)
        resp = await get_structured_completion(prompt, self.response_model)
        return resp.get('parsed_content') if resp else None