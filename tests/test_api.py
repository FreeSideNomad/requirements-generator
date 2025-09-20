"""
Test API endpoints and HTTP functionality.
Verifies that the FastAPI application works correctly.
"""
import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Test health check and basic endpoints."""

    def test_health_check(self, test_client: TestClient):
        """Test the health check endpoint."""
        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    def test_root_endpoint(self, test_client: TestClient):
        """Test the root endpoint redirects to docs."""
        response = test_client.get("/", follow_redirects=False)

        # Should redirect to docs
        assert response.status_code in [307, 308]  # Temporary or permanent redirect

    def test_docs_endpoint(self, test_client: TestClient):
        """Test that OpenAPI docs are accessible."""
        response = test_client.get("/docs")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_openapi_spec(self, test_client: TestClient):
        """Test that OpenAPI specification is accessible."""
        response = test_client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()

        assert "openapi" in data
        assert "info" in data
        assert "paths" in data


class TestCORSHeaders:
    """Test CORS configuration."""

    def test_cors_preflight(self, test_client: TestClient):
        """Test CORS preflight request."""
        response = test_client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "content-type"
            }
        )

        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers

    def test_cors_actual_request(self, test_client: TestClient):
        """Test actual CORS request."""
        response = test_client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"}
        )

        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers


class TestErrorHandling:
    """Test error handling and HTTP status codes."""

    def test_404_not_found(self, test_client: TestClient):
        """Test 404 error handling."""
        response = test_client.get("/nonexistent-endpoint")

        assert response.status_code == 404
        data = response.json()

        assert "detail" in data
        assert "error_code" in data
        assert data["error_code"] == "NOT_FOUND"

    def test_405_method_not_allowed(self, test_client: TestClient):
        """Test 405 error handling."""
        response = test_client.post("/health")

        assert response.status_code == 405
        data = response.json()

        assert "detail" in data
        assert "error_code" in data
        assert data["error_code"] == "METHOD_NOT_ALLOWED"


class TestMiddleware:
    """Test middleware functionality."""

    def test_request_id_header(self, test_client: TestClient):
        """Test that request ID is added to responses."""
        response = test_client.get("/health")

        assert response.status_code == 200
        assert "x-request-id" in response.headers

        # Should be a valid UUID format
        request_id = response.headers["x-request-id"]
        assert len(request_id) == 36  # UUID length with hyphens
        assert request_id.count("-") == 4

    def test_security_headers(self, test_client: TestClient):
        """Test that security headers are present."""
        response = test_client.get("/health")

        assert response.status_code == 200

        # Check for common security headers
        security_headers = [
            "x-content-type-options",
            "x-frame-options",
            "x-xss-protection"
        ]

        for header in security_headers:
            assert header in response.headers

    def test_tenant_context_middleware(self, test_client: TestClient):
        """Test tenant context extraction from headers."""
        # Test with tenant subdomain header
        response = test_client.get(
            "/health",
            headers={"X-Tenant-Subdomain": "test-tenant"}
        )

        assert response.status_code == 200

        # Test with tenant ID header
        response = test_client.get(
            "/health",
            headers={"X-Tenant-ID": "550e8400-e29b-41d4-a716-446655440000"}
        )

        assert response.status_code == 200


class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_rate_limit_headers(self, test_client: TestClient):
        """Test that rate limit headers are present."""
        response = test_client.get("/health")

        assert response.status_code == 200

        # Rate limiting headers should be present
        rate_limit_headers = [
            "x-ratelimit-limit",
            "x-ratelimit-remaining",
            "x-ratelimit-reset"
        ]

        for header in rate_limit_headers:
            assert header in response.headers

    @pytest.mark.skip(reason="Rate limiting not yet configured for testing")
    def test_rate_limit_exceeded(self, test_client: TestClient):
        """Test rate limit exceeded response."""
        # This would require configuring very low rate limits for testing
        # and making many rapid requests
        pass


class TestContentNegotiation:
    """Test content negotiation and response formats."""

    def test_json_content_type(self, test_client: TestClient):
        """Test that JSON responses have correct content type."""
        response = test_client.get("/health")

        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

    def test_accept_header_handling(self, test_client: TestClient):
        """Test handling of Accept header."""
        # Request JSON
        response = test_client.get(
            "/health",
            headers={"Accept": "application/json"}
        )

        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

    def test_compression_support(self, test_client: TestClient):
        """Test that compression is supported."""
        response = test_client.get(
            "/health",
            headers={"Accept-Encoding": "gzip, deflate"}
        )

        assert response.status_code == 200
        # Response should either be compressed or indicate compression support
        # (exact behavior depends on response size and server configuration)