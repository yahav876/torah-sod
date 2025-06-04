"""
Error handlers for Torah Search application
"""
from flask import jsonify
import structlog

logger = structlog.get_logger()


def register_error_handlers(app):
    """Register error handlers for the application."""
    
    @app.errorhandler(400)
    def bad_request(error):
        logger.warning("bad_request", error=str(error))
        return jsonify({
            'error': 'Bad Request',
            'message': str(error),
            'success': False
        }), 400
    
    @app.errorhandler(404)
    def not_found(error):
        logger.warning("not_found", path=error.description)
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found',
            'success': False
        }), 404
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        logger.warning("rate_limit_exceeded", error=str(error))
        return jsonify({
            'error': 'Rate Limit Exceeded',
            'message': 'Too many requests. Please try again later.',
            'success': False
        }), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error("internal_server_error", error=str(error), exc_info=True)
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'success': False
        }), 500
    
    @app.errorhandler(Exception)
    def unhandled_exception(error):
        logger.error("unhandled_exception", error=str(error), exc_info=True)
        
        # In production, don't expose internal errors
        if app.config.get('DEBUG'):
            message = str(error)
        else:
            message = 'An unexpected error occurred'
        
        return jsonify({
            'error': 'Server Error',
            'message': message,
            'success': False
        }), 500
