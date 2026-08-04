"""
Unit tests for Rate Limiter logic.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict

# Global storage for rate limits
rate_limits: Dict[str, Dict] = {}

class RateLimiter:
    """Token Bucket rate limiter implementation."""
    
    def __init__(self, ip_limit: int = 5, ip_window: int = 10):
        self.ip_limit = ip_limit
        self.ip_window = ip_window
    
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
        
        # Decrement tokens for each request
        if rate_limits[client_key]["tokens"] > 0:
            rate_limits[client_key]["tokens"] -= 1
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


def test_rate_limiter_logic():
    """Test rate limiter logic: 5 requests succeed, 6th fails."""
    rate_limiter = RateLimiter(ip_limit=5, ip_window=10)
    client_key = "test_client"
    
    # Manually set initial tokens
    rate_limits[client_key] = {
        "tokens": 5,
        "last_updated": datetime.now(),
        "requests": 0
    }
    
    # Send 5 requests (should succeed)
    for _ in range(5):
        assert rate_limiter._check_rate_limit(client_key)
    
    # Send 6th request (should fail)
    assert not rate_limiter._check_rate_limit(client_key)
    
    # Reset the rate limiter by setting tokens back to 5
    rate_limits[client_key]["tokens"] = 5
    rate_limits[client_key]["last_updated"] = datetime.now()
    
    # Send another request (should succeed again)
    assert rate_limiter._check_rate_limit(client_key)


if __name__ == "__main__":
    test_rate_limiter_logic()
    print("All tests passed!")