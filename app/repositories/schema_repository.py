from sqlalchemy import text
from sqlalchemy.engine import Engine
from typing import List, Dict, Any


class SchemaRepository:
    """
    Repository responsible for querying PostgreSQL's built-in system views.
    Retrieves structural metadata (tables, columns, types) from 'information_schema'
    without touching any actual business data in the target database.

    All methods accept a schema_name parameter (default 'public') so callers
    can introspect any PostgreSQL schema, not just the default one.
    """

    def __init__(self, engine: Engine):
        # The engine here is a transient connection to the *target* database
        # (the database being analyzed), not our copilot's own database.
        self.engine = engine

    def get_tables(self, schema_name: str = "public") -> List[Dict[str, Any]]:
        """
        Queries information_schema.tables to retrieve all user-defined BASE TABLEs
        in the specified schema of the target database.

        Args:
            schema_name: PostgreSQL schema to inspect. Defaults to 'public'.

        Returns:
            A list of dicts, each containing a 'table_name' key.
        """
        query = text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = :schema_name
              AND table_type   = 'BASE TABLE'
            ORDER BY table_name
        """)
        with self.engine.connect() as conn:
            rows = conn.execute(query, {"schema_name": schema_name}).fetchall()
        return [{"table_name": row[0]} for row in rows]

    def get_columns(
        self, table_name: str, schema_name: str = "public"
    ) -> List[Dict[str, Any]]:
        """
        Queries information_schema.columns to retrieve column names, data types,
        and nullability for a specific table in the given schema.

        Args:
            table_name:  The name of the table to inspect.
            schema_name: PostgreSQL schema containing the table. Defaults to 'public'.

        Returns:
            A list of dicts with 'name', 'data_type', and 'is_nullable' keys.
        """
        query = text("""
            SELECT column_name,
                   data_type,
                   is_nullable
            FROM information_schema.columns
            WHERE table_schema = :schema_name
              AND table_name   = :table_name
            ORDER BY ordinal_position
        """)
        with self.engine.connect() as conn:
            rows = conn.execute(
                query, {"schema_name": schema_name, "table_name": table_name}
            ).fetchall()
        return [
            {
                "name": row[0],
                "data_type": row[1],
                # information_schema returns 'YES' or 'NO' as a string
                "is_nullable": row[2].upper() == "YES",
            }
            for row in rows
        ]
