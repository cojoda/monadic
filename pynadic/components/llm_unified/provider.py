from abc import ABC, abstractmethod
from typing import Optional
import json


class LLMProvider(ABC):
    """Base class for all LLM providers used by the unified interface."""

    def __init__(self, name: str, api_key: Optional[str] = None, endpoint: Optional[str] = None):
        self.name = name
        self.api_key = api_key
        self.endpoint = endpoint

    @abstractmethod
    def generate(self, system_prompt: str, user_input: str) -> str:
        """Return a string payload (ideally JSON) containing the structured data.
        Subclasses should implement the actual HTTP call.
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"<LLMProvider name={self.name}>"

    @staticmethod
    def _ensure_json_string(payload: object) -> str:
        """Coerce a provider output to a JSON string.
        - If payload is a string, return it directly.
        - If payload is a dict or list, serialize using json.dumps.
        - Otherwise, raise ValueError.
        """
        if isinstance(payload, str):
            return payload
        try:
            return json.dumps(payload)
        except Exception as exc:
            raise ValueError(f"Unable to serialize provider output to JSON: {exc}") from exc


__all__ = ["LLMProvider"]
