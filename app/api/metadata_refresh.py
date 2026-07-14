from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.repositories.connection_repository import ConnectionRepository
from app.repositories.sync_job_repository import SyncJobRepository
from app.schemas.job_schema import JobAcceptedResponse
from app.schemas.metadata_change_schema import (
    RefreshStatusResponse,
    MetadataChangeResponse,
)
from app.services.metadata_refresh_service import MetadataRefreshService
from app.tasks.metadata_tasks import refresh_metadata_task

router = APIRouter(
    prefix="/connections/{connection_id}/metadata",
    tags=["Metadata Refresh"]
)


@router.post(
    "/refresh",
    response_model=JobAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Refresh metadata and detect changes (async)",
    description=(
        "Queues a background job that reads the live target database, compares it "
        "against the stored metadata catalog, records any detected changes, then "
        "updates the catalog to match. Returns immediately with a job_id — poll "
        "GET /connections/{connection_id}/jobs/{job_id} for status and results. "
        "See docs/phase-1/step-13.md."
    ),
)
def refresh_metadata(
    connection_id: int,
    schema_name: str = Query("public", description="PostgreSQL schema to refresh."),
    db: Session = Depends(get_db),
) -> JobAcceptedResponse:
    if not ConnectionRepository(db).get_by_id(connection_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database connection with ID {connection_id} not found."
        )

    job = SyncJobRepository(db).create(connection_id, job_type="refresh", schema_name=schema_name)
    refresh_metadata_task.delay(job.id, connection_id, schema_name)

    return JobAcceptedResponse(
        job_id=job.id,
        status="pending",
        message="Metadata refresh queued.",
    )


@router.get(
    "/changes",
    response_model=List[MetadataChangeResponse],
    status_code=status.HTTP_200_OK,
    summary="Get metadata change history",
    description="Returns the full history of detected metadata changes for a connection, most recent first.",
)
def get_metadata_changes(
    connection_id: int,
    db: Session = Depends(get_db),
) -> List[MetadataChangeResponse]:
    service = MetadataRefreshService(db)
    return service.get_changes(connection_id)


@router.get(
    "/status",
    response_model=RefreshStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get latest refresh status",
    description="Returns the timestamp of the most recently detected change and the total change count.",
)
def get_refresh_status(
    connection_id: int,
    db: Session = Depends(get_db),
) -> RefreshStatusResponse:
    service = MetadataRefreshService(db)
    return service.get_refresh_status(connection_id)
