"""Tests for QuizLab RAG chunking."""
from rag.chunking import chunk_document, chunk_pages, clean_text
from rag.config import MIN_CHUNK_SIZE


SAMPLE_TEXT = """
DBSCAN (Density-Based Spatial Clustering of Applications with Noise) is a clustering algorithm
that groups together points that are closely packed, marking as outliers points that lie alone
in low-density regions.

DBSCAN defines clusters as dense regions separated by sparse regions. It requires two parameters:
epsilon (eps) and minimum points (minPts). The algorithm is particularly useful for discovering
clusters of arbitrary shape and for identifying noise.

Advantages of DBSCAN include: it does not require specifying the number of clusters,
it can find arbitrarily shaped clusters, and it is robust to outliers.

Disadvantages include sensitivity to parameter settings and varying density clusters.
""" * 3


def test_clean_text_removes_excess_whitespace():
    result = clean_text("  hello   world\n\n\n\nfoo  ")
    assert "hello world" in result
    assert "\n\n\n" not in result


def test_chunk_document_produces_non_empty_chunks():
    chunks = chunk_document(SAMPLE_TEXT, "doc1", "test.pdf")
    assert len(chunks) >= 1
    for c in chunks:
        assert c["text"].strip()
        assert len(c["text"]) >= MIN_CHUNK_SIZE
        assert c["document_id"] == "doc1"
        assert c["document_name"] == "test.pdf"
        assert c["chunk_id"]
        assert c["topic"]


def test_chunk_pages_preserves_page_metadata():
    pages = [
        {"page_number": 32, "text": "DBSCAN is a density-based clustering algorithm. " * 20, "chapter": "Chapter 4"},
        {"page_number": 33, "text": "Advantages of DBSCAN include robustness to outliers. " * 20},
    ]
    chunks = chunk_pages(pages, "doc2", "Data_Mining.pdf")
    assert len(chunks) >= 2
    page_nums = {c["page_number"] for c in chunks}
    assert 32 in page_nums or 33 in page_nums
    assert all(c["document_name"] == "Data_Mining.pdf" for c in chunks)
    assert any(c.get("chapter") == "Chapter 4" or c["page_number"] == 32 for c in chunks)


def test_no_empty_chunks():
    chunks = chunk_document(SAMPLE_TEXT, "doc3", "sample.pdf")
    assert all(c["text"].strip() for c in chunks)
