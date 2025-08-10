from __future__ import annotations

from typing import Optional, Type

from pydantic import BaseModel

from .registry import Registry
from .interface import predict as _predict


class UnifiedClient:
    """A lightweight, stateful wrapper around the unified LLM interface.

    It holds a Registry instance (defaulting to a fresh Registry) and delegates the
    actual prediction work to the shared 'predict' function defined in llm_unified.interface.
    """

    def __init__(self, registry: Optional[Registry] = None):
        self._registry = registry or Registry()

    def predict(self, system_prompt: str, user_input: str, output_model: Type[BaseModel], provider_names: Optional[list[str]] = None) -> BaseModel:
        """Infer a structured output by querying the configured providers in order.

        - system_prompt: high-level instructions/system prompt for the LLM.
        - user_input: the user's query or input data.
        - output_model: a Pydantic model describing the desired structured output.
        - provider_names: optional list of provider names to try in order (e.g. ["openai_responses", "gemini"]).
        - Returns an instance of output_model populated with parsed data.
        """
        return _predict(system_prompt, user_input, output_model, provider_names, self._registry)


__all__ = ["UnifiedClient"]
