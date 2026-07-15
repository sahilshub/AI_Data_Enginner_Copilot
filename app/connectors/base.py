from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple


class SourceConnector(ABC):
    """
    Interface every data source (Postgres, and later Snowflake/BigQuery/etc.)
    must implement. Services depend on this interface only — never on a
    specific source's client library, SQL dialect, or credential shape.

    Return shapes are fixed across all implementations so nothing downstream
    (schemas, services) needs to know which source produced the data:
      - get_tables()       -> [{"table_name": str}, ...]
      - get_columns()      -> [{"name": str, "data_type": str, "is_nullable": bool}, ...]
      - get_foreign_keys() -> [{"source_schema": str, "source_table": str, "source_column": str,
                                 "target_schema": str, "target_table": str, "target_column": str}, ...]
    """

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        database: str,
        extra_config: Optional[Dict[str, Any]] = None,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.extra_config = extra_config or {}

    @abstractmethod
    def test_connection(self) -> Tuple[bool, str]:
        """Returns (success, message) without raising on failure."""
        raise NotImplementedError

    @abstractmethod
    def get_tables(self, schema_name: str) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_columns(self, table_name: str, schema_name: str) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_columns_bulk(self, schema_name: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Returns every table's columns for the whole schema in one call —
        implementations should do this in a single round-trip, not by
        calling get_columns() in a loop. Return shape: table_name -> list
        of column dicts (same shape get_columns() returns per-table).
        """
        raise NotImplementedError

    @abstractmethod
    def get_foreign_keys(self, schema_name: str) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def dispose(self) -> None:
        """
        Releases any held resources (e.g. closes a connection pool). Called
        by ConnectorCache.invalidate() when a connection is deleted or its
        credentials change — connectors are cached and reused across
        requests, so this is the only place resources get released.
        """
        raise NotImplementedError
