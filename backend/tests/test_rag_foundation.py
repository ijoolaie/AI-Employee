from app.rag.text import chunk_text
from app.rag.service import cosine_similarity


def test_chunking_has_overlap_and_no_empty_chunks():
    text = "word " * 800
    chunks = chunk_text(text, chunk_size=100, overlap=20)
    assert len(chunks) > 1
    assert all(chunks)


def test_cosine_similarity():
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0
