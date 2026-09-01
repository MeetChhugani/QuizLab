"""End-to-end RAG pipeline tests (retrieval; LLM mocked)."""
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch):
    import rag.config as cfg
    import rag.vector_store as vs

    tmp = tempfile.mkdtemp(prefix="quizlab_e2e_")
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


SAMPLE_PAGES = [
    {
        "page_number": 1,
        "text": (
            "DBSCAN is a density-based clustering algorithm used in data mining. "
            "It identifies clusters of varying shapes and handles noise effectively. "
        ) * 15,
        "chapter": "Clustering",
    }
]

MOCK_LLM_RESPONSE = """{
  "analysis": {
    "main_topics": ["DBSCAN"],
    "subtopics": ["Density-based clustering"],
    "difficulty_level": "Intermediate",
    "estimated_reading_time": "10 minutes",
    "learning_objectives": ["Understand DBSCAN"],
    "recommended_num_questions": 5
  },
  "questions": [
    {
      "question": "What does DBSCAN stand for?",
      "options": {"A": "A", "B": "B", "C": "C", "D": "D"},
      "correct": "A",
      "explanation": "DBSCAN expands to Density-Based Spatial Clustering.",
      "difficulty": "Easy",
      "topic": "DBSCAN"
    }
  ],
  "flashcards": [
    {"front": "What is DBSCAN?", "back": "A density-based clustering algorithm.", "topic": "DBSCAN", "difficulty": "Easy"}
  ]
}"""


def test_e2e_ingest_retrieve_generate():
    from rag.ingestion import compute_content_hash, ingest_document
    from rag.pipeline import rag_generate_learning_material
    from rag.retriever import retrieve, has_useful_context

    h = compute_content_hash("e2e test content")
    ingest_result = ingest_document(
        pages=SAMPLE_PAGES,
        document_name="test.pdf",
        content_hash=h,
        session_id="e2e",
    )
    assert ingest_result["chunks_added"] > 0

    chunks = retrieve("What is DBSCAN?", session_id="e2e", document_id=ingest_result["document_id"])
    assert has_useful_context(chunks)
    assert any("dbscan" in c["chunk_text"].lower() for c in chunks)

    mock_provider = MagicMock()
    mock_provider.generate.return_value = MOCK_LLM_RESPONSE

    with patch("rag.pipeline.get_llm_provider", return_value=mock_provider):
        material, err = rag_generate_learning_material(
            retrieval_query="DBSCAN clustering",
            custom_focus="DBSCAN",
            api_key="test-key",
            session_id="e2e",
            document_id=ingest_result["document_id"],
        )

    assert err is None
    assert material is not None
    assert "questions" in material
    assert "flashcards" in material
    assert material["_rag_sources"]


def test_rag_chat_no_context():
    from rag.pipeline import rag_chat

    answer, sources, err = rag_chat(
        "What is quantum computing?",
        api_key="fake",
        session_id="empty_session",
    )
    assert "does not contain enough information" in answer.lower() or "couldn't find" in answer.lower()
    assert sources == []
