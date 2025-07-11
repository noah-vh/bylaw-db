"""
Scraping job manager with Celery task definitions and comprehensive error handling.
Manages the orchestration of scraping jobs with progress tracking and reliability.
"""

import logging
import json
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import uuid4

import asyncio
import asyncpg
from celery import Celery, Task
from celery.exceptions import Retry
from supabase import create_client, Client
from tenacity import retry, stop_after_attempt, wait_exponential

from .municipality_scraper import MunicipalityScraper
from ..storage.document_preserver import DocumentPreserver
from ..utils.config import get_settings

logger = logging.getLogger(__name__)

# Initialize Celery app
celery_app = Celery(
    'bylaw_scraper',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0',
    include=['backend.src.scrapers.job_manager']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max per task
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    task_default_retry_delay=60,
    task_max_retries=3,
    result_expires=3600,
)


class CallbackTask(Task):
    """Base task class with callback support."""
    
    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds."""
        logger.info(f"Task {task_id} succeeded: {retval}")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails."""
        logger.error(f"Task {task_id} failed: {exc}")
        logger.error(f"Error info: {einfo}")
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried."""
        logger.warning(f"Task {task_id} retrying: {exc}")


class ScrapingJobManager:
    """
    Manages scraping jobs with database integration and error handling.
    """
    
    def __init__(self, db_pool: asyncpg.Pool, supabase_client: Client):
        self.db_pool = db_pool
        self.supabase = supabase_client
        self.document_preserver = DocumentPreserver(supabase_client, db_pool)
    
    async def create_scraping_job(
        self,
        municipality_id: str,
        job_type: str = 'manual',
        triggered_by: Optional[str] = None,
        config_id: Optional[str] = None
    ) -> str:
        """
        Create a new scraping job record.
        
        Args:
            municipality_id: Municipality UUID
            job_type: Type of job ('manual', 'scheduled', 'update')
            triggered_by: User ID who triggered the job
            config_id: Scraping configuration ID
            
        Returns:
            Job ID
        """
        async with self.db_pool.acquire() as conn:
            query = """
            INSERT INTO scraping_jobs (
                municipality_id, config_id, job_type, status, triggered_by
            ) VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """
            
            job_id = await conn.fetchval(
                query, municipality_id, config_id, job_type, 'pending', triggered_by
            )
            
            return str(job_id)
    
    async def update_job_status(
        self,
        job_id: str,
        status: str,
        **kwargs
    ):
        """
        Update job status and metadata.
        
        Args:
            job_id: Job ID
            status: New status
            **kwargs: Additional fields to update
        """
        async with self.db_pool.acquire() as conn:
            # Build dynamic update query
            set_clauses = ['status = $2']
            params = [job_id, status]
            
            for key, value in kwargs.items():
                if key in ['started_at', 'completed_at', 'duration_seconds', 
                          'documents_found', 'documents_processed', 'documents_changed',
                          'error_message', 'error_details', 'celery_task_id']:
                    set_clauses.append(f"{key} = ${len(params) + 1}")
                    params.append(value)
            
            query = f"""
            UPDATE scraping_jobs 
            SET {', '.join(set_clauses)}
            WHERE id = $1
            """
            
            await conn.execute(query, *params)
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get current job status."""
        async with self.db_pool.acquire() as conn:
            query = """
            SELECT * FROM scraping_jobs WHERE id = $1
            """
            row = await conn.fetchrow(query, job_id)
            return dict(row) if row else None
    
    async def get_scraping_config(self, municipality_id: str) -> Optional[Dict[str, Any]]:
        """Get scraping configuration for municipality."""
        async with self.db_pool.acquire() as conn:
            query = """
            SELECT * FROM scraping_configs 
            WHERE municipality_id = $1 AND is_active = true
            """
            row = await conn.fetchrow(query, municipality_id)
            return dict(row) if row else None
    
    async def increment_failure_count(self, config_id: str, error_message: str):
        """Increment failure count for a configuration."""
        async with self.db_pool.acquire() as conn:
            query = """
            UPDATE scraping_configs 
            SET failure_count = failure_count + 1,
                last_error = $2,
                updated_at = NOW()
            WHERE id = $1
            """
            await conn.execute(query, config_id, error_message)
    
    async def reset_failure_count(self, config_id: str):
        """Reset failure count after successful scraping."""
        async with self.db_pool.acquire() as conn:
            query = """
            UPDATE scraping_configs 
            SET failure_count = 0,
                last_error = NULL,
                last_run_at = NOW(),
                updated_at = NOW()
            WHERE id = $1
            """
            await conn.execute(query, config_id)
    
    async def should_scrape(self, municipality_id: str) -> bool:
        """
        Check if municipality should be scraped based on configuration and recent activity.
        
        Args:
            municipality_id: Municipality UUID
            
        Returns:
            True if scraping should proceed
        """
        config = await self.get_scraping_config(municipality_id)
        
        if not config:
            return False
        
        # Check if too many recent failures
        if config.get('failure_count', 0) >= 5:
            return False
        
        # Check if recently scraped
        if last_run := config.get('last_run_at'):
            # Don't scrape if last run was less than 1 hour ago
            if datetime.utcnow() - last_run < timedelta(hours=1):
                return False
        
        return True


@celery_app.task(bind=True, base=CallbackTask)
def scrape_municipality(self, municipality_id: str, job_id: str, config: Dict[str, Any]):
    """
    Celery task for scraping a municipality.
    
    Args:
        municipality_id: Municipality UUID
        job_id: Scraping job ID
        config: Scraping configuration
    """
    settings = get_settings()
    
    # Initialize async components
    async def run_scraping():
        # Create database connection
        db_pool = await asyncpg.create_pool(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
            min_size=1,
            max_size=5
        )
        
        # Initialize Supabase client
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        
        # Initialize job manager
        job_manager = ScrapingJobManager(db_pool, supabase)
        
        start_time = datetime.utcnow()
        
        try:
            # Update job status to running
            await job_manager.update_job_status(
                job_id,
                'running',
                started_at=start_time,
                celery_task_id=self.request.id
            )
            
            # Initialize scraper
            scraper = MunicipalityScraper(municipality_id, config)
            
            # Perform scraping
            results = scraper.scrape()
            
            # Process results
            documents_found = len(results['documents'])
            documents_processed = 0
            documents_changed = 0
            
            for doc in results['documents']:
                try:
                    # Preserve document
                    preservation_result = await job_manager.document_preserver.preserve_document(
                        municipality_id=municipality_id,
                        url=doc['url'],
                        document_type='webpage',
                        scraper_version=scraper.scraper_version,
                        content=doc.get('content', ''),
                        metadata=doc.get('metadata', {}),
                        screenshot_path=doc.get('screenshot_path'),
                        pdf_content=doc.get('pdf_content'),
                        assets=doc.get('assets')
                    )
                    
                    if preservation_result['success']:
                        documents_processed += 1
                        
                        # Check if document changed
                        if preservation_result.get('content_changed'):
                            documents_changed += 1
                    
                except Exception as e:
                    logger.error(f"Error preserving document {doc['url']}: {e}")
            
            # Update job status to completed
            end_time = datetime.utcnow()
            duration = int((end_time - start_time).total_seconds())
            
            await job_manager.update_job_status(
                job_id,
                'completed',
                completed_at=end_time,
                duration_seconds=duration,
                documents_found=documents_found,
                documents_processed=documents_processed,
                documents_changed=documents_changed
            )
            
            # Reset failure count on success
            if config.get('id'):
                await job_manager.reset_failure_count(config['id'])
            
            return {
                'job_id': job_id,
                'status': 'completed',
                'documents_found': documents_found,
                'documents_processed': documents_processed,
                'documents_changed': documents_changed,
                'duration_seconds': duration
            }
            
        except Exception as e:
            logger.error(f"Scraping job {job_id} failed: {e}")
            logger.error(traceback.format_exc())
            
            # Update job status to failed
            await job_manager.update_job_status(
                job_id,
                'failed',
                completed_at=datetime.utcnow(),
                error_message=str(e),
                error_details=json.dumps({
                    'traceback': traceback.format_exc(),
                    'error_type': type(e).__name__
                })
            )
            
            # Increment failure count
            if config.get('id'):
                await job_manager.increment_failure_count(config['id'], str(e))
            
            # Re-raise for Celery retry mechanism
            raise self.retry(countdown=60, max_retries=3, exc=e)
        
        finally:
            await db_pool.close()
    
    # Run the async function
    return asyncio.get_event_loop().run_until_complete(run_scraping())


@celery_app.task(bind=True, base=CallbackTask)
def schedule_municipality_scraping(self, municipality_id: str, triggered_by: str = None):
    """
    Schedule scraping for a municipality based on its configuration.
    
    Args:
        municipality_id: Municipality UUID
        triggered_by: User ID who triggered the job
    """
    async def run_scheduling():
        settings = get_settings()
        
        # Create database connection
        db_pool = await asyncpg.create_pool(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
            min_size=1,
            max_size=5
        )
        
        # Initialize Supabase client
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        
        # Initialize job manager
        job_manager = ScrapingJobManager(db_pool, supabase)
        
        try:
            # Check if scraping should proceed
            if not await job_manager.should_scrape(municipality_id):
                logger.info(f"Skipping scraping for municipality {municipality_id} - conditions not met")
                return {'status': 'skipped', 'reason': 'conditions not met'}
            
            # Get configuration
            config = await job_manager.get_scraping_config(municipality_id)
            if not config:
                logger.warning(f"No configuration found for municipality {municipality_id}")
                return {'status': 'skipped', 'reason': 'no configuration'}
            
            # Create job
            job_id = await job_manager.create_scraping_job(
                municipality_id=municipality_id,
                job_type='scheduled',
                triggered_by=triggered_by,
                config_id=config['id']
            )
            
            # Queue scraping task
            scrape_municipality.delay(municipality_id, job_id, config)
            
            return {
                'status': 'scheduled',
                'job_id': job_id,
                'municipality_id': municipality_id
            }
            
        finally:
            await db_pool.close()
    
    return asyncio.get_event_loop().run_until_complete(run_scheduling())


@celery_app.task(bind=True, base=CallbackTask)
def batch_scrape_municipalities(self, municipality_ids: List[str], triggered_by: str = None):
    """
    Batch schedule scraping for multiple municipalities.
    
    Args:
        municipality_ids: List of municipality UUIDs
        triggered_by: User ID who triggered the job
    """
    results = []
    
    for municipality_id in municipality_ids:
        try:
            result = schedule_municipality_scraping.delay(municipality_id, triggered_by)
            results.append({
                'municipality_id': municipality_id,
                'task_id': result.id,
                'status': 'queued'
            })
        except Exception as e:
            logger.error(f"Error scheduling scraping for {municipality_id}: {e}")
            results.append({
                'municipality_id': municipality_id,
                'status': 'error',
                'error': str(e)
            })
    
    return {
        'batch_id': self.request.id,
        'total_municipalities': len(municipality_ids),
        'results': results
    }


@celery_app.task(bind=True, base=CallbackTask)
def cleanup_old_jobs(self, days_to_keep: int = 30):
    """
    Clean up old scraping jobs and related data.
    
    Args:
        days_to_keep: Number of days to keep job records
    """
    async def run_cleanup():
        settings = get_settings()
        
        # Create database connection
        db_pool = await asyncpg.create_pool(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
            min_size=1,
            max_size=5
        )
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            async with db_pool.acquire() as conn:
                # Delete old jobs
                query = """
                DELETE FROM scraping_jobs 
                WHERE created_at < $1 AND status IN ('completed', 'failed')
                """
                deleted_count = await conn.fetchval(
                    f"SELECT COUNT(*) FROM scraping_jobs WHERE created_at < $1 AND status IN ('completed', 'failed')",
                    cutoff_date
                )
                
                await conn.execute(query, cutoff_date)
                
                logger.info(f"Cleaned up {deleted_count} old scraping jobs")
                
                return {
                    'status': 'completed',
                    'deleted_jobs': deleted_count,
                    'cutoff_date': cutoff_date.isoformat()
                }
                
        finally:
            await db_pool.close()
    
    return asyncio.get_event_loop().run_until_complete(run_cleanup())


# Periodic tasks
@celery_app.task(bind=True, base=CallbackTask)
def run_scheduled_scraping(self):
    """
    Run scheduled scraping for all municipalities with active configurations.
    """
    async def run_scheduled():
        settings = get_settings()
        
        # Create database connection
        db_pool = await asyncpg.create_pool(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
            min_size=1,
            max_size=5
        )
        
        try:
            async with db_pool.acquire() as conn:
                # Get municipalities with active configurations
                query = """
                SELECT sc.municipality_id, sc.schedule_cron, sc.next_run_at
                FROM scraping_configs sc
                JOIN municipalities m ON sc.municipality_id = m.id
                WHERE sc.is_active = true 
                AND sc.next_run_at <= NOW()
                AND m.scraping_enabled = true
                """
                
                rows = await conn.fetch(query)
                
                scheduled_count = 0
                for row in rows:
                    municipality_id = str(row['municipality_id'])
                    
                    # Schedule scraping
                    schedule_municipality_scraping.delay(municipality_id, 'system')
                    scheduled_count += 1
                
                logger.info(f"Scheduled scraping for {scheduled_count} municipalities")
                
                return {
                    'status': 'completed',
                    'scheduled_count': scheduled_count
                }
                
        finally:
            await db_pool.close()
    
    return asyncio.get_event_loop().run_until_complete(run_scheduled())


# Celery beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    'run-scheduled-scraping': {
        'task': 'backend.src.scrapers.job_manager.run_scheduled_scraping',
        'schedule': 300.0,  # Every 5 minutes
    },
    'cleanup-old-jobs': {
        'task': 'backend.src.scrapers.job_manager.cleanup_old_jobs',
        'schedule': 86400.0,  # Daily
        'kwargs': {'days_to_keep': 30}
    },
}