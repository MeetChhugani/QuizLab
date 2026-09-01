"""Document-aware recursive text chunking for RAG."""
import re
from typing import Any

from rag.config import CHUNK_OVERLAP, CHUNK_SIZE, MIN_CHUNK_SIZE

# Split hierarchy: paragraphs → sentences → words
_SEPARATORS = ["\n\n", "\n", ". ", "? ", "! ", "; ", ", ", " "]


def clean_text(text: str) -> str:
    """Normalize whitespace and remove control characters."""
    if not text:
        return ""
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _split_text(text: str, separators: list[str]) -> list[str]:
    """Recursively split text using the separator hierarchy."""
    if not text:
        return []
    if len(text) <= CHUNK_SIZE:
        return [text] if len(text.strip()) >= MIN_CHUNK_SIZE else []

    sep = separators[0] if separators else " "
    next_seps = separators[1:] if len(separators) > 1 else [" "]

    parts = text.split(sep) if sep != " " else text.split()
    chunks: list[str] = []
    current = ""

    for i, part in enumerate(parts):
        piece = part if sep == " " else part + (sep if i < len(parts) - 1 else "")
        candidate = (current + piece).strip() if current else piece.strip()

        if len(candidate) <= CHUNK_SIZE:
            current = candidate if not current else current + (sep if sep != " " else " ") + piece
        else:
            if current and len(current.strip()) >= MIN_CHUNK_SIZE:
                chunks.append(current.strip())
            if len(piece) > CHUNK_SIZE and next_seps:
                chunks.extend(_split_text(piece, next_seps))
                current = ""
            else:
                current = piece

    if current and len(current.strip()) >= MIN_CHUNK_SIZE:
        chunks.append(current.strip())

    return chunks


def _merge_with_overlap(chunks: list[str]) -> list[str]:
    """Apply overlap between consecutive chunks."""
    if not chunks or CHUNK_OVERLAP <= 0:
        return chunks

    overlapped: list[str] = []
    for i, chunk in enumerate(chunks):
        if i == 0:
            overlapped.append(chunk)
            continue
        prev = overlapped[-1]
        overlap_text = prev[-CHUNK_OVERLAP:] if len(prev) > CHUNK_OVERLAP else prev
        merged = overlap_text + " " + chunk
        if len(merged) > CHUNK_SIZE * 1.5:
            overlapped.append(chunk)
        else:
            overlapped.append(merged.strip())
    return overlapped


def _infer_topic(text: str) -> str:
    """Infer a lightweight topic label from chunk content (first heading-like line)."""
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if len(line) < 120 and (
            line.isupper()
            or re.match(r"^(chapter|section|unit|topic|module)\s+\d", line, re.I)
            or re.match(r"^\d+[\.\)]\s+\w", line)
        ):
            return line[:100]
        break
    words = text.split()[:6]
    return " ".join(words)[:80] if words else "General"


def chunk_pages(
    pages: list[dict[str, Any]],
    document_id: str,
    document_name: str,
) -> list[dict[str, Any]]:
    """
    Chunk page-level extracted text with metadata.

    Each page dict should have: page_number (1-based), text, and optionally chapter/section.
    Returns list of chunk dicts ready for embedding.
    """
    all_chunks: list[dict[str, Any]] = []
    chunk_index = 0

    for page in pages:
        page_num = page.get("page_number", 0)
        raw = page.get("text", "")
        chapter = page.get("chapter") or page.get("section") or ""
        cleaned = clean_text(raw)
        if not cleaned or len(cleaned) < MIN_CHUNK_SIZE:
            continue

        page_chunks = _split_text(cleaned, _SEPARATORS.copy())
        page_chunks = _merge_with_overlap(page_chunks)

        for text in page_chunks:
            if len(text.strip()) < MIN_CHUNK_SIZE:
                continue
            chunk_id = f"{document_id}_p{page_num}_c{chunk_index}"
            all_chunks.append(
                {
                    "chunk_id": chunk_id,
                    "document_id": document_id,
                    "document_name": document_name,
                    "page_number": page_num,
                    "text": text,
                    "topic": chapter or _infer_topic(text),
                    "chapter": chapter or "",
                }
            )
            chunk_index += 1

    return all_chunks


def chunk_document(
    text: str,
    document_id: str,
    document_name: str,
    page_number: int = 0,
) -> list[dict[str, Any]]:
    """Chunk a single text blob (e.g. pasted text) without page boundaries."""
    cleaned = clean_text(text)
    if not cleaned:
        return []

    pages = [{"page_number": page_number or 1, "text": cleaned}]
    return chunk_pages(pages, document_id, document_name)


def generate_document_id(content_hash: str) -> str:
    """Create a stable document ID from content hash."""
    return f"doc_{content_hash[:16]}"
