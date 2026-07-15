from abc import ABC, abstractmethod
from typing import Optional, Tuple


class LLMProvider(ABC):
    """
    Interface every hosted LLM provider (Anthropic, OpenAI, Gemini, Grok,
    and later any other) must implement. Services depend on this interface
    only — never on a specific provider's SDK shape. Same pattern as
    SourceConnector (app/connectors/base.py) for database sources.

    Bring-your-own-key: the app never ships with or defaults to a key —
    api_key always comes from a user-registered AIProviderConfig.
    """

    def __init__(self, api_key: str, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model or self.default_model

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Model to use when the user didn't specify one at registration time."""
        raise NotImplementedError

    @abstractmethod
    def test_connection(self) -> Tuple[bool, str]:
        """Returns (success, message) without raising on failure."""
        raise NotImplementedError

    @abstractmethod
    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        """
        Sends prompt (+ optional system instructions) to the provider and
        returns the generated text response.
        """
        raise NotImplementedError
