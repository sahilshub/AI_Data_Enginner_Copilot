from app.api.health import router as health_router
from app.api.connections import router as connections_router
from app.api.schema import router as schema_router

__all__ = ["health_router", "connections_router", "schema_router"]
