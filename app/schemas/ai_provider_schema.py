from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class AIProviderCreate(BaseModel):
    """Schema for registering a new LLM provider config."""
    provider: str = Field(
        ...,
        description="anthropic, openai, gemini, or grok.",
        json_schema_extra={"example": "anthropic"}
    )
    api_key: str = Field(..., description="Your own API key for this provider.")
    default_model: Optional[str] = Field(
        default=None,
        description="Provider-specific model name. Omit to use that provider's default."
    )


class AIProviderResponse(BaseModel):
    """
    Schema for provider-config responses. Does NOT expose api_key, same
    security posture as ConnectionResponse excluding passwords.
    """
    id: int
    provider: str
    default_model: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
