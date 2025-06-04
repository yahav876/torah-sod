"""
Shared Configuration for Torah Search Microservices
"""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class DatabaseConfig:
    """Database configuration"""
    postgres_url: str = os.getenv('POSTGRES_URL', 'postgresql://torah:torah@localhost/torah_search')
    pool_size: int = int(os.getenv('DB_POOL_SIZE', '20'))
    max_overflow: int = int(os.getenv('DB_MAX_OVERFLOW', '10'))


@dataclass
class RedisConfig:
    """Redis configuration"""
    url: str = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    max_connections: int = int(os.getenv('REDIS_MAX_CONNECTIONS', '50'))
    socket_timeout: int = int(os.getenv('REDIS_SOCKET_TIMEOUT', '30'))


@dataclass
class ElasticsearchConfig:
    """Elasticsearch configuration"""
    hosts: list = None
    index_name: str = os.getenv('ES_INDEX_NAME', 'torah_search')
    timeout: int = int(os.getenv('ES_TIMEOUT', '30'))
    max_retries: int = int(os.getenv('ES_MAX_RETRIES', '3'))
    
    def __post_init__(self):
        if self.hosts is None:
            self.hosts = [os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200')]


@dataclass
class CeleryConfig:
    """Celery configuration"""
    broker_url: str = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/1')
    result_backend: str = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2')
    task_serializer: str = 'json'
    result_serializer: str = 'json'
    accept_content: list = None
    timezone: str = 'UTC'
    enable_utc: bool = True
    
    # Task routing
    task_routes: dict = None
    
    # Performance settings
    worker_prefetch_multiplier: int = int(os.getenv('CELERY_PREFETCH_MULTIPLIER', '4'))
    task_compression: str = 'gzip'
    result_compression: str = 'gzip'
    
    def __post_init__(self):
        if self.accept_content is None:
            self.accept_content = ['json']
        
        if self.task_routes is None:
            self.task_routes = {
                'app.workers.search_tasks.*': {'queue': 'search'},
                'app.workers.index_tasks.*': {'queue': 'indexing'},
                'app.workers.maintenance_tasks.*': {'queue': 'maintenance'},
            }


@dataclass
class SearchConfig:
    """Search engine configuration"""
    max_phrase_length: int = int(os.getenv('MAX_PHRASE_LENGTH', '100'))
    max_words: int = int(os.getenv('MAX_WORDS', '10'))
    max_results: int = int(os.getenv('MAX_RESULTS', '1000'))
    max_variants: int = int(os.getenv('MAX_VARIANTS', '5000'))
    timeout_seconds: int = int(os.getenv('SEARCH_TIMEOUT', '30'))
    cache_ttl: int = int(os.getenv('SEARCH_CACHE_TTL', '3600'))
    
    # Performance limits
    background_threshold_words: int = int(os.getenv('BACKGROUND_THRESHOLD_WORDS', '3'))
    quick_search_limit: int = int(os.getenv('QUICK_SEARCH_LIMIT', '100'))


@dataclass
class APIConfig:
    """API configuration"""
    host: str = os.getenv('API_HOST', '0.0.0.0')
    port: int = int(os.getenv('API_PORT', '8000'))
    debug: bool = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Rate limiting
    rate_limit_per_minute: int = int(os.getenv('RATE_LIMIT_PER_MINUTE', '60'))
    rate_limit_per_hour: int = int(os.getenv('RATE_LIMIT_PER_HOUR', '1000'))
    
    # Security
    secret_key: str = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    cors_origins: list = None
    
    def __post_init__(self):
        if self.cors_origins is None:
            origins = os.getenv('CORS_ORIGINS', '*')
            self.cors_origins = [o.strip() for o in origins.split(',')]


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = os.getenv('LOG_LEVEL', 'INFO')
    format: str = os.getenv('LOG_FORMAT', 'json')
    file_path: Optional[str] = os.getenv('LOG_FILE_PATH')


@dataclass
class MonitoringConfig:
    """Monitoring configuration"""
    metrics_enabled: bool = os.getenv('METRICS_ENABLED', 'True').lower() == 'true'
    metrics_port: int = int(os.getenv('METRICS_PORT', '8001'))
    health_check_enabled: bool = os.getenv('HEALTH_CHECK_ENABLED', 'True').lower() == 'true'


class Config:
    """Main configuration class"""
    
    def __init__(self):
        self.database = DatabaseConfig()
        self.redis = RedisConfig()
        self.elasticsearch = ElasticsearchConfig()
        self.celery = CeleryConfig()
        self.search = SearchConfig()
        self.api = APIConfig()
        self.logging = LoggingConfig()
        self.monitoring = MonitoringConfig()
        
        # Environment
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.is_production = self.environment == 'production'
        self.is_development = self.environment == 'development'


# Global config instance
config = Config()
