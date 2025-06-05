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
    """Perform search with selectable mechanism."""
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
        
        # Get search type (default to indexed)
        search_type = data.get('search_type', 'indexed')
        
        # Log search request
        logger.info("search_request", phrase=phrase, type=search_type, ip=get_remote_address())
        
        word_count = len(phrase.split())
        
        # Check if we should use background search for very complex queries
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
            perform_background_search.delay(job_id, phrase, search_type)
            
            return jsonify({
                'job_id': job_id,
                'status': 'pending',
                'message': 'Complex search queued for processing',
                'success': True
            }), 202
        
        # Choose search service based on type
        if search_type == 'memory':
            # Use in-memory search
            with SearchService() as search_service:
                result = search_service.search(phrase)
        else:
            # Use indexed search (default)
            from app.services.indexed_search_service import IndexedSearchService
            search_service = IndexedSearchService()
            result = search_service.search(phrase)
        
        # Record statistics
        try:
            stats = SearchStatistics(
                search_phrase=phrase,
                word_count=word_count,
                search_time=result.get('search_time', 0),
                results_count=result.get('total_variants', 0),
                cache_hit='cached' in result.get('search_method', ''),
                client_ip=get_remote_address(),
                user_agent=request.headers.get('User-Agent', '')
            )
            db.session.add(stats)
            db.session.commit()
        except Exception as e:
            logger.error("stats_recording_error", error=str(e))
        
        return jsonify(result)
        
    except Exception as e:
        logger.error("indexed_search_error", error=str(e), exc_info=True)
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
        
        # Include partial results if available
        from app.models.database import SearchResult
        
        # If completed, include full results
        if job.status == 'completed' and job.result_id:
            result = SearchResult.query.get(job.result_id)
            if result:
                import json
                response['results'] = json.loads(result.results_json)
        # If still running, include any partial results
        elif job.status == 'running':
            # Get partial results from Redis if available
            try:
                from app.shared.redis_client import get_redis_client
                redis = get_redis_client()
                partial_key = f"partial_results:{job_id}"
                partial_results = redis.get(partial_key)
                
                if partial_results:
                    import json
                    response['partial_results'] = json.loads(partial_results)
            except Exception as e:
                logger.error("partial_results_error", error=str(e))
        
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


@bp.route('/admin/clear-cache', methods=['POST'])
def clear_cache():
    """Clear all cached searches from Redis and database."""
    try:
        # Clear Redis cache
        from app.shared.redis_client import get_redis_client
        redis = get_redis_client()
        if redis:
            # Clear search cache keys
            search_keys = redis.keys('*search*')
            if search_keys:
                redis.delete(*search_keys)
            
            # Clear partial results
            partial_keys = redis.keys('partial_results:*')
            if partial_keys:
                redis.delete(*partial_keys)
            
            # Clear Flask-Caching keys
            cache_keys = redis.keys('flask_cache*')
            if cache_keys:
                redis.delete(*cache_keys)
        
        # Clear database cache
        from app.models.database import db, SearchResult
        SearchResult.query.delete()
        db.session.commit()
        
        logger.info("cache_cleared", source="admin_request")
        
        return jsonify({
            'success': True,
            'message': 'All search caches cleared successfully'
        })
        
    except Exception as e:
        logger.error("cache_clear_error", error=str(e))
        return jsonify({
            'success': False,
            'error': f'Failed to clear cache: {str(e)}'
        }), 500


@bp.route('/performance', methods=['GET'])
@cache.cached(timeout=30)
def performance_stats():
    """Get performance statistics for debugging."""
    try:
        from app.services.torah_service import TorahService
        from app.models.database import TorahWord
        
        torah_service = TorahService()
        word_index_count = TorahWord.query.count()
        
        stats = {
            'torah_lines_loaded': len(torah_service.get_torah_lines()),
            'torah_text_size_mb': round(len(torah_service.get_torah_text()) / 1024 / 1024, 2),
            'memory_cache_size': len(getattr(torah_service, '_search_cache', {})),
            'word_index_count': word_index_count,
            'index_ready': word_index_count > 0,
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


@bp.route('/admin/build-index', methods=['POST'])
def build_search_index():
    """Build the word-level search index for ultra-fast searches."""
    try:
        from app.services.indexed_search_service import build_word_index
        from app.models.database import TorahVerse, TorahWord
        
        # Check if verses exist
        verse_count = TorahVerse.query.count()
        if verse_count == 0:
            return jsonify({
                'success': False,
                'error': 'No Torah verses found. Please index Torah text first.'
            }), 400
        
        # Check current index
        current_word_count = TorahWord.query.count()
        
        logger.info("building_search_index", verse_count=verse_count, current_words=current_word_count)
        
        # Build the index
        start_time = time.time()
        words_indexed = build_word_index()
        build_time = time.time() - start_time
        
        return jsonify({
            'success': True,
            'message': 'Search index built successfully',
            'statistics': {
                'verses_processed': verse_count,
                'words_indexed': words_indexed,
                'build_time_seconds': round(build_time, 2),
                'words_per_second': round(words_indexed / build_time, 0) if build_time > 0 else 0
            }
        })
        
    except Exception as e:
        logger.error("build_index_error", error=str(e), exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to build search index'
        }), 500
