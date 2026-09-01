"""Central configuration for the QuizLab RAG pipeline."""
import os

# Base paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
CHROMA_PERSIST_DIR = os.path.join(DATA_DIR, "chroma_db")
INGESTION_REGISTRY_PATH = os.path.join(DATA_DIR, "ingestion_registry.json")

# Chunking
CHUNK_SIZE = int(os.environ.get("RAG_CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.environ.get("RAG_CHUNK_OVERLAP", "100"))
MIN_CHUNK_SIZE = int(os.environ.get("RAG_MIN_CHUNK_SIZE", "80"))

# Retrieval
TOP_K = int(os.environ.get("RAG_TOP_K", "5"))
MAX_CONTEXT_CHARS = int(os.environ.get("RAG_MAX_CONTEXT_CHARS", "6000"))

# Embeddings
EMBEDDING_MODEL = os.environ.get(
    "RAG_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)
EMBEDDING_BATCH_SIZE = int(os.environ.get("RAG_EMBEDDING_BATCH_SIZE", "32"))

# ChromaDB
CHROMA_COLLECTION_NAME = os.environ.get(
    "RAG_CHROMA_COLLECTION", "quizlab_documents"
)

# Conversation
MAX_CONVERSATION_TURNS = int(os.environ.get("RAG_MAX_CONVERSATION_TURNS", "6"))

# Hugging Face LLM Configuration
HF_TOKEN_ENV = "HF_TOKEN"
DEFAULT_LLM_MODEL = os.environ.get("HF_MODEL", "meta-llama/Llama-3.3-70B-Instruct")

