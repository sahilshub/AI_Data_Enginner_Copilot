from typing import Optional, Tuple

import anthropic

from app.llm.base import LLMProvider


class AnthropicProvider(LLMProvider):
    """Wraps the Anthropic Messages API (Claude models)."""

    @property
    def default_model(self) -> str:
        return "claude-sonnet-4-5"

    def test_connection(self) -> Tuple[bool, str]:
        try:
            self.generate("Reply with the single word: OK", system=None)
            return True, "Successfully connected to Anthropic."
        except Exception as e:
            return False, f"Connection failure: {str(e)}"

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        client = anthropic.Anthropic(api_key=self.api_key)
        kwargs = {
            "model": self.model,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system
        response = client.messages.create(**kwargs)
        return response.content[0].text
