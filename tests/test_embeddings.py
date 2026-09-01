"""Tests for QuizLab RAG embeddings."""
import pytest

from rag.embeddings import embed_documents, embed_query, embed_text, embedding_dimension


def test_embed_text_returns_vector():
    vec = embed_text("DBSCAN is a clustering algorithm")
    assert isinstance(vec, list)
    assert len(vec) > 0
    assert all(isinstance(v, float) for v in vec)


def test_embed_query_consistent_dimension():
    v1 = embed_query("What is DBSCAN?")
    v2 = embed_query("Explain density-based clustering")
    assert len(v1) == len(v2)
    assert len(v1) == embedding_dimension()


def test_embed_documents_batch():
    texts = [
        "DBSCAN clusters dense regions",
        "K-means requires number of clusters",
        "Neural networks use layers",
    ]
    vectors = embed_documents(texts)
    assert len(vectors) == 3
    dim = embedding_dimension()
    assert all(len(v) == dim for v in vectors)


def test_embed_empty_raises():
    with pytest.raises(ValueError):
        embed_text("")
