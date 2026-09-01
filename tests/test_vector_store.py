"""Tests for QuizLab vector store and retrieval."""
import shutil
import tempfile
import os

import pytest

# Use isolated temp dirs for each test module run
_TEST_DIR = tempfile.mkdtemp(prefix="quizlab_rag_test_")


@pytest.fixture(autouse=True)
def isolated_vector_store(monkeypatch):
    """Point ChromaDB and registry to temp directory."""
    import rag.config as cfg
    import rag.vector_store as vs
    import rag.ingestion as ing

    chroma_dir = os.path.join(_TEST_DIR, "chroma")
    data_dir = os.path.join(_TEST_DIR, "data")
    os.makedirs(chroma_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)

    monkeypatch.setattr(cfg, "CHROMA_PERSIST_DIR", chroma_dir)
    monkeypatch.setattr(cfg, "DATA_DIR", data_dir)
    monkeypatch.setattr(cfg, "INGESTION_REGISTRY_PATH", os.path.join(data_dir, "registry.json"))
    vs.reset_client()
    yield
    vs.reset_client()


DBSCAN_PAGES = [
    {
        "page_number": 32,
        "text": (
            "DBSCAN (Density-Based Spatial Clustering of Applications with Noise) "
            "is a popular density-based clustering algorithm. It groups points that "
            "are closely packed into clusters and marks outliers in sparse regions. "
        ) * 8,
        "chapter": "Chapter 4 Clustering",
    },
    {
        "page_number": 33,
        "text": (
            "Advantages of DBSCAN: does not require specifying cluster count, "
            "finds arbitrary shaped clusters, robust to outliers. Parameters: eps and minPts. "
        ) * 8,
    },
]

KMEANS_PAGE = [
    {
        "page_number": 10,
        "text": (
            "K-means clustering partitions data into K clusters by minimizing "
            "within-cluster variance. Requires specifying K in advance. "
        ) * 8,
    }
]


def test_ingest_and_search_dbscan():
    from rag.ingestion import compute_content_hash, ingest_document
    from rag.retriever import retrieve

    content = "dbscan test content unique 12345"
    h = compute_content_hash(content)
    result = ingest_document(
        pages=DBSCAN_PAGES,
        document_name="Data_Mining.pdf",
        content_hash=h,
        session_id="test_session",
    )
    assert result["status"] == "indexed"
    assert result["chunks_added"] > 0

    chunks = retrieve(
        "Explain DBSCAN",
        top_k=5,
        session_id="test_session",
        document_id=result["document_id"],
    )
    assert len(chunks) >= 1
    combined = " ".join(c["chunk_text"].lower() for c in chunks)
    assert "dbscan" in combined


def test_metadata_preserved():
    from rag.ingestion import compute_content_hash, ingest_document
    from rag.vector_store import get_document

    h = compute_content_hash("metadata test 67890")
    result = ingest_document(
        pages=DBSCAN_PAGES,
        document_name="Data_Mining.pdf",
        content_hash=h,
        session_id="meta_session",
    )
    doc_id = result["document_id"]
    stored = get_document(doc_id, session_id="meta_session")
    assert len(stored) > 0
    meta = stored[0]["metadata"]
    assert meta["document_name"] == "Data_Mining.pdf"
    assert meta["document_id"] == doc_id
    assert meta["chunk_id"]
    assert int(meta["page_number"]) in (32, 33)


def test_duplicate_ingestion_skipped():
    from rag.ingestion import compute_content_hash, ingest_document

    h = compute_content_hash("duplicate test abc")
    r1 = ingest_document(
        pages=DBSCAN_PAGES,
        document_name="Data_Mining.pdf",
        content_hash=h,
        session_id="dup_session",
    )
    r2 = ingest_document(
        pages=DBSCAN_PAGES,
        document_name="Data_Mining.pdf",
        content_hash=h,
        session_id="dup_session",
    )
    assert r1["status"] == "indexed"
    assert r2["status"] == "already_indexed"
    assert r2["chunks_added"] == 0


def test_delete_document():
    from rag.ingestion import compute_content_hash, ingest_document
    from rag.vector_store import delete_document, document_exists

    h = compute_content_hash("delete test xyz")
    result = ingest_document(
        pages=KMEANS_PAGE,
        document_name="ML.pdf",
        content_hash=h,
        session_id="del_session",
    )
    doc_id = result["document_id"]
    assert document_exists(doc_id, session_id="del_session")
    deleted = delete_document(doc_id, session_id="del_session")
    assert deleted > 0
    assert not document_exists(doc_id, session_id="del_session")
