import json
import os
from typing import Optional
import requests

from .provider import LLMProvider


class OpenAIProvider(LLMProvider):
    """OpenAI provider wrapper (Chat Completions)."""

    name = "openai"

    def __init__(self, api_key: Optional[str] = None, endpoint: Optional[str] = None):
        super().__init__(name=self.name, api_key=(api_key or os.getenv("OPENAI_API_KEY")), endpoint=(endpoint or "https://api.openai.com/v1/chat/completions"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")

    def generate(self, system_prompt: str, user_input: str) -> str:
        if not self.api_key:
            raise RuntimeError("OpenAI API key not configured. Set OPENAI_API_KEY or provide via constructor.")
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ]
        payload = {"model": self.model, "messages": messages, "temperature": 0.2}
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        resp = requests.post(self.endpoint, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        try:
            return data["choices"][0]["message"]["content"]
        except Exception:
            if isinstance(data, dict) and data.get("choices") and isinstance(data["choices"], list):
                c = data["choices"][0]
                if isinstance(c, dict) and "text" in c:
                    return c["text"]
        raise ValueError("Invalid OpenAI response format")
