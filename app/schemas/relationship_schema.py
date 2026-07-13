from pydantic import BaseModel, Field

class RelationshipResponse(BaseModel):
    """
    Response schema representing a direct link between a source column and target column.
    """
    source_table: str = Field(..., description="Table containing the foreign key reference.")
    source_column: str = Field(..., description="Column acting as the foreign key.")
    target_table: str = Field(..., description="Table being referenced by the foreign key.")
    target_column: str = Field(..., description="Column in target table being referenced.")

    model_config = {
        "from_attributes": True
    }

class TableRelationshipResponse(BaseModel):
    """
    Response schema returning relationship connections for a specific table.
    """
    target_table: str = Field(..., description="The connected table.")
    relationship_type: str = Field(..., description="The type of the relationship link (e.g. foreign_key).")

    model_config = {
        "from_attributes": True
    }

class DiscoverRelationshipsResponse(BaseModel):
    """
    Response message indicating successful completion of the sync operation.
    """
    message: str = Field(..., description="Status description.")
    relationships_discovered: int = Field(..., description="Number of relationships found and saved.")
