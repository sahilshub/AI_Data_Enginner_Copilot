from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.repositories.connection_repository import ConnectionRepository
from app.repositories.schema_repository import SchemaRepository
from app.schemas.schema_response import TableResponse, ColumnResponse, TableDetailResponse
from typing import List


class SchemaService:
    """
    Orchestrates database schema discovery.

    Responsibilities:
      1. Load the saved connection credentials from our copilot's own database.
      2. Build a transient SQLAlchemy engine pointing at the *target* database.
      3. Delegate raw metadata queries to SchemaRepository.
      4. Transform raw rows into typed Pydantic response objects.

    The service knows *nothing* about SQL syntax or HTTP. It only coordinates.
    """

    def __init__(self, db: Session):
        # db is the session to our copilot's own database (to look up credentials)
        self.connection_repo = ConnectionRepository(db)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_engine_for_connection(self, connection_id: int):
        """
        Loads a saved DatabaseConnection record and builds a transient
        SQLAlchemy engine pointed at that external target database.

        Raises 404 if the connection_id does not exist.
        """
        db_conn = self.connection_repo.get_by_id(connection_id)
        if not db_conn:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Database connection with ID {connection_id} not found."
            )

        # Build the connection URL from stored credentials
        url = (
            f"postgresql+psycopg2://{db_conn.username}:{db_conn.password}"
            f"@{db_conn.host}:{db_conn.port}/{db_conn.database}"
        )

        # connect_timeout prevents an unreachable host from hanging indefinitely
        return create_engine(url, connect_args={"connect_timeout": 5})

    # ------------------------------------------------------------------
    # Public service methods
    # ------------------------------------------------------------------

    def get_tables(self, connection_id: int) -> List[TableResponse]:
        """
        Returns all user-defined tables in the public schema of the
        target database identified by connection_id.
        """
        engine = self._get_engine_for_connection(connection_id)
        repo = SchemaRepository(engine)

        try:
            raw = repo.get_tables()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to retrieve tables from target database: {str(e)}"
            )

        return [TableResponse(table_name=row["table_name"]) for row in raw]

    def get_table_details(
        self, connection_id: int, table_name: str
    ) -> TableDetailResponse:
        """
        Returns full column metadata (name, data_type) for a single table
        in the target database.
        """
        engine = self._get_engine_for_connection(connection_id)
        repo = SchemaRepository(engine)

        try:
            raw_columns = repo.get_columns(table_name)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to retrieve columns from target database: {str(e)}"
            )

        if not raw_columns:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Table '{table_name}' not found in the target database."
            )

        columns = [
            ColumnResponse(name=col["name"], data_type=col["data_type"])
            for col in raw_columns
        ]
        return TableDetailResponse(table_name=table_name, columns=columns)
