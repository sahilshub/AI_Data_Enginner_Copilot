from app.llm.openai_provider import OpenAIProvider


class GroqProvider(OpenAIProvider):
    """
    Groq's API is OpenAI-SDK-compatible — same request/response shape, just
    a different base_url and model catalog. Reuses OpenAIProvider's
    generate()/test_connection()/generate_with_tools() entirely rather than
    reimplementing them — tool-calling (Phase 2, Step 4) comes for free.

    Note: Groq (the LPU-based inference company, hosting open models like
    Llama) is a different company from xAI's "Grok" model — easy to mix up
    given the near-identical name. This provider is Groq.
    """

    base_url = "https://api.groq.com/openai/v1"

    @property
    def default_model(self) -> str:
        return "llama-3.3-70b-versatile"
