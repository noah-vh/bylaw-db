"""
Structured logging utility for the Bylaw DB application.
Provides consistent logging across all services with proper formatting and context.
"""

import sys
import os
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, Union
from pathlib import Path
import structlog
from structlog.stdlib import LoggerFactory


def setup_logging(
    service_name: str = "bylaw-db",
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    enable_json_logs: bool = True
) -> None:
    """
    Configure structured logging for the application.
    
    Args:
        service_name: Name of the service for log context
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file path for log output
        enable_json_logs: Whether to use JSON formatted logs
    """
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if enable_json_logs else structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure stdlib logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper())
    )
    
    # Add file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        
        if enable_json_logs:
            formatter = logging.Formatter('%(message)s')
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        file_handler.setFormatter(formatter)
        logging.getLogger().addHandler(file_handler)
    
    # Set service context
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(service=service_name)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured structured logger
    """
    return structlog.get_logger(name)


class LoggerMixin:
    """Mixin class to add logging capabilities to any class."""
    
    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        """Get logger instance for this class."""
        return get_logger(self.__class__.__name__)


class RequestLogger:
    """Request logging middleware for FastAPI."""
    
    def __init__(self, logger_name: str = "api"):
        self.logger = get_logger(logger_name)
    
    async def log_request(self, request, response, process_time: float):
        """Log API request details."""
        
        # Extract request info
        request_data = {
            "method": request.method,
            "url": str(request.url),
            "user_agent": request.headers.get("user-agent"),
            "remote_addr": request.client.host if request.client else None,
            "content_length": request.headers.get("content-length"),
            "content_type": request.headers.get("content-type"),
        }
        
        # Extract response info
        response_data = {
            "status_code": response.status_code,
            "content_length": response.headers.get("content-length"),
            "content_type": response.headers.get("content-type"),
        }
        
        # Log with appropriate level based on status code
        if response.status_code >= 500:
            self.logger.error(
                "API request failed",
                request=request_data,
                response=response_data,
                process_time=process_time
            )
        elif response.status_code >= 400:
            self.logger.warning(
                "API request error",
                request=request_data,
                response=response_data,
                process_time=process_time
            )
        else:
            self.logger.info(
                "API request completed",
                request=request_data,
                response=response_data,
                process_time=process_time
            )


class AuditLogger:
    """Audit logging for sensitive operations."""
    
    def __init__(self):
        self.logger = get_logger("audit")
    
    def log_user_action(
        self,
        action: str,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True
    ):
        """Log user actions for audit trail."""
        
        audit_data = {
            "action": action,
            "user_id": user_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "success": success,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if details:
            audit_data["details"] = details
        
        if success:
            self.logger.info("User action completed", **audit_data)
        else:
            self.logger.error("User action failed", **audit_data)
    
    def log_data_access(
        self,
        table: str,
        operation: str,
        user_id: Optional[str] = None,
        record_count: int = 1,
        filters: Optional[Dict[str, Any]] = None
    ):
        """Log data access for compliance."""
        
        self.logger.info(
            "Data access",
            table=table,
            operation=operation,
            user_id=user_id,
            record_count=record_count,
            filters=filters,
            timestamp=datetime.utcnow().isoformat()
        )


class ScrapingLogger:
    """Specialized logger for scraping operations."""
    
    def __init__(self, jurisdiction: str, job_id: Optional[str] = None):
        self.logger = get_logger("scraping")
        self.jurisdiction = jurisdiction
        self.job_id = job_id
    
    def log_scraping_start(self, url: str, job_type: str):
        """Log start of scraping job."""
        self.logger.info(
            "Scraping job started",
            jurisdiction=self.jurisdiction,
            job_id=self.job_id,
            url=url,
            job_type=job_type
        )
    
    def log_scraping_progress(self, processed: int, total: int, url: str):
        """Log scraping progress."""
        self.logger.info(
            "Scraping progress",
            jurisdiction=self.jurisdiction,
            job_id=self.job_id,
            processed=processed,
            total=total,
            url=url,
            progress_percent=round((processed / total) * 100, 2) if total > 0 else 0
        )
    
    def log_document_found(self, document_url: str, document_type: str, title: str):
        """Log when a document is found."""
        self.logger.info(
            "Document found",
            jurisdiction=self.jurisdiction,
            job_id=self.job_id,
            document_url=document_url,
            document_type=document_type,
            title=title
        )
    
    def log_document_processed(self, document_id: str, pages: int, file_size: int):
        """Log when a document is processed."""
        self.logger.info(
            "Document processed",
            jurisdiction=self.jurisdiction,
            job_id=self.job_id,
            document_id=document_id,
            pages=pages,
            file_size=file_size
        )
    
    def log_scraping_error(self, error: str, url: str, retry_count: int = 0):
        """Log scraping errors."""
        self.logger.error(
            "Scraping error",
            jurisdiction=self.jurisdiction,
            job_id=self.job_id,
            error=error,
            url=url,
            retry_count=retry_count
        )
    
    def log_scraping_complete(self, documents_found: int, documents_processed: int, duration: float):
        """Log completion of scraping job."""
        self.logger.info(
            "Scraping job completed",
            jurisdiction=self.jurisdiction,
            job_id=self.job_id,
            documents_found=documents_found,
            documents_processed=documents_processed,
            duration=duration,
            success_rate=round((documents_processed / documents_found) * 100, 2) if documents_found > 0 else 0
        )


class PerformanceLogger:
    """Logger for performance metrics."""
    
    def __init__(self):
        self.logger = get_logger("performance")
    
    def log_query_performance(
        self,
        query_type: str,
        execution_time: float,
        record_count: int,
        table: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ):
        """Log database query performance."""
        
        # Determine log level based on execution time
        if execution_time > 5.0:
            log_level = "error"
        elif execution_time > 2.0:
            log_level = "warning"
        else:
            log_level = "info"
        
        getattr(self.logger, log_level)(
            "Database query performance",
            query_type=query_type,
            execution_time=execution_time,
            record_count=record_count,
            table=table,
            filters=filters
        )
    
    def log_api_performance(
        self,
        endpoint: str,
        method: str,
        response_time: float,
        status_code: int,
        payload_size: Optional[int] = None
    ):
        """Log API endpoint performance."""
        
        # Determine log level based on response time
        if response_time > 3.0:
            log_level = "error"
        elif response_time > 1.0:
            log_level = "warning"
        else:
            log_level = "info"
        
        getattr(self.logger, log_level)(
            "API performance",
            endpoint=endpoint,
            method=method,
            response_time=response_time,
            status_code=status_code,
            payload_size=payload_size
        )


def configure_uvicorn_logging():
    """Configure uvicorn logging to use structured logging."""
    
    # Disable uvicorn's default logging
    logging.getLogger("uvicorn.access").disabled = True
    logging.getLogger("uvicorn.error").disabled = True
    
    # Use our structured logger
    uvicorn_logger = get_logger("uvicorn")
    
    class UvicornLogHandler(logging.Handler):
        def emit(self, record):
            uvicorn_logger.info(record.getMessage())
    
    # Add our handler
    logging.getLogger("uvicorn").addHandler(UvicornLogHandler())


# Initialize logging based on environment
def init_logging():
    """Initialize logging configuration based on environment variables."""
    
    service_name = os.getenv("SERVICE_NAME", "bylaw-db")
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_file = os.getenv("LOG_FILE")
    environment = os.getenv("ENVIRONMENT", "development")
    
    # Use JSON logs in production
    enable_json_logs = environment == "production"
    
    setup_logging(
        service_name=service_name,
        log_level=log_level,
        log_file=log_file,
        enable_json_logs=enable_json_logs
    )
    
    # Configure uvicorn logging
    configure_uvicorn_logging()


# Auto-initialize if imported
if __name__ != "__main__":
    init_logging()