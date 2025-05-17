from monadic.data import chunk



def test_chunk(chunk_init):
    role, data, uid, context = chunk_init.param
    result = chunk.Chunk(role, data, uid, context)
    
    assert result.role == role
    assert result.data == data
    assert result.uid == uid
    # assert result.context ==

    assert result.to_dict() == {
        'role': role,
        'content': data
    }
    