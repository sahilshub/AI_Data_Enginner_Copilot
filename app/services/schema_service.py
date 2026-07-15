from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.repositories.connection_repository import ConnectionRepository
from app.connectors.factory import get_connector
from app.connectors.cache import connector_cache
from app.connectors.base import SourceConnector
from app.schemas.schema_response import TableResponse, ColumnResponse, TableDetailResponse
from app.core.security import decrypt_password
from typing import List


class SchemaService:
    """
    Orchestrates database schema discovery.

    Responsibilities:
      1. Load the saved connection credentials from our copilot's own database.
      2. Resolve the right SourceConnector for the connection's dialect.
      3. Delegate raw metadata queries to that connector.
      4. Transform raw rows into typed Pydantic response objects.

    The service knows *nothing* about SQL syntax, credential shape, or HTTP —
    all of that is behind SourceConnector. See app/connectors/.
    """

    def __init__(self, db: Session):
        # db is the session to our copilot's own database (to look up credentials)
        self.connection_repo = ConnectionRepository(db)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_connector(self, connection_id: int) -> SourceConnector:
        """
        Loads a saved DatabaseConnection record and resolves the
        SourceConnector for its dialect. Raises 404 if the connection_id
        does not exist, or 400 if the dialect isn't supported yet.
        """
        db_conn = self.connection_repo.get_by_id(connection_id)
        if not db_conn:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Database connection with ID {connection_id} not found."
            )

        return connector_cache.get_or_create(
            connection_id,
            lambda: get_connector(
                dialect=db_conn.dialect,
                host=db_conn.host,
                port=db_conn.port,
                username=db_conn.username,
                password=decrypt_password(db_conn.password),
                database=db_conn.database,
                extra_config=db_conn.extra_config,
            ),
        )

    # ------------------------------------------------------------------
    # Public service methods
    # ------------------------------------------------------------------

    def get_tables(
        self, connection_id: int, schema_name: str = "public"
    ) -> List[TableResponse]:
        """
        Returns all user-defined tables in the specified schema of the
        target database identified by connection_id.

        Args:
            connection_id: ID of the saved connection record.
            schema_name:   PostgreSQL schema to inspect. Defaults to 'public'.
        """
        connector = self._get_connector(connection_id)

        try:
            raw = connector.get_tables(schema_name)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to retrieve tables from target database: {str(e)}"
            )

        return [TableResponse(table_name=row["table_name"]) for row in raw]

    def get_table_details(
        self, connection_id: int, table_name: str, schema_name: str = "public"
    ) -> TableDetailResponse:
        """
        Returns full column metadata (name, data_type) for a single table
        in the specified schema of the target database.

        Args:
            connection_id: ID of the saved connection record.
            table_name:    Name of the table to inspect.
            schema_name:   PostgreSQL schema containing the table. Defaults to 'public'.
        """
        connector = self._get_connector(connection_id)

        try:
            raw_columns = connector.get_columns(table_name, schema_name)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to retrieve columns from target database: {str(e)}"
            )

        if not raw_columns:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Table '{table_name}' not found in schema '{schema_name}'."
            )

        columns = [
            ColumnResponse(name=col["name"], data_type=col["data_type"])
            for col in raw_columns
        ]
        return TableDetailResponse(table_name=table_name, columns=columns)
