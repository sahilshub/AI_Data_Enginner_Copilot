from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List

from app.core.security import decrypt_password
from app.repositories.ai_provider_repository import AIProviderRepository
from app.llm.factory import is_supported_provider, get_llm_provider
from app.schemas.ai_provider_schema import AIProviderCreate, AIProviderUpdate
from app.models.ai_provider_config import AIProviderConfig


class AIProviderService:
    """
    Service layer for registering/listing/activating/deleting LLM provider
    configs. Mirrors ConnectionService's shape: reject unsupported provider
    names up front, verify the key actually works before saving, encrypt
    at rest.

    Exactly one provider is "active" at a time (Phase 2, Step 3) — every AI
    feature (QAService today, others later) reads AIProviderRepository.get_active()
    rather than accepting a per-call provider selection.
    """

    def __init__(self, db: Session):
        self.repo = AIProviderRepository(db)

    def register_provider(self, schema_in: AIProviderCreate) -> AIProviderConfig:
        if not is_supported_provider(schema_in.provider):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Provider '{schema_in.provider}' is not yet supported."
            )

        # Verify the key actually works before persisting it — same
        # business rule ConnectionService.create_connection enforces for
        # database credentials.
        llm = get_llm_provider(schema_in.provider, schema_in.api_key, schema_in.default_model)
        success, message = llm.test_connection()
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Provider verification failed: {message}"
            )

        # The very first provider ever registered becomes active
        # automatically — otherwise /ask (and everything else) would 400
        # immediately after the one obvious setup step a new user just did.
        # Every later registration stays inactive until explicitly activated.
        is_first_provider = self.repo.count() == 0

        return self.repo.create(
            schema_in.provider, schema_in.api_key, schema_in.default_model, is_active=is_first_provider
        )

    def get_providers(self) -> List[AIProviderConfig]:
        return self.repo.get_all()

    def activate_provider(self, provider_id: int) -> AIProviderConfig:
        if not self.repo.get_by_id(provider_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AI provider config with ID {provider_id} not found."
            )
        return self.repo.set_active(provider_id)

    def delete_provider(self, provider_id: int) -> None:
        provider = self.repo.get_by_id(provider_id)
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AI provider config with ID {provider_id} not found."
            )

        was_active = provider.is_active
        self.repo.delete(provider)

        if was_active:
            # Keep AI features working rather than silently going dark —
            # auto-promote the most recently registered remaining provider.
            replacement = self.repo.get_most_recent_excluding(provider_id)
            if replacement:
                self.repo.set_active(replacement.id)

    def update_provider(self, provider_id: int, schema_in: AIProviderUpdate) -> AIProviderConfig:
        """
        Partially updates a registered provider-config (api_key and/or
        default_model — never is_active, see AIProviderUpdate's docstring).
        Re-verifies the merged (existing + updated) credentials work before
        saving — same business rule ConnectionService.update_connection
        enforces for database connections.
        """
        provider = self.repo.get_by_id(provider_id)
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AI provider config with ID {provider_id} not found."
            )

        updates = schema_in.model_dump(exclude_unset=True, exclude_none=True)
        if not updates:
            return provider

        merged_api_key = updates.get("api_key") or decrypt_password(provider.api_key)
        merged_model = updates.get("default_model", provider.default_model)

        llm = get_llm_provider(provider.provider, merged_api_key, merged_model)
        success, message = llm.test_connection()
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Provider verification failed: {message}"
            )

        return self.repo.update(provider, updates)
