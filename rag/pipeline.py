"""High-level RAG pipeline orchestration for QuizLab."""
from typing import Any

from rag.config import DEFAULT_LLM_MODEL, MAX_CONVERSATION_TURNS, TOP_K
from rag.ingestion import IngestionError, ingest_document
from rag.prompts import (
    NO_CONTEXT_RESPONSE,
    RAG_CHAT_SYSTEM,
    RAG_FLASHCARD_GENERATION,
    RAG_QUERY_REWRITE,
    RAG_QUIZ_GENERATION,
    RAG_SINGLE_QUESTION,
)
from rag.retriever import (
    build_context,
    format_sources,
    has_useful_context,
    retrieve,
)
from services.llm import get_llm_provider
from utils import _clean_and_parse_json


def _llm_error_message(exc: Exception | None = None) -> str:
    """Return an actionable provider error including the raw exception detail."""
    detail = f" | Detail: {exc}" if exc else ""
    return f"Hugging Face API error{detail}"


def get_session_id(st_session_state: dict | None = None) -> str:
    """Derive an isolation key for vector storage (future multi-user support)."""
    if st_session_state and st_session_state.get("rag_session_id"):
        return st_session_state["rag_session_id"]
    return "default"


def index_uploaded_content(
    *,
    pages: list[dict] | None = None,
    text: str | None = None,
    document_name: str,
    content_hash: str,
    session_id: str = "default",
) -> dict:
    """Index document into vector store. Returns ingestion result."""
    return ingest_document(
        pages=pages,
        text=text,
        document_name=document_name,
        content_hash=content_hash,
        session_id=session_id,
    )


def _rewrite_query_for_retrieval(
    question: str,
    conversation: list[dict],
    api_key: str,
    model_name: str,
) -> str:
    """Use LLM to expand follow-up questions into standalone retrieval queries."""
    if not conversation:
        return question

    recent = conversation[-MAX_CONVERSATION_TURNS:]
    conv_text = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in recent
    )
    prompt = RAG_QUERY_REWRITE.format(conversation=conv_text, question=question)

    try:
        provider = get_llm_provider(token=api_key, default_model=model_name)
        rewritten = provider.generate(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=150,
        )
        return rewritten if rewritten else question
    except Exception:
        return question


def _format_conversation_context(conversation: list[dict]) -> str:
    if not conversation:
        return ""
    recent = conversation[-MAX_CONVERSATION_TURNS:]
    lines = [f"{m['role'].title()}: {m['content']}" for m in recent]
    return "RECENT CONVERSATION:\n" + "\n".join(lines)


def rag_chat(
    question: str,
    *,
    api_key: str,
    model_name: str = DEFAULT_LLM_MODEL,
    session_id: str = "default",
    document_id: str | None = None,
    conversation: list[dict] | None = None,
    top_k: int | None = None,
) -> tuple[str, list[dict], str | None]:
    """
    RAG-powered chat. Returns (answer, sources, error).
    """
    conversation = conversation or []

    retrieval_query = _rewrite_query_for_retrieval(
        question, conversation, api_key, model_name
    )
    chunks = retrieve(
        retrieval_query,
        top_k=top_k or TOP_K,
        session_id=session_id,
        document_id=document_id,
    )

    if not has_useful_context(chunks):
        return NO_CONTEXT_RESPONSE, [], None

    context = build_context(chunks)
    conv_ctx = _format_conversation_context(conversation)
    prompt = RAG_CHAT_SYSTEM.format(
        retrieved_context=context,
        conversation_context=conv_ctx,
        question=question,
    )

    try:
        provider = get_llm_provider(token=api_key, default_model=model_name)
        answer = provider.generate(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1500,
        )
        sources = format_sources(chunks)
        return answer, sources, None
    except Exception as exc:
        return "", [], _llm_error_message(exc)


def rag_generate_learning_material(
    retrieval_query: str,
    custom_focus: str,
    api_key: str,
    model_name: str = DEFAULT_LLM_MODEL,
    session_id: str = "default",
    document_id: str | None = None,
    temperature: float = 0.35,
    seed: int = 0,
    top_k: int | None = None,
) -> tuple[dict | None, str | None]:
    """Generate quiz + flashcards grounded in retrieved chunks."""
    query = custom_focus.strip() or retrieval_query or "key concepts and definitions"
    chunks = retrieve(
        query,
        top_k=top_k or TOP_K,
        session_id=session_id,
        document_id=document_id,
    )

    if not chunks:
        return None, "No relevant content found in indexed documents. Please upload and index material first."

    context = build_context(chunks)
    focus_instruction = (
        f"- Focus specifically on: '{custom_focus}'." if custom_focus.strip() else ""
    )
    seed_instruction = (
        f"\n- Session seed: {seed}. Vary question focus across sessions."
        if seed
        else ""
    )

    prompt = RAG_QUIZ_GENERATION.format(
        retrieved_context=context,
        focus_instruction=focus_instruction,
        seed_instruction=seed_instruction,
    )

    try:
        provider = get_llm_provider(token=api_key, default_model=model_name)
        raw = provider.generate(
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=4096,
        )
        data = _clean_and_parse_json(raw)
        if "analysis" not in data or "questions" not in data or "flashcards" not in data:
            raise ValueError("Missing critical fields in RAG generation response.")
        data["_rag_sources"] = format_sources(chunks)
        return data, None
    except Exception as exc:
        return None, _llm_error_message(exc)


def rag_generate_flashcards(
    topic: str,
    count: int,
    api_key: str,
    model_name: str = DEFAULT_LLM_MODEL,
    session_id: str = "default",
    document_id: str | None = None,
) -> tuple[list | None, str | None]:
    """Generate flashcards from retrieved content."""
    chunks = retrieve(
        topic or "important concepts",
        top_k=TOP_K,
        session_id=session_id,
        document_id=document_id,
    )
    if not chunks:
        return None, "No relevant content found for flashcard generation."

    context = build_context(chunks)
    focus = f"Focus on topic: {topic}" if topic else ""
    prompt = RAG_FLASHCARD_GENERATION.format(
        retrieved_context=context,
        focus_instruction=focus,
        count=count,
    )

    try:
        provider = get_llm_provider(token=api_key, default_model=model_name)
        raw = provider.generate(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=2000,
        )
        data = _clean_and_parse_json(raw)
        if isinstance(data, dict) and "flashcards" in data:
            data = data["flashcards"]
        return data, None
    except Exception as exc:
        return None, _llm_error_message(exc)
