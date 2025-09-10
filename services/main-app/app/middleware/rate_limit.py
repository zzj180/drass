from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict
from datetime import datetime, timedelta
import asyncio

from app.core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple rate limiting middleware
    In production, use Redis for distributed rate limiting
    """
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = {}
        self.cleanup_task = None
        
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and docs
        if request.url.path in ["/health", "/metrics", "/api/docs", "/api/redoc", "/api/openapi.json"]:
            return await call_next(request)
        
        # Get client identifier (IP address or user ID)
        client_id = request.client.host if request.client else "unknown"
        
        # Check if user is authenticated (has more lenient limits)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # Authenticated users get 2x the rate limit
            rate_limit = self.requests_per_minute * 2
        else:
            rate_limit = self.requests_per_minute
        
        # Check rate limit
        now = datetime.utcnow()
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        # Remove old requests outside the window
        cutoff = now - timedelta(minutes=1)
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > cutoff
        ]
        
        # Check if limit is exceeded
        if len(self.requests[client_id]) >= rate_limit:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Too Many Requests",
                    "message": f"Rate limit exceeded. Maximum {rate_limit} requests per minute.",
                    "retry_after": 60
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(rate_limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int((now + timedelta(minutes=1)).timestamp()))
                }
            )
        
        # Add current request
        self.requests[client_id].append(now)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = rate_limit - len(self.requests[client_id])
        response.headers["X-RateLimit-Limit"] = str(rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int((now + timedelta(minutes=1)).timestamp()))
        
        # Schedule cleanup if not already scheduled
        if not self.cleanup_task or self.cleanup_task.done():
            self.cleanup_task = asyncio.create_task(self._cleanup_old_requests())
        
        return response
    
    async def _cleanup_old_requests(self):
        """
        Periodically clean up old request records to prevent memory leak
        """
        await asyncio.sleep(300)  # Clean up every 5 minutes
        
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=2)
        
        # Remove clients with no recent requests
        clients_to_remove = []
        for client_id, requests in self.requests.items():
            # Remove old requests
            self.requests[client_id] = [
                req_time for req_time in requests
                if req_time > cutoff
            ]
            
            # Mark empty clients for removal
            if not self.requests[client_id]:
                clients_to_remove.append(client_id)
        
        # Remove empty clients
        for client_id in clients_to_remove:
            del self.requests[client_id]