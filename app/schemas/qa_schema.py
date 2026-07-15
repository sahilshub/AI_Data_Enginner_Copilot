from pydantic import BaseModel, Field
from typing import Optional


class QARequest(BaseModel):
    """Request payload for asking a natural-language question about a connection's schema."""
    question: str = Field(..., min_length=1, description="Natural-language question about this connection's schema.")
    provider_id: Optional[int] = Field(
        default=None,
        description="Which registered AI provider to use. Omit to use the most recently registered one."
    )


class QAResponse(BaseModel):
    """Response containing the LLM-generated answer."""
    answer: str = Field(..., description="The provider's generated answer.")
    provider: str = Field(..., description="Which provider answered (anthropic, openai, gemini, or grok).")
    model: str = Field(..., description="Which model was used.")
