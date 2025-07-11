"""
Configuration management for the bylaw-db application.
"""

import os
from typing import Optional
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Database settings
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "bylaw_db"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "password"
    
    # Supabase settings
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    
    # Redis settings
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Scraping settings
    SCRAPER_USER_AGENT: str = "Mozilla/5.0 (compatible; BylawDB/1.0; +https://bylawdb.com/bot)"
    MAX_CONCURRENT_SCRAPERS: int = 5
    REQUEST_DELAY: float = 1.0
    
    # Storage settings
    STORAGE_BUCKET: str = "source-documents"
    
    # Security settings
    SECRET_KEY: str = "your-secret-key-change-this"
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings (singleton)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings