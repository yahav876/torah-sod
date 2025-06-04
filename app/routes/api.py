"""
API routes for Torah Search
"""
from flask import Blueprint, request, jsonify, current_app
from flask_limiter.util import get_remote_address
from app.services.search_service import SearchService
from app.tasks.search_tasks import perform_background_search
from app.models.database import db, SearchJob, SearchStatistics
from app.shared.metrics import search_requests_total
from app.app_factory import limiter, cache
import uuid
import structlog
from datetime import datetime

logger = structlog.get_logger()

bp = Blueprint('api', __name__)


@bp.route('/search', methods=['POST'])
@limiter.limit("20 per minute")
@limiter.limit("100 per hour")
def search():
    """Perform synchronous search."""
    try:
        data = request.get_json()
        if not data or 'phrase' not in data:
            return jsonify({'error': 'Missing phrase parameter', 'success': False}), 400
        
        phrase = data['phrase'].strip()
        if not phrase:
            return jsonify({'error': 'Empty phrase provided', 'success': False}), 400
        
        if len(phrase) > current_app.config['MAX_PHRASE_LENGTH']:
            return jsonify({
                'error': f'Phrase too long (max {current_app.config["MAX_PHRASE_LENGTH"]} characters)',
                'success': False
            }), 400
        
        # Log search request
        logger.info("search_request", phrase=phrase, ip=get_remote_address())
        
        # Check if we should do background search
        word_count = len(phrase.split())
        if word_count > current_app.config.get('MAX_WORDS', 10):
            # Create background job
            job_id = str(uuid.uuid4())
            job = SearchJob(
                job_id=job_id,
                search_phrase=phrase,
                status='pending',
                client_ip=get_remote_address()
            )
            db.session.add(job)
            db.session.commit()
            
            # Queue background task
            perform_background_search.delay(job_id, phrase)
            
            return jsonify({
                'job_id': job_id,
                'status': 'pending',
                'message': 'Search queued for processing',
                'success': True
            }), 202
        
        # Perform synchronous search
        with SearchService() as service:
            result = service.search(phrase)
        
        # Record statistics
        try:
            stats = SearchStatistics(
                search_phrase=phrase,
                word_count=word_count,
                search_time=result.get('search_time', 0),
                results_count=result.get('total_variants', 0),
                cache_hit=False,
                client_ip=get_remote_address(),
                user_agent=request.headers.get('User-Agent', '')
            )
            db.session.add(stats)
            db.session.commit()
        except Exception as e:
            logger.error("stats_recording_error", error=str(e))
        
        return jsonify(result)
        
    except Exception as e:
        logger.error("api_search_error", error=str(e), exc_info=True)
        return jsonify({'error': 'Internal server error', 'success': False}), 500


@bp.route('/search/status/<job_id>', methods=['GET'])
@cache.cached(timeout=5)
def search_status(job_id):
    """Check status of background search job."""
    try:
        job = SearchJob.query.filter_by(job_id=job_id).first()
        if not job:
            return jsonify({'error': 'Job not found', 'success': False}), 404
        
        response = job.to_dict()
        
        # If completed, include results
        if job.status == 'completed' and job.result_id:
            from app.models.database import SearchResult
            result = SearchResult.query.get(job.result_id)
            if result:
                import json
                response['results'] = json.loads(result.results_json)
        
        return jsonify(response)
        
    except Exception as e:
        logger.error("status_check_error", job_id=job_id, error=str(e))
        return jsonify({'error': 'Internal server error', 'success': False}), 500


@bp.route('/stats', methods=['GET'])
@cache.cached(timeout=60)
def stats():
    """Get application statistics."""
    try:
        from app.services.torah_service import TorahService
        from app.models.database import TorahVerse, SearchResult
        
        torah_service = TorahService()
        
        stats = {
            'torah_verses': TorahVerse.query.count(),
            'cached_searches': SearchResult.query.count(),
            'total_searches': SearchStatistics.query.count(),
            'recent_searches': SearchStatistics.query.order_by(
                SearchStatistics.created_at.desc()
            ).limit(10).all()
        }
        
        # Format recent searches
        stats['recent_searches'] = [
            {
                'phrase': s.search_phrase,
                'results': s.results_count,
                'time': s.search_time,
                'timestamp': s.created_at.isoformat()
            }
            for s in stats['recent_searches']
        ]
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error("stats_error", error=str(e))
        return jsonify({'error': 'Internal server error', 'success': False}), 500


@bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        # Check database
        from app.models.database import db
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        
        # Check Redis if configured
        redis_healthy = True
        if current_app.config.get('REDIS_URL'):
            try:
                from app.shared.redis_client import get_redis_client
                redis = get_redis_client()
                redis.ping()
            except:
                redis_healthy = False
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'redis': 'connected' if redis_healthy else 'disconnected',
            'version': '2.0.0'
        })
        
    except Exception as e:
        logger.error("health_check_error", error=str(e))
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503


@bp.route('/health/alb', methods=['GET'])
def alb_health_check():
    """Lightweight health check for ALB - no database check."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })


@bp.route('/performance', methods=['GET'])
@cache.cached(timeout=30)
def performance_stats():
    """Get performance statistics for debugging."""
    try:
        from app.services.torah_service import TorahService
        
        torah_service = TorahService()
        
        stats = {
            'torah_lines_loaded': len(torah_service.get_torah_lines()),
            'torah_text_size_mb': round(len(torah_service.get_torah_text()) / 1024 / 1024, 2),
            'memory_cache_size': len(getattr(torah_service, '_search_cache', {})),
            'max_workers': current_app.config.get('MAX_WORKERS', 4),
            'batch_size_multiplier': current_app.config.get('BATCH_SIZE_MULTIPLIER', 100),
            'database_pool_size': current_app.config['SQLALCHEMY_ENGINE_OPTIONS']['pool_size'],
            'redis_pool_size': current_app.config.get('REDIS_CONNECTION_POOL_SIZE', 20),
            'environment': current_app.config.get('FLASK_ENV', 'unknown'),
            'search_timeout': current_app.config.get('SEARCH_TIMEOUT', 300)
        }
        
        return jsonify({
            'success': True,
            'performance_config': stats
        })
        
    except Exception as e:
        logger.error("performance_stats_error", error=str(e))
        return jsonify({
            'success': False,
            'error': 'Failed to get performance stats'
        }), 500
