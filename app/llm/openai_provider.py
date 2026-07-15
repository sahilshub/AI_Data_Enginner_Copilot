from typing import Optional, Tuple

from openai import OpenAI

from app.llm.base import LLMProvider


class OpenAIProvider(LLMProvider):
    """
    Wraps the OpenAI Chat Completions API. Also the base class for
    GrokProvider — xAI's API is OpenAI-SDK-compatible (same request/response
    shape, different base_url and model catalog).
    """

    base_url: Optional[str] = None  # None = OpenAI's default endpoint

    @property
    def default_model(self) -> str:
        return "gpt-4o-mini"

    def test_connection(self) -> Tuple[bool, str]:
        try:
            self.generate("Reply with the single word: OK", system=None)
            return True, "Successfully connected."
        except Exception as e:
            return False, f"Connection failure: {str(e)}"

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        return response.choices[0].message.content
