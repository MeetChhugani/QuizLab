"""Abstract LLM Provider interface for QuizLab AI."""
from abc import ABC, abstractmethod


class LLMProviderError(Exception):
    """Base exception for LLM provider errors."""
    pass


class AuthenticationError(LLMProviderError):
    """Raised when authentication (token/key) is missing or invalid."""
    pass


class ModelUnavailableError(LLMProviderError):
    """Raised when the requested LLM model is loading or unavailable."""
    pass


class RateLimitError(LLMProviderError):
    """Raised when provider rate limits are exceeded."""
    pass


class TimeoutNetworkError(LLMProviderError):
    """Raised on network connection or timeout issues."""
    pass


class LLMProvider(ABC):
    """Abstract base class defining the provider-agnostic interface for LLM inference."""

    @abstractmethod
    def generate(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs: dict,
    ) -> str:
        """
        Generate text/chat completion from messages.

        Args:
            messages: List of message dicts with 'role' ('system', 'user', 'assistant') and 'content'.
            model: Optional model name to override default.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in generated response.
            **kwargs: Additional provider-specific parameters.

        Returns:
            The generated assistant text response string.
        """
        pass
