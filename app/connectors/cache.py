import threading
from typing import Callable, Dict

from app.connectors.base import SourceConnector


class ConnectorCache:
    """
    Reuses SourceConnector instances (and whatever connection pool they own)
    across requests, keyed by connection_id.

    Without this, every service call created a brand-new SourceConnector —
    for PostgresConnector, a brand-new SQLAlchemy engine and connection
    pool — and discarded it the moment the request finished. That defeats
    pooling entirely: every single API call paid a fresh TCP handshake +
    auth round-trip to the *target* database, even just to list tables.

    Thread-safe: FastAPI's sync routes run in a thread pool, so concurrent
    requests for different (or the same) connection_id are expected.
    """

    def __init__(self) -> None:
        self._connectors: Dict[int, SourceConnector] = {}
        self._lock = threading.Lock()

    def get_or_create(self, connection_id: int, factory: Callable[[], SourceConnector]) -> SourceConnector:
        """
        Returns the cached connector for connection_id, creating one via
        `factory` on first use. `factory` is only invoked on a cache miss —
        callers can safely put credential decryption inside it without
        paying that cost on every call.
        """
        with self._lock:
            connector = self._connectors.get(connection_id)
            if connector is None:
                connector = factory()
                self._connectors[connection_id] = connector
            return connector

    def invalidate(self, connection_id: int) -> None:
        """
        Evicts and disposes the cached connector for a connection. Call this
        whenever a connection's stored credentials could no longer match
        what's cached — currently just on delete, since there's no
        "update connection" endpoint yet.
        """
        with self._lock:
            connector = self._connectors.pop(connection_id, None)
        if connector is not None:
            connector.dispose()


# Single process-wide instance — every service shares this.
connector_cache = ConnectorCache()
