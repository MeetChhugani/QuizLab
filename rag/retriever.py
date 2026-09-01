"""RAG retriever: query embedding → vector search → context assembly."""
import re
from typing import Any

from rag.config import MAX_CONTEXT_CHARS, TOP_K
from rag.embeddings import embed_query
from rag.vector_store import search


def parse_page_range(query: str) -> tuple[int | None, int | None]:
    """Extract page range from queries like 'pages 20-30'."""
    match = re.search(r"pages?\s+(\d+)\s*[-–to]+\s*(\d+)", query, re.I)
    if match:
        return int(match.group(1)), int(match.group(2))
    match = re.search(r"page\s+(\d+)", query, re.I)
    if match:
        p = int(match.group(1))
        return p, p
    return None, None


def parse_chapter_filter(query: str) -> str | None:
    """Extract chapter reference from query."""
    match = re.search(r"chapter\s+(\d+|[IVXLC]+)", query, re.I)
    if match:
        return f"Chapter {match.group(1)}"
    return None


def retrieve(
    query: str,
    *,
    top_k: int | None = None,
    session_id: str = "default",
    document_id: str | None = None,
    page_min: int | None = None,
    page_max: int | None = None,
    topic: str | None = None,
) -> list[dict[str, Any]]:
    """
    Retrieve top-K relevant chunks for a query.
    Returns list of {chunk_text, metadata, distance, similarity}.
    """
    if not query or not query.strip():
        return []

    top_k = top_k or TOP_K

    # Auto-parse filters from natural language if not explicitly provided
    if page_min is None and page_max is None:
        page_min, page_max = parse_page_range(query)

    try:
        query_vec = embed_query(query.strip())
    except Exception:
        return []

    return search(
        query_vec,
        top_k=top_k,
        session_id=session_id,
        document_id=document_id,
        page_min=page_min,
        page_max=page_max,
        topic=topic,
    )


def build_context(
    chunks: list[dict[str, Any]],
    max_chars: int | None = None,
) -> str:
    """Assemble retrieved chunks into a context string for the LLM."""
    max_chars = max_chars or MAX_CONTEXT_CHARS
    parts = []
    total = 0

    for i, chunk in enumerate(chunks, 1):
        meta = chunk.get("metadata") or {}
        doc_name = meta.get("document_name", "Document")
        page = meta.get("page_number")
        header = f"[Source {i}: {doc_name}"
        if page and int(page) > 0:
            header += f", Page {page}"
        header += "]"
        body = chunk.get("chunk_text") or chunk.get("text") or ""
        block = f"{header}\n{body}"

        if total + len(block) > max_chars:
            remaining = max_chars - total
            if remaining > 200:
                parts.append(block[:remaining] + "...")
            break
        parts.append(block)
        total += len(block) + 2

    return "\n\n".join(parts)


def format_sources(chunks: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Format unique source citations from retrieved chunks."""
    seen = set()
    sources = []

    for chunk in chunks:
        meta = chunk.get("metadata") or {}
        doc_name = meta.get("document_name", "Document")
        page = meta.get("page_number")
        chapter = meta.get("chapter") or meta.get("topic") or ""

        key = (doc_name, page, chapter)
        if key in seen:
            continue
        seen.add(key)

        entry = {"document_name": doc_name}
        if page and int(page) > 0:
            entry["page_number"] = str(int(page))
        if chapter and chapter != "General":
            entry["chapter"] = chapter
        sources.append(entry)

    return sources


def has_useful_context(chunks: list[dict[str, Any]], min_similarity: float = 0.25) -> bool:
    """Check if retrieval returned sufficiently relevant chunks."""
    if not chunks:
        return False
    for c in chunks:
        sim = c.get("similarity")
        if sim is None or sim >= min_similarity:
            return True
    return False
