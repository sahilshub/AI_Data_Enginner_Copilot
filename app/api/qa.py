from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.qa_schema import QARequest, QAResponse
from app.services.qa_service import QAService

router = APIRouter(prefix="/connections/{connection_id}", tags=["Schema Q&A"])


@router.post(
    "/ask",
    response_model=QAResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask a natural-language question about this connection's schema",
    description=(
        "Answers a question using the connection's stored metadata catalog (tables, columns, "
        "relationships) as context, via a registered LLM provider. Requires at least one "
        "provider registered via POST /ai/providers. See docs/phase-2/step-1.md."
    ),
)
def ask_question(connection_id: int, request: QARequest, db: Session = Depends(get_db)) -> QAResponse:
    service = QAService(db)
    return service.ask(connection_id, request)
