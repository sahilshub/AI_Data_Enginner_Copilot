import json
from typing import List, Optional, Tuple

from openai import OpenAI

from app.llm.base import LLMProvider, ToolDefinition, ToolExecutor


class OpenAIProvider(LLMProvider):
    """
    Wraps the OpenAI Chat Completions API. Also the base class for
    GroqProvider — Groq's API is OpenAI-SDK-compatible (same request/
    response shape, different base_url and model catalog), so it inherits
    tool-calling support from here for free.
    """

    base_url: Optional[str] = None  # None = OpenAI's default endpoint
    supports_tool_calling = True

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

    def generate_with_tools(
        self,
        question: str,
        system: str,
        tools: List[ToolDefinition],
        tool_executor: ToolExecutor,
        max_rounds: int = 8,
    ) -> str:
        client = OpenAI(api_key=self.api_key, base_url=self.base_url)

        # ToolDefinition is already {"name", "description", "parameters"} —
        # OpenAI just wants it wrapped in a {"type": "function", "function": ...}
        # envelope. No other reshaping needed, which is exactly why OpenAI/Groq
        # were the natural first providers to implement this for.
        openai_tools = [{"type": "function", "function": tool} for tool in tools]

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": question},
        ]

        for _ in range(max_rounds):
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=openai_tools,
                tool_choice="auto",
            )
            message = response.choices[0].message

            if not message.tool_calls:
                return message.content

            # The assistant's tool-call request must be echoed back verbatim
            # before any tool results — OpenAI's API requires that ordering.
            messages.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in message.tool_calls
                ],
            })

            for tool_call in message.tool_calls:
                arguments = json.loads(tool_call.function.arguments or "{}")
                result = tool_executor(tool_call.function.name, arguments)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })

        raise RuntimeError(f"Exceeded max_rounds ({max_rounds}) of tool calls without a final answer.")
