import pytest
from monadic.history.data_chunk import Chunk



@pytest.fixture(params=[
    ([Chunk('user', 'hello'), Chunk('user', 'world')], 'hello\n\n[...]\n\nworld'),
    ([Chunk('user', 'hello'), Chunk('assistant', 'world')], 'hello'),
    ([Chunk('user', 'a')], 'a'),
    ([], None),
])
def merge_list(request):
    return request.param




@pytest.fixture(params=[
    ([Chunk('user', 'hello'), Chunk('user', 'world')], 0, 0, 0),
    ([Chunk('user', 'hello'), Chunk('user', 'world')], 0, 1, 1),
    ([Chunk('user', 'hello'), Chunk('user', 'world')], 0, 2, 2),
    ([Chunk('user', 'a')], 0, 0, 0),
    ([Chunk('user', 'a')], 0, 1, 1),
    ([Chunk('user', 'a')], 0, 2, 1),
    ([], 0, 0, 0),
    ([], 0, 1, 0),
])
def cut_list(request):
    return request.param