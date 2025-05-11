from monadic.history import chunk_ops



def test_merge(merge_list):
    chunks, expected = merge_list
    result = chunk_ops.merge(chunks)
    if result is None:
        assert expected is None
    else:
        assert result.get_content() == expected


def test_cut(cut_list):
    chunks, start, stop, expected = cut_list
    result = chunk_ops.cut(chunks, start, stop)
    