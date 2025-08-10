import os
from typing import Optional, Tuple, Dict
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

    def generate(self, system_prompt: str, user_input: str) -> Tuple[str, Dict[str, Optional[int]]]:
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
        text = ""
        if candidates:
            first = candidates[0]
            if isinstance(first, dict):
                text = first.get("content") or first.get("text") or first.get("output") or ""
        if text is None:
            text = ""
        if text == "":
            # Be strict here to surface API deviations clearly
            raise ValueError("Invalid Gemini response format: no usable text found")

        # Usage extraction with a robust approach. Only store if at least one counter exists.
        usage: Dict[str, Optional[int]] = None  # type: ignore
        if isinstance(data, dict):
            raw_usage = data.get("usage") or data.get("tokenUsage")
            if isinstance(raw_usage, dict):
                input_tokens = raw_usage.get("promptTokens") or raw_usage.get("inputTokens")
                output_tokens = raw_usage.get("completionTokens") or raw_usage.get("outputTokens")
                # Normalize to ints when possible
                def _to_int(v: object | None) -> Optional[int]:
                    if v is None:
                        return None
                    if isinstance(v, int):
                        return v
                    if isinstance(v, float):
                        return int(v)
                    if isinstance(v, str):
                        try:
                            if v.isdigit():
                                return int(v)
                            return int(float(v))
                        except Exception:
                            return None
                    return None

                in_t = _to_int(input_tokens)
                out_t = _to_int(output_tokens)
                if in_t is not None or out_t is not None:
                    usage = {
                        "input_tokens": in_t,
                        "output_tokens": out_t,
                    }

        self._last_usage = usage
        return text, usage
