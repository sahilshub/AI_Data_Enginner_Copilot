from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from app.core.database import Base


class AIProviderConfig(Base):
    """
    ORM model representing the 'ai_provider_configs' table — a
    user-registered LLM provider (Anthropic, OpenAI, Gemini, or Grok) plus
    their own API key, used to answer natural-language questions (Phase 2,
    Step 1). Bring-your-own-key: the app never ships with or defaults to
    any provider's key.
    """
    __tablename__ = "ai_provider_configs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    provider = Column(String, nullable=False, comment="anthropic, openai, gemini, or grok.")
    api_key = Column(String, nullable=False)  # Fernet-encrypted at rest — see app/core/security.py.
    default_model = Column(String, nullable=True, comment="Provider-specific model name; falls back to that provider's own default if unset.")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
