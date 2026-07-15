from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List

from app.repositories.connection_repository import ConnectionRepository
from app.repositories.metadata_repository import MetadataRepository
from app.connectors.factory import get_connector
from app.connectors.cache import connector_cache
from app.connectors.base import SourceConnector
from app.schemas.metadata_schema import (
    SyncResponse,
    StoredTableResponse,
    StoredTableDetailResponse,
    StoredColumnResponse,
)
from app.core.logging import get_logger
from app.core.security import decrypt_password

logger = get_logger("app.metadata_sync")


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

    def _get_connector(self, connection_id: int) -> SourceConnector:
        """
        Loads saved credentials from the Copilot DB and resolves the
        SourceConnector for the connection's dialect.
        """
        db_conn = self.conn_repo.get_by_id(connection_id)
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
    # SYNC
    # ------------------------------------------------------------------

    def sync_connection_metadata(
        self, connection_id: int, schema_name: str = "public"
    ) -> SyncResponse:
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
        logger.info("metadata_sync_started", extra={"connection_id": connection_id, "schema_name": schema_name})

        connector = self._get_connector(connection_id)

        try:
            raw_tables = connector.get_tables(schema_name)
        except Exception as e:
            logger.error(
                "metadata_sync_failed",
                extra={"connection_id": connection_id, "schema_name": schema_name, "error": str(e)},
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to read tables from target database: {str(e)}"
            )

        # One round-trip for every table's columns, instead of one round-trip
        # per table — see SchemaRepository.get_columns_bulk().
        try:
            columns_by_table = connector.get_columns_bulk(schema_name)
        except Exception:
            columns_by_table = {}  # Non-fatal: sync proceeds with tables but no columns

        # Delete stale records — cascade will also remove old columns
        self.meta_repo.delete_tables_by_connection(connection_id)

        tables_synced = 0
        for raw_table in raw_tables:
            table_name = raw_table["table_name"]

            # Persist table record, storing the actual schema_name
            table_record = self.meta_repo.save_table(
                connection_id=connection_id,
                table_name=table_name,
                schema_name=schema_name,
            )

            for raw_col in columns_by_table.get(table_name, []):
                self.meta_repo.save_column(
                    table_id=table_record.id,
                    column_name=raw_col["name"],
                    data_type=raw_col["data_type"],
                    is_nullable=raw_col["is_nullable"],
                )

            tables_synced += 1

        # One commit for the entire sync — atomicity
        self.meta_repo.commit()

        logger.info(
            "metadata_sync_completed",
            extra={"connection_id": connection_id, "tables_synced": tables_synced},
        )

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
        self, connection_id: int, table_name: str, schema_name: str = "public"
    ) -> StoredTableDetailResponse:
        """
        Returns a stored table record with all its column details.
        Serves from Copilot DB — no network call to target database.
        """
        table_record = self.meta_repo.get_table_by_name(connection_id, table_name, schema_name)
        if not table_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"No stored metadata found for table '{table_name}' in schema "
                    f"'{schema_name}' on connection {connection_id}. Run POST /metadata/sync "
                    f"first, or pass the correct `schema_name` query parameter."
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
