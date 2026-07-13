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
