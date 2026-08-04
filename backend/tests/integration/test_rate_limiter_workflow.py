"""
Integration tests for Rate Limiter.
"""

import asyncio
import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from moza.core.rate_limiter import RateLimiter
from datetime import datetime, timedelta


@pytest.fixture
def test_app():
    """Create a test FastAPI app with rate limiter."""
    app = FastAPI()
    
    @app.get("/test")
    async def test_endpoint(request: Request):
        return {"message": "Success"}
    
    rate_limiter = RateLimiter(ip_limit=5, ip_window=10)  # 5 requests in 10 seconds
    app.middleware("http")(rate_limiter)
    
    return app


@pytest.fixture
def test_client(test_app):
    """Create a test client for the FastAPI app."""
    return TestClient(test_app)


@pytest.mark.asyncio
async def test_rate_limiter_workflow(test_client):
    """Test rate limiter workflow: 5 requests succeed, 6th fails."""
    
    # Send 5 requests (should succeed)
    for _ in range(5):
        response = test_client.get("/test")
        assert response.status_code == 200
    
    # Send 6th request (should fail)
    response = test_client.get("/test")
    assert response.status_code == 429
    assert "Too Many Requests" in response.text
    assert "Retry-After" in response.headers
    
    # Wait for the rate limit window to reset
    await asyncio.sleep(10)
    
    # Send another request (should succeed again)
    response = test_client.get("/test")
    assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])