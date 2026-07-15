from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.ai_provider_config import AIProviderConfig
from app.core.security import encrypt_password


class AIProviderRepository:
    """
    Repository for registered LLM provider configs. Mirrors
    ConnectionRepository's shape (app/repositories/connection_repository.py)
    — same encrypt-on-write pattern, reusing app/core/security.py rather
    than inventing a second encryption approach for a second kind of secret.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, provider: str, api_key: str, default_model: Optional[str]) -> AIProviderConfig:
        record = AIProviderConfig(
            provider=provider,
            api_key=encrypt_password(api_key),
            default_model=default_model,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_all(self) -> List[AIProviderConfig]:
        return self.db.query(AIProviderConfig).order_by(AIProviderConfig.created_at.desc()).all()

    def get_by_id(self, provider_id: int) -> Optional[AIProviderConfig]:
        return self.db.query(AIProviderConfig).filter(AIProviderConfig.id == provider_id).first()

    def get_most_recent(self) -> Optional[AIProviderConfig]:
        """
        Used to resolve a default provider when /ask is called without an
        explicit provider_id. Simple "most recently registered" — no
        separate is_default flag yet; add one if this stops being good
        enough once multiple providers are commonly registered at once.
        """
        return self.db.query(AIProviderConfig).order_by(AIProviderConfig.created_at.desc()).first()

    def delete(self, db_obj: AIProviderConfig) -> None:
        self.db.delete(db_obj)
        self.db.commit()
