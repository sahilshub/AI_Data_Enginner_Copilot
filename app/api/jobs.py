from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.repositories.connection_repository import ConnectionRepository
from app.repositories.sync_job_repository import SyncJobRepository
from app.schemas.job_schema import JobResponse

router = APIRouter(
    prefix="/connections/{connection_id}/jobs",
    tags=["Async Jobs"]
)


@router.get(
    "",
    response_model=List[JobResponse],
    status_code=status.HTTP_200_OK,
    summary="Get recent job history",
    description="Returns the most recent sync/refresh jobs for a connection, most recent first.",
)
def get_jobs(
    connection_id: int,
    db: Session = Depends(get_db),
) -> List[JobResponse]:
    if not ConnectionRepository(db).get_by_id(connection_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database connection with ID {connection_id} not found."
        )
    jobs = SyncJobRepository(db).get_by_connection(connection_id)
    return [JobResponse.model_validate(j) for j in jobs]


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    status_code=status.HTTP_200_OK,
    summary="Get job status",
    description=(
        "Returns the current status of an async sync/refresh job. Poll this "
        "after POST /metadata/sync or POST /metadata/refresh returns a job_id."
    ),
)
def get_job(
    connection_id: int,
    job_id: int,
    db: Session = Depends(get_db),
) -> JobResponse:
    job = SyncJobRepository(db).get_by_id(job_id)
    if not job or job.connection_id != connection_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found for connection {connection_id}."
        )
    return JobResponse.model_validate(job)
