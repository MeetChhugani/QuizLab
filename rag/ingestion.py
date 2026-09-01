"""Document ingestion pipeline: extract → clean → chunk → embed → store."""
import hashlib
import json
import os
from typing import Any

from rag.chunking import chunk_document, chunk_pages, clean_text, generate_document_id
from rag import config
from rag.embeddings import embed_documents
from rag.vector_store import add_documents, delete_document, document_exists


class IngestionError(Exception):
    """Raised when document ingestion fails."""


def _ensure_registry_dir():
    os.makedirs(config.DATA_DIR, exist_ok=True)


def _load_registry() -> dict:
    _ensure_registry_dir()
    if os.path.exists(config.INGESTION_REGISTRY_PATH):
        try:
            with open(config.INGESTION_REGISTRY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_registry(registry: dict) -> None:
    _ensure_registry_dir()
    with open(config.INGESTION_REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)


def compute_content_hash(content: bytes | str) -> str:
    """SHA-256 hash for duplicate detection."""
    if isinstance(content, str):
        content = content.encode("utf-8", errors="ignore")
    return hashlib.sha256(content).hexdigest()


def is_document_indexed(content_hash: str, session_id: str = "default") -> dict | None:
    """Return registry entry if document already indexed for this session."""
    registry = _load_registry()
    key = f"{session_id}:{content_hash}"
    entry = registry.get(key)
    if entry and document_exists(entry["document_id"], session_id):
        return entry
    return None


def ingest_document(
    *,
    pages: list[dict[str, Any]] | None = None,
    text: str | None = None,
    document_name: str,
    content_hash: str,
    session_id: str = "default",
    force_reindex: bool = False,
) -> dict[str, Any]:
    """
    Full ingestion pipeline. Returns document metadata dict.

    Provide either `pages` (list with page_number, text) or plain `text`.
    """
    existing = is_document_indexed(content_hash, session_id)
    if existing and not force_reindex:
        return {
            **existing,
            "status": "already_indexed",
            "chunks_added": 0,
        }

    document_id = generate_document_id(content_hash)

    if existing and force_reindex:
        delete_document(document_id, session_id)

    if pages:
        cleaned_pages = []
        for p in pages:
            t = clean_text(p.get("text", ""))
            if t:
                cleaned_pages.append({**p, "text": t})
        if not cleaned_pages:
            raise IngestionError(
                "No readable text could be extracted from this document. "
                "It may be empty, image-only, or require OCR."
            )
        chunks = chunk_pages(cleaned_pages, document_id, document_name)
    elif text:
        cleaned = clean_text(text)
        if len(cleaned) < 80:
            raise IngestionError(
                "Document contains too little text to index. "
                "Ensure the PDF is text-based or paste content directly."
            )
        chunks = chunk_document(cleaned, document_id, document_name)
    else:
        raise IngestionError("No content provided for ingestion.")

    if not chunks:
        raise IngestionError(
            "Chunking produced no usable segments. The document may be too short or poorly formatted."
        )

    try:
        texts = [c["text"] for c in chunks]
        embeddings = embed_documents(texts)
    except Exception as e:
        raise IngestionError(f"Embedding generation failed: {e}") from e

    try:
        added = add_documents(chunks, embeddings, session_id)
    except Exception as e:
        raise IngestionError(f"Vector store write failed: {e}") from e

    entry = {
        "document_id": document_id,
        "document_name": document_name,
        "content_hash": content_hash,
        "chunk_count": added,
        "session_id": session_id,
        "status": "indexed",
    }

    registry = _load_registry()
    registry[f"{session_id}:{content_hash}"] = entry
    _save_registry(registry)

    return {**entry, "chunks_added": added}


def list_indexed_documents(session_id: str = "default") -> list[dict]:
    """List all indexed documents for a session."""
    registry = _load_registry()
    return [
        v for k, v in registry.items()
        if k.startswith(f"{session_id}:") and document_exists(v["document_id"], session_id)
    ]
