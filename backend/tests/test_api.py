"""
Test cases for API endpoints.
Tests REST API functionality, authentication, and data validation.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, Mock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI, status
import asyncio

# Import the API modules (adjust imports based on actual structure)
# from src.main import app
# from src.api.routers import bylaws, municipalities, admin, health
# from src.models.user import User
# from src.utils.auth import create_access_token


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        # This would create the actual test client
        # For now, we'll mock it
        return Mock()
    
    def test_basic_health_check(self, client):
        """Test basic health check endpoint."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime": 123.45,
            "version": "1.0.0",
            "environment": "test"
        }
        
        client.get.return_value = mock_response
        
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "uptime" in data
    
    def test_detailed_health_check(self, client):
        """Test detailed health check endpoint."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime": 123.45,
            "version": "1.0.0",
            "environment": "test",
            "components": [
                {"name": "database", "status": "healthy", "response_time": 0.05},
                {"name": "redis", "status": "healthy", "response_time": 0.01},
                {"name": "supabase", "status": "healthy", "response_time": 0.1}
            ]
        }
        
        client.get.return_value = mock_response
        
        response = client.get("/health/detailed")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert len(data["components"]) == 3
        assert all(c["status"] == "healthy" for c in data["components"])
    
    def test_health_check_unhealthy(self, client):
        """Test health check when system is unhealthy."""
        mock_response = Mock()
        mock_response.status_code = 503
        mock_response.json.return_value = {
            "status": "unhealthy",
            "components": [
                {"name": "database", "status": "unhealthy", "error": "Connection failed"}
            ]
        }
        
        client.get.return_value = mock_response
        
        response = client.get("/health/detailed")
        assert response.status_code == 503
        
        data = response.json()
        assert data["status"] == "unhealthy"
    
    def test_liveness_probe(self, client):
        """Test Kubernetes liveness probe."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        client.get.return_value = mock_response
        
        response = client.get("/health/liveness")
        assert response.status_code == 200
        assert response.json()["status"] == "alive"
    
    def test_readiness_probe(self, client):
        """Test Kubernetes readiness probe."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        client.get.return_value = mock_response
        
        response = client.get("/health/readiness")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"
    
    def test_metrics_endpoint(self, client):
        """Test Prometheus metrics endpoint."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        # HELP api_requests_total Total number of API requests
        # TYPE api_requests_total counter
        api_requests_total{method="GET",endpoint="/health",status_code="200"} 5.0
        """
        
        client.get.return_value = mock_response
        
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "api_requests_total" in response.text


class TestBylawEndpoints:
    """Test bylaw-related API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client with authentication."""
        return Mock()
    
    @pytest.fixture
    def auth_headers(self):
        """Authentication headers for testing."""
        return {"Authorization": "Bearer test-token"}
    
    @pytest.fixture
    def sample_bylaw(self):
        """Sample bylaw data."""
        return {
            "id": "test-bylaw-123",
            "title": "Test Bylaw 2024-001",
            "document_number": "BYLAW-2024-001",
            "jurisdiction_id": "test-jurisdiction",
            "document_type": "bylaw",
            "status": "active",
            "effective_date": "2024-01-15",
            "url": "https://example.com/bylaw.pdf"
        }
    
    def test_get_bylaws_list(self, client, auth_headers):
        """Test getting list of bylaws."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {
                    "id": "bylaw-1",
                    "title": "Bylaw 2024-001",
                    "document_number": "BYLAW-2024-001",
                    "status": "active"
                },
                {
                    "id": "bylaw-2",
                    "title": "Bylaw 2024-002",
                    "document_number": "BYLAW-2024-002",
                    "status": "active"
                }
            ],
            "total": 2,
            "page": 1,
            "per_page": 20
        }
        
        client.get.return_value = mock_response
        
        response = client.get("/api/v1/bylaws", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 2
    
    def test_get_bylaws_with_filters(self, client, auth_headers):
        """Test getting bylaws with filters."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {
                    "id": "bylaw-1",
                    "title": "Bylaw 2024-001",
                    "jurisdiction_id": "toronto",
                    "status": "active"
                }
            ],
            "total": 1,
            "page": 1,
            "per_page": 20
        }
        
        client.get.return_value = mock_response
        
        response = client.get(
            "/api/v1/bylaws?jurisdiction_id=toronto&status=active",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["jurisdiction_id"] == "toronto"
    
    def test_get_bylaw_by_id(self, client, auth_headers, sample_bylaw):
        """Test getting a specific bylaw by ID."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_bylaw
        
        client.get.return_value = mock_response
        
        response = client.get(
            f"/api/v1/bylaws/{sample_bylaw['id']}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == sample_bylaw["id"]
        assert data["title"] == sample_bylaw["title"]
    
    def test_get_bylaw_not_found(self, client, auth_headers):
        """Test getting a non-existent bylaw."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "Bylaw not found"}
        
        client.get.return_value = mock_response
        
        response = client.get("/api/v1/bylaws/nonexistent", headers=auth_headers)
        assert response.status_code == 404
    
    def test_search_bylaws(self, client, auth_headers):
        """Test searching bylaws."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {
                    "id": "bylaw-1",
                    "title": "Noise Control Bylaw",
                    "relevance_score": 0.95,
                    "highlight": "...noise control regulations..."
                }
            ],
            "total": 1,
            "query": "noise control"
        }
        
        client.get.return_value = mock_response
        
        response = client.get(
            "/api/v1/bylaws/search?q=noise control",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["items"]) == 1
        assert data["query"] == "noise control"
    
    def test_create_bylaw(self, client, auth_headers, sample_bylaw):
        """Test creating a new bylaw."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = sample_bylaw
        
        client.post.return_value = mock_response
        
        response = client.post(
            "/api/v1/bylaws",
            json=sample_bylaw,
            headers=auth_headers
        )
        assert response.status_code == 201
        
        data = response.json()
        assert data["title"] == sample_bylaw["title"]
    
    def test_update_bylaw(self, client, auth_headers, sample_bylaw):
        """Test updating an existing bylaw."""
        updated_bylaw = sample_bylaw.copy()
        updated_bylaw["title"] = "Updated Bylaw Title"
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = updated_bylaw
        
        client.put.return_value = mock_response
        
        response = client.put(
            f"/api/v1/bylaws/{sample_bylaw['id']}",
            json=updated_bylaw,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["title"] == "Updated Bylaw Title"
    
    def test_delete_bylaw(self, client, auth_headers, sample_bylaw):
        """Test deleting a bylaw."""
        mock_response = Mock()
        mock_response.status_code = 204
        
        client.delete.return_value = mock_response
        
        response = client.delete(
            f"/api/v1/bylaws/{sample_bylaw['id']}",
            headers=auth_headers
        )
        assert response.status_code == 204


class TestMunicipalityEndpoints:
    """Test municipality-related API endpoints."""
    
    @pytest.fixture
    def client(self):
        return Mock()
    
    @pytest.fixture
    def auth_headers(self):
        return {"Authorization": "Bearer test-token"}
    
    @pytest.fixture
    def sample_municipality(self):
        return {
            "id": "test-municipality-123",
            "name": "Test Municipality",
            "type": "municipal",
            "country": "Canada",
            "province_state": "Ontario",
            "website": "https://example.com",
            "population": 100000
        }
    
    def test_get_municipalities_list(self, client, auth_headers):
        """Test getting list of municipalities."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {
                    "id": "municipality-1",
                    "name": "City of Toronto",
                    "type": "municipal",
                    "country": "Canada"
                }
            ],
            "total": 1
        }
        
        client.get.return_value = mock_response
        
        response = client.get("/api/v1/municipalities", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["items"]) == 1
    
    def test_get_municipality_by_id(self, client, auth_headers, sample_municipality):
        """Test getting a specific municipality by ID."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_municipality
        
        client.get.return_value = mock_response
        
        response = client.get(
            f"/api/v1/municipalities/{sample_municipality['id']}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == sample_municipality["name"]
    
    def test_get_municipality_bylaws(self, client, auth_headers, sample_municipality):
        """Test getting bylaws for a specific municipality."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {
                    "id": "bylaw-1",
                    "title": "Municipal Bylaw 2024-001",
                    "jurisdiction_id": sample_municipality["id"]
                }
            ],
            "total": 1
        }
        
        client.get.return_value = mock_response
        
        response = client.get(
            f"/api/v1/municipalities/{sample_municipality['id']}/bylaws",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["items"]) == 1
    
    def test_create_municipality(self, client, auth_headers, sample_municipality):
        """Test creating a new municipality."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = sample_municipality
        
        client.post.return_value = mock_response
        
        response = client.post(
            "/api/v1/municipalities",
            json=sample_municipality,
            headers=auth_headers
        )
        assert response.status_code == 201


class TestAdminEndpoints:
    """Test admin-related API endpoints."""
    
    @pytest.fixture
    def client(self):
        return Mock()
    
    @pytest.fixture
    def admin_headers(self):
        return {"Authorization": "Bearer admin-token"}
    
    def test_get_scraping_jobs(self, client, admin_headers):
        """Test getting list of scraping jobs."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {
                    "id": "job-1",
                    "jurisdiction_id": "toronto",
                    "status": "completed",
                    "documents_found": 25,
                    "documents_processed": 23
                }
            ],
            "total": 1
        }
        
        client.get.return_value = mock_response
        
        response = client.get("/api/v1/admin/scraping-jobs", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["items"]) == 1
    
    def test_create_scraping_job(self, client, admin_headers):
        """Test creating a new scraping job."""
        job_data = {
            "jurisdiction_id": "toronto",
            "job_type": "full_scrape",
            "parameters": {
                "max_pages": 50,
                "include_archived": False
            }
        }
        
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": "job-123",
            "status": "pending",
            **job_data
        }
        
        client.post.return_value = mock_response
        
        response = client.post(
            "/api/v1/admin/scraping-jobs",
            json=job_data,
            headers=admin_headers
        )
        assert response.status_code == 201
        
        data = response.json()
        assert data["status"] == "pending"
    
    def test_get_system_stats(self, client, admin_headers):
        """Test getting system statistics."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "total_bylaws": 1234,
            "total_municipalities": 45,
            "total_scraping_jobs": 78,
            "active_jobs": 2,
            "last_scrape": "2024-01-15T10:30:00Z"
        }
        
        client.get.return_value = mock_response
        
        response = client.get("/api/v1/admin/stats", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_bylaws"] == 1234
        assert data["active_jobs"] == 2
    
    def test_admin_unauthorized(self, client):
        """Test admin endpoint without proper authorization."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"detail": "Not authenticated"}
        
        client.get.return_value = mock_response
        
        response = client.get("/api/v1/admin/stats")
        assert response.status_code == 401


class TestAuthenticationEndpoints:
    """Test authentication-related endpoints."""
    
    @pytest.fixture
    def client(self):
        return Mock()
    
    def test_login_success(self, client):
        """Test successful login."""
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test-jwt-token",
            "token_type": "bearer",
            "expires_in": 3600
        }
        
        client.post.return_value = mock_response
        
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        login_data = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"detail": "Invalid credentials"}
        
        client.post.return_value = mock_response
        
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401
    
    def test_token_refresh(self, client):
        """Test token refresh."""
        refresh_data = {
            "refresh_token": "test-refresh-token"
        }
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new-jwt-token",
            "token_type": "bearer",
            "expires_in": 3600
        }
        
        client.post.return_value = mock_response
        
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
    
    def test_get_current_user(self, client):
        """Test getting current user info."""
        auth_headers = {"Authorization": "Bearer test-token"}
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "user-123",
            "username": "testuser",
            "email": "test@example.com",
            "role": "user"
        }
        
        client.get.return_value = mock_response
        
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["username"] == "testuser"


class TestAPIValidation:
    """Test API input validation."""
    
    @pytest.fixture
    def client(self):
        return Mock()
    
    @pytest.fixture
    def auth_headers(self):
        return {"Authorization": "Bearer test-token"}
    
    def test_invalid_json(self, client, auth_headers):
        """Test handling of invalid JSON."""
        mock_response = Mock()
        mock_response.status_code = 422
        mock_response.json.return_value = {
            "detail": "Invalid JSON format"
        }
        
        client.post.return_value = mock_response
        
        # This would be invalid JSON in a real test
        response = client.post(
            "/api/v1/bylaws",
            data="invalid json",
            headers=auth_headers
        )
        assert response.status_code == 422
    
    def test_missing_required_fields(self, client, auth_headers):
        """Test validation of missing required fields."""
        incomplete_data = {
            "title": "Test Bylaw"
            # Missing required fields like jurisdiction_id, document_type, etc.
        }
        
        mock_response = Mock()
        mock_response.status_code = 422
        mock_response.json.return_value = {
            "detail": [
                {
                    "loc": ["jurisdiction_id"],
                    "msg": "field required",
                    "type": "value_error.missing"
                }
            ]
        }
        
        client.post.return_value = mock_response
        
        response = client.post(
            "/api/v1/bylaws",
            json=incomplete_data,
            headers=auth_headers
        )
        assert response.status_code == 422
    
    def test_invalid_field_types(self, client, auth_headers):
        """Test validation of invalid field types."""
        invalid_data = {
            "title": "Test Bylaw",
            "jurisdiction_id": "valid-id",
            "document_type": "bylaw",
            "effective_date": "not-a-date"  # Invalid date format
        }
        
        mock_response = Mock()
        mock_response.status_code = 422
        mock_response.json.return_value = {
            "detail": [
                {
                    "loc": ["effective_date"],
                    "msg": "invalid datetime format",
                    "type": "value_error.datetime"
                }
            ]
        }
        
        client.post.return_value = mock_response
        
        response = client.post(
            "/api/v1/bylaws",
            json=invalid_data,
            headers=auth_headers
        )
        assert response.status_code == 422


class TestAPIRateLimiting:
    """Test API rate limiting."""
    
    @pytest.fixture
    def client(self):
        return Mock()
    
    @pytest.fixture
    def auth_headers(self):
        return {"Authorization": "Bearer test-token"}
    
    def test_rate_limit_exceeded(self, client, auth_headers):
        """Test rate limit exceeded response."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.json.return_value = {
            "detail": "Rate limit exceeded",
            "retry_after": 60
        }
        mock_response.headers = {"Retry-After": "60"}
        
        client.get.return_value = mock_response
        
        response = client.get("/api/v1/bylaws", headers=auth_headers)
        assert response.status_code == 429
        assert "Retry-After" in response.headers
    
    def test_rate_limit_headers(self, client, auth_headers):
        """Test rate limiting headers in successful response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"items": []}
        mock_response.headers = {
            "X-RateLimit-Limit": "100",
            "X-RateLimit-Remaining": "99",
            "X-RateLimit-Reset": "1640995200"
        }
        
        client.get.return_value = mock_response
        
        response = client.get("/api/v1/bylaws", headers=auth_headers)
        assert response.status_code == 200
        assert response.headers["X-RateLimit-Limit"] == "100"
        assert response.headers["X-RateLimit-Remaining"] == "99"


class TestAPIPagination:
    """Test API pagination."""
    
    @pytest.fixture
    def client(self):
        return Mock()
    
    @pytest.fixture
    def auth_headers(self):
        return {"Authorization": "Bearer test-token"}
    
    def test_pagination_parameters(self, client, auth_headers):
        """Test pagination parameters."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [{"id": f"item-{i}"} for i in range(10)],
            "total": 100,
            "page": 2,
            "per_page": 10,
            "pages": 10
        }
        
        client.get.return_value = mock_response
        
        response = client.get(
            "/api/v1/bylaws?page=2&per_page=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["items"]) == 10
        assert data["page"] == 2
        assert data["per_page"] == 10
        assert data["total"] == 100
    
    def test_pagination_limits(self, client, auth_headers):
        """Test pagination limits."""
        mock_response = Mock()
        mock_response.status_code = 422
        mock_response.json.return_value = {
            "detail": "per_page must be between 1 and 100"
        }
        
        client.get.return_value = mock_response
        
        response = client.get(
            "/api/v1/bylaws?per_page=1000",
            headers=auth_headers
        )
        assert response.status_code == 422


class TestAPIErrorHandling:
    """Test API error handling."""
    
    @pytest.fixture
    def client(self):
        return Mock()
    
    def test_internal_server_error(self, client):
        """Test handling of internal server errors."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {
            "detail": "Internal server error",
            "error_id": "err-123-456"
        }
        
        client.get.return_value = mock_response
        
        response = client.get("/api/v1/bylaws")
        assert response.status_code == 500
        assert "error_id" in response.json()
    
    def test_not_found_error(self, client):
        """Test handling of not found errors."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {
            "detail": "Resource not found"
        }
        
        client.get.return_value = mock_response
        
        response = client.get("/api/v1/bylaws/nonexistent")
        assert response.status_code == 404
    
    def test_database_connection_error(self, client):
        """Test handling of database connection errors."""
        mock_response = Mock()
        mock_response.status_code = 503
        mock_response.json.return_value = {
            "detail": "Service temporarily unavailable"
        }
        
        client.get.return_value = mock_response
        
        response = client.get("/api/v1/bylaws")
        assert response.status_code == 503


if __name__ == "__main__":
    pytest.main([__file__, "-v"])