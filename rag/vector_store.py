"""Persistent ChromaDB vector store for QuizLab RAG."""
import os
from typing import Any

import chromadb
from chromadb.config import Settings

from rag import config


def _ensure_data_dir():
    os.makedirs(config.DATA_DIR, exist_ok=True)
    os.makedirs(config.CHROMA_PERSIST_DIR, exist_ok=True)


_client = None


def _get_client():
    global _client
    if _client is None:
        _ensure_data_dir()
        _client = chromadb.PersistentClient(
            path=config.CHROMA_PERSIST_DIR,
            settings=Settings(anonymized_telemetry=False),
        )
    return _client


def _get_collection(session_id: str = "default"):
    """Get or create a collection scoped by session for future multi-user isolation."""
    client = _get_client()
    name = f"{config.CHROMA_COLLECTION_NAME}_{session_id}"
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )


def add_documents(
    chunks: list[dict[str, Any]],
    embeddings: list[list[float]],
    session_id: str = "default",
) -> int:
    """
    Add document chunks with embeddings to the vector store.
    Returns number of chunks added.
    """
    if not chunks:
        return 0
    if len(chunks) != len(embeddings):
        raise ValueError("chunks and embeddings length mismatch")

    collection = _get_collection(session_id)
    ids = [c["chunk_id"] for c in chunks]
    documents = [c["text"] for c in chunks]
    metadatas = [
        {
            "document_id": c["document_id"],
            "document_name": c["document_name"],
            "page_number": int(c.get("page_number") or 0),
            "chunk_id": c["chunk_id"],
            "topic": c.get("topic") or "",
            "chapter": c.get("chapter") or "",
        }
        for c in chunks
    ]

    # Upsert to avoid duplicate chunk IDs on re-index
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )
    return len(chunks)


def search(
    query_embedding: list[float],
    top_k: int = 5,
    session_id: str = "default",
    document_id: str | None = None,
    page_min: int | None = None,
    page_max: int | None = None,
    topic: str | None = None,
) -> list[dict[str, Any]]:
    """
    Similarity search with optional metadata filtering.
    Returns list of {chunk_text, metadata, distance, similarity}.
    """
    collection = _get_collection(session_id)
    where = _build_where_filter(document_id, page_min, page_max, topic)

    kwargs: dict[str, Any] = {
        "query_embeddings": [query_embedding],
        "n_results": top_k,
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        kwargs["where"] = where

    try:
        results = collection.query(**kwargs)
        return _format_results(results)
    except Exception:
        # Do not silently return content outside an explicit filter. Chroma
        # versions differ in their support for compound filters, so retrieve a
        # bounded candidate set and apply the same constraints locally.
        if not where:
            raise
        kwargs.pop("where", None)
        candidate_count = max(top_k * 10, top_k)
        count = collection.count()
        kwargs["n_results"] = min(candidate_count, count)
        if not kwargs["n_results"]:
            return []
        candidates = _format_results(collection.query(**kwargs))
        return _apply_filters(candidates, document_id, page_min, page_max, topic)[:top_k]


def _build_where_filter(
    document_id: str | None,
    page_min: int | None,
    page_max: int | None,
    topic: str | None,
) -> dict | None:
    clauses = []
    if document_id:
        clauses.append({"document_id": {"$eq": document_id}})
    if page_min is not None:
        clauses.append({"page_number": {"$gte": int(page_min)}})
    if page_max is not None:
        clauses.append({"page_number": {"$lte": int(page_max)}})
    if topic:
        clauses.append({"topic": {"$eq": topic}})

    if not clauses:
        return None
    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}


def _format_results(results: dict) -> list[dict[str, Any]]:
    formatted = []
    if not results or not results.get("ids") or not results["ids"][0]:
        return formatted

    ids = results["ids"][0]
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0]

    for i, chunk_id in enumerate(ids):
        distance = dists[i] if i < len(dists) else None
        similarity = 1.0 - distance if distance is not None else None
        meta = metas[i] if i < len(metas) else {}
        formatted.append(
            {
                "chunk_id": chunk_id,
                "chunk_text": docs[i] if i < len(docs) else "",
                "metadata": meta or {},
                "distance": distance,
                "similarity": similarity,
            }
        )
    return formatted


def _apply_filters(
    chunks: list[dict[str, Any]],
    document_id: str | None,
    page_min: int | None,
    page_max: int | None,
    topic: str | None,
) -> list[dict[str, Any]]:
    """Local equivalent of the supported metadata filters."""
    filtered = []
    topic_key = topic.casefold() if topic else None
    for chunk in chunks:
        metadata = chunk.get("metadata") or {}
        page = int(metadata.get("page_number") or 0)
        if document_id and metadata.get("document_id") != document_id:
            continue
        if page_min is not None and page < page_min:
            continue
        if page_max is not None and page > page_max:
            continue
        if topic_key and (metadata.get("topic") or "").casefold() != topic_key:
            continue
        filtered.append(chunk)
    return filtered


def delete_document(document_id: str, session_id: str = "default") -> int:
    """Delete all chunks belonging to a document."""
    collection = _get_collection(session_id)
    try:
        existing = collection.get(where={"document_id": {"$eq": document_id}})
        ids = existing.get("ids") or []
        if ids:
            collection.delete(ids=ids)
        return len(ids)
    except Exception:
        return 0


def get_document(document_id: str, session_id: str = "default") -> list[dict[str, Any]]:
    """Retrieve all chunks for a document."""
    collection = _get_collection(session_id)
    try:
        result = collection.get(
            where={"document_id": {"$eq": document_id}},
            include=["documents", "metadatas"],
        )
        chunks = []
        ids = result.get("ids") or []
        docs = result.get("documents") or []
        metas = result.get("metadatas") or []
        for i, cid in enumerate(ids):
            chunks.append(
                {
                    "chunk_id": cid,
                    "chunk_text": docs[i] if i < len(docs) else "",
                    "metadata": metas[i] if i < len(metas) else {},
                }
            )
        return chunks
    except Exception:
        return []


def clear_collection(session_id: str = "default") -> None:
    """Remove all vectors in the session collection."""
    client = _get_client()
    name = f"{config.CHROMA_COLLECTION_NAME}_{session_id}"
    try:
        client.delete_collection(name)
    except Exception:
        pass
    _get_collection(session_id)


def document_exists(document_id: str, session_id: str = "default") -> bool:
    """Check if any chunks exist for document_id."""
    collection = _get_collection(session_id)
    try:
        result = collection.get(
            where={"document_id": {"$eq": document_id}},
            limit=1,
            include=[],
        )
        return bool(result.get("ids"))
    except Exception:
        return False


def reset_client():
    """Reset client singleton (for testing)."""
    global _client
    _client = None
