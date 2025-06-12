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
    
    # Ensure the logs directory has the correct permissions
    try:
        os.chmod(logs_dir, 0o777)  # Full permissions for all users
    except Exception as e:
        print(f"Warning: Could not set permissions on logs directory: {e}")
    
    # Configure file handler for Celery logs
    log_file_path = os.path.join(logs_dir, 'celery-worker.log')
    
    # Create the log file if it doesn't exist and set permissions
    if not os.path.exists(log_file_path):
        try:
            with open(log_file_path, 'a'):
                pass
            os.chmod(log_file_path, 0o666)  # Read/write for all users
        except Exception as e:
            print(f"Warning: Could not create or set permissions on log file: {e}")
    
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
