import pytest

from monadic.context.context_manager import Context



@pytest.fixture(params=[
    ('user', 'foo', 0, Context(None, [])),
])
def chunk_init(request):
    return request

