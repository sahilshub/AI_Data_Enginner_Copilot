from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func

from app.core.database import Base


class SyncJob(Base):
    """
    ORM model representing the 'sync_jobs' table in the Copilot DB.

    Durable record of an async metadata sync/refresh run, correlated to a
    Celery task via celery_task_id. Celery's Redis result backend is
    TTL-based and can be evicted — this row is the source of truth for
    "did it finish, and what happened" after the triggering request is long
    gone.
    """
    __tablename__ = "sync_jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    connection_id = Column(
        Integer,
        ForeignKey("database_connections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    job_type = Column(String, nullable=False, comment="'sync' or 'refresh'.")
    schema_name = Column(String, nullable=False, default="public")
    status = Column(
        String,
        nullable=False,
        default="pending",
        comment="pending, running, completed, or failed.",
    )
    celery_task_id = Column(String, nullable=True, index=True)

    result_summary = Column(JSON, nullable=True)
    error_message = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
