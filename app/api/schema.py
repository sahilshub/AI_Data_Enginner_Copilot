from fastapi import APIRouter, Depends, Query, status
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
        "Connects live to the target database and returns all user-defined tables "
        "in the specified schema. Use `schema_name` to target non-default schemas "
        "such as `analytics` or `staging`."
    )
)
def list_tables(
    connection_id: int,
    schema_name: str = Query("public", description="PostgreSQL schema to inspect."),
    db: Session = Depends(get_db)
) -> List[TableResponse]:
    service = SchemaService(db)
    return service.get_tables(connection_id, schema_name)


@router.get(
    "/tables/{table_name}",
    response_model=TableDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get table column details",
    description=(
        "Connects live to the target database and returns column names and "
        "data types for the requested table. Use `schema_name` to target "
        "tables in non-default schemas."
    )
)
def get_table_details(
    connection_id: int,
    table_name: str,
    schema_name: str = Query("public", description="PostgreSQL schema containing the table."),
    db: Session = Depends(get_db)
) -> TableDetailResponse:
    service = SchemaService(db)
    return service.get_table_details(connection_id, table_name, schema_name)
