from typing import Optional

from fastapi import HTTPException, status

from app.llm.base import LLMProvider
from app.llm.anthropic_provider import AnthropicProvider
from app.llm.openai_provider import OpenAIProvider
from app.llm.gemini_provider import GeminiProvider
from app.llm.groq_provider import GroqProvider

# Every provider this app can actually call today. Add an entry here (and a
# provider class) when a new one is implemented — nothing else needs to
# change. Same pattern as app/connectors/factory.py for database sources.
_PROVIDERS = {
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "groq": GroqProvider,
}


def get_llm_provider(provider: str, api_key: str, model: Optional[str] = None) -> LLMProvider:
    """
    Resolves a provider name to an LLMProvider instance. Raises 400 for an
    unsupported provider immediately, rather than failing confusingly later
    inside a generation call.
    """
    provider_cls = _PROVIDERS.get(provider)
    if provider_cls is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Provider '{provider}' is not yet supported. "
                f"Currently supported: {', '.join(sorted(_PROVIDERS.keys()))}."
            ),
        )
    return provider_cls(api_key=api_key, model=model)


def is_supported_provider(provider: str) -> bool:
    """Used at registration time to reject unsupported providers up front."""
    return provider in _PROVIDERS
