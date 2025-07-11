"""
Prometheus metrics collection for the Bylaw DB application.
Provides comprehensive monitoring of application performance and health.
"""

import time
import functools
from typing import Dict, Any, Optional, Callable
from prometheus_client import (
    Counter, Histogram, Gauge, Summary, Info,
    CollectorRegistry, REGISTRY, generate_latest,
    multiprocess, values
)
import os
from contextlib import contextmanager

# Create custom registry for the application
app_registry = CollectorRegistry()

# API Metrics
api_requests_total = Counter(
    'api_requests_total',
    'Total number of API requests',
    ['method', 'endpoint', 'status_code'],
    registry=app_registry
)

api_request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=app_registry
)

api_request_size = Summary(
    'api_request_size_bytes',
    'API request size in bytes',
    ['method', 'endpoint'],
    registry=app_registry
)

api_response_size = Summary(
    'api_response_size_bytes',
    'API response size in bytes',
    ['method', 'endpoint'],
    registry=app_registry
)

# Database Metrics
db_queries_total = Counter(
    'db_queries_total',
    'Total number of database queries',
    ['table', 'operation', 'status'],
    registry=app_registry
)

db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['table', 'operation'],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
    registry=app_registry
)

db_connections_active = Gauge(
    'db_connections_active',
    'Number of active database connections',
    registry=app_registry
)

db_connection_errors = Counter(
    'db_connection_errors_total',
    'Total number of database connection errors',
    ['error_type'],
    registry=app_registry
)

# Scraping Metrics
scraping_jobs_total = Counter(
    'scraping_jobs_total',
    'Total number of scraping jobs',
    ['jurisdiction', 'job_type', 'status'],
    registry=app_registry
)

scraping_job_duration = Histogram(
    'scraping_job_duration_seconds',
    'Scraping job duration in seconds',
    ['jurisdiction', 'job_type'],
    buckets=(60, 300, 600, 1800, 3600, 7200, 14400),
    registry=app_registry
)

scraping_documents_found = Counter(
    'scraping_documents_found_total',
    'Total number of documents found during scraping',
    ['jurisdiction', 'document_type'],
    registry=app_registry
)

scraping_documents_processed = Counter(
    'scraping_documents_processed_total',
    'Total number of documents processed during scraping',
    ['jurisdiction', 'document_type', 'status'],
    registry=app_registry
)

scraping_errors = Counter(
    'scraping_errors_total',
    'Total number of scraping errors',
    ['jurisdiction', 'error_type'],
    registry=app_registry
)

# Celery Metrics
celery_tasks_total = Counter(
    'celery_tasks_total',
    'Total number of Celery tasks',
    ['task_name', 'status'],
    registry=app_registry
)

celery_task_duration = Histogram(
    'celery_task_duration_seconds',
    'Celery task duration in seconds',
    ['task_name'],
    buckets=(1, 10, 30, 60, 300, 600, 1800, 3600),
    registry=app_registry
)

celery_queue_length = Gauge(
    'celery_queue_length',
    'Number of tasks in Celery queue',
    ['queue_name'],
    registry=app_registry
)

celery_workers_active = Gauge(
    'celery_workers_active',
    'Number of active Celery workers',
    registry=app_registry
)

# System Metrics
system_memory_usage = Gauge(
    'system_memory_usage_bytes',
    'System memory usage in bytes',
    ['type'],
    registry=app_registry
)

system_cpu_usage = Gauge(
    'system_cpu_usage_percent',
    'System CPU usage percentage',
    registry=app_registry
)

system_disk_usage = Gauge(
    'system_disk_usage_bytes',
    'System disk usage in bytes',
    ['path', 'type'],
    registry=app_registry
)

# Application Metrics
app_info = Info(
    'app_info',
    'Application information',
    registry=app_registry
)

app_startup_time = Gauge(
    'app_startup_time_seconds',
    'Application startup time in seconds',
    registry=app_registry
)

app_uptime = Gauge(
    'app_uptime_seconds',
    'Application uptime in seconds',
    registry=app_registry
)

# Document Processing Metrics
document_processing_total = Counter(
    'document_processing_total',
    'Total number of documents processed',
    ['document_type', 'status'],
    registry=app_registry
)

document_processing_duration = Histogram(
    'document_processing_duration_seconds',
    'Document processing duration in seconds',
    ['document_type'],
    buckets=(1, 5, 10, 30, 60, 300, 600),
    registry=app_registry
)

document_size_processed = Summary(
    'document_size_processed_bytes',
    'Size of documents processed in bytes',
    ['document_type'],
    registry=app_registry
)

document_pages_processed = Summary(
    'document_pages_processed',
    'Number of pages processed per document',
    ['document_type'],
    registry=app_registry
)


class MetricsCollector:
    """Centralized metrics collection and management."""
    
    def __init__(self):
        self.start_time = time.time()
        self._setup_app_info()
    
    def _setup_app_info(self):
        """Set up application information metrics."""
        app_info.info({
            'version': os.getenv('APP_VERSION', 'unknown'),
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'python_version': os.getenv('PYTHON_VERSION', 'unknown'),
            'build_date': os.getenv('BUILD_DATE', 'unknown')
        })
        
        app_startup_time.set(time.time() - self.start_time)
    
    def update_uptime(self):
        """Update application uptime metric."""
        app_uptime.set(time.time() - self.start_time)
    
    def record_api_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration: float,
        request_size: Optional[int] = None,
        response_size: Optional[int] = None
    ):
        """Record API request metrics."""
        api_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code
        ).inc()
        
        api_request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
        
        if request_size is not None:
            api_request_size.labels(
                method=method,
                endpoint=endpoint
            ).observe(request_size)
        
        if response_size is not None:
            api_response_size.labels(
                method=method,
                endpoint=endpoint
            ).observe(response_size)
    
    def record_db_query(
        self,
        table: str,
        operation: str,
        duration: float,
        status: str = "success"
    ):
        """Record database query metrics."""
        db_queries_total.labels(
            table=table,
            operation=operation,
            status=status
        ).inc()
        
        db_query_duration.labels(
            table=table,
            operation=operation
        ).observe(duration)
    
    def record_scraping_job(
        self,
        jurisdiction: str,
        job_type: str,
        status: str,
        duration: Optional[float] = None,
        documents_found: int = 0,
        documents_processed: int = 0
    ):
        """Record scraping job metrics."""
        scraping_jobs_total.labels(
            jurisdiction=jurisdiction,
            job_type=job_type,
            status=status
        ).inc()
        
        if duration is not None:
            scraping_job_duration.labels(
                jurisdiction=jurisdiction,
                job_type=job_type
            ).observe(duration)
        
        if documents_found > 0:
            scraping_documents_found.labels(
                jurisdiction=jurisdiction,
                document_type="unknown"
            ).inc(documents_found)
        
        if documents_processed > 0:
            scraping_documents_processed.labels(
                jurisdiction=jurisdiction,
                document_type="unknown",
                status=status
            ).inc(documents_processed)
    
    def record_celery_task(
        self,
        task_name: str,
        status: str,
        duration: Optional[float] = None
    ):
        """Record Celery task metrics."""
        celery_tasks_total.labels(
            task_name=task_name,
            status=status
        ).inc()
        
        if duration is not None:
            celery_task_duration.labels(
                task_name=task_name
            ).observe(duration)
    
    def record_document_processing(
        self,
        document_type: str,
        status: str,
        duration: float,
        file_size: Optional[int] = None,
        pages: Optional[int] = None
    ):
        """Record document processing metrics."""
        document_processing_total.labels(
            document_type=document_type,
            status=status
        ).inc()
        
        document_processing_duration.labels(
            document_type=document_type
        ).observe(duration)
        
        if file_size is not None:
            document_size_processed.labels(
                document_type=document_type
            ).observe(file_size)
        
        if pages is not None:
            document_pages_processed.labels(
                document_type=document_type
            ).observe(pages)
    
    def update_system_metrics(self):
        """Update system resource metrics."""
        try:
            import psutil
            
            # Memory metrics
            memory = psutil.virtual_memory()
            system_memory_usage.labels(type='used').set(memory.used)
            system_memory_usage.labels(type='available').set(memory.available)
            system_memory_usage.labels(type='total').set(memory.total)
            
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            system_cpu_usage.set(cpu_percent)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            system_disk_usage.labels(path='/', type='used').set(disk.used)
            system_disk_usage.labels(path='/', type='free').set(disk.free)
            system_disk_usage.labels(path='/', type='total').set(disk.total)
            
        except ImportError:
            # psutil not available, skip system metrics
            pass
    
    def get_metrics(self) -> str:
        """Get all metrics in Prometheus format."""
        return generate_latest(app_registry)


# Global metrics collector instance
metrics_collector = MetricsCollector()


def timed_metric(metric_name: str, labels: Optional[Dict[str, str]] = None):
    """Decorator to automatically time function execution and record metrics."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                status = "success"
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                
                # Record the metric
                if metric_name == "api_request":
                    metrics_collector.record_api_request(
                        method=labels.get("method", "unknown"),
                        endpoint=labels.get("endpoint", "unknown"),
                        status_code=labels.get("status_code", 200),
                        duration=duration
                    )
                elif metric_name == "db_query":
                    metrics_collector.record_db_query(
                        table=labels.get("table", "unknown"),
                        operation=labels.get("operation", "unknown"),
                        duration=duration,
                        status=status
                    )
                elif metric_name == "celery_task":
                    metrics_collector.record_celery_task(
                        task_name=labels.get("task_name", func.__name__),
                        status=status,
                        duration=duration
                    )
        
        return wrapper
    return decorator


@contextmanager
def timer(metric_name: str, labels: Optional[Dict[str, str]] = None):
    """Context manager for timing operations."""
    start_time = time.time()
    try:
        yield
        status = "success"
    except Exception:
        status = "error"
        raise
    finally:
        duration = time.time() - start_time
        
        # Record appropriate metric based on metric_name
        if metric_name == "db_query" and labels:
            metrics_collector.record_db_query(
                table=labels.get("table", "unknown"),
                operation=labels.get("operation", "unknown"),
                duration=duration,
                status=status
            )
        elif metric_name == "document_processing" and labels:
            metrics_collector.record_document_processing(
                document_type=labels.get("document_type", "unknown"),
                status=status,
                duration=duration
            )


def setup_metrics_multiprocess():
    """Setup metrics for multiprocess mode (for production)."""
    if os.getenv("PROMETHEUS_MULTIPROC_DIR"):
        # Use multiprocess mode
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
        return registry
    else:
        return app_registry


def cleanup_metrics():
    """Clean up metrics on application shutdown."""
    if os.getenv("PROMETHEUS_MULTIPROC_DIR"):
        multiprocess.mark_process_dead(os.getpid())


# Export commonly used functions
__all__ = [
    'metrics_collector',
    'timed_metric',
    'timer',
    'setup_metrics_multiprocess',
    'cleanup_metrics'
]