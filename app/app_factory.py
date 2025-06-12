"""
Application factory for Torah Search
"""
import os
import logging
from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache

from app.config.settings import get_config
from app.models.database import db, init_db
from app.shared.logging import setup_logging
from app.shared.metrics import setup_metrics

# Initialize extensions
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per hour", "20 per minute"]
)
cache = Cache()


def create_app(config_name=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    config_class = get_config(config_name)
    app.config.from_object(config_class)
    
    # Set a secret key for sessions
    app.secret_key = app.config.get('SECRET_KEY', os.urandom(24))
    
    # Setup logging
    setup_logging(app)
    app.logger.info(f"Creating Torah Search app with config: {config_name or 'default'}")
    
    # Initialize extensions
    CORS(app)
    limiter.init_app(app)
    cache.init_app(app)
    
    # Initialize database
    init_db(app)
    
    # Setup metrics if enabled
    if app.config.get('PROMETHEUS_METRICS'):
        setup_metrics(app)
    
    # Register blueprints
    from app.routes import api, web
    app.register_blueprint(api.bp, url_prefix='/api')
    app.register_blueprint(web.bp)
    
    # Register error handlers
    from app.shared.error_handlers import register_error_handlers
    register_error_handlers(app)
    
    # Load Torah text into memory on startup
    with app.app_context():
        from app.services.torah_service import TorahService
        TorahService.initialize()
    
    return app
