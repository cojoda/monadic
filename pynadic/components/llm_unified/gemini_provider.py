import os
from typing import Optional
import requests

from .provider import LLMProvider


class GeminiProvider(LLMProvider):
    """Google Gemini (Generative AI) provider wrapper."""

    name = "gemini"

    def __init__(self, api_key: Optional[str] = None, endpoint: Optional[str] = None, model: str = "models/text-bison-001", max_tokens: int = 512, temperature: float = 0.2):
        super().__init__(name=self.name, api_key=(api_key or os.getenv("GOOGLE_GEMINI_API_KEY")), endpoint=(endpoint or "https://generativelanguage.googleapis.com/v1beta2/models/{model}:generateText"))
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    def generate(self, system_prompt: str, user_input: str) -> str:
        if not self.api_key:
            raise RuntimeError("Google Gemini API key not configured. Set GOOGLE_GEMINI_API_KEY env var or pass api_key.")
        prompt_text = f"{system_prompt}\n{user_input}"
        payload = {
            "prompt": {"text": prompt_text},
            "temperature": self.temperature,
            "maxOutputTokens": self.max_tokens,
        }
        url = self.endpoint.format(model=self.model)
        headers = {"Content-Type": "application/json"}
        params = {"key": self.api_key}
        resp = requests.post(url, json=payload, headers=headers, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        candidates = data.get("candidates") or []
        if candidates:
            first = candidates[0]
            return first.get("content") or first.get("text") or ""
        raise ValueError("Invalid Gemini response format")
