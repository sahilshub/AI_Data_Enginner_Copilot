from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.schemas.search_schema import (
    SearchResponse,
    TableSearchResult,
    ColumnSearchResult,
    RelationshipSearchResult,
)
from app.services.search_service import SearchService

router = APIRouter(tags=["Schema Search"])


@router.get(
    "/search/tables",
    response_model=List[TableSearchResult],
    status_code=status.HTTP_200_OK,
    summary="Search tables in the metadata catalog",
    description=(
        "Performs a case-insensitive keyword search across synced table names "
        "in the local metadata catalog. Optionally scope results to a single "
        "connection using `connection_id`."
    ),
)
def search_tables(
    q: str = Query(..., min_length=1, description="Keyword to search for."),
    connection_id: Optional[int] = Query(
        None,
        description="Restrict search to a specific connection. Omit to search all connections."
    ),
    db: Session = Depends(get_db),
) -> List[TableSearchResult]:
    """
    Thin HTTP handler — validates query params, delegates to SearchService.
    No business logic lives here.
    """
    service = SearchService(db)
    return service.search_tables(query=q, connection_id=connection_id)


@router.get(
    "/search/columns",
    response_model=List[ColumnSearchResult],
    status_code=status.HTTP_200_OK,
    summary="Search columns in the metadata catalog",
    description=(
        "Performs a case-insensitive keyword search across synced column names "
        "and data types in the local metadata catalog. Optionally scope results "
        "to a single connection using `connection_id`."
    ),
)
def search_columns(
    q: str = Query(..., min_length=1, description="Keyword to search for."),
    connection_id: Optional[int] = Query(
        None,
        description="Restrict search to a specific connection. Omit to search all connections."
    ),
    db: Session = Depends(get_db),
) -> List[ColumnSearchResult]:
    """
    Thin HTTP handler — validates query params, delegates to SearchService.
    No business logic lives here.
    """
    service = SearchService(db)
    return service.search_columns(query=q, connection_id=connection_id)


@router.get(
    "/search/relationships",
    response_model=List[RelationshipSearchResult],
    status_code=status.HTTP_200_OK,
    summary="Search relationships in the metadata catalog",
    description=(
        "Performs a case-insensitive keyword search across synced relationships "
        "(matching source/target tables and columns) in the local metadata catalog. "
        "Optionally scope results to a single connection using `connection_id`."
    ),
)
def search_relationships(
    q: str = Query(..., min_length=1, description="Keyword to search for."),
    connection_id: Optional[int] = Query(
        None,
        description="Restrict search to a specific connection. Omit to search all connections."
    ),
    db: Session = Depends(get_db),
) -> List[RelationshipSearchResult]:
    """
    Thin HTTP handler — validates query params, delegates to SearchService.
    No business logic lives here.
    """
    service = SearchService(db)
    return service.search_relationships(query=q, connection_id=connection_id)


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
