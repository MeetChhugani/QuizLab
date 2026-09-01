"""Hugging Face Inference Provider implementation for QuizLab AI."""
import os
from typing import Any

from huggingface_hub import InferenceClient
from huggingface_hub.utils import HfHubHTTPError

from services.llm.provider import (
    AuthenticationError,
    LLMProvider,
    LLMProviderError,
    ModelUnavailableError,
    RateLimitError,
    TimeoutNetworkError,
)

DEFAULT_HF_MODEL = os.environ.get("HF_MODEL", "meta-llama/Llama-3.3-70B-Instruct")


def _resolve_hf_token(passed_token: str | None = None) -> str:
    """Safely resolve Hugging Face token from explicit arg, env var, or Streamlit secrets."""
    if passed_token and passed_token.strip():
        return passed_token.strip()

    env_token = os.environ.get("HF_TOKEN", "").strip()
    if env_token:
        return env_token

    try:
        import streamlit as st
        secret_token = st.secrets.get("HF_TOKEN", "")
        if secret_token and isinstance(secret_token, str):
            return secret_token.strip()
    except Exception:
        pass

    return ""


class HuggingFaceProvider(LLMProvider):
    """Hugging Face Inference Provider using official huggingface_hub SDK."""

    def __init__(self, token: str | None = None, default_model: str | None = None):
        self.token = token
        self.default_model = default_model or DEFAULT_HF_MODEL

    def generate(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs: Any,
    ) -> str:
        token = _resolve_hf_token(kwargs.get("api_key") or kwargs.get("token") or self.token)
        if not token:
            raise AuthenticationError(
                "Hugging Face Token (HF_TOKEN) is missing. "
                "Please set HF_TOKEN in your .env file or Streamlit secrets."
            )

        model_name = model or self.default_model
        clamped_temp = max(0.01, min(float(temperature), 1.0))

        try:
            client = InferenceClient(token=token, timeout=60.0)
            response = client.chat_completion(
                messages=messages,
                model=model_name,
                temperature=clamped_temp,
                max_tokens=max_tokens,
            )

            if not response.choices or not response.choices[0].message:
                raise LLMProviderError("Empty response received from Hugging Face Inference API.")

            content = response.choices[0].message.content
            return content.strip() if content else ""

        except HfHubHTTPError as exc:
            status_code = getattr(getattr(exc, "response", None), "status_code", None)
            if status_code in (401, 403):
                raise AuthenticationError(
                    f"Hugging Face authentication failed for model '{model_name}'. Please verify HF_TOKEN."
                ) from exc
            elif status_code == 429:
                raise RateLimitError(
                    f"Hugging Face Inference API rate limit reached for model '{model_name}'."
                ) from exc
            elif status_code == 503:
                raise ModelUnavailableError(
                    f"Hugging Face model '{model_name}' is currently loading or unavailable."
                ) from exc
            else:
                raise LLMProviderError(
                    f"Hugging Face Inference error ({status_code or 'HTTP Error'}): {exc}"
                ) from exc

        except (AuthenticationError, RateLimitError, ModelUnavailableError, TimeoutNetworkError):
            raise

        except Exception as exc:
            err_str = str(exc).lower()
            if "timeout" in err_str or "connection" in err_str:
                raise TimeoutNetworkError(
                    f"Network error connecting to Hugging Face Inference API: {exc}"
                ) from exc
            raise LLMProviderError(f"Hugging Face inference execution failed: {exc}") from exc
