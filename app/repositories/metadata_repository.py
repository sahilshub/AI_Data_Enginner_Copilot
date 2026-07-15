from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.schema_table import SchemaTable
from app.models.schema_column import SchemaColumn


class MetadataRepository:
    """
    Repository responsible for persisting and retrieving schema metadata
    inside the Copilot's own database (schema_tables / schema_columns).

    This is the READ side of our metadata catalog. The SchemaRepository
    reads from target databases; this repository reads from and writes to
    our own platform database.
    """

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Table operations
    # ------------------------------------------------------------------

    def get_tables_by_connection(self, connection_id: int) -> List[SchemaTable]:
        """Returns all stored table records for a given connection."""
        return (
            self.db.query(SchemaTable)
            .filter(SchemaTable.connection_id == connection_id)
            .order_by(SchemaTable.table_name)
            .all()
        )

    def get_table_by_name(
        self, connection_id: int, table_name: str, schema_name: str = "public"
    ) -> Optional[SchemaTable]:
        """Returns a single stored table record by connection and name."""
        return (
            self.db.query(SchemaTable)
            .filter(
                SchemaTable.connection_id == connection_id,
                SchemaTable.table_name == table_name,
                SchemaTable.schema_name == schema_name,
            )
            .first()
        )

    def delete_tables_by_connection(self, connection_id: int) -> None:
        """
        Removes all stored table (and cascade: column) records for a connection.
        Called before re-syncing so stale data is replaced cleanly.
        """
        (
            self.db.query(SchemaTable)
            .filter(SchemaTable.connection_id == connection_id)
            .delete(synchronize_session=False)
        )
        self.db.commit()

    def save_table(
        self, connection_id: int, table_name: str, schema_name: str = "public"
    ) -> SchemaTable:
        """Creates and persists a new SchemaTable record."""
        record = SchemaTable(
            connection_id=connection_id,
            table_name=table_name,
            schema_name=schema_name,
        )
        self.db.add(record)
        self.db.flush()   # flush to get the auto-generated id without full commit
        return record

    # ------------------------------------------------------------------
    # Column operations
    # ------------------------------------------------------------------

    def save_column(
        self,
        table_id: int,
        column_name: str,
        data_type: str,
        is_nullable: bool,
    ) -> SchemaColumn:
        """Creates and persists a new SchemaColumn record."""
        record = SchemaColumn(
            table_id=table_id,
            column_name=column_name,
            data_type=data_type,
            is_nullable=is_nullable,
        )
        self.db.add(record)
        return record

    def get_columns_by_table(self, table_id: int) -> List[SchemaColumn]:
        """Returns all stored column records for a given table."""
        return (
            self.db.query(SchemaColumn)
            .filter(SchemaColumn.table_id == table_id)
            .all()
        )

    def count_columns_by_connection(self, connection_id: int) -> int:
        """
        Returns the total column count across every table for a connection
        in a single query. Prefer this over summing len(get_columns_by_table(t.id))
        in a per-table loop — that pattern is one query per table against
        the Copilot's own DB (cheap individually, but still O(N) round-trips
        for something a single COUNT(*) JOIN answers directly).
        """
        return (
            self.db.query(SchemaColumn)
            .join(SchemaTable, SchemaColumn.table_id == SchemaTable.id)
            .filter(SchemaTable.connection_id == connection_id)
            .count()
        )

    # ------------------------------------------------------------------
    # Commit helper
    # ------------------------------------------------------------------

    def commit(self) -> None:
        """Commits the current unit of work."""
        self.db.commit()
