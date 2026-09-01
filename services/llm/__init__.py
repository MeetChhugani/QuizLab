"""LLM Provider package for QuizLab AI."""
from services.llm.huggingface import DEFAULT_HF_MODEL, HuggingFaceProvider
from services.llm.provider import (
    AuthenticationError,
    LLMProvider,
    LLMProviderError,
    ModelUnavailableError,
    RateLimitError,
    TimeoutNetworkError,
)


def get_llm_provider(
    token: str | None = None,
    default_model: str | None = None,
    provider_name: str = "huggingface",
) -> LLMProvider:
    """
    Factory function returning an initialized LLMProvider instance.

    Args:
        token: Optional API token/key.
        default_model: Optional default model identifier.
        provider_name: Provider identifier (default 'huggingface').

    Returns:
        An instance of LLMProvider interface.
    """
    if provider_name.lower() in ("huggingface", "hf"):
        return HuggingFaceProvider(token=token, default_model=default_model)

    raise ValueError(f"Unsupported LLM provider: '{provider_name}'")


__all__ = [
    "LLMProvider",
    "LLMProviderError",
    "AuthenticationError",
    "ModelUnavailableError",
    "RateLimitError",
    "TimeoutNetworkError",
    "HuggingFaceProvider",
    "DEFAULT_HF_MODEL",
    "get_llm_provider",
]
