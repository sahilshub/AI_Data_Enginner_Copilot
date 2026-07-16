from pydantic import BaseModel, Field


class QARequest(BaseModel):
    """
    Request payload for asking a natural-language question about a
    connection's schema. No provider selection here — every AI task uses
    whichever provider is currently active (Phase 2, Step 3); switch it
    via PATCH /ai/providers/{id}/activate, not per request.
    """
    question: str = Field(..., min_length=1, description="Natural-language question about this connection's schema.")


class QAResponse(BaseModel):
    """Response containing the LLM-generated answer."""
    answer: str = Field(..., description="The provider's generated answer.")
    provider: str = Field(..., description="Which provider answered (anthropic, openai, gemini, or groq).")
    model: str = Field(..., description="Which model was used.")
