import json
from typing import List, Type, TypeVar, Optional
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

from .registry import Registry


def predict(system_prompt: str, user_input: str, output_model: Type[T], provider_names: List[str] | None = None, registry: Optional[Registry] = None) -> T:
    """Unified interface to generate structured output using multiple providers.

    - system_prompt: high-level instructions for the LLM.
    - user_input: the user's query or data.
    - output_model: a Pydantic model describing the desired schema.
    - provider_names: optional list[str] to specify provider order; defaults to OpenAI Responses API then Gemini.
    - registry: optional pre-configured Registry instance (for tests).
    """
    reg = registry or Registry()
    providers = provider_names or ["openai_responses", "gemini"]

    last_error: Exception | None = None
    for name in providers:
        provider = reg.get_provider(name)
        try:
            content = provider.generate(system_prompt, user_input)
        except Exception as exc:
            last_error = exc
            continue
        # Normalize to JSON string using provider's helper when possible
        try:
            json_str = provider._ensure_json_string(content)
        except Exception as exc:
            last_error = exc
            continue
        # Try to parse JSON string into the provided Pydantic model
        try:
            return output_model.parse_raw(json_str)
        except (ValidationError, json.JSONDecodeError, ValueError):
            # Try an alternative parsing path: if json_str isn't a raw string but a JSON structure
            try:
                obj = json.loads(json_str)
                return output_model.parse_obj(obj)
            except Exception as ve:
                last_error = ve
                continue
        except Exception as ve:
            last_error = ve
            continue

    raise ValueError(f"Unable to parse output with provided providers. Last error: {last_error}")
