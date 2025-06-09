"""
Configuration settings for different environments
"""
import os
from datetime import timedelta


class BaseConfig:
    """Base configuration with common settings."""
    
    # Core Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Torah file location
    TORAH_FILE = os.path.join(os.path.dirname(__file__), '../../torah.txt')
    
    # Search settings
    MAX_RESULTS = int(os.environ.get('MAX_RESULTS', '1000'))
    MAX_PHRASE_LENGTH = int(os.environ.get('MAX_PHRASE_LENGTH', '100'))
    MAX_WORDS = int(os.environ.get('MAX_WORDS', '10'))
    SEARCH_TIMEOUT = int(os.environ.get('SEARCH_TIMEOUT', '300'))  # 5 minutes
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 15,
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'pool_timeout': 20,
        'max_overflow': 25,
        'echo': False,
        'connect_args': {}
    }
    
    # Redis settings with connection pooling
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    REDIS_CONNECTION_POOL_SIZE = int(os.environ.get('REDIS_POOL_SIZE', '20'))
    REDIS_CONNECTION_POOL_MAX_CONNECTIONS = int(os.environ.get('REDIS_MAX_CONNECTIONS', '50'))
    
    # Celery settings
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/0'
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TIMEZONE = 'UTC'
    CELERY_ENABLE_UTC = True
    CELERY_TASK_ROUTES = {
        'app.tasks.search_tasks.perform_background_search': {'queue': 'search'},
        'app.tasks.index_tasks.index_torah_text': {'queue': 'indexing'},
    }
    
    # Cache settings
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/1'
    CACHE_DEFAULT_TIMEOUT = 3600  # 1 hour
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/2'
    
    # Elasticsearch settings
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL') or 'http://localhost:9200'
    ELASTICSEARCH_INDEX = 'torah_search'
    
    # Monitoring
    PROMETHEUS_METRICS = os.environ.get('PROMETHEUS_METRICS', 'false').lower() == 'true'
    SENTRY_DSN = os.environ.get('SENTRY_DSN')
    
    # Worker settings (optimized for t3.2xlarge: 8 vCPU, 32GB RAM)
    MAX_WORKERS = int(os.environ.get('MAX_WORKERS', '12'))  # 1.5x vCPUs for I/O bound tasks
    WORKER_MEMORY_LIMIT = int(os.environ.get('WORKER_MEMORY_LIMIT', '2048'))  # MB - more memory per worker
    BATCH_SIZE_MULTIPLIER = int(os.environ.get('BATCH_SIZE_MULTIPLIER', '150'))  # Optimized batch size
    
    # Parallel search settings
    USE_BOOK_PARALLEL_SEARCH = os.environ.get('USE_BOOK_PARALLEL_SEARCH', 'false').lower() == 'true'


class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    DEBUG = True
    TESTING = False
    
    # More verbose logging in development
    LOG_LEVEL = 'DEBUG'
    
    # Shorter timeouts for faster development
    SEARCH_TIMEOUT = 60
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes


class ProductionConfig(BaseConfig):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    
    # Security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Performance settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'max_overflow': 30
    }
    
    # Longer cache in production
    CACHE_DEFAULT_TIMEOUT = 7200  # 2 hours
    
    # More workers in production
    MAX_WORKERS = int(os.environ.get('MAX_WORKERS', '8'))
    
    LOG_LEVEL = 'INFO'


class TestingConfig(BaseConfig):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    
    # Use in-memory database for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable caching in tests
    CACHE_TYPE = 'null'
    
    # Fast timeouts for tests
    SEARCH_TIMEOUT = 10
    CACHE_DEFAULT_TIMEOUT = 1


class AWSConfig(ProductionConfig):
    """AWS-specific production configuration."""
    
    # Use AWS services
    REDIS_URL = os.environ.get('AWS_ELASTICACHE_URL')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///:memory:'
    ELASTICSEARCH_URL = os.environ.get('AWS_ELASTICSEARCH_URL')
    
    # AWS-specific settings
    AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
    AWS_S3_BUCKET = os.environ.get('AWS_S3_BUCKET')
    
    # CloudWatch logging
    CLOUDWATCH_LOG_GROUP = os.environ.get('CLOUDWATCH_LOG_GROUP', 'tzfanim-search')
    
    # Auto-scaling settings
    MIN_WORKERS = int(os.environ.get('MIN_WORKERS', '2'))
    MAX_WORKERS = int(os.environ.get('MAX_WORKERS', '20'))


config_mapping = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'aws': AWSConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """Get configuration class based on environment."""
    config_name = config_name or os.environ.get('FLASK_ENV', 'default')
    return config_mapping.get(config_name, DevelopmentConfig)
