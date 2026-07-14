import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings

# Attributes every stdlib LogRecord carries by default. Anything else found on
# a record came from `extra={...}` at the call site and should be surfaced as
# a structured field rather than silently dropped.
_STANDARD_RECORD_ATTRS = set(logging.LogRecord("", 0, "", 0, "", None, None).__dict__.keys())


class JSONFormatter(logging.Formatter):
    """
    Renders each log record as a single JSON line.

    Usage: `logger.info("metadata_sync_completed", extra={"connection_id": 123, "tables_synced": 58})`
    produces `{"timestamp": ..., "level": "INFO", "event": "metadata_sync_completed",
    "connection_id": 123, "tables_synced": 58}`.

    Structured logs are the point of this step: `grep`-ing or piping to a log
    aggregator only works if fields are consistently named and machine-parseable,
    not embedded in a free-text sentence.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "event": record.getMessage(),
            "logger": record.name,
        }

        for key, value in record.__dict__.items():
            if key not in _STANDARD_RECORD_ATTRS and key not in payload:
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging() -> None:
    """
    Installs the JSON formatter on the root logger. Call once at application
    startup (see app/main.py). Idempotent — safe to call more than once
    (e.g. under `--reload`), since it replaces rather than accumulates handlers.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.DEBUG if settings.ENVIRONMENT == "development" else logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Returns a module-scoped logger. Formatting/handlers come from configure_logging()."""
    return logging.getLogger(name)
