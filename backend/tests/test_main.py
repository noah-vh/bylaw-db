"""
Test cases for the main FastAPI application.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Mock the Supabase client before importing the app
with patch('src.utils.supabase_client.supabase_manager'):
    from src.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert data["message"] == "Welcome to the Bylaw Database API"


def test_health_endpoint():
    """Test the health check endpoint."""
    with patch('src.utils.supabase_client.supabase_manager.health_check_all') as mock_health:
        mock_health.return_value = {"anon": True, "service": True}
        
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "checks" in data


def test_api_info_endpoint():
    """Test the API info endpoint."""
    response = client.get("/api/v1/info")
    assert response.status_code == 200
    
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "endpoints" in data


def test_cors_headers():
    """Test CORS headers are present."""
    response = client.options("/")
    assert response.status_code == 200
    # Note: In real tests, you'd check for actual CORS headers


def test_404_handling():
    """Test 404 error handling."""
    response = client.get("/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_exception_handling():
    """Test exception handling."""
    # This would test the custom exception handlers
    pass


def test_openapi_schema():
    """Test OpenAPI schema generation."""
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    
    schema = response.json()
    assert "info" in schema
    assert "paths" in schema
    assert "components" in schema


def test_request_logging():
    """Test request logging middleware."""
    response = client.get("/")
    
    # Check custom headers
    assert "X-API-Version" in response.headers
    assert "X-Process-Time" in response.headers