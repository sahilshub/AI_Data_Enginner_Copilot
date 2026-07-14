from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.monitoring import metrics
from app.schemas.health_schema import HealthResponse, DetailedHealthResponse
from app.services.health_service import HealthService

router = APIRouter(tags=["System Health"])

@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Get system health status",
    description="Endpoint used to verify that the server is online and accepting requests."
)
def check_health() -> HealthResponse:
    """
    Handles GET /health HTTP requests.
    Delegates the processing to HealthService and returns a validated HealthResponse schema.
    """
    return HealthService.get_status()


@router.get(
    "/health/details",
    response_model=DetailedHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Get detailed health status",
    description="Checks the application and its dependencies (currently the Copilot's own catalog database)."
)
def check_detailed_health(db: Session = Depends(get_db)) -> DetailedHealthResponse:
    """
    Handles GET /health/details HTTP requests.
    """
    return HealthService.get_detailed_status(db)


@router.get(
    "/metrics",
    status_code=status.HTTP_200_OK,
    summary="Get in-memory request/refresh metrics",
    description=(
        "Returns process-local counters: total/failed requests, average request "
        "duration, and metadata refresh counts. Reset on process restart — not "
        "persisted. See app/core/monitoring.py."
    ),
)
def get_metrics() -> dict:
    """
    Handles GET /metrics HTTP requests.
    """
    return metrics.snapshot()
