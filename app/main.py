from fastapi import FastAPI
from app.api.health import router as health_router
from app.api.connections import router as connections_router
from app.core.config import settings

# Initialize the FastAPI application with metadata loaded from configuration settings
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Register endpoints from different domains/controllers
app.include_router(health_router)
app.include_router(connections_router)

@app.get("/", tags=["Root"])
def read_root():
    """
    Root endpoint offering a simple welcome message and directions to docs.
    """
    return {
        "message": f"Welcome to the {settings.PROJECT_NAME}.",
        "documentation": "/docs"
    }


