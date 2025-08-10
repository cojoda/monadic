"""Configuration helpers for llm_unified."""
import os
from typing import Optional


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """Fetch an environment variable with an optional default."""
    return os.getenv(key, default)


def load_config() -> dict:
    """Return a snapshot of API key related config from the environment."""
    return {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        "GOOGLE_GEMINI_API_KEY": os.getenv("GOOGLE_GEMINI_API_KEY"),
    }
