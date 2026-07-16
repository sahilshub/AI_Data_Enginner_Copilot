from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Tuple

# Canonical, provider-agnostic tool definition shape — matches OpenAI's
# function-calling schema directly (name/description/parameters as JSON
# Schema), which is why OpenAI/Groq needed no translation layer to be the
# first providers implemented (Phase 2, Step 4). A provider whose wire
# format differs (Anthropic's input_schema, Gemini's FunctionDeclaration)
# translates from this shape internally — callers (QAService) never see
# provider-specific formats.
ToolDefinition = Dict[str, Any]

# (tool_name, arguments) -> result text. Supplied by the caller (QAService)
# so LLMProvider implementations never need to know what a tool actually
# does — only how to run the request/tool-call/result loop with a provider.
ToolExecutor = Callable[[str, Dict[str, Any]], str]


class LLMProvider(ABC):
    """
    Interface every hosted LLM provider (Anthropic, OpenAI, Gemini, Groq,
    and later any other) must implement. Services depend on this interface
    only — never on a specific provider's SDK shape. Same pattern as
    SourceConnector (app/connectors/base.py) for database sources.

    Bring-your-own-key: the app never ships with or defaults to a key —
    api_key always comes from a user-registered AIProviderConfig.
    """

    #: Whether generate_with_tools() has a real implementation for this
    #: provider. False by default — only providers that actually implement
    #: tool-calling (OpenAI, and Groq by inheriting it) set this True.
    #: Callers (QAService) check this and fail clearly rather than letting
    #: the default generate_with_tools() raise a confusing error deep in a
    #: request. See docs/phase-2/step-4.md.
    supports_tool_calling: bool = False

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

    def generate_with_tools(
        self,
        question: str,
        system: str,
        tools: List[ToolDefinition],
        tool_executor: ToolExecutor,
        max_rounds: int = 8,
    ) -> str:
        """
        Runs an adaptive request/tool-call/result loop: the model decides
        whether to call one of `tools`, receives the result via
        `tool_executor`, and repeats — up to max_rounds — until it returns
        a final answer with no further tool calls.

        Default implementation refuses — only providers that actually
        implement this (OpenAIProvider, and GroqProvider by inheriting it)
        should be usable for /ask. Not an @abstractmethod because
        LLMProvider subclasses without tool-calling support (Anthropic,
        Gemini, for now) still need to be instantiable for plain
        generate() calls elsewhere (provider registration's test_connection()).
        """
        raise NotImplementedError(
            f"{type(self).__name__} does not support tool-calling yet. "
            f"Activate an OpenAI or Groq provider for /ask."
        )
