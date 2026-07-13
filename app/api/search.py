from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.schemas.search_schema import SearchResponse
from app.services.search_service import SearchService

router = APIRouter(tags=["Schema Search"])


@router.get(
    "/search",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search the metadata catalog",
    description=(
        "Performs a case-insensitive keyword search across all synced tables, "
        "columns, and relationships in the local metadata catalog. "
        "Optionally scope results to a single connection using `connection_id`. "
        "Run metadata sync and relationship discovery before searching."
    ),
)
def search_catalog(
    q: str = Query(..., min_length=1, description="Keyword to search for."),
    connection_id: Optional[int] = Query(
        None,
        description="Restrict search to a specific connection. Omit to search all connections."
    ),
    db: Session = Depends(get_db),
) -> SearchResponse:
    """
    Thin HTTP handler — validates query params, delegates to SearchService.
    No business logic lives here.
    """
    service = SearchService(db)
    return service.search(query=q, connection_id=connection_id)
