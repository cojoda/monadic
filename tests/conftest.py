import pytest
from monadic.history.data_chunk import Chunk
from monadic.history.chunk_ops import merge


@pytest.fixture
def sample_chunks():
    return [
        Chunk(role="user", content="hello"),
        Chunk(role="user", content="world"),
    ]