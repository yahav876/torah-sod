"""
Background search tasks using Celery
"""
from celery import current_task
from app.tasks.celery_app import celery
from app.services.search_service import SearchService
from app.models.database import db, SearchJob, SearchResult
from datetime import datetime
import json
import structlog

logger = structlog.get_logger()


@celery.task(bind=True, name='app.tasks.search_tasks.perform_background_search')
def perform_background_search(self, job_id, phrase, search_type='indexed'):
    """Perform search as a background task."""
    try:
        # Update job status
        job = SearchJob.query.filter_by(job_id=job_id).first()
        if not job:
            logger.error("job_not_found", job_id=job_id)
            return
        
        job.status = 'running'
        job.started_at = datetime.utcnow()
        db.session.commit()
        
        # Update progress
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 10, 'total': 100, 'status': 'Initializing search...'}
        )
        
        # Set up partial results tracking
        partial_results = []
        
        # Create a callback function to collect partial results
        def collect_partial_results(result_batch):
            nonlocal partial_results
            if result_batch and len(result_batch) > 0:
                partial_results.extend(result_batch)
                # Store partial results in Redis
                try:
                    from app.shared.redis_client import get_redis_client
                    redis = get_redis_client()
                    if redis:
                        import json
                        partial_key = f"partial_results:{job_id}"
                        redis.setex(
                            partial_key,
                            3600,  # 1 hour expiration
                            json.dumps(partial_results)
                        )
                except Exception as e:
                    logger.error("redis_partial_results_error", error=str(e))
        
        # Perform search based on type with partial results callback
        if search_type == 'memory':
            # Use in-memory search
            with SearchService() as service:
                # Disable cache for background searches and explicitly set is_memory_search=True
                result = service.search(phrase, use_cache=False, partial_results_callback=collect_partial_results, is_memory_search=True)
        else:
            # Use indexed search
            from app.services.indexed_search_service import IndexedSearchService
            search_service = IndexedSearchService()
            result = search_service.search(phrase, use_cache=False, partial_results_callback=collect_partial_results)
        
        # Update progress
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 90, 'total': 100, 'status': 'Saving results...'}
        )
        
        # Save results
        search_result = SearchResult(
            search_phrase=phrase,
            search_hash='',  # Will be set by the service
            results_json=json.dumps(result),
            total_variants=result.get('total_variants', 0),
            search_time=result.get('search_time', 0)
        )
        db.session.add(search_result)
        db.session.flush()
        
        # Update job
        job.status = 'completed'
        job.completed_at = datetime.utcnow()
        job.result_id = search_result.id
        job.progress = 100
        db.session.commit()
        
        logger.info("background_search_completed", job_id=job_id, phrase=phrase)
        
        return {
            'job_id': job_id,
            'status': 'completed',
            'result_id': search_result.id
        }
        
    except Exception as e:
        logger.error("background_search_error", job_id=job_id, error=str(e), exc_info=True)
        
        # Update job with error
        try:
            job = SearchJob.query.filter_by(job_id=job_id).first()
            if job:
                job.status = 'failed'
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
                db.session.commit()
        except:
            pass
        
        raise
