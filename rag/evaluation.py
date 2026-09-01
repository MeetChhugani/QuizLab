"""Retrieval quality evaluation for QuizLab RAG."""
from typing import Any

from rag.retriever import retrieve


def evaluate_retrieval(
    test_cases: list[dict[str, Any]],
    session_id: str = "default",
    top_k: int = 5,
) -> dict[str, Any]:
    """
    Evaluate retrieval against a test dataset.

    Each test case: {"question": "...", "expected_topic": "DBSCAN", "document_id": optional}
    Measures whether expected_topic appears in top-1, top-3, top-5 results.
    """
    results = []
    top1_hits = top3_hits = top5_hits = 0

    for case in test_cases:
        question = case["question"]
        expected = (case.get("expected_topic") or "").lower()
        doc_id = case.get("document_id")

        chunks = retrieve(
            question,
            top_k=top_k,
            session_id=session_id,
            document_id=doc_id,
        )

        def _matches(chunk: dict) -> bool:
            text = (chunk.get("chunk_text") or "").lower()
            meta = chunk.get("metadata") or {}
            topic = (meta.get("topic") or "").lower()
            return expected in text or expected in topic

        hit_at = None
        for i, chunk in enumerate(chunks):
            if _matches(chunk):
                hit_at = i + 1
                break

        case_result = {
            "question": question,
            "expected_topic": case.get("expected_topic"),
            "hit_rank": hit_at,
            "retrieved_count": len(chunks),
        }
        results.append(case_result)

        if hit_at == 1:
            top1_hits += 1
        if hit_at and hit_at <= 3:
            top3_hits += 1
        if hit_at and hit_at <= 5:
            top5_hits += 1

    n = len(test_cases) or 1
    return {
        "total_cases": len(test_cases),
        "top1_accuracy": top1_hits / n,
        "top3_accuracy": top3_hits / n,
        "top5_accuracy": top5_hits / n,
        "cases": results,
    }


DEFAULT_EVAL_DATASET = [
    {"question": "What is DBSCAN?", "expected_topic": "DBSCAN"},
    {"question": "Explain density-based clustering", "expected_topic": "DBSCAN"},
    {"question": "What are the advantages of DBSCAN?", "expected_topic": "DBSCAN"},
    {"question": "Define machine learning supervised learning", "expected_topic": "supervised"},
    {"question": "What is a neural network?", "expected_topic": "neural"},
]
