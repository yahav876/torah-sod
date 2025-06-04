#!/usr/bin/env python3
"""
Optimized Torah Search Web Application
Main entry point for the production-ready Flask application.
"""

import os
import sys
from app.app_factory import create_app
from app.shared.logging import RequestLogger
import structlog

# Set up structured logging
logger = structlog.get_logger()


def main():
    """Main application entry point."""
    # Get environment
    env = os.environ.get('FLASK_ENV', 'development')
    port = int(os.environ.get('PORT', 5001))
    host = os.environ.get('HOST', '0.0.0.0')
    
    # Create application
    app = create_app(env)
    
    # Add request logging middleware in development
    if env == 'development':
        app.wsgi_app = RequestLogger(app.wsgi_app)
    
    # Log startup information
    logger.info(
        "starting_torah_search_app",
        environment=env,
        host=host,
        port=port,
        debug=app.debug,
        workers=app.config.get('MAX_WORKERS'),
        database=app.config.get('SQLALCHEMY_DATABASE_URI', 'sqlite').split('://')[0]
    )
    
    # Run application
    if env == 'development':
        # Development server with auto-reload
        app.run(host=host, port=port, debug=True, use_reloader=True)
    else:
        # Production should use gunicorn or similar WSGI server
        logger.warning(
            "running_development_server_in_production",
            message="Use a production WSGI server like gunicorn instead"
        )
        app.run(host=host, port=port, debug=False)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("application_shutdown_requested")
        sys.exit(0)
    except Exception as e:
        logger.error("application_startup_failed", error=str(e), exc_info=True)
        sys.exit(1)
