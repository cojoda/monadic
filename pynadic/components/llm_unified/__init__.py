""" llm_unified package public API. """

# NOTE: Keep the public surface lightweight. Consumers can import submodules as needed.

from .registry import Registry
from .interface import predict
from .unified_client import UnifiedClient

__all__ = [
    "Registry",
    "predict",
    "UnifiedClient",
]
