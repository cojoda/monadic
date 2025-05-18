import pytest

from monadic.context.context_ops import Context



@pytest.fixture(params=[
    ('user', 'foo', 0, Context(None, [])),
])
def chunk_init(request):
    return request

