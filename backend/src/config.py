"""
Configuration management for the Bylaw Database API.
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Application settings
    app_name: str = "Bylaw Database API"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(default="development", description="Environment (development, staging, production)")
    
    # API settings
    api_v1_str: str = "/api/v1"
    allowed_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"],
        description="Allowed CORS origins"
    )
    
    # Supabase settings
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_anon_key: str = Field(..., description="Supabase anonymous key")
    supabase_service_key: Optional[str] = Field(None, description="Supabase service role key for admin operations")
    
    # Storage settings
    storage_backend: str = Field(default="supabase", description="Storage backend (supabase, s3, local)")
    storage_bucket_name: str = Field(default="source-documents", description="Storage bucket name")
    local_storage_path: Optional[str] = Field(default="./storage", description="Local storage path")
    
    # S3 settings (optional)
    s3_endpoint_url: Optional[str] = Field(None, description="S3 endpoint URL")
    s3_access_key_id: Optional[str] = Field(None, description="S3 access key ID")
    s3_secret_access_key: Optional[str] = Field(None, description="S3 secret access key")
    s3_region: Optional[str] = Field(default="us-east-1", description="S3 region")
    
    # Security settings
    secret_key: str = Field(..., description="Secret key for JWT tokens")
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=30, description="Access token expiration time")
    
    # Scraping settings
    scraper_user_agent: str = Field(
        default="BylawDB/1.0 (https://bylawdb.com; contact@bylawdb.com)",
        description="User agent for web scraping"
    )
    scraper_timeout: int = Field(default=30, description="Scraper timeout in seconds")
    scraper_max_retries: int = Field(default=3, description="Maximum scraper retries")
    
    # Redis settings (for Celery)
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis URL")
    
    # Pagination settings
    default_page_size: int = Field(default=20, description="Default page size")
    max_page_size: int = Field(default=100, description="Maximum page size")
    
    @validator("allowed_origins", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @property
    def supabase_key(self) -> str:
        """Get the appropriate Supabase key based on context."""
        return self.supabase_service_key or self.supabase_anon_key


# Create global settings instance
settings = Settings()