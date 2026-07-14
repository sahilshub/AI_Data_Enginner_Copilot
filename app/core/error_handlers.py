from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.logging import get_logger

logger = get_logger("app.errors")

# Maps HTTP status codes to a stable machine-readable slug for the `error` field.
# Falls back to "http_error" / "internal_server_error" for anything not listed.
_STATUS_SLUGS = {
    status.HTTP_400_BAD_REQUEST: "bad_request",
    status.HTTP_404_NOT_FOUND: "not_found",
    status.HTTP_409_CONFLICT: "conflict",
    422: "validation_error",  # status.HTTP_422_UNPROCESSABLE_ENTITY is deprecated in this Starlette version
    status.HTTP_502_BAD_GATEWAY: "upstream_error",
}


def register_exception_handlers(app: FastAPI) -> None:
    """
    Installs centralized handlers so every error response — expected
    (HTTPException raised deliberately by a service) or unexpected (an
    uncaught exception) — has the same shape: {"error": slug, "message": ...}.
    Without this, an uncaught exception would leak a raw 500 with no
    structured log entry, and callers would have to branch on response shape.
    """

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        if exc.status_code >= 500:
            logger.error(
                "request_failed",
                extra={"path": request.url.path, "status_code": exc.status_code, "detail": exc.detail},
            )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": _STATUS_SLUGS.get(exc.status_code, "http_error"),
                "message": exc.detail,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": "validation_error",
                "message": exc.errors(),
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "unhandled_exception",
            extra={"path": request.url.path, "error": str(exc)},
            exc_info=exc,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred.",
            },
        )
