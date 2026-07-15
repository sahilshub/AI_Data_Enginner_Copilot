from app.llm.openai_provider import OpenAIProvider


class GrokProvider(OpenAIProvider):
    """
    xAI's Grok API is OpenAI-SDK-compatible — same request/response shape,
    just a different base_url and model catalog. Reuses OpenAIProvider's
    generate()/test_connection() entirely rather than reimplementing them.
    """

    base_url = "https://api.x.ai/v1"

    @property
    def default_model(self) -> str:
        return "grok-4"
