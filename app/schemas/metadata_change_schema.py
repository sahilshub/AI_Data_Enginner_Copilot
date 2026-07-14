from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class MetadataChangeResponse(BaseModel):
    """A single detected metadata change record."""
    change_type: str = Field(..., description="TABLE_ADDED, TABLE_REMOVED, COLUMN_ADDED, "
                                                "COLUMN_REMOVED, COLUMN_TYPE_CHANGED, "
                                                "RELATIONSHIP_ADDED, or RELATIONSHIP_REMOVED.")
    object_type: str = Field(..., description="TABLE, COLUMN, or RELATIONSHIP.")
    object_name: str = Field(..., description="Identifier of the changed object, e.g. 'customers.phone_number'.")
    previous_value: Optional[str] = Field(None, description="Value before the change, when applicable.")
    new_value: Optional[str] = Field(None, description="Value after the change, when applicable.")
    detected_at: datetime = Field(..., description="When this change was detected.")

    model_config = {"from_attributes": True}


class RefreshResponse(BaseModel):
    """Response returned after a metadata refresh run."""
    message: str = Field(..., description="Human-readable status message.")
    changes_detected: int = Field(..., description="Number of changes detected and recorded during this refresh.")


class RefreshStatusResponse(BaseModel):
    """Summary of the most recent refresh for a connection."""
    last_refresh: Optional[datetime] = Field(
        None, description="Timestamp of the most recently detected change, or null if never refreshed."
    )
    changes_detected: int = Field(..., description="Total number of changes ever recorded for this connection.")
