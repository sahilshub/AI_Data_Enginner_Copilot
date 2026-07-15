from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List

from app.repositories.connection_repository import ConnectionRepository
from app.repositories.relationship_repository import RelationshipRepository
from app.connectors.factory import get_connector
from app.connectors.cache import connector_cache
from app.connectors.base import SourceConnector
from app.schemas.relationship_schema import (
    RelationshipResponse,
    TableRelationshipResponse,
    DiscoverRelationshipsResponse,
)
from app.core.security import decrypt_password

class RelationshipService:
    """
    Service layer responsible for orchestrating the discovery, mapping, and serving of
    database table relationships (foreign keys) inside the platform catalog.
    """
    def __init__(self, db: Session):
        self.db = db
        self.conn_repo = ConnectionRepository(db)
        self.rel_repo = RelationshipRepository(db)

    # ------------------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------------------

    def _get_connector(self, connection_id: int) -> SourceConnector:
        """
        Loads registered connection settings and resolves the SourceConnector
        for its dialect.
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

    # ------------------------------------------------------------------------------
    # Public Service Actions
    # ------------------------------------------------------------------------------

    def discover_relationships(
        self, connection_id: int, schema_name: str = "public"
    ) -> DiscoverRelationshipsResponse:
        """
        Connects to the target database to extract existing foreign key constraints
        and saves them locally in the Copilot DB schema catalog.
        Replaces previous relationship records for the connection.
        """
        connector = self._get_connector(connection_id)

        try:
            # Query target constraints
            fkeys = connector.get_foreign_keys(schema_name)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to read constraints from target database: {str(e)}"
            )

        # Clear existing mappings
        self.rel_repo.delete_by_connection(connection_id)

        # Ingest new mappings
        saved_count = 0
        for fk in fkeys:
            self.rel_repo.create(
                connection_id=connection_id,
                source_schema=fk["source_schema"],
                source_table=fk["source_table"],
                source_column=fk["source_column"],
                target_schema=fk["target_schema"],
                target_table=fk["target_table"],
                target_column=fk["target_column"]
            )
            saved_count += 1

        self.rel_repo.commit()

        return DiscoverRelationshipsResponse(
            message="Relationships discovered and synchronized successfully.",
            relationships_discovered=saved_count
        )

    def get_relationships(self, connection_id: int) -> List[RelationshipResponse]:
        """
        Serves all recorded relationship mappings from the local database.
        No direct connection to the target database is established.
        """
        # Validate connection exists
        if not self.conn_repo.get_by_id(connection_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Database connection with ID {connection_id} not found."
            )
            
        records = self.rel_repo.get_by_connection(connection_id)
        return [RelationshipResponse.model_validate(r) for r in records]

    def get_table_relationships(
        self, connection_id: int, table_name: str, schema_name: str = "public"
    ) -> List[TableRelationshipResponse]:
        """
        Serves recorded connections specific to a table (where it acts as the source/foreign key).
        Returns a list of target tables and their relationship link type.
        """
        # Validate connection exists
        if not self.conn_repo.get_by_id(connection_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Database connection with ID {connection_id} not found."
            )

        records = self.rel_repo.get_by_table(connection_id, table_name, schema_name)
        return [
            TableRelationshipResponse(
                target_schema=r.target_schema,
                target_table=r.target_table,
                relationship_type=r.relationship_type
            )
            for r in records
        ]
