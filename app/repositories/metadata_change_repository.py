from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.models.metadata_change import MetadataChange


class MetadataChangeRepository:
    """
    Repository responsible for persisting and retrieving metadata change
    history (Phase 1, Step 9) inside the Copilot's own database.

    This is an append-only log — records are written once by
    MetadataRefreshService and never updated or deleted during normal use.
    """

    def __init__(self, db: Session):
        self.db = db

    def save_changes(self, connection_id: int, changes: List[Dict[str, Any]]) -> None:
        """
        Persists a batch of detected changes for a connection.

        Args:
            connection_id: The connection these changes belong to.
            changes: A list of dicts with keys: change_type, object_type,
                     object_name, previous_value (optional), new_value (optional).
        """
        for change in changes:
            record = MetadataChange(
                connection_id=connection_id,
                change_type=change["change_type"],
                object_type=change["object_type"],
                object_name=change["object_name"],
                previous_value=change.get("previous_value"),
                new_value=change.get("new_value"),
            )
            self.db.add(record)
        self.db.commit()

    def get_changes(self, connection_id: int) -> List[MetadataChange]:
        """
        Retrieves the full change history for a connection, most recent first.
        """
        return (
            self.db.query(MetadataChange)
            .filter(MetadataChange.connection_id == connection_id)
            .order_by(MetadataChange.detected_at.desc())
            .all()
        )

    def get_latest_change(self, connection_id: int) -> Optional[MetadataChange]:
        """
        Retrieves the single most recently detected change for a connection,
        used to report the last-refresh timestamp.
        """
        return (
            self.db.query(MetadataChange)
            .filter(MetadataChange.connection_id == connection_id)
            .order_by(MetadataChange.detected_at.desc())
            .first()
        )
