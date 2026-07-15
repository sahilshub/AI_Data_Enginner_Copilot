from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List

from app.repositories.ai_provider_repository import AIProviderRepository
from app.llm.factory import is_supported_provider, get_llm_provider
from app.schemas.ai_provider_schema import AIProviderCreate
from app.models.ai_provider_config import AIProviderConfig


class AIProviderService:
    """
    Service layer for registering/listing/deleting LLM provider configs.
    Mirrors ConnectionService's shape: reject unsupported provider names up
    front, verify the key actually works before saving, encrypt at rest.
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

        return self.repo.create(schema_in.provider, schema_in.api_key, schema_in.default_model)

    def get_providers(self) -> List[AIProviderConfig]:
        return self.repo.get_all()

    def delete_provider(self, provider_id: int) -> None:
        provider = self.repo.get_by_id(provider_id)
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AI provider config with ID {provider_id} not found."
            )
        self.repo.delete(provider)
