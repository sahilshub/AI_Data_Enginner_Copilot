from sqlalchemy import Column, Integer, String, DateTime, JSON
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
    password = Column(String, nullable=False)  # Fernet-encrypted at rest — see app/core/security.py. Never read this column directly; decrypt via decrypt_password().
    database = Column(String, nullable=False)

    # Catch-all for source-specific config that doesn't fit host/port/username/
    # password/database — e.g. a future BigQuery connector's service-account
    # JSON + project id, or Snowflake's account/warehouse/role. Unused by
    # PostgresConnector today; exists so adding a new source later doesn't
    # require another schema migration. See app/connectors/.
    extra_config = Column(JSON, nullable=True)

    # Auditing Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
