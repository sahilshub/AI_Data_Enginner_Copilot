from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.metadata_schema import (
    SyncResponse,
    StoredTableResponse,
    StoredTableDetailResponse,
)
from app.services.metadata_sync_service import MetadataSyncService

router = APIRouter(
    prefix="/connections/{connection_id}/metadata",
    tags=["Metadata Catalog"]
)


@router.post(
    "/sync",
    response_model=SyncResponse,
    status_code=status.HTTP_200_OK,
    summary="Sync schema metadata",
    description=(
        "Connects to the target database, discovers all tables and columns, "
        "and persists a fresh snapshot into the Copilot's metadata catalog. "
        "Existing metadata for this connection is replaced atomically."
    ),
)
def sync_metadata(
    connection_id: int,
    schema_name: str = Query(
        "public",
        description="PostgreSQL schema to sync. Use for non-default schemas like 'analytics' or 'staging'."
    ),
    db: Session = Depends(get_db),
) -> SyncResponse:
    service = MetadataSyncService(db)
    return service.sync_connection_metadata(connection_id, schema_name)


@router.get(
    "/tables",
    response_model=List[StoredTableResponse],
    status_code=status.HTTP_200_OK,
    summary="Get stored tables",
    description=(
        "Returns all table records from the Copilot's metadata catalog for a connection. "
        "No connection to the target database is made. "
        "Run POST /metadata/sync first to populate the catalog."
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
        "from the Copilot's metadata catalog. No live database query."
    ),
)
def get_stored_table_detail(
    connection_id: int,
    table_name: str,
    db: Session = Depends(get_db),
) -> StoredTableDetailResponse:
    service = MetadataSyncService(db)
    return service.get_stored_table_detail(connection_id, table_name)
