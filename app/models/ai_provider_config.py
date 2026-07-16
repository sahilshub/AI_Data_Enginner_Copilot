from sqlalchemy import Boolean, Column, Integer, String, DateTime
from sqlalchemy.sql import func

from app.core.database import Base


class AIProviderConfig(Base):
    """
    ORM model representing the 'ai_provider_configs' table — a
    user-registered LLM provider (Anthropic, OpenAI, Gemini, or Groq) plus
    their own API key, used for AI-related tasks (Phase 2, Step 1).
    Bring-your-own-key: the app never ships with or defaults to any
    provider's key.

    Exactly one row can have is_active=True at a time (Phase 2, Step 3) —
    that's the provider every AI feature uses. Enforced both here (see
    AIProviderRepository.set_active()) and at the DB level via a partial
    unique index (see the Step 3 migration) as defense in depth.
    """
    __tablename__ = "ai_provider_configs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    provider = Column(String, nullable=False, comment="anthropic, openai, gemini, or groq.")
    api_key = Column(String, nullable=False)  # Fernet-encrypted at rest — see app/core/security.py.
    default_model = Column(String, nullable=True, comment="Provider-specific model name; falls back to that provider's own default if unset.")
    is_active = Column(Boolean, nullable=False, default=False, comment="The one provider all AI tasks use. At most one row is ever True.")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
