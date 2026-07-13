from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.schema_response import TableResponse, TableDetailResponse
from app.services.schema_service import SchemaService

router = APIRouter(
    prefix="/connections/{connection_id}/schema",
    tags=["Schema Discovery"]
)


@router.get(
    "/tables",
    response_model=List[TableResponse],
    status_code=status.HTTP_200_OK,
    summary="List all tables",
    description=(
        "Connects to the target database identified by connection_id and returns "
        "a list of all user-defined tables found in the public schema."
    )
)
def list_tables(
    connection_id: int,
    db: Session = Depends(get_db)
) -> List[TableResponse]:
    """
    Handles GET /connections/{connection_id}/schema/tables.
    Thin route: validates path parameter, delegates to SchemaService, returns result.
    """
    service = SchemaService(db)
    return service.get_tables(connection_id)


@router.get(
    "/tables/{table_name}",
    response_model=TableDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get table details",
    description=(
        "Connects to the target database and returns the column names and data types "
        "for the requested table."
    )
)
def get_table_details(
    connection_id: int,
    table_name: str,
    db: Session = Depends(get_db)
) -> TableDetailResponse:
    """
    Handles GET /connections/{connection_id}/schema/tables/{table_name}.
    Thin route: delegates to SchemaService for introspection and response building.
    """
    service = SchemaService(db)
    return service.get_table_details(connection_id, table_name)
