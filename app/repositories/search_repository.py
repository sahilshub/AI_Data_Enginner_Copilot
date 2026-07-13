from sqlalchemy.orm import Session
from typing import List

from app.models.schema_table import SchemaTable
from app.models.schema_column import SchemaColumn
from app.models.schema_relationship import SchemaRelationship


class SearchRepository:
    """
    Repository responsible for full-text keyword searches across the local
    metadata catalog stored in the Copilot DB.

    We use PostgreSQL ILIKE (case-insensitive LIKE) for substring matching.
    This is fast enough for a metadata catalog — tables/columns rarely number
    in the millions. Full vector search comes in Phase 2 (RAG).
    """

    def __init__(self, db: Session):
        self.db = db

    def search_tables(
        self, query: str, connection_id: int | None = None
    ) -> List[SchemaTable]:
        """
        Returns all SchemaTable records whose table_name contains the query string.
        Optionally scoped to a single connection.
        """
        q = self.db.query(SchemaTable).filter(
            SchemaTable.table_name.ilike(f"%{query}%")
        )
        if connection_id is not None:
            q = q.filter(SchemaTable.connection_id == connection_id)
        return q.order_by(SchemaTable.table_name).all()

    def search_columns(
        self, query: str, connection_id: int | None = None
    ) -> List[SchemaColumn]:
        """
        Returns all SchemaColumn records whose column_name or data_type
        contains the query string. Joins to SchemaTable to carry
        connection_id, table_name, and schema_name into the result.
        """
        q = (
            self.db.query(SchemaColumn)
            .join(SchemaTable, SchemaColumn.table_id == SchemaTable.id)
            .filter(
                SchemaColumn.column_name.ilike(f"%{query}%")
                | SchemaColumn.data_type.ilike(f"%{query}%")
            )
        )
        if connection_id is not None:
            q = q.filter(SchemaTable.connection_id == connection_id)
        return q.order_by(SchemaTable.table_name, SchemaColumn.column_name).all()

    def search_relationships(
        self, query: str, connection_id: int | None = None
    ) -> List[SchemaRelationship]:
        """
        Returns all SchemaRelationship records where either the source_table
        or target_table contains the query string.
        """
        q = self.db.query(SchemaRelationship).filter(
            SchemaRelationship.source_table.ilike(f"%{query}%")
            | SchemaRelationship.target_table.ilike(f"%{query}%")
            | SchemaRelationship.source_column.ilike(f"%{query}%")
            | SchemaRelationship.target_column.ilike(f"%{query}%")
        )
        if connection_id is not None:
            q = q.filter(SchemaRelationship.connection_id == connection_id)
        return q.order_by(SchemaRelationship.source_table).all()
