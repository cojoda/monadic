from abc import ABC, abstractmethod
from typing import List, Dict, Any, Type
from pydantic import BaseModel

from llm_provider import get_structured_completion

class LLMTask(ABC):
    def __init__(self, goal: str):
        self.goal = goal

    @property
    @abstractmethod
    def system_prompt(self) -> str: ...

    @property
    @abstractmethod
    def response_model(self) -> Type[BaseModel]: ...

    @abstractmethod
    def construct_prompt(self, **kwargs: Any) -> List[Dict[str, str]]: ...

    async def execute(self, **kwargs: Any) -> Any:
        return (await get_structured_completion(self.construct_prompt(**kwargs), self.response_model) or {}).get('parsed_content')
