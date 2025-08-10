import os
from typing import Optional
import requests

from .provider import LLMProvider


class OpenAIResponsesProvider(LLMProvider):
    """OpenAI Responses API provider wrapper (2025 release)."""

    name = "openai_responses"

    def __init__(self, api_key: Optional[str] = None, endpoint: Optional[str] = None, model: str = "gpt-4o"):
        super().__init__(name=self.name, api_key=(api_key or os.getenv("OPENAI_API_KEY")), endpoint=(endpoint or "https://api.openai.com/v1/responses"))
        self.model = model

    def generate(self, system_prompt: str, user_input: str) -> str:
        if not self.api_key:
            raise RuntimeError("OpenAI Responses API key not configured. Set OPENAI_API_KEY env var or pass api_key.")
        prompt = f"{system_prompt}\n\n{user_input}"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "max_tokens": 1024,
            "temperature": 0.2,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        resp = requests.post(self.endpoint, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        # Normalize common shapes
        if isinstance(data, dict):
            # OpenAI style with choices
            choices = data.get("choices")
            if isinstance(choices, list) and choices:
                first = choices[0]
                if isinstance(first, dict):
                    msg = None
                    if "message" in first and isinstance(first["message"], dict):
                        msg = first["message"].get("content")
                    if not msg:
                        msg = first.get("content") or first.get("text")
                    if msg is not None:
                        return msg
            # Direct completion
            if "completion" in data:
                return data["completion"]
            if "text" in data:
                return data["text"]
        elif isinstance(data, str):
            return data
        raise ValueError("Invalid OpenAI Responses API response format")
