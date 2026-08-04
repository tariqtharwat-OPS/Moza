"""
Integration tests for Rate Limiter.
"""

import asyncio
import pytest
from fastapi import FastAPI, Request, HTTPException
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from typing import Dict

# Global storage for rate limits
rate_limits: Dict[str, Dict] = {}

class RateLimiter:
    """Token Bucket rate limiter implementation."""
    
    def __init__(self, ip_limit: int = 5, ip_window: int = 10):
        self.ip_limit = ip_limit
        self.ip_window = ip_window
    
    def _get_client_key(self, request) -> str:
        """Extract client IP for rate limiting."""
        return request.client.host
    
    def _update_rate_limit(self, client_key: str) -> None:
        """Update the rate limit data for a client."""
        if client_key not in rate_limits:
            rate_limits[client_key] = {
                "tokens": self.ip_limit,
                "last_updated": datetime.now(),
                "requests": 0
            }
        
        now = datetime.now()
        elapsed = (now - rate_limits[client_key]["last_updated"]).total_seconds()
        
        # Refill tokens based on elapsed time
        tokens_to_refill = int(elapsed / self.ip_window * self.ip_limit)
        rate_limits[client_key]["tokens"] = min(self.ip_limit, rate_limits[client_key]["tokens"] + tokens_to_refill)
        rate_limits[client_key]["last_updated"] = now
        rate_limits[client_key]["requests"] += 1
    
    def _check_rate_limit(self, client_key: str) -> bool:
        """Check if the client has exceeded the rate limit."""
        if client_key not in rate_limits:
            self._update_rate_limit(client_key)
            return True
        
        now = datetime.now()
        elapsed = (now - rate_limits[client_key]["last_updated"]).total_seconds()
        
        # Refill tokens based on elapsed time
        tokens_to_refill = int(elapsed / self.ip_window * self.ip_limit)
        rate_limits[client_key]["tokens"] = min(self.ip_limit, rate_limits[client_key]["tokens"] + tokens_to_refill)
        rate_limits[client_key]["last_updated"] = now
        
        if rate_limits[client_key]["tokens"] <= 0:
            return False
        
        rate_limits[client_key]["tokens"] -= 1
        rate_limits[client_key]["requests"] += 1
        return True
    
    async def __call__(self, request, call_next):
        """FastAPI middleware to enforce rate limiting."""
        client_key = self._get_client_key(request)
        
        self._update_rate_limit(client_key)
        if rate_limits[client_key]["tokens"] <= 0:
            retry_after = self.ip_window - (datetime.now() - rate_limits[client_key]["last_updated"]).total_seconds()
            raise HTTPException(status_code=429, detail="Too Many Requests", headers={
                "Retry-After": str(int(retry_after))
            })
        
        return await call_next(request)


@pytest.fixture
def test_app():
    """Create a test FastAPI app with rate limiter."""
    app = FastAPI()
    
    @app.get("/test")
    async def test_endpoint(request: Request):
        return {"message": "Success"}
    
    rate_limiter = RateLimiter(ip_limit=5, ip_window=10)
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