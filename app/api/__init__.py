from app.api.health import router as health_router
from app.api.connections import router as connections_router
from app.api.schema import router as schema_router
from app.api.metadata import router as metadata_router
from app.api.relationship import router as relationship_router
from app.api.search import router as search_router

__all__ = [
    "health_router",
    "connections_router",
    "schema_router",
    "metadata_router",
    "relationship_router",
    "search_router",
]
