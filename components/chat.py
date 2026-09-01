"""Streamlit UI component for RAG-powered chat with study material."""
import streamlit as st

from rag.pipeline import rag_chat


def render_sources(sources: list[dict]) -> None:
    """Display source citations below a RAG answer."""
    if not sources:
        return
    st.markdown("**Sources:**")
    for src in sources:
        parts = [src.get("document_name", "Document")]
        if src.get("page_number"):
            parts.append(f"Page {src['page_number']}")
        if src.get("chapter"):
            parts.append(src["chapter"])
        st.markdown(f"• {' — '.join(parts)}")


def render_chat_view(
    api_key: str,
    model_name: str,
    session_id: str,
    document_id: str | None = None,
    document_name: str = "Study Material",
) -> None:
    """Render the Chat with My Study Material interface."""
    st.markdown("## 💬 Chat With My Study Material")
    st.markdown(
        f"Ask questions about **{document_name}**. Answers are grounded in your uploaded material."
    )

    if "rag_chat_history" not in st.session_state:
        st.session_state["rag_chat_history"] = []

    # Display chat history
    for msg in st.session_state["rag_chat_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                render_sources(msg["sources"])

    user_input = st.chat_input("Ask about your study material...")
    if user_input:
        if not api_key:
            st.error("Hugging Face Token (HF_TOKEN) is required for chat.")
            return

        st.session_state["rag_chat_history"].append(
            {"role": "user", "content": user_input}
        )

        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Searching your material..."):
                answer, sources, err = rag_chat(
                    user_input,
                    api_key=api_key,
                    model_name=model_name,
                    session_id=session_id,
                    document_id=document_id,
                    conversation=st.session_state["rag_chat_history"][:-1],
                )
            if err:
                st.error(f"Chat failed: {err}")
            else:
                st.markdown(answer)
                render_sources(sources)
                st.session_state["rag_chat_history"].append(
                    {"role": "assistant", "content": answer, "sources": sources}
                )

    if st.session_state["rag_chat_history"]:
        if st.button("🗑️ Clear Chat History", key="clear_rag_chat"):
            st.session_state["rag_chat_history"] = []
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🏠 Back to Knowledge Profile", key="chat_back_home"):
        st.session_state["active_view"] = "extracted_knowledge"
        st.rerun()
