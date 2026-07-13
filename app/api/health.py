from fastapi import APIRouter, status
from app.schemas.health_schema import HealthResponse
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
