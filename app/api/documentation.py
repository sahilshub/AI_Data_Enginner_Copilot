from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.documentation_schema import (
    DatabaseDocumentationResponse,
    TableDocumentationResponse,
    RelationshipDocumentationResponse,
)
from app.services.documentation_service import DocumentationService

router = APIRouter(
    prefix="/connections/{connection_id}/documentation",
    tags=["Schema Documentation"]
)


@router.get(
    "/database",
    response_model=DatabaseDocumentationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate database overview documentation",
    description=(
        "Generates a human-readable overview of a connection's synced metadata: "
        "table/column/relationship counts and table names. Reads only from the "
        "Copilot's metadata catalog — run POST /metadata/sync first."
    ),
)
def get_database_documentation(
    connection_id: int,
    db: Session = Depends(get_db),
) -> DatabaseDocumentationResponse:
    service = DocumentationService(db)
    return service.generate_database_documentation(connection_id)


@router.get(
    "/table/{table_name}",
    response_model=TableDocumentationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate table documentation",
    description=(
        "Generates human-readable documentation for a single table: its columns "
        "and its relationships (as either source or target). Use `schema_name` "
        "if the table was synced from a non-default schema."
    ),
)
def get_table_documentation(
    connection_id: int,
    table_name: str,
    schema_name: str = Query(
        "public",
        description="PostgreSQL schema the table was synced from."
    ),
    db: Session = Depends(get_db),
) -> TableDocumentationResponse:
    service = DocumentationService(db)
    return service.generate_table_documentation(connection_id, table_name, schema_name)


@router.get(
    "/relationships",
    response_model=RelationshipDocumentationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate relationship documentation",
    description=(
        "Generates human-readable documentation listing every discovered "
        "relationship for a connection."
    ),
)
def get_relationship_documentation(
    connection_id: int,
    db: Session = Depends(get_db),
) -> RelationshipDocumentationResponse:
    service = DocumentationService(db)
    return service.generate_relationship_documentation(connection_id)
