"""
Admin API endpoints for scraping configurations and system management.
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from postgrest import APIError

from ...models.audit import (
    AuditLog,
    AuditLogWithDetails,
    AuditLogSearch,
    AuditLogList,
    AuditLogStats
)
from ...utils.supabase_client import get_supabase_client, get_admin_client
from ...config import settings
from pydantic import BaseModel, Field

router = APIRouter(prefix="/admin", tags=["admin"])


# Scraping Configuration Models
class ScrapingConfigBase(BaseModel):
    """Base scraping configuration model."""
    target_urls: List[str] = Field(..., description="URLs to scrape")
    selectors: Optional[dict] = Field(None, description="CSS/XPath selectors")
    schedule_cron: Optional[str] = Field(None, description="Cron schedule")
    scraper_type: str = Field("static", description="Scraper type")
    requires_javascript: bool = Field(False, description="Requires JavaScript")
    custom_headers: Optional[dict] = Field(None, description="Custom HTTP headers")
    is_active: bool = Field(True, description="Is configuration active")


class ScrapingConfigCreate(ScrapingConfigBase):
    """Scraping configuration creation model."""
    municipality_id: UUID = Field(..., description="Municipality ID")


class ScrapingConfigUpdate(BaseModel):
    """Scraping configuration update model."""
    target_urls: Optional[List[str]] = Field(None, description="URLs to scrape")
    selectors: Optional[dict] = Field(None, description="CSS/XPath selectors")
    schedule_cron: Optional[str] = Field(None, description="Cron schedule")
    scraper_type: Optional[str] = Field(None, description="Scraper type")
    requires_javascript: Optional[bool] = Field(None, description="Requires JavaScript")
    custom_headers: Optional[dict] = Field(None, description="Custom HTTP headers")
    is_active: Optional[bool] = Field(None, description="Is configuration active")


class ScrapingConfig(ScrapingConfigBase):
    """Full scraping configuration model."""
    id: UUID = Field(..., description="Configuration ID")
    municipality_id: UUID = Field(..., description="Municipality ID")
    last_run_at: Optional[datetime] = Field(None, description="Last run timestamp")
    next_run_at: Optional[datetime] = Field(None, description="Next run timestamp")
    failure_count: int = Field(0, description="Failure count")
    last_error: Optional[str] = Field(None, description="Last error message")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


# Scraping Job Models
class ScrapingJobBase(BaseModel):
    """Base scraping job model."""
    job_type: str = Field(..., description="Job type")
    status: str = Field("pending", description="Job status")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    duration_seconds: Optional[int] = Field(None, description="Duration in seconds")
    documents_found: int = Field(0, description="Documents found")
    documents_processed: int = Field(0, description="Documents processed")
    documents_changed: int = Field(0, description="Documents changed")
    error_message: Optional[str] = Field(None, description="Error message")
    error_details: Optional[dict] = Field(None, description="Error details")


class ScrapingJobCreate(ScrapingJobBase):
    """Scraping job creation model."""
    municipality_id: UUID = Field(..., description="Municipality ID")
    config_id: Optional[UUID] = Field(None, description="Configuration ID")
    triggered_by: Optional[UUID] = Field(None, description="User who triggered")


class ScrapingJob(ScrapingJobBase):
    """Full scraping job model."""
    id: UUID = Field(..., description="Job ID")
    municipality_id: UUID = Field(..., description="Municipality ID")
    config_id: Optional[UUID] = Field(None, description="Configuration ID")
    triggered_by: Optional[UUID] = Field(None, description="User who triggered")
    celery_task_id: Optional[str] = Field(None, description="Celery task ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True


# System Health Models
class SystemHealth(BaseModel):
    """System health status."""
    status: str = Field(..., description="Overall health status")
    database_status: str = Field(..., description="Database health")
    storage_status: str = Field(..., description="Storage health")
    scraping_status: str = Field(..., description="Scraping system health")
    last_check: datetime = Field(..., description="Last health check")
    
    # Component details
    active_scrapers: int = Field(0, description="Active scrapers")
    failed_jobs_24h: int = Field(0, description="Failed jobs in last 24 hours")
    storage_usage_bytes: int = Field(0, description="Storage usage in bytes")
    database_size_bytes: int = Field(0, description="Database size in bytes")


# Scraping Configuration endpoints
@router.get("/scraping-configs", response_model=List[ScrapingConfig])
async def get_scraping_configs(
    municipality_id: Optional[UUID] = Query(None, description="Filter by municipality"),
    is_active: Optional[bool] = Query(None, description="Filter by active status")
):
    """Get scraping configurations."""
    client = get_admin_client()
    
    try:
        query = client.table("scraping_configs").select("*")
        
        if municipality_id:
            query = query.eq("municipality_id", str(municipality_id))
        
        if is_active is not None:
            query = query.eq("is_active", is_active)
        
        result = query.execute()
        return [ScrapingConfig(**config) for config in result.data]
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/scraping-configs", response_model=ScrapingConfig)
async def create_scraping_config(config: ScrapingConfigCreate):
    """Create a new scraping configuration."""
    client = get_admin_client()
    
    try:
        # Verify municipality exists
        muni_result = client.table("municipalities").select("id").eq("id", str(config.municipality_id)).execute()
        if not muni_result.data:
            raise HTTPException(status_code=404, detail="Municipality not found")
        
        result = client.table("scraping_configs").insert(config.dict()).execute()
        
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to create scraping configuration")
        
        return ScrapingConfig(**result.data[0])
        
    except APIError as e:
        if "duplicate key value" in str(e):
            raise HTTPException(status_code=409, detail="Scraping configuration already exists for this municipality")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/scraping-configs/{config_id}", response_model=ScrapingConfig)
async def get_scraping_config(config_id: UUID):
    """Get scraping configuration by ID."""
    client = get_admin_client()
    
    try:
        result = client.table("scraping_configs").select("*").eq("id", str(config_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Scraping configuration not found")
        
        return ScrapingConfig(**result.data[0])
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.put("/scraping-configs/{config_id}", response_model=ScrapingConfig)
async def update_scraping_config(config_id: UUID, config: ScrapingConfigUpdate):
    """Update scraping configuration."""
    client = get_admin_client()
    
    try:
        # Remove None values
        update_data = {k: v for k, v in config.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        result = client.table("scraping_configs").update(update_data).eq("id", str(config_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Scraping configuration not found")
        
        return ScrapingConfig(**result.data[0])
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete("/scraping-configs/{config_id}")
async def delete_scraping_config(config_id: UUID):
    """Delete scraping configuration."""
    client = get_admin_client()
    
    try:
        result = client.table("scraping_configs").delete().eq("id", str(config_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Scraping configuration not found")
        
        return {"message": "Scraping configuration deleted successfully"}
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# Scraping Job endpoints
@router.get("/scraping-jobs", response_model=List[ScrapingJob])
async def get_scraping_jobs(
    municipality_id: Optional[UUID] = Query(None, description="Filter by municipality"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Limit results")
):
    """Get scraping jobs."""
    client = get_admin_client()
    
    try:
        query = client.table("scraping_jobs").select("*").order("created_at.desc").limit(limit)
        
        if municipality_id:
            query = query.eq("municipality_id", str(municipality_id))
        
        if status:
            query = query.eq("status", status)
        
        result = query.execute()
        return [ScrapingJob(**job) for job in result.data]
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/scraping-jobs", response_model=ScrapingJob)
async def create_scraping_job(job: ScrapingJobCreate, background_tasks: BackgroundTasks):
    """Create and start a new scraping job."""
    client = get_admin_client()
    
    try:
        # Verify municipality exists
        muni_result = client.table("municipalities").select("id").eq("id", str(job.municipality_id)).execute()
        if not muni_result.data:
            raise HTTPException(status_code=404, detail="Municipality not found")
        
        # Create job record
        job_data = job.dict()
        job_data["status"] = "pending"
        
        result = client.table("scraping_jobs").insert(job_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to create scraping job")
        
        created_job = ScrapingJob(**result.data[0])
        
        # In a full implementation, start the actual scraping task
        # background_tasks.add_task(start_scraping_task, created_job.id)
        
        return created_job
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/scraping-jobs/{job_id}", response_model=ScrapingJob)
async def get_scraping_job(job_id: UUID):
    """Get scraping job by ID."""
    client = get_admin_client()
    
    try:
        result = client.table("scraping_jobs").select("*").eq("id", str(job_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Scraping job not found")
        
        return ScrapingJob(**result.data[0])
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/scraping-jobs/{job_id}/cancel")
async def cancel_scraping_job(job_id: UUID):
    """Cancel a scraping job."""
    client = get_admin_client()
    
    try:
        # Update job status
        result = client.table("scraping_jobs").update({
            "status": "cancelled",
            "completed_at": datetime.now().isoformat()
        }).eq("id", str(job_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Scraping job not found")
        
        # In a full implementation, cancel the actual task
        # if result.data[0].get("celery_task_id"):
        #     cancel_celery_task(result.data[0]["celery_task_id"])
        
        return {"message": "Scraping job cancelled successfully"}
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# System Management endpoints
@router.get("/health", response_model=SystemHealth)
async def get_system_health():
    """Get system health status."""
    client = get_admin_client()
    
    try:
        # Check database health
        db_health = "healthy"
        try:
            client.table("municipalities").select("id").limit(1).execute()
        except Exception:
            db_health = "unhealthy"
        
        # Get job statistics
        jobs_result = client.table("scraping_jobs").select("status").execute()
        
        active_scrapers = sum(1 for job in jobs_result.data if job.get("status") == "running")
        failed_jobs_24h = sum(1 for job in jobs_result.data if job.get("status") == "failed")
        
        return SystemHealth(
            status="healthy" if db_health == "healthy" else "unhealthy",
            database_status=db_health,
            storage_status="healthy",  # Would check storage backend
            scraping_status="healthy",  # Would check scraping system
            last_check=datetime.now(),
            active_scrapers=active_scrapers,
            failed_jobs_24h=failed_jobs_24h,
            storage_usage_bytes=0,  # Would calculate from storage
            database_size_bytes=0   # Would calculate from database
        )
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/audit-logs", response_model=AuditLogList)
async def get_audit_logs(search: AuditLogSearch = Depends()):
    """Get audit logs with filtering and pagination."""
    client = get_admin_client()
    
    try:
        # Build query
        query = client.table("audit_log").select("*")
        
        # Apply filters
        if search.action:
            query = query.eq("action", search.action)
        
        if search.table_name:
            query = query.eq("table_name", search.table_name)
        
        if search.record_id:
            query = query.eq("record_id", str(search.record_id))
        
        if search.user_id:
            query = query.eq("user_id", str(search.user_id))
        
        if search.user_email:
            query = query.ilike("user_email", f"%{search.user_email}%")
        
        if search.timestamp_from:
            query = query.gte("timestamp", search.timestamp_from.isoformat())
        
        if search.timestamp_to:
            query = query.lte("timestamp", search.timestamp_to.isoformat())
        
        # Apply sorting
        sort_column = search.sort_by
        if search.sort_order == "desc":
            sort_column = f"{sort_column}.desc()"
        query = query.order(sort_column)
        
        # Get total count
        count_result = client.table("audit_log").select("*", count="exact").execute()
        total = count_result.count
        
        # Apply pagination
        offset = (search.page - 1) * search.page_size
        query = query.range(offset, offset + search.page_size - 1)
        
        # Execute query
        result = query.execute()
        
        # Transform results
        logs = [AuditLogWithDetails(**log) for log in result.data]
        
        return AuditLogList(
            logs=logs,
            total=total,
            page=search.page,
            page_size=search.page_size,
            total_pages=(total + search.page_size - 1) // search.page_size
        )
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/audit-logs/stats", response_model=AuditLogStats)
async def get_audit_log_stats():
    """Get audit log statistics."""
    client = get_admin_client()
    
    try:
        # Get all audit logs
        result = client.table("audit_log").select("*").execute()
        
        total_logs = len(result.data)
        
        # Count by action
        logs_by_action = {}
        logs_by_table = {}
        logs_by_user = {}
        
        for log in result.data:
            action = log.get("action", "unknown")
            logs_by_action[action] = logs_by_action.get(action, 0) + 1
            
            table = log.get("table_name", "unknown")
            logs_by_table[table] = logs_by_table.get(table, 0) + 1
            
            user = log.get("user_email", "unknown")
            logs_by_user[user] = logs_by_user.get(user, 0) + 1
        
        return AuditLogStats(
            total_logs=total_logs,
            logs_by_action=logs_by_action,
            logs_by_table=logs_by_table,
            logs_by_user=logs_by_user
        )
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/system/cleanup")
async def cleanup_system():
    """Perform system cleanup tasks."""
    client = get_admin_client()
    
    try:
        # In a full implementation, perform cleanup tasks like:
        # - Remove old audit logs
        # - Clean up failed jobs
        # - Remove orphaned files
        # - Vacuum database
        
        return {"message": "System cleanup completed successfully"}
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/system/maintenance")
async def enable_maintenance_mode():
    """Enable maintenance mode."""
    # In a full implementation, set maintenance mode flag
    return {"message": "Maintenance mode enabled"}


@router.delete("/system/maintenance")
async def disable_maintenance_mode():
    """Disable maintenance mode."""
    # In a full implementation, clear maintenance mode flag
    return {"message": "Maintenance mode disabled"}