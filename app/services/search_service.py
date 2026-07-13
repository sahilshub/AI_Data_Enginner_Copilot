from sqlalchemy.orm import Session
from typing import Optional

from app.repositories.search_repository import SearchRepository
from app.schemas.search_schema import (
    SearchResponse,
    TableSearchResult,
    ColumnSearchResult,
    RelationshipSearchResult,
)


class SearchService:
    """
    Orchestrates cross-entity search across the local metadata catalog.

    The search always runs against the Copilot DB — no connection to any
    target database is made. Only previously synced metadata is searchable.

    This design decision is intentional:
    - Search must be instant and offline-capable.
    - It must not create load on target databases.
    - It serves as the foundation for RAG context retrieval in Phase 2.
    """

    def __init__(self, db: Session):
        self.db = db
        self.repo = SearchRepository(db)

    def search(
        self, query: str, connection_id: Optional[int] = None
    ) -> SearchResponse:
        """
        Performs a case-insensitive keyword search across tables, columns,
        and relationships in the local metadata catalog.

        Args:
            query:         The keyword to search for.
            connection_id: When provided, restricts results to a single connection.
                           When None, searches across all connections.

        Returns:
            A SearchResponse containing matched tables, columns, and relationships,
            plus a total_results count.
        """
        # Execute searches in parallel against each entity type
        raw_tables = self.repo.search_tables(query, connection_id)
        raw_columns = self.repo.search_columns(query, connection_id)
        raw_relationships = self.repo.search_relationships(query, connection_id)

        # Map ORM records to Pydantic response models
        tables = [
            TableSearchResult(
                connection_id=t.connection_id,
                table_name=t.table_name,
                schema_name=t.schema_name,
            )
            for t in raw_tables
        ]

        columns = [
            ColumnSearchResult(
                # Navigate the ORM relationship to get the parent table fields
                connection_id=c.table.connection_id,
                table_name=c.table.table_name,
                schema_name=c.table.schema_name,
                column_name=c.column_name,
                data_type=c.data_type,
                is_nullable=c.is_nullable,
            )
            for c in raw_columns
        ]

        relationships = [
            RelationshipSearchResult(
                connection_id=r.connection_id,
                source_table=r.source_table,
                source_column=r.source_column,
                target_table=r.target_table,
                target_column=r.target_column,
                relationship_type=r.relationship_type,
            )
            for r in raw_relationships
        ]

        return SearchResponse(
            query=query,
            tables=tables,
            columns=columns,
            relationships=relationships,
            total_results=len(tables) + len(columns) + len(relationships),
        )
