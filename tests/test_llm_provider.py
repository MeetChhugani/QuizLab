"""Unit tests for the LLM Provider abstraction and Hugging Face integration."""
from unittest.mock import MagicMock, patch

import pytest

from services.llm import (
    AuthenticationError,
    HuggingFaceProvider,
    LLMProviderError,
    ModelUnavailableError,
    RateLimitError,
    TimeoutNetworkError,
    get_llm_provider,
)


def test_get_llm_provider_factory():
    provider = get_llm_provider(token="hf_test_123", provider_name="huggingface")
    assert isinstance(provider, HuggingFaceProvider)
    assert provider.token == "hf_test_123"

    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        get_llm_provider(provider_name="unsupported_provider")


def test_huggingface_provider_missing_token(monkeypatch):
    monkeypatch.delenv("HF_TOKEN", raising=False)
    provider = HuggingFaceProvider(token="")
    with pytest.raises(AuthenticationError, match="HF_TOKEN"):
        provider.generate([{"role": "user", "content": "Hello"}])


def test_huggingface_provider_successful_generate():
    provider = HuggingFaceProvider(token="hf_test_token")

    mock_chat_completion = MagicMock()
    mock_chat_completion.choices = [
        MagicMock(message=MagicMock(content="Sample response text"))
    ]

    with patch("services.llm.huggingface.InferenceClient") as mock_client_cls:
        mock_instance = MagicMock()
        mock_instance.chat_completion.return_value = mock_chat_completion
        mock_client_cls.return_value = mock_instance

        result = provider.generate([{"role": "user", "content": "Hello"}])
        assert result == "Sample response text"
        mock_client_cls.assert_called_once_with(token="hf_test_token", timeout=60.0)


def test_huggingface_provider_error_mapping():
    from huggingface_hub.utils import HfHubHTTPError

    provider = HuggingFaceProvider(token="hf_test_token")

    with patch("services.llm.huggingface.InferenceClient") as mock_client_cls:
        mock_instance = MagicMock()
        
        # Test 401 Authentication error
        mock_response_401 = MagicMock(status_code=401)
        mock_instance.chat_completion.side_effect = HfHubHTTPError("Unauthorized", response=mock_response_401)
        mock_client_cls.return_value = mock_instance
        with pytest.raises(AuthenticationError):
            provider.generate([{"role": "user", "content": "Hello"}])

        # Test 429 Rate limit error
        mock_response_429 = MagicMock(status_code=429)
        mock_instance.chat_completion.side_effect = HfHubHTTPError("Rate Limit", response=mock_response_429)
        with pytest.raises(RateLimitError):
            provider.generate([{"role": "user", "content": "Hello"}])

        # Test 503 Model unavailable error
        mock_response_503 = MagicMock(status_code=503)
        mock_instance.chat_completion.side_effect = HfHubHTTPError("Loading", response=mock_response_503)
        with pytest.raises(ModelUnavailableError):
            provider.generate([{"role": "user", "content": "Hello"}])
