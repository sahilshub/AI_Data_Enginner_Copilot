from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

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

    def create(self, provider: str, api_key: str, default_model: Optional[str], is_active: bool = False) -> AIProviderConfig:
        record = AIProviderConfig(
            provider=provider,
            api_key=encrypt_password(api_key),
            default_model=default_model,
            is_active=is_active,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def count(self) -> int:
        """Used to detect whether a new registration is the first ever (see AIProviderService)."""
        return self.db.query(AIProviderConfig).count()

    def get_all(self) -> List[AIProviderConfig]:
        return self.db.query(AIProviderConfig).order_by(AIProviderConfig.created_at.desc()).all()

    def get_by_id(self, provider_id: int) -> Optional[AIProviderConfig]:
        return self.db.query(AIProviderConfig).filter(AIProviderConfig.id == provider_id).first()

    def get_active(self) -> Optional[AIProviderConfig]:
        """The one provider every AI feature uses (Phase 2, Step 3)."""
        return self.db.query(AIProviderConfig).filter(AIProviderConfig.is_active.is_(True)).first()

    def get_most_recent_excluding(self, provider_id: int) -> Optional[AIProviderConfig]:
        """
        Used to auto-promote a replacement active provider when the
        currently-active one is deleted (see AIProviderService.delete_provider).
        """
        return (
            self.db.query(AIProviderConfig)
            .filter(AIProviderConfig.id != provider_id)
            .order_by(AIProviderConfig.created_at.desc())
            .first()
        )

    def set_active(self, provider_id: int) -> AIProviderConfig:
        """
        Marks provider_id as the sole active provider, unsetting every
        other row first. Raises nothing — caller (AIProviderService) is
        responsible for confirming provider_id exists before calling this.
        """
        self.db.query(AIProviderConfig).filter(AIProviderConfig.id != provider_id).update(
            {"is_active": False}
        )
        record = self.get_by_id(provider_id)
        record.is_active = True
        self.db.commit()
        self.db.refresh(record)
        return record

    def update(self, db_obj: AIProviderConfig, updates: Dict[str, Any]) -> AIProviderConfig:
        """
        Applies a partial update to an existing provider-config.
        `updates` should only contain keys the caller actually wants to
        change (already filtered — see AIProviderService.update_provider).
        Encrypts `api_key` if it's one of the provided keys.
        """
        for field, value in updates.items():
            if field == "api_key":
                value = encrypt_password(value)
            setattr(db_obj, field, value)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, db_obj: AIProviderConfig) -> None:
        self.db.delete(db_obj)
        self.db.commit()
