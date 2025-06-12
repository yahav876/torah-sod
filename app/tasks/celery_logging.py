"""
Celery logging configuration
"""
import os
import logging
from logging.handlers import RotatingFileHandler


def setup_celery_logging():
    """Configure logging for Celery workers."""
    # Create logs directory if it doesn't exist
    logs_dir = '/app/logs'
    os.makedirs(logs_dir, exist_ok=True)
    
    # Configure file handler for Celery logs
    log_file_path = os.path.join(logs_dir, 'celery-worker.log')
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=10
    )
    
    # Set formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Get Celery logger
    celery_logger = logging.getLogger('celery')
    celery_logger.setLevel(logging.INFO)
    
    # Add handler to logger
    celery_logger.addHandler(file_handler)
    
    # Get Celery task logger
    task_logger = logging.getLogger('celery.task')
    task_logger.setLevel(logging.INFO)
    task_logger.addHandler(file_handler)
    
    # Get Celery worker logger
    worker_logger = logging.getLogger('celery.worker')
    worker_logger.setLevel(logging.INFO)
    worker_logger.addHandler(file_handler)
    
    return celery_logger
