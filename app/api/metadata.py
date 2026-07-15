from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.metadata_schema import (
    StoredTableResponse,
    StoredTableDetailResponse,
)
from app.services.metadata_sync_service import MetadataSyncService

router = APIRouter(
    prefix="/connections/{connection_id}/metadata",
    tags=["Metadata Catalog"]
)


@router.get(
    "/tables",
    response_model=List[StoredTableResponse],
    status_code=status.HTTP_200_OK,
    summary="Get stored tables",
    description=(
        "Returns all table records from the Copilot's metadata catalog for a connection. "
        "No connection to the target database is made. "
        "Run POST /metadata/refresh first to populate the catalog."
    ),
)
def get_stored_tables(
    connection_id: int,
    db: Session = Depends(get_db),
) -> List[StoredTableResponse]:
    service = MetadataSyncService(db)
    return service.get_stored_tables(connection_id)


@router.get(
    "/tables/{table_name}",
    response_model=StoredTableDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get stored table with columns",
    description=(
        "Returns a stored table record including all column details "
        "from the Copilot's metadata catalog. No live database query. "
        "Use `schema_name` if the table was synced from a non-default schema."
    ),
)
def get_stored_table_detail(
    connection_id: int,
    table_name: str,
    schema_name: str = Query(
        "public",
        description="PostgreSQL schema the table was synced from."
    ),
    db: Session = Depends(get_db),
) -> StoredTableDetailResponse:
    service = MetadataSyncService(db)
    return service.get_stored_table_detail(connection_id, table_name, schema_name)
