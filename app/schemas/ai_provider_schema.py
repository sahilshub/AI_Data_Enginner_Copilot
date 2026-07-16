from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class AIProviderCreate(BaseModel):
    """Schema for registering a new LLM provider config."""
    provider: str = Field(
        ...,
        description="anthropic, openai, gemini, or groq.",
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
    is_active: bool = Field(..., description="Whether this is the one provider all AI tasks currently use.")
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AIProviderUpdate(BaseModel):
    """
    Schema for partially updating a provider config. Every field is
    optional — only the ones provided are changed. `api_key` is optional
    too: omit it to keep the existing (encrypted) one, same reasoning as
    ConnectionUpdate.password.

    Deliberately has no `is_active` field. Activation must go through
    PATCH /ai/providers/{id}/activate (AIProviderRepository.set_active()),
    which unsets every other provider first — setting is_active directly
    through a general update would bypass that and could violate the
    "exactly one active" DB constraint (Phase 2, Step 3).
    """
    api_key: Optional[str] = Field(default=None, description="New API key. Omit to keep the existing one.")
    default_model: Optional[str] = Field(
        default=None,
        description="New provider-specific model name."
    )
