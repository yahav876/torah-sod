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
def perform_background_search(self, job_id, phrase):
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
        
        # Perform search
        with SearchService() as service:
            # Disable cache for background searches
            result = service.search(phrase, use_cache=False)
        
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
