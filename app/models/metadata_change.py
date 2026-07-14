from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.core.database import Base


class MetadataChange(Base):
    """
    ORM model representing the 'metadata_changes' table in the Copilot DB.

    Each row records one detected difference between a previous metadata
    snapshot and a freshly re-discovered one (see MetadataRefreshService).
    This is an append-only change history — rows are never updated or
    deleted by normal operation, only inserted on each refresh.
    """
    __tablename__ = "metadata_changes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    connection_id = Column(
        Integer,
        ForeignKey("database_connections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    change_type = Column(
        String,
        nullable=False,
        comment="One of: TABLE_ADDED, TABLE_REMOVED, COLUMN_ADDED, COLUMN_REMOVED, "
                "COLUMN_TYPE_CHANGED, RELATIONSHIP_ADDED, RELATIONSHIP_REMOVED."
    )
    object_type = Column(
        String,
        nullable=False,
        comment="The kind of object the change applies to: TABLE, COLUMN, or RELATIONSHIP."
    )
    object_name = Column(
        String,
        nullable=False,
        comment="Human-readable identifier of the changed object, e.g. 'customers.phone_number'."
    )
    previous_value = Column(String, nullable=True)
    new_value = Column(String, nullable=True)

    detected_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
