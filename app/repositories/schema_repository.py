from sqlalchemy import text
from sqlalchemy.engine import Engine
from typing import List, Dict, Any

class SchemaRepository:
    """
    Repository responsible for querying PostgreSQL's built-in system views.
    Retrieves structural metadata (tables, columns, types) from 'information_schema'
    without touching any actual business data in the target database.
    """

    def __init__(self, engine: Engine):
        # The engine here is a transient connection to the *target* database
        # (the database being analyzed), not our copilot's own database.
        self.engine = engine

    def get_tables(self) -> List[Dict[str, Any]]:
        """
        Queries information_schema.tables to retrieve all user-defined tables
        in the 'public' schema of the target database.

        Returns:
            A list of dicts, each containing a 'table_name' key.
        """
        query = text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        with self.engine.connect() as conn:
            rows = conn.execute(query).fetchall()
        return [{"table_name": row[0]} for row in rows]

    def get_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Queries information_schema.columns to retrieve column names and data types
        for a specific table.

        Args:
            table_name: The name of the table to inspect.

        Returns:
            A list of dicts, each with 'name' and 'data_type' keys.
        """
        query = text("""
            SELECT column_name,
                   data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = :table_name
            ORDER BY ordinal_position
        """)
        with self.engine.connect() as conn:
            rows = conn.execute(query, {"table_name": table_name}).fetchall()
        return [{"name": row[0], "data_type": row[1]} for row in rows]
