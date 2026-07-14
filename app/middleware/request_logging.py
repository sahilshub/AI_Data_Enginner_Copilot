import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.logging import get_logger
from app.core.monitoring import metrics

logger = get_logger("app.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Runs for every request: times it, emits one structured log line, and
    records it into the in-memory metrics store. This is the only place
    that needs to know about both logging and metrics for the request
    lifecycle — individual routes/services stay unaware of either.
    """

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        metrics.record_request(status_code=response.status_code, duration_ms=duration_ms)

        logger.info(
            "http_request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            },
        )
        return response
