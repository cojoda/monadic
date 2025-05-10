

def test_merge(sample_chunks):
    merged = merge(sample_chunks)
    assert merged.get_content() == 'hello\n\n[...]\n\nworld'