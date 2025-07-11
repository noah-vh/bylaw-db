"""
Health check endpoints for monitoring application status.
Provides comprehensive health checks for all system components.
"""

import os
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, Response
from pydantic import BaseModel
import asyncpg
import redis
from supabase import create_client, Client
from ..utils.logger import get_logger
from ..utils.metrics import metrics_collector
import psutil

logger = get_logger(__name__)
router = APIRouter()


class HealthStatus(BaseModel):
    """Health check status model."""
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: datetime
    uptime: float
    version: str
    environment: str


class ComponentHealth(BaseModel):
    """Individual component health model."""
    name: str
    status: str
    response_time: Optional[float] = None
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class DetailedHealthResponse(BaseModel):
    """Detailed health check response."""
    status: str
    timestamp: datetime
    uptime: float
    version: str
    environment: str
    components: List[ComponentHealth]
    system: Optional[Dict[str, Any]] = None


class HealthChecker:
    """Centralized health checking for all components."""
    
    def __init__(self):
        self.start_time = time.time()
        self.database_url = os.getenv("DATABASE_URL")
        self.redis_url = os.getenv("REDIS_URL")
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
    
    async def check_database(self) -> ComponentHealth:
        """Check database connectivity and performance."""
        start_time = time.time()
        
        try:
            if not self.database_url:
                return ComponentHealth(
                    name="database",
                    status="unhealthy",
                    error="DATABASE_URL not configured"
                )
            
            conn = await asyncpg.connect(self.database_url)
            
            try:
                # Test basic connectivity
                await conn.execute("SELECT 1")
                
                # Check connection pool status
                pool_stats = await conn.fetchrow("""
                    SELECT 
                        count(*) as total_connections,
                        count(*) filter (where state = 'active') as active_connections,
                        count(*) filter (where state = 'idle') as idle_connections
                    FROM pg_stat_activity 
                    WHERE datname = current_database()
                """)
                
                response_time = time.time() - start_time
                
                return ComponentHealth(
                    name="database",
                    status="healthy",
                    response_time=response_time,
                    details={
                        "total_connections": pool_stats["total_connections"],
                        "active_connections": pool_stats["active_connections"],
                        "idle_connections": pool_stats["idle_connections"]
                    }
                )
                
            finally:
                await conn.close()
                
        except Exception as e:
            response_time = time.time() - start_time
            return ComponentHealth(
                name="database",
                status="unhealthy",
                response_time=response_time,
                error=str(e)
            )
    
    async def check_redis(self) -> ComponentHealth:
        """Check Redis connectivity and performance."""
        start_time = time.time()
        
        try:
            if not self.redis_url:
                return ComponentHealth(
                    name="redis",
                    status="unhealthy",
                    error="REDIS_URL not configured"
                )
            
            r = redis.from_url(self.redis_url)
            
            # Test connectivity
            await asyncio.to_thread(r.ping)
            
            # Get Redis info
            info = await asyncio.to_thread(r.info)
            
            response_time = time.time() - start_time
            
            return ComponentHealth(
                name="redis",
                status="healthy",
                response_time=response_time,
                details={
                    "used_memory": info.get("used_memory_human"),
                    "connected_clients": info.get("connected_clients"),
                    "uptime": info.get("uptime_in_seconds")
                }
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            return ComponentHealth(
                name="redis",
                status="unhealthy",
                response_time=response_time,
                error=str(e)
            )
    
    async def check_supabase(self) -> ComponentHealth:
        """Check Supabase connectivity."""
        start_time = time.time()
        
        try:
            if not all([self.supabase_url, self.supabase_key]):
                return ComponentHealth(
                    name="supabase",
                    status="unhealthy",
                    error="Supabase credentials not configured"
                )
            
            supabase: Client = create_client(self.supabase_url, self.supabase_key)
            
            # Test connectivity with a simple query
            result = supabase.table("jurisdictions").select("id").limit(1).execute()
            
            response_time = time.time() - start_time
            
            return ComponentHealth(
                name="supabase",
                status="healthy",
                response_time=response_time,
                details={
                    "url": self.supabase_url,
                    "connection_test": "success"
                }
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            return ComponentHealth(
                name="supabase",
                status="unhealthy",
                response_time=response_time,
                error=str(e)
            )
    
    async def check_celery(self) -> ComponentHealth:
        """Check Celery worker status."""
        start_time = time.time()
        
        try:
            if not self.redis_url:
                return ComponentHealth(
                    name="celery",
                    status="unhealthy",
                    error="Redis URL not configured for Celery"
                )
            
            # Check if we can connect to Celery through Redis
            r = redis.from_url(self.redis_url)
            
            # Check active workers (simplified check)
            # In a real implementation, you'd want to use Celery's inspect API
            celery_info = await asyncio.to_thread(r.info, "replication")
            
            response_time = time.time() - start_time
            
            return ComponentHealth(
                name="celery",
                status="healthy",
                response_time=response_time,
                details={
                    "broker": "redis",
                    "connection": "healthy"
                }
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            return ComponentHealth(
                name="celery",
                status="degraded",
                response_time=response_time,
                error=str(e)
            )
    
    async def check_system_resources(self) -> ComponentHealth:
        """Check system resource usage."""
        start_time = time.time()
        
        try:
            # Memory usage
            memory = psutil.virtual_memory()
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Determine status based on resource usage
            status = "healthy"
            if memory.percent > 90 or cpu_percent > 90 or disk.percent > 90:
                status = "unhealthy"
            elif memory.percent > 80 or cpu_percent > 80 or disk.percent > 80:
                status = "degraded"
            
            response_time = time.time() - start_time
            
            return ComponentHealth(
                name="system",
                status=status,
                response_time=response_time,
                details={
                    "memory_percent": memory.percent,
                    "cpu_percent": cpu_percent,
                    "disk_percent": disk.percent,
                    "memory_available": memory.available,
                    "disk_free": disk.free
                }
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            return ComponentHealth(
                name="system",
                status="unhealthy",
                response_time=response_time,
                error=str(e)
            )
    
    async def check_all_components(self) -> List[ComponentHealth]:
        """Check all components in parallel."""
        tasks = [
            self.check_database(),
            self.check_redis(),
            self.check_supabase(),
            self.check_celery(),
            self.check_system_resources()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        components = []
        for result in results:
            if isinstance(result, Exception):
                components.append(ComponentHealth(
                    name="unknown",
                    status="unhealthy",
                    error=str(result)
                ))
            else:
                components.append(result)
        
        return components
    
    def get_overall_status(self, components: List[ComponentHealth]) -> str:
        """Determine overall health status from components."""
        if any(c.status == "unhealthy" for c in components):
            return "unhealthy"
        elif any(c.status == "degraded" for c in components):
            return "degraded"
        else:
            return "healthy"
    
    def get_uptime(self) -> float:
        """Get application uptime in seconds."""
        return time.time() - self.start_time


# Global health checker instance
health_checker = HealthChecker()


@router.get("/health", response_model=HealthStatus)
async def basic_health_check():
    """Basic health check endpoint."""
    uptime = health_checker.get_uptime()
    
    # Update metrics
    metrics_collector.update_uptime()
    
    return HealthStatus(
        status="healthy",
        timestamp=datetime.utcnow(),
        uptime=uptime,
        version=os.getenv("APP_VERSION", "unknown"),
        environment=os.getenv("ENVIRONMENT", "development")
    )


@router.get("/health/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check():
    """Detailed health check with all components."""
    start_time = time.time()
    
    try:
        # Check all components
        components = await health_checker.check_all_components()
        
        # Get overall status
        overall_status = health_checker.get_overall_status(components)
        
        # Get system information
        system_info = None
        try:
            system_info = {
                "python_version": os.getenv("PYTHON_VERSION", "unknown"),
                "platform": os.getenv("PLATFORM", "unknown"),
                "hostname": os.getenv("HOSTNAME", "unknown"),
                "process_id": os.getpid(),
                "thread_count": psutil.Process().num_threads(),
                "file_descriptors": psutil.Process().num_fds() if hasattr(psutil.Process(), 'num_fds') else None
            }
        except Exception as e:
            logger.warning(f"Failed to get system info: {e}")
        
        # Update metrics
        metrics_collector.update_uptime()
        
        check_duration = time.time() - start_time
        
        # Log health check
        logger.info(
            "Health check completed",
            overall_status=overall_status,
            component_count=len(components),
            check_duration=check_duration
        )
        
        return DetailedHealthResponse(
            status=overall_status,
            timestamp=datetime.utcnow(),
            uptime=health_checker.get_uptime(),
            version=os.getenv("APP_VERSION", "unknown"),
            environment=os.getenv("ENVIRONMENT", "development"),
            components=components,
            system=system_info
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/health/liveness")
async def liveness_probe():
    """Kubernetes liveness probe endpoint."""
    return {"status": "alive", "timestamp": datetime.utcnow()}


@router.get("/health/readiness")
async def readiness_probe():
    """Kubernetes readiness probe endpoint."""
    try:
        # Check critical components only
        database_health = await health_checker.check_database()
        redis_health = await health_checker.check_redis()
        
        if database_health.status == "unhealthy" or redis_health.status == "unhealthy":
            raise HTTPException(
                status_code=503,
                detail="Service not ready"
            )
        
        return {"status": "ready", "timestamp": datetime.utcnow()}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Service not ready: {str(e)}"
        )


@router.get("/health/startup")
async def startup_probe():
    """Kubernetes startup probe endpoint."""
    try:
        # Check if application has finished starting up
        uptime = health_checker.get_uptime()
        
        # Consider the app started if it's been running for at least 10 seconds
        if uptime < 10:
            raise HTTPException(
                status_code=503,
                detail="Application still starting up"
            )
        
        return {"status": "started", "uptime": uptime, "timestamp": datetime.utcnow()}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Startup check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Startup check failed: {str(e)}"
        )


@router.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint."""
    try:
        # Update system metrics before returning
        metrics_collector.update_system_metrics()
        
        # Get metrics in Prometheus format
        metrics_output = metrics_collector.get_metrics()
        
        return Response(
            content=metrics_output,
            media_type="text/plain"
        )
        
    except Exception as e:
        logger.error(f"Metrics endpoint failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate metrics: {str(e)}"
        )