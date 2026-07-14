from pydantic import BaseModel, Field

class HealthResponse(BaseModel):
    """
    Schema for the health check response.
    Defines the shape and types of the response returned by the /health endpoint.
    """
    status: str = Field(
        default="healthy",
        description="The status of the application, typically 'healthy' when running correctly."
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy"
            }
        }
    }


class DetailedHealthResponse(BaseModel):
    """
    Schema for the detailed health check response (GET /health/details).
    Reports the application's own status plus its dependencies, so a caller
    can tell "the process is up" apart from "the process can actually do its job".
    """
    application: str = Field(..., description="'healthy' if the process is serving requests.")
    database: str = Field(..., description="'healthy' if the Copilot's own catalog DB is reachable, else 'unhealthy'.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "application": "healthy",
                "database": "healthy"
            }
        }
    }
