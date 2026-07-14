from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.relationship_schema import (
    RelationshipResponse,
    TableRelationshipResponse,
    DiscoverRelationshipsResponse,
)
from app.services.relationship_service import RelationshipService

router = APIRouter(
    prefix="/connections/{connection_id}/relationships",
    tags=["Schema Relationships"]
)

@router.post(
    "/discover",
    response_model=DiscoverRelationshipsResponse,
    status_code=status.HTTP_200_OK,
    summary="Discover and sync schema relationships",
    description=(
        "Queries foreign key constraints in the target database and "
        "stores the relationships locally. Replaces existing relationships for this connection. "
        "Use the `schema_name` query parameter to target a non-default schema (e.g. `analytics`)."
    )
)
def discover_relationships(
    connection_id: int,
    schema_name: str = "public",
    db: Session = Depends(get_db)
) -> DiscoverRelationshipsResponse:
    service = RelationshipService(db)
    return service.discover_relationships(connection_id, schema_name)

@router.get(
    "",
    response_model=List[RelationshipResponse],
    status_code=status.HTTP_200_OK,
    summary="Get stored relationships",
    description="Lists all discovered relationships for this connection from local catalog database."
)
def get_relationships(
    connection_id: int,
    db: Session = Depends(get_db)
) -> List[RelationshipResponse]:
    """
    HTTP GET handler returning all saved relationships.
    """
    service = RelationshipService(db)
    return service.get_relationships(connection_id)

@router.get(
    "/{table_name}",
    response_model=List[TableRelationshipResponse],
    status_code=status.HTTP_200_OK,
    summary="Get connections for a specific table",
    description=(
        "Returns list of tables linked to target table by foreign key constraints. "
        "Use `schema_name` if the table lives in a non-default schema — table names "
        "are only unique within a schema."
    )
)
def get_table_relationships(
    connection_id: int,
    table_name: str,
    schema_name: str = Query("public", description="PostgreSQL schema containing the table."),
    db: Session = Depends(get_db)
) -> List[TableRelationshipResponse]:
    """
    HTTP GET handler returning relationships matching source table name.
    """
    service = RelationshipService(db)
    return service.get_table_relationships(connection_id, table_name, schema_name)
