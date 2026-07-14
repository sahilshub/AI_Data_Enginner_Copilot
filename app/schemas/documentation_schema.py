from pydantic import BaseModel, Field
from typing import List

from app.schemas.relationship_schema import RelationshipResponse
from app.schemas.metadata_schema import StoredColumnResponse


class DatabaseDocumentationResponse(BaseModel):
    """High-level, human-readable overview of a connection's synced metadata."""
    connection_name: str = Field(..., description="Name of the registered connection.")
    database_name: str = Field(..., description="Name of the target database.")
    table_count: int = Field(..., description="Number of tables in the metadata catalog.")
    column_count: int = Field(..., description="Total number of columns across all tables.")
    relationship_count: int = Field(..., description="Total number of discovered relationships.")
    tables: List[str] = Field(..., description="Names of all synced tables.")


class TableDocumentationResponse(BaseModel):
    """Human-readable documentation for a single table, including its columns and relationships."""
    table_name: str = Field(..., description="Name of the table.")
    schema_name: str = Field(..., description="PostgreSQL schema containing the table.")
    columns: List[StoredColumnResponse] = Field(..., description="All columns belonging to this table.")
    relationships: List[RelationshipResponse] = Field(
        ..., description="Relationships where this table participates as either source or target."
    )


class RelationshipDocumentationResponse(BaseModel):
    """Documentation describing all discovered relationships for a connection."""
    relationships: List[RelationshipResponse] = Field(..., description="All discovered relationships.")
    total_count: int = Field(..., description="Total number of relationships.")
