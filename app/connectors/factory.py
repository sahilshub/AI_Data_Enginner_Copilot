from typing import Any, Dict, Optional

from fastapi import HTTPException, status

from app.connectors.base import SourceConnector
from app.connectors.postgres_connector import PostgresConnector

# Every dialect this app can actually introspect today. Add an entry here
# (and a connector class) when a new source is implemented — nothing else
# needs to change.
_CONNECTORS = {
    "postgresql": PostgresConnector,
}


def get_connector(
    dialect: str,
    host: str,
    port: int,
    username: str,
    password: str,
    database: str,
    extra_config: Optional[Dict[str, Any]] = None,
) -> SourceConnector:
    """
    Resolves a dialect string to a SourceConnector instance. Raises 400 for
    an unsupported dialect immediately, rather than letting callers hit a
    confusing failure later inside schema introspection.
    """
    connector_cls = _CONNECTORS.get(dialect)
    if connector_cls is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Dialect '{dialect}' is not yet supported. "
                f"Currently supported: {', '.join(sorted(_CONNECTORS.keys()))}."
            ),
        )
    return connector_cls(
        host=host,
        port=port,
        username=username,
        password=password,
        database=database,
        extra_config=extra_config,
    )


def is_supported_dialect(dialect: str) -> bool:
    """Used at connection-creation time to reject unsupported dialects up front."""
    return dialect in _CONNECTORS
