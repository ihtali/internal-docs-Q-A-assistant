from app.ingest import chunk_text


def test_chunk_text_splits_and_overlaps():
    text = "word " * 1000
    chunks = chunk_text(text, chunk_size=200, overlap=40)
    assert len(chunks) > 1
    assert all(len(chunk) <= 260 for chunk in chunks)
    assert chunks[0] != chunks[1]
