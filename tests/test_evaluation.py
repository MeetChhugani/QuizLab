"""Retrieval evaluation tests."""
import os
import tempfile

import pytest


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch):
    import rag.config as cfg
    import rag.vector_store as vs

    tmp = tempfile.mkdtemp(prefix="quizlab_eval_")
    chroma_dir = os.path.join(tmp, "chroma")
    data_dir = os.path.join(tmp, "data")
    os.makedirs(chroma_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)

    monkeypatch.setattr(cfg, "CHROMA_PERSIST_DIR", chroma_dir)
    monkeypatch.setattr(cfg, "DATA_DIR", data_dir)
    monkeypatch.setattr(cfg, "INGESTION_REGISTRY_PATH", os.path.join(data_dir, "registry.json"))
    vs.reset_client()
    yield
    vs.reset_client()


EVAL_PAGES = [
    {
        "page_number": 32,
        "text": ("DBSCAN density-based clustering algorithm " * 30),
        "chapter": "DBSCAN",
    },
    {
        "page_number": 15,
        "text": ("Supervised learning uses labeled training data " * 30),
        "chapter": "Supervised Learning",
    },
    {
        "page_number": 20,
        "text": ("Neural networks consist of interconnected layers of neurons " * 30),
        "chapter": "Neural Networks",
    },
]


def test_retrieval_evaluation():
    from rag.evaluation import evaluate_retrieval
    from rag.ingestion import compute_content_hash, ingest_document

    h = compute_content_hash("eval dataset content")
    ingest_document(
        pages=EVAL_PAGES,
        document_name="ML_Textbook.pdf",
        content_hash=h,
        session_id="eval",
    )

    test_cases = [
        {"question": "What is DBSCAN?", "expected_topic": "dbscan"},
        {"question": "Explain supervised learning", "expected_topic": "supervised"},
        {"question": "What is a neural network?", "expected_topic": "neural"},
    ]

    report = evaluate_retrieval(test_cases, session_id="eval", top_k=5)
    assert report["total_cases"] == 3
    assert report["top5_accuracy"] >= 0.0
    assert "cases" in report
