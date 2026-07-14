from pydantic import BaseModel, Field
from typing import List, Optional


class TableSearchResult(BaseModel):
    """A single table matched by a search query."""
    connection_id: int
    table_name: str
    schema_name: str

    model_config = {"from_attributes": True}


class ColumnSearchResult(BaseModel):
    """A single column matched by a search query."""
    connection_id: int
    table_name: str
    schema_name: str
    column_name: str
    data_type: str
    is_nullable: bool

    model_config = {"from_attributes": True}


class RelationshipSearchResult(BaseModel):
    """A single relationship matched by a search query."""
    connection_id: int
    source_schema: str
    source_table: str
    source_column: str
    target_schema: str
    target_table: str
    target_column: str
    relationship_type: str

    model_config = {"from_attributes": True}


class SearchResponse(BaseModel):
    """Aggregated result of a full-catalog search across tables, columns and relationships."""
    query: str = Field(..., description="The original search term.")
    tables: List[TableSearchResult] = Field(default_factory=list)
    columns: List[ColumnSearchResult] = Field(default_factory=list)
    relationships: List[RelationshipSearchResult] = Field(default_factory=list)
    total_results: int = Field(..., description="Sum of all matched records.")
