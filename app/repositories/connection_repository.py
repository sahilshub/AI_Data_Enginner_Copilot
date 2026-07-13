from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.connection import DatabaseConnection
from app.schemas.connection_schema import ConnectionCreate

class ConnectionRepository:
    """
    Repository class executing CRUD operations for 'database_connections'.
    Encapsulates raw SQLAlchemy session queries, adhering to the Repository pattern.
    """
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, connection_id: int) -> Optional[DatabaseConnection]:
        """
        Retrieves a database connection by its primary key ID.
        """
        return self.db.query(DatabaseConnection).filter(DatabaseConnection.id == connection_id).first()

    def get_by_name(self, name: str) -> Optional[DatabaseConnection]:
        """
        Retrieves a database connection by its unique name.
        """
        return self.db.query(DatabaseConnection).filter(DatabaseConnection.name == name).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[DatabaseConnection]:
        """
        Retrieves all registered database connections with support for pagination.
        """
        return self.db.query(DatabaseConnection).offset(skip).limit(limit).all()

    def create(self, schema_in: ConnectionCreate) -> DatabaseConnection:
        """
        Creates and persists a new DatabaseConnection database record.
        """
        db_connection = DatabaseConnection(
            name=schema_in.name,
            dialect=schema_in.dialect,
            host=schema_in.host,
            port=schema_in.port,
            username=schema_in.username,
            password=schema_in.password,
            database=schema_in.database
        )
        self.db.add(db_connection)
        self.db.commit()
        self.db.refresh(db_connection)
        return db_connection

    def delete(self, db_obj: DatabaseConnection) -> None:
        """
        Removes a database connection record from the database.
        """
        self.db.delete(db_obj)
        self.db.commit()
