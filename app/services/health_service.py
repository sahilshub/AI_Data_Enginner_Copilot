from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.schemas.health_schema import HealthResponse, DetailedHealthResponse

logger = get_logger("app.health")


class HealthService:
    """
    Service responsible for handling application health checks.
    Houses the business logic for verifying that system components (and in the future,
    databases, cache servers, and AI endpoints) are fully functional.
    """

    @staticmethod
    def get_status() -> HealthResponse:
        """
        Retrieves the health status of the application.

        Currently returns a static 'healthy' response, but is architected to
        allow future diagnostic checks on databases, vectors, or external LLM API pings.
        """
        # Future-proofing: Here we will inject connection probes for databases and AI providers.
        return HealthResponse(status="healthy")

    @staticmethod
    def get_detailed_status(db: Session) -> DetailedHealthResponse:
        """
        Checks the application's own dependencies — currently just the
        Copilot's own catalog database (never a target/external database;
        those are only ever reachable via a registered connection).
        """
        try:
            db.execute(text("SELECT 1"))
            database_status = "healthy"
        except Exception as e:
            logger.error("health_check_database_failed", extra={"error": str(e)})
            database_status = "unhealthy"

        return DetailedHealthResponse(
            application="healthy",
            database=database_status,
        )
