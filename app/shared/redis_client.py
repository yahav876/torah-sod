"""
Redis client helper
"""
import redis
from flask import current_app
import structlog

logger = structlog.get_logger()

_redis_client = None


def get_redis_client():
    """Get Redis client instance."""
    global _redis_client
    
    if _redis_client is None:
        try:
            redis_url = current_app.config.get('REDIS_URL')
            if redis_url:
                _redis_client = redis.from_url(redis_url, decode_responses=True)
                _redis_client.ping()
                logger.info("redis_connected", url=redis_url)
            else:
                logger.warning("redis_url_not_configured")
        except Exception as e:
            logger.error("redis_connection_error", error=str(e))
            raise
    
    return _redis_client
