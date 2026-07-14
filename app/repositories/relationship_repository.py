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

    def get_by_table(
        self, connection_id: int, table_name: str, schema_name: str = "public"
    ) -> List[SchemaRelationship]:
        """
        Retrieves all stored relationship metadata where the source_table is
        the requested table, scoped to a schema (tables of the same name can
        exist in different schemas on one connection).
        """
        return (
            self.db.query(SchemaRelationship)
            .filter(
                SchemaRelationship.connection_id == connection_id,
                SchemaRelationship.source_table == table_name,
                SchemaRelationship.source_schema == schema_name,
            )
            .all()
        )

    def get_by_table_either_direction(
        self, connection_id: int, table_name: str, schema_name: str = "public"
    ) -> List[SchemaRelationship]:
        """
        Retrieves all stored relationships where the table participates as either
        the source or the target — used for table documentation, where both
        parent and child links are relevant. Scoped to a schema for the same
        reason as get_by_table().
        """
        return (
            self.db.query(SchemaRelationship)
            .filter(
                SchemaRelationship.connection_id == connection_id,
                (
                    (SchemaRelationship.source_table == table_name)
                    & (SchemaRelationship.source_schema == schema_name)
                )
                | (
                    (SchemaRelationship.target_table == table_name)
                    & (SchemaRelationship.target_schema == schema_name)
                )
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
        source_schema: str = "public",
        target_schema: str = "public",
        relationship_type: str = "foreign_key"
    ) -> SchemaRelationship:
        """
        Persists a new database relationship record into the local catalog.
        """
        record = SchemaRelationship(
            connection_id=connection_id,
            source_schema=source_schema,
            source_table=source_table,
            source_column=source_column,
            target_schema=target_schema,
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
        Queries PostgreSQL's native system catalogs (pg_constraint et al.) to
        discover all FOREIGN KEY constraints in the specified schema.

        Args:
            engine:      SQLAlchemy engine pointed at the target database.
            schema_name: PostgreSQL schema to inspect. Defaults to 'public'.
                         Pass a different value (e.g. 'analytics', 'staging') to
                         introspect custom schemas.

        Returns:
            A list of dicts with keys: source_schema, source_table, source_column,
            target_schema, target_table, target_column. target_schema can differ
            from source_schema/schema_name for a cross-schema foreign key —
            it's read from the referenced table's own namespace, not assumed
            to match source_schema.

        Note:
            This deliberately queries pg_catalog instead of information_schema.
            information_schema views (table_constraints, key_column_usage,
            constraint_column_usage, ...) apply SQL-standard visibility/
            permission checks across the *entire* catalog before filtering,
            which on a database with substantial catalog size can make a
            single query take tens of seconds — even though it's already one
            query, not one-per-table. pg_constraint/pg_class/pg_namespace/
            pg_attribute are plain indexed system tables with no such
            overhead and are the standard fast path for FK introspection.

            `unnest(con.conkey, con.confkey)` pairs source and target key
            columns positionally (conkey[i] always corresponds to confkey[i]
            by construction) — this is what the old information_schema query
            needed a three-way join + position_in_unique_constraint to
            achieve, and gets here for free from how Postgres stores
            composite foreign keys.

            `SELECT DISTINCT` still guards against multiple separate FK
            constraint objects resolving to the same logical relationship
            (e.g. inherited/partitioned tables each declaring their own copy).
        """
        query = text("""
            SELECT DISTINCT
                ns_src.nspname  AS source_schema,
                cls_src.relname AS source_table,
                att_src.attname AS source_column,
                ns_tgt.nspname  AS target_schema,
                cls_tgt.relname AS target_table,
                att_tgt.attname AS target_column
            FROM pg_constraint con
            JOIN pg_class     cls_src ON cls_src.oid = con.conrelid
            JOIN pg_namespace ns_src  ON ns_src.oid  = cls_src.relnamespace
            JOIN pg_class     cls_tgt ON cls_tgt.oid = con.confrelid
            JOIN pg_namespace ns_tgt  ON ns_tgt.oid  = cls_tgt.relnamespace
            CROSS JOIN LATERAL unnest(con.conkey, con.confkey) AS cols(src_attnum, tgt_attnum)
            JOIN pg_attribute att_src
              ON att_src.attrelid = con.conrelid AND att_src.attnum = cols.src_attnum
            JOIN pg_attribute att_tgt
              ON att_tgt.attrelid = con.confrelid AND att_tgt.attnum = cols.tgt_attnum
            WHERE con.contype = 'f'
              AND ns_src.nspname = :schema_name
            ORDER BY source_table, source_column
        """)
        with engine.connect() as conn:
            rows = conn.execute(query, {"schema_name": schema_name}).fetchall()

        return [
            {
                "source_schema": row[0],
                "source_table":  row[1],
                "source_column": row[2],
                "target_schema": row[3],
                "target_table":  row[4],
                "target_column": row[5],
            }
            for row in rows
        ]
