"""
Logging configuration for Torah Search application
"""
import logging
import sys
import os
import structlog
from flask import has_request_context, request
import time
from logging.handlers import RotatingFileHandler


def add_request_context(logger, method_name, event_dict):
    """Add request context to logs."""
    if has_request_context():
        event_dict['request_id'] = request.headers.get('X-Request-ID', '')
        event_dict['remote_addr'] = request.remote_addr
        event_dict['method'] = request.method
        event_dict['path'] = request.path
    return event_dict


def setup_logging(app):
    """Configure structured logging for the application."""
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            add_request_context,
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Set up Flask logging
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
    
    # Create logs directory if it doesn't exist
    logs_dir = '/app/logs'
    os.makedirs(logs_dir, exist_ok=True)
    
    # Ensure the logs directory has the correct permissions
    try:
        os.chmod(logs_dir, 0o777)  # Full permissions for all users
    except Exception as e:
        print(f"Warning: Could not set permissions on logs directory: {e}")
    
    # Configure file handler
    log_file_path = os.path.join(logs_dir, 'torah-search.log')
    
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
    file_handler.setFormatter(logging.Formatter('%(message)s'))
    file_handler.setLevel(log_level)
    
    # Configure root logger with both stdout and file handlers
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers and add our handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add stdout handler
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(logging.Formatter('%(message)s'))
    stdout_handler.setLevel(log_level)
    root_logger.addHandler(stdout_handler)
    
    # Add file handler
    root_logger.addHandler(file_handler)
    
    # Disable some noisy loggers
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    # Create app logger
    app.logger.setLevel(log_level)
    for handler in app.logger.handlers[:]:
        app.logger.removeHandler(handler)
    app.logger.addHandler(file_handler)
    app.logger.addHandler(stdout_handler)
    
    # Log startup
    logger = structlog.get_logger()
    logger.info(
        "Torah Search logging initialized",
        log_level=logging.getLevelName(log_level),
        environment=app.config.get('FLASK_ENV', 'default')
    )
    
    return logger


def get_logger():
    """Get the configured structlog logger."""
    return structlog.get_logger()


class RequestLogger:
    """Middleware for request/response logging."""
    
    def __init__(self, app):
        self.app = app
        self.logger = structlog.get_logger()
    
    def __call__(self, environ, start_response):
        start_time = time.time()
        
        def custom_start_response(status, headers):
            duration = time.time() - start_time
            self.logger.info(
                "request_completed",
                method=environ.get('REQUEST_METHOD'),
                path=environ.get('PATH_INFO'),
                status=status.split()[0],
                duration_ms=round(duration * 1000, 2),
                remote_addr=environ.get('REMOTE_ADDR'),
                user_agent=environ.get('HTTP_USER_AGENT', '')
            )
            return start_response(status, headers)
        
        return self.app(environ, custom_start_response)
