from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "ai_data_copilot",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.metadata_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Redis result backend is TTL-based, not a durable audit log — the
    # SyncJob row in Postgres is the source of truth for job history.
    # This just bounds how long Celery itself keeps the raw result around.
    result_expires=3600,
)
