from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class DatabaseConnection(Base):
    """
    SQLAlchemy ORM model representing the 'database_connections' table.
    Stores the configuration details and credentials needed to connect to target data stores.
    """
    __tablename__ = "database_connections"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True, index=True, nullable=False)
    
    # Connection Properties
    dialect = Column(String, nullable=False, default="postgresql")  # e.g., postgresql, mysql, sqlite
    host = Column(String, nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)  # Note: Stored as plaintext for simplicity. In production, this must be encrypted!
    database = Column(String, nullable=False)

    # Auditing Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
