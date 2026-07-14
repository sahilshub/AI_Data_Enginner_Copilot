from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any, Dict, Optional


class JobAcceptedResponse(BaseModel):
    """Returned immediately when a sync/refresh job is queued."""
    job_id: int = Field(..., description="ID to poll via GET /connections/{id}/jobs/{job_id}.")
    status: str = Field(..., description="Always 'pending' at creation time.")
    message: str = Field(..., description="Human-readable acknowledgement.")


class JobResponse(BaseModel):
    """Current state of an async sync/refresh job."""
    id: int
    job_type: str = Field(..., description="'sync' or 'refresh'.")
    schema_name: str
    status: str = Field(..., description="pending, running, completed, or failed.")
    result_summary: Optional[Dict[str, Any]] = Field(
        None, description="Present once completed — e.g. {'tables_synced': 90}."
    )
    error_message: Optional[str] = Field(None, description="Present only if status is 'failed'.")
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
