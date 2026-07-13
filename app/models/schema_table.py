from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class SchemaTable(Base):
    """
    ORM model representing the 'schema_tables' table in the Copilot DB.

    Each row is a snapshot of one discovered table from a target database.
    The combination of (connection_id, schema_name, table_name) is unique —
    this enforces that a table cannot be recorded twice for the same connection.
    """
    __tablename__ = "schema_tables"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign key back to the registered connection that owns this table
    connection_id = Column(
        Integer,
        ForeignKey("database_connections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    schema_name = Column(
        String,
        nullable=False,
        default="public",
        comment="PostgreSQL schema (e.g. 'public'). Reserved for future multi-schema support."
    )
    table_name = Column(String, nullable=False)
    discovered_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp of when this table was first ingested into the metadata catalog."
    )

    # One table → many columns
    columns = relationship(
        "SchemaColumn",
        back_populates="table",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # Composite unique constraint — prevents duplicate table records per connection
    __table_args__ = (
        UniqueConstraint("connection_id", "schema_name", "table_name", name="uq_schema_table"),
    )
