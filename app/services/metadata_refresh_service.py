from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Any, Dict, List, Tuple

from app.repositories.connection_repository import ConnectionRepository
from app.repositories.schema_repository import SchemaRepository
from app.repositories.metadata_repository import MetadataRepository
from app.repositories.relationship_repository import RelationshipRepository
from app.repositories.metadata_change_repository import MetadataChangeRepository
from app.services.metadata_sync_service import MetadataSyncService
from app.services.relationship_service import RelationshipService
from app.schemas.metadata_change_schema import (
    MetadataChangeResponse,
    RefreshResponse,
    RefreshStatusResponse,
)
from app.core.logging import get_logger
from app.core.monitoring import metrics

logger = get_logger("app.metadata_refresh")

RelationshipKey = Tuple[str, str, str, str]


class MetadataRefreshService:
    """
    Compares the currently stored metadata snapshot against a fresh read of
    the target database, records what changed, then updates the catalog to
    match (Phase 1, Step 9).

    Diff detection is done here directly against the target database via
    SchemaRepository / RelationshipRepository.get_foreign_keys_from_target
    (the same introspection primitives Step 4/6 already use). The actual
    catalog update is delegated to the existing MetadataSyncService and
    RelationshipService — refresh's job is to notice and record *what*
    changed, not to reimplement how the catalog gets written.
    """

    def __init__(self, db: Session):
        self.db = db
        self.conn_repo = ConnectionRepository(db)
        self.meta_repo = MetadataRepository(db)
        self.rel_repo = RelationshipRepository(db)
        self.change_repo = MetadataChangeRepository(db)

    def _get_target_engine(self, connection_id: int):
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
    # Diff detection
    # ------------------------------------------------------------------

    def detect_changes(self, connection_id: int, schema_name: str = "public") -> List[Dict[str, Any]]:
        """
        Reads the current catalog snapshot and a fresh live snapshot, and
        returns a list of change dicts (change_type, object_type, object_name,
        previous_value, new_value) describing every difference found.
        Does not persist anything or touch the catalog.
        """
        target_engine = self._get_target_engine(connection_id)
        schema_repo = SchemaRepository(target_engine)

        # --- Before: what the catalog currently holds ---
        before_tables = {
            t.table_name: t for t in self.meta_repo.get_tables_by_connection(connection_id)
            if t.schema_name == schema_name
        }
        before_columns = {
            table_name: {
                c.column_name: c for c in self.meta_repo.get_columns_by_table(table.id)
            }
            for table_name, table in before_tables.items()
        }
        before_relationships: Dict[RelationshipKey, None] = {
            (r.source_table, r.source_column, r.target_table, r.target_column): None
            for r in self.rel_repo.get_by_connection(connection_id)
        }

        # --- After: a fresh live read of the target database ---
        try:
            raw_tables = schema_repo.get_tables(schema_name)
            after_columns = {
                rt["table_name"]: {
                    c["name"]: c for c in schema_repo.get_columns(rt["table_name"], schema_name)
                }
                for rt in raw_tables
            }
            raw_fks = RelationshipRepository.get_foreign_keys_from_target(target_engine, schema_name)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to read live metadata from target database: {str(e)}"
            )
        after_tables = set(after_columns.keys())
        after_relationships: Dict[RelationshipKey, None] = {
            (fk["source_table"], fk["source_column"], fk["target_table"], fk["target_column"]): None
            for fk in raw_fks
        }

        changes: List[Dict[str, Any]] = []
        before_table_names = set(before_tables.keys())

        for table_name in after_tables - before_table_names:
            changes.append({
                "change_type": "TABLE_ADDED",
                "object_type": "TABLE",
                "object_name": table_name,
            })

        for table_name in before_table_names - after_tables:
            changes.append({
                "change_type": "TABLE_REMOVED",
                "object_type": "TABLE",
                "object_name": table_name,
            })

        for table_name in before_table_names & after_tables:
            before_cols = before_columns.get(table_name, {})
            after_cols = after_columns.get(table_name, {})
            before_col_names = set(before_cols.keys())
            after_col_names = set(after_cols.keys())

            for col_name in after_col_names - before_col_names:
                changes.append({
                    "change_type": "COLUMN_ADDED",
                    "object_type": "COLUMN",
                    "object_name": f"{table_name}.{col_name}",
                    "new_value": after_cols[col_name]["data_type"],
                })

            for col_name in before_col_names - after_col_names:
                changes.append({
                    "change_type": "COLUMN_REMOVED",
                    "object_type": "COLUMN",
                    "object_name": f"{table_name}.{col_name}",
                    "previous_value": before_cols[col_name].data_type,
                })

            for col_name in before_col_names & after_col_names:
                before_type = before_cols[col_name].data_type
                after_type = after_cols[col_name]["data_type"]
                if before_type != after_type:
                    changes.append({
                        "change_type": "COLUMN_TYPE_CHANGED",
                        "object_type": "COLUMN",
                        "object_name": f"{table_name}.{col_name}",
                        "previous_value": before_type,
                        "new_value": after_type,
                    })

        for rel in set(after_relationships) - set(before_relationships):
            changes.append({
                "change_type": "RELATIONSHIP_ADDED",
                "object_type": "RELATIONSHIP",
                "object_name": f"{rel[0]}.{rel[1]} -> {rel[2]}.{rel[3]}",
            })

        for rel in set(before_relationships) - set(after_relationships):
            changes.append({
                "change_type": "RELATIONSHIP_REMOVED",
                "object_type": "RELATIONSHIP",
                "object_name": f"{rel[0]}.{rel[1]} -> {rel[2]}.{rel[3]}",
            })

        return changes

    # ------------------------------------------------------------------
    # Public service actions
    # ------------------------------------------------------------------

    def refresh_metadata(self, connection_id: int, schema_name: str = "public") -> RefreshResponse:
        """
        Detects changes against the live target database, records them,
        then updates the catalog (tables/columns/relationships) to match.
        """
        logger.info("metadata_refresh_started", extra={"connection_id": connection_id, "schema_name": schema_name})

        try:
            changes = self.detect_changes(connection_id, schema_name)

            if changes:
                self.change_repo.save_changes(connection_id, changes)

            # Catalog update is delegated — see class docstring.
            MetadataSyncService(self.db).sync_connection_metadata(connection_id, schema_name)
            RelationshipService(self.db).discover_relationships(connection_id, schema_name)
        except Exception as e:
            metrics.record_metadata_refresh(success=False)
            logger.error(
                "metadata_refresh_failed",
                extra={"connection_id": connection_id, "schema_name": schema_name, "error": str(e)},
            )
            raise

        metrics.record_metadata_refresh(success=True)
        logger.info(
            "metadata_refresh_completed",
            extra={"connection_id": connection_id, "changes_detected": len(changes)},
        )

        return RefreshResponse(
            message="Metadata refreshed successfully.",
            changes_detected=len(changes),
        )

    def get_changes(self, connection_id: int) -> List[MetadataChangeResponse]:
        """Serves the full recorded change history for a connection."""
        if not self.conn_repo.get_by_id(connection_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Database connection with ID {connection_id} not found."
            )
        records = self.change_repo.get_changes(connection_id)
        return [MetadataChangeResponse.model_validate(r) for r in records]

    def get_refresh_status(self, connection_id: int) -> RefreshStatusResponse:
        """Reports the timestamp of the last detected change and the total change count."""
        if not self.conn_repo.get_by_id(connection_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Database connection with ID {connection_id} not found."
            )
        latest = self.change_repo.get_latest_change(connection_id)
        total = len(self.change_repo.get_changes(connection_id))
        return RefreshStatusResponse(
            last_refresh=latest.detected_at if latest else None,
            changes_detected=total,
        )
