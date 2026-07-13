from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.models.schema_relationship import SchemaRelationship

class RelationshipRepository:
    """
    Repository layer responsible for querying foreign key relationships from target database metadata
    and performing CRUD operations on local 'schema_relationships' records inside Copilot DB.
    """
    def __init__(self, db: Session):
        self.db = db

    # ==============================================================================
    # Local Catalog Operations (Copilot DB)
    # ==============================================================================

    def get_by_connection(self, connection_id: int) -> List[SchemaRelationship]:
        """
        Retrieves all stored database relationship metadata for a connection ID.
        """
        return (
            self.db.query(SchemaRelationship)
            .filter(SchemaRelationship.connection_id == connection_id)
            .all()
        )

    def get_by_table(self, connection_id: int, table_name: str) -> List[SchemaRelationship]:
        """
        Retrieves all stored relationship metadata where the source_table is the requested table.
        """
        return (
            self.db.query(SchemaRelationship)
            .filter(
                SchemaRelationship.connection_id == connection_id,
                SchemaRelationship.source_table == table_name
            )
            .all()
        )

    def delete_by_connection(self, connection_id: int) -> None:
        """
        Removes all stored database relationship metadata records for a connection ID.
        Used to cleanly replace snapshots on new syncs.
        """
        (
            self.db.query(SchemaRelationship)
            .filter(SchemaRelationship.connection_id == connection_id)
            .delete(synchronize_session=False)
        )
        self.db.commit()

    def create(
        self,
        connection_id: int,
        source_table: str,
        source_column: str,
        target_table: str,
        target_column: str,
        relationship_type: str = "foreign_key"
    ) -> SchemaRelationship:
        """
        Persists a new database relationship record into the local catalog.
        """
        record = SchemaRelationship(
            connection_id=connection_id,
            source_table=source_table,
            source_column=source_column,
            target_table=target_table,
            target_column=target_column,
            relationship_type=relationship_type
        )
        self.db.add(record)
        return record

    def commit(self) -> None:
        """
        Commits local session changes.
        """
        self.db.commit()

    # ==============================================================================
    # Target Database Introspection (Target DB)
    # ==============================================================================

    @staticmethod
    def get_foreign_keys_from_target(
        engine: Engine, schema_name: str = "public"
    ) -> List[Dict[str, Any]]:
        """
        Queries information_schema on the external target database to discover all
        FOREIGN KEY constraints in the specified schema.

        Args:
            engine:      SQLAlchemy engine pointed at the target database.
            schema_name: PostgreSQL schema to inspect. Defaults to 'public'.
                         Pass a different value (e.g. 'analytics', 'staging') to
                         introspect custom schemas.

        Returns:
            A list of dicts with keys: source_table, source_column,
            target_table, target_column.
        """
        query = text("""
            SELECT
                kcu.table_name  AS source_table,
                kcu.column_name AS source_column,
                ccu.table_name  AS target_table,
                ccu.column_name AS target_column
            FROM
                information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                 AND tc.table_schema    = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                 AND ccu.table_schema   = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_schema    = :schema_name
        """)
        with engine.connect() as conn:
            rows = conn.execute(query, {"schema_name": schema_name}).fetchall()

        return [
            {
                "source_table":  row[0],
                "source_column": row[1],
                "target_table":  row[2],
                "target_column": row[3],
            }
            for row in rows
        ]
