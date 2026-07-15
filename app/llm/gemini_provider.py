from typing import Optional, Tuple

from google import genai
from google.genai import types

from app.llm.base import LLMProvider


class GeminiProvider(LLMProvider):
    """
    Wraps Google's Gemini API via the google-genai SDK (the current one —
    the older google-generativeai package is fully end-of-life). Uses a
    genai.Client per instance, so unlike the deprecated SDK's process-global
    configure(), two GeminiProvider instances with different keys don't
    interfere with each other.
    """

    @property
    def default_model(self) -> str:
        return "gemini-2.5-flash"

    def test_connection(self) -> Tuple[bool, str]:
        try:
            self.generate("Reply with the single word: OK", system=None)
            return True, "Successfully connected to Gemini."
        except Exception as e:
            return False, f"Connection failure: {str(e)}"

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        client = genai.Client(api_key=self.api_key)
        config = types.GenerateContentConfig(system_instruction=system) if system else None
        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config,
        )
        return response.text
