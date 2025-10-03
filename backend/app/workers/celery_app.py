"""
Celery application configuration for background task processing
"""

from celery import Celery
from app.core.config import settings

# Create Celery instance
celery_app = Celery(
    "bibbi_worker",
    broker=settings.redis_url,
    backend=settings.redis_url
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max per task
    task_soft_time_limit=25 * 60,  # Soft limit at 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    result_expires=3600,  # Results expire after 1 hour
)

# Task routes
celery_app.conf.task_routes = {
    "app.workers.tasks.process_upload": {"queue": "file_processing"},
    "app.workers.tasks.send_email": {"queue": "notifications"},
}

# Import tasks (this registers them with Celery)
from app.workers import tasks  # noqa
