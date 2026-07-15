from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.repositories.sync_job_repository import SyncJobRepository
from app.services.metadata_refresh_service import MetadataRefreshService

logger = get_logger("app.tasks.metadata")


@celery_app.task(name="metadata.refresh", bind=True)
def refresh_metadata_task(
    self, job_id: int, connection_id: int, schema_name: str, include_relationships: bool = True
) -> None:
    """
    Runs MetadataRefreshService in a Celery worker process. Opens its own
    DB session — a task cannot reuse the FastAPI request's session, since
    it runs in a different process entirely, asynchronously, after the
    triggering request has already returned.

    This is now the only metadata-update task (Phase 1, Step 14) — there's
    no separate sync_metadata_task anymore, since refresh is a strict
    superset of what a schema-only sync did.
    """
    db = SessionLocal()
    job_repo = SyncJobRepository(db)
    try:
        job_repo.set_celery_task_id(job_id, self.request.id)
        job_repo.mark_running(job_id)

        result = MetadataRefreshService(db).refresh_metadata(connection_id, schema_name, include_relationships)

        job_repo.mark_completed(job_id, {
            "message": result.message,
            "changes_detected": result.changes_detected,
        })
    except Exception as e:
        # Note: MetadataRefreshService already records failure metrics
        # internally before re-raising — not duplicated here.
        logger.error("refresh_task_failed", extra={"job_id": job_id, "connection_id": connection_id, "error": str(e)})
        job_repo.mark_failed(job_id, str(e))
    finally:
        db.close()
