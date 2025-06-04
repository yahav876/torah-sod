"""
Logging configuration for Torah Search application
"""
import logging
import sys
import structlog
from flask import has_request_context, request
import time


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
    
    # Configure root logger
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )
    
    # Disable some noisy loggers
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    # Create app logger
    app.logger.setLevel(log_level)
    
    # Log startup
    logger = structlog.get_logger()
    logger.info(
        "Torah Search logging initialized",
        log_level=logging.getLevelName(log_level),
        environment=app.config.get('FLASK_ENV', 'default')
    )
    
    return logger


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
