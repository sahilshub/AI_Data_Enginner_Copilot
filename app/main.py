from fastapi import FastAPI
from app.api.health import router as health_router
from app.api.connections import router as connections_router
from app.api.schema import router as schema_router
from app.api.metadata import router as metadata_router
from app.api.relationship import router as relationship_router
from app.api.search import router as search_router
from app.api.documentation import router as documentation_router
from app.api.metadata_refresh import router as metadata_refresh_router
from app.api.jobs import router as jobs_router
from app.api.ai_providers import router as ai_providers_router
from app.api.qa import router as qa_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.error_handlers import register_exception_handlers
from app.middleware.request_logging import RequestLoggingMiddleware

configure_logging()
logger = get_logger("app.startup")

# Initialize the FastAPI application with metadata loaded from configuration settings
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(RequestLoggingMiddleware)
register_exception_handlers(app)

logger.info("application_started", extra={"environment": settings.ENVIRONMENT})

# Register endpoints from different domains/controllers
app.include_router(health_router)
app.include_router(connections_router)
app.include_router(schema_router)
app.include_router(metadata_router)
app.include_router(relationship_router)
app.include_router(search_router)
app.include_router(documentation_router)
app.include_router(metadata_refresh_router)
app.include_router(jobs_router)
app.include_router(ai_providers_router)
app.include_router(qa_router)

@app.get("/", tags=["Root"])
def read_root():
    """
    Root endpoint offering a simple welcome message and directions to docs.
    """
    return {
        "message": f"Welcome to the {settings.PROJECT_NAME}.",
        "documentation": "/docs"
    }


