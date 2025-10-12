"""
Celery application configuration for background task processing
"""

import logging
import ssl
from celery import Celery
from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Diagnostic: Log Redis URL (sanitized to hide password)
redis_url_parts = settings.redis_url.split('@')
redis_host = redis_url_parts[-1] if '@' in settings.redis_url else settings.redis_url
logger.info(f"🔍 Celery broker connecting to Redis: ...@{redis_host}")
logger.info(f"🔍 Redis URL protocol: {settings.redis_url.split('://')[0]}://")

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

    # ============================================
    # Connection Reliability & Retry Logic
    # ============================================
    broker_connection_retry_on_startup=True,  # Retry connection on worker startup
    broker_connection_retry=True,              # Retry on connection loss
    broker_connection_max_retries=10,          # Max retry attempts

    # ============================================
    # Upstash-Compatible Transport Options
    # ============================================
    broker_transport_options={
        # NOTE: socket_keepalive options REMOVED - incompatible with Upstash
        # TCP keepalive options (TCP_KEEPIDLE, TCP_KEEPCNT, TCP_KEEPINTVL)
        # cause Error 22 (EINVAL) in sock.setsockopt() when connecting to Upstash
        # over public internet. These are Linux-specific options that Upstash rejects.

        # Connection pooling and timeouts
        'health_check_interval': 30,       # Health check every 30 seconds
        'visibility_timeout': 3600,        # Task visibility timeout (1 hour)
        'max_connections': 10,             # Conservative limit for free tier
        'socket_timeout': 30,              # Socket operation timeout
        'socket_connect_timeout': 30,      # Connection establishment timeout

        # ============================================
        # SSL/TLS Configuration for rediss:// protocol
        # ============================================
        # SSL options must be nested under 'ssl' key for Kombu's Redis transport
        # Parameter is 'cert_reqs' (not 'ssl_cert_reqs') when nested
        'ssl': {
            'cert_reqs': ssl.CERT_NONE,    # Disable SSL certificate verification
        },
    },
)

logger.info("✅ Celery broker configuration applied with SSL and retry logic")

# Task routes
celery_app.conf.task_routes = {
    "app.workers.tasks.process_upload": {"queue": "file_processing"},
    "app.workers.tasks.send_email": {"queue": "notifications"},
}

# Import tasks (this registers them with Celery)
from app.workers import tasks  # noqa
