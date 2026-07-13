from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class SchemaColumn(Base):
    """
    ORM model representing the 'schema_columns' table in the Copilot DB.

    Each row is a snapshot of one column belonging to a discovered table.
    Storing is_nullable enriches the AI context later — an LLM writing SQL
    can decide whether a WHERE clause must guard against NULLs.
    """
    __tablename__ = "schema_columns"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign key back to the parent table record
    table_id = Column(
        Integer,
        ForeignKey("schema_tables.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    column_name = Column(String, nullable=False)
    data_type = Column(String, nullable=False)
    is_nullable = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether the column allows NULL values. Sourced from information_schema.columns."
    )
    discovered_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Many-to-one back to the parent SchemaTable
    table = relationship("SchemaTable", back_populates="columns")
