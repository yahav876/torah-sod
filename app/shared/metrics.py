"""
Prometheus metrics for Torah Search application
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from flask import Response
import time
import functools


# Define metrics
search_requests_total = Counter(
    'torah_search_requests_total',
    'Total number of search requests',
    ['method', 'endpoint', 'status']
)

search_duration_seconds = Histogram(
    'torah_search_duration_seconds',
    'Search request duration in seconds',
    ['search_type']
)

active_searches = Gauge(
    'torah_active_searches',
    'Number of currently active searches'
)

cache_hits_total = Counter(
    'torah_cache_hits_total',
    'Total number of cache hits',
    ['cache_type']
)

torah_verses_indexed = Gauge(
    'torah_verses_indexed',
    'Number of Torah verses indexed in database'
)

search_phrase_length = Histogram(
    'torah_search_phrase_length',
    'Length of search phrases',
    buckets=[1, 5, 10, 20, 50, 100]
)

results_found = Histogram(
    'torah_search_results_found',
    'Number of results found per search',
    buckets=[0, 1, 10, 50, 100, 500, 1000, 5000]
)


def setup_metrics(app):
    """Setup Prometheus metrics endpoint."""
    
    @app.route('/metrics')
    def metrics():
        return Response(generate_latest(), mimetype='text/plain')
    
    # Middleware to track requests
    @app.before_request
    def before_request():
        from flask import request, g
        g.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        from flask import request, g
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            search_requests_total.labels(
                method=request.method,
                endpoint=request.endpoint or 'unknown',
                status=response.status_code
            ).inc()
        return response
    
    app.logger.info("Prometheus metrics initialized at /metrics")


def track_search_metrics(search_type='web'):
    """Decorator to track search metrics."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            active_searches.inc()
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                
                # Track duration
                duration = time.time() - start_time
                search_duration_seconds.labels(search_type=search_type).observe(duration)
                
                # Track results count if available
                if isinstance(result, dict) and 'total_variants' in result:
                    results_found.observe(result['total_variants'])
                
                return result
            finally:
                active_searches.dec()
        
        return wrapper
    return decorator


def track_cache_hit(cache_type='redis'):
    """Track cache hits."""
    cache_hits_total.labels(cache_type=cache_type).inc()


def get_metrics():
    """Get all defined metrics."""
    return {
        'search_requests_total': search_requests_total,
        'search_duration_seconds': search_duration_seconds,
        'active_searches': active_searches,
        'cache_hits_total': cache_hits_total,
        'torah_verses_indexed': torah_verses_indexed,
        'search_phrase_length': search_phrase_length,
        'results_found': results_found
    }
