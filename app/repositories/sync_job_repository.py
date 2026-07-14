from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import Any, Dict, List, Optional

from app.models.sync_job import SyncJob


class SyncJobRepository:
    """
    Repository for the durable async-job history (SyncJob rows). Written by
    both the API (job creation) and Celery workers (status updates) — see
    app/tasks/metadata_tasks.py.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, connection_id: int, job_type: str, schema_name: str) -> SyncJob:
        """Creates a job row in 'pending' status. Caller commits."""
        job = SyncJob(
            connection_id=connection_id,
            job_type=job_type,
            schema_name=schema_name,
            status="pending",
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def set_celery_task_id(self, job_id: int, celery_task_id: str) -> None:
        self.db.query(SyncJob).filter(SyncJob.id == job_id).update(
            {"celery_task_id": celery_task_id}
        )
        self.db.commit()

    def mark_running(self, job_id: int) -> None:
        self.db.query(SyncJob).filter(SyncJob.id == job_id).update(
            {"status": "running", "started_at": func.now()}
        )
        self.db.commit()

    def mark_completed(self, job_id: int, result_summary: Dict[str, Any]) -> None:
        self.db.query(SyncJob).filter(SyncJob.id == job_id).update(
            {"status": "completed", "completed_at": func.now(), "result_summary": result_summary}
        )
        self.db.commit()

    def mark_failed(self, job_id: int, error_message: str) -> None:
        self.db.query(SyncJob).filter(SyncJob.id == job_id).update(
            {"status": "failed", "completed_at": func.now(), "error_message": error_message}
        )
        self.db.commit()

    def get_by_id(self, job_id: int) -> Optional[SyncJob]:
        return self.db.query(SyncJob).filter(SyncJob.id == job_id).first()

    def get_by_connection(self, connection_id: int, limit: int = 20) -> List[SyncJob]:
        return (
            self.db.query(SyncJob)
            .filter(SyncJob.connection_id == connection_id)
            .order_by(SyncJob.created_at.desc())
            .limit(limit)
            .all()
        )
