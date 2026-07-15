from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.repositories.connection_repository import ConnectionRepository
from app.repositories.metadata_repository import MetadataRepository
from app.repositories.relationship_repository import RelationshipRepository
from app.schemas.documentation_schema import (
    DatabaseDocumentationResponse,
    TableDocumentationResponse,
    RelationshipDocumentationResponse,
)
from app.schemas.relationship_schema import RelationshipResponse
from app.schemas.metadata_schema import StoredColumnResponse


class DocumentationService:
    """
    Generates human-readable documentation from metadata already stored in
    the Copilot's catalog (Phase 1, Step 8). Purely a read/formatting layer:
    no target-database calls, no new storage.

    Deliberately composes the existing MetadataRepository and
    RelationshipRepository rather than introducing a separate
    DocumentationRepository — both already expose exactly the reads this
    step needs (tables, columns, relationships), and a third repository
    re-querying the same tables would just duplicate that logic.
    """

    def __init__(self, db: Session):
        self.db = db
        self.conn_repo = ConnectionRepository(db)
        self.meta_repo = MetadataRepository(db)
        self.rel_repo = RelationshipRepository(db)

    def _require_connection(self, connection_id: int):
        connection = self.conn_repo.get_by_id(connection_id)
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Database connection with ID {connection_id} not found."
            )
        return connection

    def generate_database_documentation(self, connection_id: int) -> DatabaseDocumentationResponse:
        """Builds a high-level overview: table/column/relationship counts and table names."""
        connection = self._require_connection(connection_id)

        tables = self.meta_repo.get_tables_by_connection(connection_id)
        column_count = self.meta_repo.count_columns_by_connection(connection_id)
        relationships = self.rel_repo.get_by_connection(connection_id)

        return DatabaseDocumentationResponse(
            connection_name=connection.name,
            database_name=connection.database,
            table_count=len(tables),
            column_count=column_count,
            relationship_count=len(relationships),
            tables=[t.table_name for t in tables],
        )

    def generate_table_documentation(
        self, connection_id: int, table_name: str, schema_name: str = "public"
    ) -> TableDocumentationResponse:
        """Builds documentation for a single table: its columns and its relationships."""
        self._require_connection(connection_id)

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
        relationships = self.rel_repo.get_by_table_either_direction(connection_id, table_name, schema_name)

        return TableDocumentationResponse(
            table_name=table_record.table_name,
            schema_name=table_record.schema_name,
            columns=[StoredColumnResponse.model_validate(c) for c in columns],
            relationships=[RelationshipResponse.model_validate(r) for r in relationships],
        )

    def generate_relationship_documentation(self, connection_id: int) -> RelationshipDocumentationResponse:
        """Builds documentation listing every discovered relationship for a connection."""
        self._require_connection(connection_id)

        relationships = self.rel_repo.get_by_connection(connection_id)
        return RelationshipDocumentationResponse(
            relationships=[RelationshipResponse.model_validate(r) for r in relationships],
            total_count=len(relationships),
        )
