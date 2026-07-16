from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.ai_provider_schema import AIProviderCreate, AIProviderResponse, AIProviderUpdate
from app.services.ai_provider_service import AIProviderService

router = APIRouter(prefix="/ai/providers", tags=["AI Providers"])


@router.post(
    "",
    response_model=AIProviderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register an LLM provider",
    description=(
        "Registers a hosted LLM provider (anthropic, openai, gemini, or groq) with your "
        "own API key. Verifies the key works before saving. The key is encrypted at rest "
        "and never returned in responses. The first provider ever registered becomes "
        "active automatically; later ones stay inactive until activated via "
        "PATCH /ai/providers/{provider_id}/activate."
    ),
)
def register_provider(schema_in: AIProviderCreate, db: Session = Depends(get_db)) -> AIProviderResponse:
    service = AIProviderService(db)
    return service.register_provider(schema_in)


@router.get(
    "",
    response_model=List[AIProviderResponse],
    status_code=status.HTTP_200_OK,
    summary="List registered LLM providers",
    description="Returns all registered provider configs. API keys are never included.",
)
def get_providers(db: Session = Depends(get_db)) -> List[AIProviderResponse]:
    service = AIProviderService(db)
    return service.get_providers()


@router.patch(
    "/{provider_id}/activate",
    response_model=AIProviderResponse,
    status_code=status.HTTP_200_OK,
    summary="Set this as the active AI provider",
    description=(
        "Marks this provider as the one all AI tasks (ask, and future AI features) use, "
        "deactivating whichever provider was previously active. Exactly one provider is "
        "ever active — see docs/phase-2/step-3.md."
    ),
)
def activate_provider(provider_id: int, db: Session = Depends(get_db)) -> AIProviderResponse:
    service = AIProviderService(db)
    return service.activate_provider(provider_id)


@router.delete(
    "/{provider_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an LLM provider config",
    description=(
        "Deletes a registered provider. If it was the active one and other providers "
        "remain, the most recently registered of those is auto-promoted to active."
    ),
)
def delete_provider(provider_id: int, db: Session = Depends(get_db)) -> None:
    service = AIProviderService(db)
    service.delete_provider(provider_id)

@router.patch(
    "/{provider_id}",
    response_model=AIProviderResponse,
    status_code=status.HTTP_200_OK,
    summary="Update an LLM provider config",
    description=(
        "Partially updates a registered provider's api_key and/or default_model — only "
        "fields provided are changed, api_key can be omitted to keep the existing one. "
        "Re-verifies the merged credentials work before saving. Does not accept is_active — "
        "use PATCH /ai/providers/{provider_id}/activate to switch the active provider."
    ),
)
def update_provider(provider_id: int, schema_in: AIProviderUpdate, db: Session = Depends(get_db)) -> AIProviderResponse:
    """
    Updates provider-config by ID. Raises 404 if the provider profile is not found.
    """
    service = AIProviderService(db)
    return service.update_provider(provider_id, schema_in)
