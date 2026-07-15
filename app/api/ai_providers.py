from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.ai_provider_schema import AIProviderCreate, AIProviderResponse
from app.services.ai_provider_service import AIProviderService

router = APIRouter(prefix="/ai/providers", tags=["AI Providers"])


@router.post(
    "",
    response_model=AIProviderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register an LLM provider",
    description=(
        "Registers a hosted LLM provider (anthropic, openai, gemini, or grok) with your "
        "own API key. Verifies the key works before saving. The key is encrypted at rest "
        "and never returned in responses."
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


@router.delete(
    "/{provider_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an LLM provider config",
)
def delete_provider(provider_id: int, db: Session = Depends(get_db)) -> None:
    service = AIProviderService(db)
    service.delete_provider(provider_id)
