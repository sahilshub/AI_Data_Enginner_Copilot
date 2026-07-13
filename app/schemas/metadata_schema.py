from pydantic import BaseModel, Field
from datetime import datetime
from typing import List


class StoredColumnResponse(BaseModel):
    """Column record served from the Copilot's metadata store."""
    id: int = Field(..., description="Primary key of the stored column record.")
    column_name: str = Field(..., description="Name of the column.")
    data_type: str = Field(..., description="PostgreSQL native data type.")
    is_nullable: bool = Field(..., description="Whether the column allows NULL values.")

    model_config = {"from_attributes": True}


class StoredTableResponse(BaseModel):
    """Table record served from the Copilot's metadata store."""
    id: int = Field(..., description="Primary key of the stored table record.")
    table_name: str = Field(..., description="Name of the table.")
    schema_name: str = Field(..., description="PostgreSQL schema containing the table.")
    discovered_at: datetime = Field(..., description="When this table was first synced.")

    model_config = {"from_attributes": True}


class StoredTableDetailResponse(BaseModel):
    """Full table record including all persisted column details."""
    id: int
    table_name: str
    schema_name: str
    discovered_at: datetime
    columns: List[StoredColumnResponse] = Field(
        ..., description="All columns belonging to this table."
    )

    model_config = {"from_attributes": True}


class SyncResponse(BaseModel):
    """Response returned after a successful metadata synchronization."""
    message: str = Field(..., description="Human-readable status message.")
    tables_synced: int = Field(..., description="Number of tables discovered and persisted.")
