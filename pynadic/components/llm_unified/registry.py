from __future__ import annotations

from typing import Dict

# Providers are imported lazily to keep import-time light
import os

from .provider import LLMProvider


def _import_openai_provider():
    from .openai_provider import OpenAIProvider
    return OpenAIProvider


def _import_openai_responses_provider():
    from .openai_responses_provider import OpenAIResponsesProvider
    return OpenAIResponsesProvider


def _import_gemini_provider():
    from .gemini_provider import GeminiProvider
    return GeminiProvider


def _import_anthropic_provider():
    from .anthropic_provider import AnthropicProvider
    return AnthropicProvider


class Registry:
    """Simple registry that holds provider instances by name."""

    def __init__(self, providers: list[LLMProvider] | None = None) -> None:
        self._providers: Dict[str, LLMProvider] = {}
        self._build()
        if providers:
            for p in providers:
                self.register(p)

    def _build(self) -> None:
        # Build default providers using environment variables if available
        OpenAIProvider = _import_openai_provider()
        OpenAIResponsesProvider = _import_openai_responses_provider()
        GeminiProvider = _import_gemini_provider()
        AnthropicProvider = _import_anthropic_provider()

        # Use environment-provided credentials if available; otherwise, let
        # the provider handle missing keys (providers should fail on use).
        self.register(OpenAIProvider())
        self.register(OpenAIResponsesProvider())
        self.register(GeminiProvider())
        self.register(AnthropicProvider())

    def register(self, provider: LLMProvider) -> None:
        self._providers[provider.name] = provider

    def get_provider(self, name: str) -> LLMProvider:
        if name not in self._providers:
            raise KeyError(f"Provider '{name}' not registered")
        return self._providers[name]


__all__ = ["Registry"]
