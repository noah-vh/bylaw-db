#!/usr/bin/env python3
"""
Startup script for the Bylaw Database API.
"""
import os
import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import and run the application
if __name__ == "__main__":
    import uvicorn
    from src.config import settings
    
    # Load environment variables
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        print(f"Loading environment from: {env_file}")
    else:
        print("No .env file found. Using default settings.")
    
    # Run the application
    print(f"Starting {settings.app_name} v{settings.app_version}")
    print(f"Environment: {settings.environment}")
    print(f"Debug mode: {settings.debug}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug",
        access_log=True
    )