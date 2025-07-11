"""
Main FastAPI application for the Bylaw Database API.
"""
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
import uvicorn

from .config import settings
from .utils.supabase_client import supabase_manager
from .api.routers import municipalities, bylaws, source_documents, admin

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Bylaw Database API...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    
    # Initialize Supabase connections
    try:
        client = supabase_manager.get_connected_client()
        logger.info("Connected to Supabase successfully")
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {e}")
        raise
    
    # Health check
    try:
        health_status = await supabase_manager.health_check_all()
        logger.info(f"Health check results: {health_status}")
        
        if not all(health_status.values()):
            logger.warning("Some health checks failed")
    except Exception as e:
        logger.error(f"Health check failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Bylaw Database API...")
    supabase_manager.disconnect_all()
    logger.info("Disconnected from Supabase")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    Bylaw Database API for managing municipal bylaws and source documents.
    
    This API provides endpoints for:
    - Managing municipalities and their bylaws
    - Tracking bylaw versions and changes
    - Storing and retrieving source documents
    - Administrative functions for scraping and system management
    
    ## Authentication
    
    Most endpoints require authentication. Use the appropriate Supabase authentication method.
    
    ## Rate Limits
    
    API endpoints are rate-limited to prevent abuse. Please implement appropriate backoff strategies.
    
    ## Data Preservation
    
    All source documents are preserved for liability protection. Deletion operations are logged and audited.
    """,
    lifespan=lifespan,
    debug=settings.debug,
    openapi_url=f"{settings.api_v1_str}/openapi.json" if settings.debug else None,
    docs_url=f"{settings.api_v1_str}/docs" if settings.debug else None,
    redoc_url=f"{settings.api_v1_str}/redoc" if settings.debug else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Add trusted host middleware for production
if settings.environment == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.bylawdb.com", "bylawdb.com", "localhost"]
    )


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    logger.warning(f"HTTP {exc.status_code} error: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url),
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Internal server error",
            "status_code": 500,
            "path": str(request.url),
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check database connection
        health_status = await supabase_manager.health_check_all()
        
        is_healthy = all(health_status.values())
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "version": settings.app_version,
            "environment": settings.environment,
            "checks": health_status,
            "timestamp": "2024-01-01T00:00:00Z"  # Would use actual timestamp
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "version": settings.app_version,
            "environment": settings.environment,
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00Z"  # Would use actual timestamp
        }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to the Bylaw Database API",
        "version": settings.app_version,
        "environment": settings.environment,
        "docs_url": f"{settings.api_v1_str}/docs" if settings.debug else None,
        "health_url": "/health"
    }


# API version info
@app.get(f"{settings.api_v1_str}/info")
async def api_info():
    """Get API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "Municipal Bylaw Database API",
        "environment": settings.environment,
        "debug": settings.debug,
        "endpoints": {
            "municipalities": f"{settings.api_v1_str}/municipalities",
            "bylaws": f"{settings.api_v1_str}/bylaws",
            "source_documents": f"{settings.api_v1_str}/source-documents",
            "admin": f"{settings.api_v1_str}/admin"
        }
    }


# Include routers
app.include_router(municipalities.router, prefix=settings.api_v1_str)
app.include_router(bylaws.router, prefix=settings.api_v1_str)
app.include_router(source_documents.router, prefix=settings.api_v1_str)
app.include_router(admin.router, prefix=settings.api_v1_str)


# Custom OpenAPI schema
def custom_openapi():
    """Generate custom OpenAPI schema."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.app_name,
        version=settings.app_version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "SupabaseAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Supabase JWT token"
        }
    }
    
    # Add global security requirement
    openapi_schema["security"] = [{"SupabaseAuth": []}]
    
    # Add server information
    openapi_schema["servers"] = [
        {
            "url": f"http://localhost:8000{settings.api_v1_str}",
            "description": "Development server"
        },
        {
            "url": f"https://api.bylawdb.com{settings.api_v1_str}",
            "description": "Production server"
        }
    ]
    
    # Add contact information
    openapi_schema["info"]["contact"] = {
        "name": "Bylaw Database Support",
        "url": "https://bylawdb.com/support",
        "email": "support@bylawdb.com"
    }
    
    # Add license information
    openapi_schema["info"]["license"] = {
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests."""
    start_time = 0  # Would use actual time
    
    # Log request
    logger.info(f"{request.method} {request.url}")
    
    # Process request
    response = await call_next(request)
    
    # Log response
    process_time = 0  # Would calculate actual time
    logger.info(f"{request.method} {request.url} - {response.status_code} - {process_time:.3f}s")
    
    # Add custom headers
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-API-Version"] = settings.app_version
    
    return response


# Main entry point
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug",
        access_log=True
    )