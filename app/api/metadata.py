from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.repositories.connection_repository import ConnectionRepository
from app.repositories.sync_job_repository import SyncJobRepository
from app.schemas.job_schema import JobAcceptedResponse
from app.schemas.metadata_schema import (
    StoredTableResponse,
    StoredTableDetailResponse,
)
from app.services.metadata_sync_service import MetadataSyncService
from app.tasks.metadata_tasks import sync_metadata_task

router = APIRouter(
    prefix="/connections/{connection_id}/metadata",
    tags=["Metadata Catalog"]
)


@router.post(
    "/sync",
    response_model=JobAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Sync schema metadata (async)",
    description=(
        "Queues a background job that connects to the target database, discovers "
        "all tables and columns, and persists a fresh snapshot into the Copilot's "
        "metadata catalog, replacing existing metadata for this connection. "
        "Returns immediately with a job_id — poll GET /connections/{connection_id}/jobs/{job_id} "
        "for status and results. See docs/phase-1/step-13.md."
    ),
)
def sync_metadata(
    connection_id: int,
    schema_name: str = Query(
        "public",
        description="PostgreSQL schema to sync. Use for non-default schemas like 'analytics' or 'staging'."
    ),
    db: Session = Depends(get_db),
) -> JobAcceptedResponse:
    if not ConnectionRepository(db).get_by_id(connection_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database connection with ID {connection_id} not found."
        )

    job = SyncJobRepository(db).create(connection_id, job_type="sync", schema_name=schema_name)
    sync_metadata_task.delay(job.id, connection_id, schema_name)

    return JobAcceptedResponse(
        job_id=job.id,
        status="pending",
        message="Metadata sync queued.",
    )


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
