from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.metadata_change_schema import (
    RefreshResponse,
    RefreshStatusResponse,
    MetadataChangeResponse,
)
from app.services.metadata_refresh_service import MetadataRefreshService

router = APIRouter(
    prefix="/connections/{connection_id}/metadata",
    tags=["Metadata Refresh"]
)


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh metadata and detect changes",
    description=(
        "Reads the live target database, compares it against the stored metadata "
        "catalog, records any detected changes (tables/columns/relationships added, "
        "removed, or changed), then updates the catalog to match the live schema."
    ),
)
def refresh_metadata(
    connection_id: int,
    schema_name: str = Query("public", description="PostgreSQL schema to refresh."),
    db: Session = Depends(get_db),
) -> RefreshResponse:
    service = MetadataRefreshService(db)
    return service.refresh_metadata(connection_id, schema_name)


@router.get(
    "/changes",
    response_model=List[MetadataChangeResponse],
    status_code=status.HTTP_200_OK,
    summary="Get metadata change history",
    description="Returns the full history of detected metadata changes for a connection, most recent first.",
)
def get_metadata_changes(
    connection_id: int,
    db: Session = Depends(get_db),
) -> List[MetadataChangeResponse]:
    service = MetadataRefreshService(db)
    return service.get_changes(connection_id)


@router.get(
    "/status",
    response_model=RefreshStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get latest refresh status",
    description="Returns the timestamp of the most recently detected change and the total change count.",
)
def get_refresh_status(
    connection_id: int,
    db: Session = Depends(get_db),
) -> RefreshStatusResponse:
    service = MetadataRefreshService(db)
    return service.get_refresh_status(connection_id)
