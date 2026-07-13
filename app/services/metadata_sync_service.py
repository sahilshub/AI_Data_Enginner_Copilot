from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List

from app.repositories.connection_repository import ConnectionRepository
from app.repositories.schema_repository import SchemaRepository
from app.repositories.metadata_repository import MetadataRepository
from app.schemas.metadata_schema import (
    SyncResponse,
    StoredTableResponse,
    StoredTableDetailResponse,
    StoredColumnResponse,
)


class MetadataSyncService:
    """
    Orchestrates the full metadata lifecycle:

    SYNC path  → target DB ──► information_schema ──► SchemaRepository
                                                          │
                                                          ▼
                                                   MetadataRepository ──► Copilot DB

    READ path  → Copilot DB ──► MetadataRepository ──► response

    The service knows nothing about HTTP. It only coordinates repositories.
    """

    def __init__(self, db: Session):
        self.db = db
        self.conn_repo = ConnectionRepository(db)
        self.meta_repo = MetadataRepository(db)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_target_engine(self, connection_id: int):
        """
        Loads saved credentials from the Copilot DB and builds a transient
        SQLAlchemy engine pointing at the *target* external database.
        """
        db_conn = self.conn_repo.get_by_id(connection_id)
        if not db_conn:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Database connection with ID {connection_id} not found."
            )
        url = (
            f"postgresql+psycopg2://{db_conn.username}:{db_conn.password}"
            f"@{db_conn.host}:{db_conn.port}/{db_conn.database}"
        )
        return create_engine(url, connect_args={"connect_timeout": 5})

    # ------------------------------------------------------------------
    # SYNC
    # ------------------------------------------------------------------

    def sync_connection_metadata(self, connection_id: int) -> SyncResponse:
        """
        Full metadata synchronization for a connection:

        1. Connect to target database.
        2. Discover all tables via information_schema.
        3. For each table, discover all columns.
        4. Delete previously stored metadata for this connection (replace strategy).
        5. Persist fresh tables and columns.
        6. Return a summary.

        Replace-on-sync is the simplest correct strategy: the entire snapshot
        is treated as atomic. Future steps can introduce incremental diffing.
        """
        target_engine = self._get_target_engine(connection_id)
        schema_repo = SchemaRepository(target_engine)

        try:
            raw_tables = schema_repo.get_tables()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to read tables from target database: {str(e)}"
            )

        # Delete stale records — cascade will also remove old columns
        self.meta_repo.delete_tables_by_connection(connection_id)

        tables_synced = 0
        for raw_table in raw_tables:
            table_name = raw_table["table_name"]

            # Persist table record and get its new id (flush, not commit yet)
            table_record = self.meta_repo.save_table(
                connection_id=connection_id,
                table_name=table_name,
            )

            # Discover and persist columns for this table
            try:
                raw_columns = schema_repo.get_columns(table_name)
            except Exception:
                raw_columns = []  # Non-fatal: skip columns for this table

            for raw_col in raw_columns:
                self.meta_repo.save_column(
                    table_id=table_record.id,
                    column_name=raw_col["name"],
                    data_type=raw_col["data_type"],
                    is_nullable=raw_col["is_nullable"],
                )

            tables_synced += 1

        # One commit for the entire sync — atomicity
        self.meta_repo.commit()

        return SyncResponse(
            message="Metadata synchronized successfully.",
            tables_synced=tables_synced,
        )

    # ------------------------------------------------------------------
    # READ from Copilot DB (no target DB contact)
    # ------------------------------------------------------------------

    def get_stored_tables(self, connection_id: int) -> List[StoredTableResponse]:
        """
        Returns all table records previously synced for a connection.
        Serves from Copilot DB — no network call to target database.
        """
        # Verify connection exists
        if not self.conn_repo.get_by_id(connection_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Database connection with ID {connection_id} not found."
            )
        records = self.meta_repo.get_tables_by_connection(connection_id)
        return [StoredTableResponse.model_validate(r) for r in records]

    def get_stored_table_detail(
        self, connection_id: int, table_name: str
    ) -> StoredTableDetailResponse:
        """
        Returns a stored table record with all its column details.
        Serves from Copilot DB — no network call to target database.
        """
        table_record = self.meta_repo.get_table_by_name(connection_id, table_name)
        if not table_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"No stored metadata found for table '{table_name}' "
                    f"on connection {connection_id}. Run POST /metadata/sync first."
                )
            )

        columns = self.meta_repo.get_columns_by_table(table_record.id)
        col_responses = [StoredColumnResponse.model_validate(c) for c in columns]

        return StoredTableDetailResponse(
            id=table_record.id,
            table_name=table_record.table_name,
            schema_name=table_record.schema_name,
            discovered_at=table_record.discovered_at,
            columns=col_responses,
        )
