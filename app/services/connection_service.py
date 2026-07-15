from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.repositories.connection_repository import ConnectionRepository
from app.connectors.factory import is_supported_dialect
from app.connectors.cache import connector_cache
from app.schemas.connection_schema import ConnectionCreate, ConnectionTest, ConnectionTestResponse
from app.models.connection import DatabaseConnection
from typing import List

class ConnectionService:
    """
    Service layer to handle business workflows for database connection credentials.
    Performs validation checks, verifies connection credentials, and interfaces with the repository.
    """
    def __init__(self, db: Session):
        self.repo = ConnectionRepository(db)

    def create_connection(self, schema_in: ConnectionCreate) -> DatabaseConnection:
        """
        Registers a new database connection configuration after validating that
        the name is unique and the connection credentials are functional.
        """
        # 1. Enforce business rule: Unique connection friendly name
        existing = self.repo.get_by_name(schema_in.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A connection with name '{schema_in.name}' already exists."
            )

        # 2. Enforce business rule: Reject unsupported dialects up front —
        # fail fast here instead of a confusing error later during schema
        # introspection (see app/connectors/factory.py).
        if not is_supported_dialect(schema_in.dialect):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Dialect '{schema_in.dialect}' is not yet supported."
            )

        # 3. Enforce business rule: Validate credentials by pinging the database before saving
        test_payload = ConnectionTest(
            dialect=schema_in.dialect,
            host=schema_in.host,
            port=schema_in.port,
            username=schema_in.username,
            password=schema_in.password,
            database=schema_in.database
        )
        test_result = self.test_connection(test_payload)
        if not test_result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Database connection verification failed: {test_result.message}"
            )

        # 4. Save connection details via Repository
        return self.repo.create(schema_in)

    def get_connections(self, skip: int = 0, limit: int = 100) -> List[DatabaseConnection]:
        """
        Retrieves a paginated list of registered database connections.
        """
        return self.repo.get_all(skip=skip, limit=limit)

    def delete_connection(self, connection_id: int) -> None:
        """
        Deletes a registered database connection configuration by its ID.
        Throws a 404 HTTP Exception if the ID does not exist.
        """
        db_connection = self.repo.get_by_id(connection_id)
        if not db_connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Database connection with ID {connection_id} not found."
            )
        self.repo.delete(db_connection)
        # Evict and dispose the cached connector (if any) — otherwise its
        # pooled connections to the now-deleted connection's target DB would
        # linger for the lifetime of the process. See app/connectors/cache.py.
        connector_cache.invalidate(connection_id)

    @staticmethod
    def test_connection(schema: ConnectionTest) -> ConnectionTestResponse:
        """
        Executes a transient diagnostic connection to verify hostname, port,
        credentials, and database accessibility. Does not persist parameters.
        """
        dialect = schema.dialect
        
        # Format the connection URI based on dialect specifications
        if dialect == "postgresql" and not dialect.endswith("+psycopg2"):
            db_url = f"postgresql+psycopg2://{schema.username}:{schema.password}@{schema.host}:{schema.port}/{schema.database}"
        else:
            db_url = f"{dialect}://{schema.username}:{schema.password}@{schema.host}:{schema.port}/{schema.database}"

        # Prevent requests from hanging indefinitely by enforcing a 5-second socket timeout
        connect_args = {}
        if "postgresql" in dialect:
            connect_args = {"connect_timeout": 5}
        elif "mysql" in dialect:
            connect_args = {"connect_timeout": 5}

        try:
            # Create a transient engine specifically for this diagnostic check
            temp_engine = create_engine(db_url, connect_args=connect_args)
            
            # Attempt to connect and execute a basic ping
            with temp_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                
            return ConnectionTestResponse(
                success=True,
                message="Successfully established connection!"
            )
        except Exception as e:
            return ConnectionTestResponse(
                success=False,
                message=f"Connection failure: {str(e)}"
            )
