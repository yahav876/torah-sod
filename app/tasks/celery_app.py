"""
Celery application configuration
"""
from celery import Celery
from app.config.settings import get_config
import os
from app.tasks.celery_logging import setup_celery_logging

# Get configuration
config = get_config(os.environ.get('FLASK_ENV', 'development'))

# Create Celery instance
celery = Celery('torah_search')

# Configure Celery
celery.conf.update(
    broker_url=config.CELERY_BROKER_URL,
    result_backend=config.CELERY_RESULT_BACKEND,
    task_serializer=config.CELERY_TASK_SERIALIZER,
    result_serializer=config.CELERY_RESULT_SERIALIZER,
    accept_content=config.CELERY_ACCEPT_CONTENT,
    timezone=config.CELERY_TIMEZONE,
    enable_utc=config.CELERY_ENABLE_UTC,
    task_routes=config.CELERY_TASK_ROUTES,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=270,  # 4.5 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    broker_connection_retry_on_startup=True,  # Suppress deprecation warning
)

# Auto-discover tasks
celery.autodiscover_tasks(['app.tasks'])

# Set up logging for Celery
setup_celery_logging()
