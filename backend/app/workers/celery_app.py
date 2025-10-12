"""
Celery application configuration for background task processing
"""

from celery import Celery
from app.core.config import settings

# Create Celery instance with broker-only mode
# No result backend needed for fire-and-forget upload tasks
# This avoids pub/sub operations that Upstash free tier doesn't fully support
celery_app = Celery(
    "taskifai_worker",
    broker=settings.redis_url
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max per task
    task_soft_time_limit=25 * 60,  # Soft limit at 25 minutes
    worker_prefetch_multiplier=4,  # Enables concurrent multi-file uploads (6 workers × 4 = 24 simultaneous tasks)
    worker_max_tasks_per_child=1000,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # result_expires removed - not needed in broker-only mode
)

# Task routes
celery_app.conf.task_routes = {
    "app.workers.tasks.process_upload": {"queue": "file_processing"},
    "app.workers.tasks.send_email": {"queue": "notifications"},
}

# Import tasks (this registers them with Celery)
from app.workers import tasks  # noqa
