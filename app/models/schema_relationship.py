from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from app.core.database import Base

class SchemaRelationship(Base):
    """
    ORM model representing the 'schema_relationships' table in the Copilot DB.
    Stores the connections between different database tables (foreign key relationships)
    which are essential for constructing correct JOIN SQL queries in later AI steps.
    """
    __tablename__ = "schema_relationships"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    connection_id = Column(
        Integer,
        ForeignKey("database_connections.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Schema-qualifying source/target independently (rather than one shared
    # schema_name) supports the rare but real case of a cross-schema FK, and
    # is required to disambiguate same-named tables living in different
    # schemas on one connection — see AGENTS.md Engineering Guardrails.
    source_schema = Column(String, nullable=False, default="public")
    source_table = Column(String, nullable=False, index=True)
    source_column = Column(String, nullable=False)

    target_schema = Column(String, nullable=False, default="public")
    target_table = Column(String, nullable=False, index=True)
    target_column = Column(String, nullable=False)

    relationship_type = Column(String, nullable=False, default="foreign_key")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Prevent saving duplicate relationships for the same connection
    __table_args__ = (
        UniqueConstraint(
            "connection_id",
            "source_schema",
            "source_table",
            "source_column",
            "target_schema",
            "target_table",
            "target_column",
            name="uq_schema_relationship"
        ),
    )
