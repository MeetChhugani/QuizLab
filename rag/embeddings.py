"""Local embedding generation using Sentence Transformers."""
from functools import lru_cache
from typing import Sequence

import numpy as np

from rag.config import EMBEDDING_BATCH_SIZE, EMBEDDING_MODEL

_model = None
_model_name_loaded = None


def _get_model():
    """Lazy-load the embedding model (singleton)."""
    global _model, _model_name_loaded
    if _model is None or _model_name_loaded != EMBEDDING_MODEL:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(EMBEDDING_MODEL)
        _model_name_loaded = EMBEDDING_MODEL
    return _model


def embed_text(text: str) -> list[float]:
    """Embed a single text string."""
    if not text or not text.strip():
        raise ValueError("Cannot embed empty text.")
    model = _get_model()
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()


def embed_documents(texts: Sequence[str], batch_size: int | None = None) -> list[list[float]]:
    """Embed multiple document chunks with batching."""
    if not texts:
        return []
    batch_size = batch_size or EMBEDDING_BATCH_SIZE
    model = _get_model()
    vectors = model.encode(
        list(texts),
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return [v.tolist() for v in vectors]


def embed_query(query: str) -> list[float]:
    """Embed a user query (same model as documents)."""
    return embed_text(query)


def embedding_dimension() -> int:
    """Return the dimensionality of the current embedding model."""
    model = _get_model()
    return model.get_sentence_embedding_dimension()


def reset_model_cache():
    """Reset cached model (for testing)."""
    global _model, _model_name_loaded
    _model = None
    _model_name_loaded = None
