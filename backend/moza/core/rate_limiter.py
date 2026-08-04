"""
Rate Limiter for Moza API protection using Token Bucket algorithm.
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

# Default rate limits
DEFAULT_IP_LIMIT = 60  # requests per minute
DEFAULT_IP_WINDOW = 60  # seconds
DEFAULT_USER_LIMIT = 10  # requests per minute for authenticated users
DEFAULT_USER_WINDOW = 60  # seconds

# In-memory storage for rate limits
rate_limits: Dict[str, Dict] = {}

class RateLimiter:
    """Token Bucket rate limiter implementation."""
    
    def __init__(self, ip_limit: int = DEFAULT_IP_LIMIT, ip_window: int = DEFAULT_IP_WINDOW,
                 user_limit: int = DEFAULT_USER_LIMIT, user_window: int = DEFAULT_USER_WINDOW):
        self.ip_limit = ip_limit
        self.ip_window = ip_window
        self.user_limit = user_limit
        self.user_window = user_window
    
    def _get_client_key(self, request: Request) -> str:
        """Extract client IP or session ID for rate limiting."""
        client_ip = request.client.host
        if request.headers.get("Authorization"):
            # Use session ID if authenticated
            return f"user_{client_ip}"
        return client_ip
    
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
    
    async def __call__(self, request: Request, call_next):
        """FastAPI middleware to enforce rate limiting."""
        client_key = self._get_client_key(request)
        
        # Exempt health check endpoints
        if request.url.path == "/health":
            return await call_next(request)
            
        self._update_rate_limit(client_key)
        if rate_limits[client_key]["tokens"] <= 0:
            retry_after = self.ip_window - (datetime.now() - rate_limits[client_key]["last_updated"]).total_seconds()
            raise HTTPException(status_code=429, detail="Too Many Requests", headers={
                "Retry-After": str(int(retry_after))
            })
        
        return await call_next(request)

# Initialize rate limiter
rate_limiter = RateLimiter()