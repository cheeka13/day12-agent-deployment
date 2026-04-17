import time
import redis
from fastapi import HTTPException, Request
from .config import settings

# Redis connection
try:
    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
except Exception:
    r = None


def check_rate_limit(request: Request, user_id: str = None):
    """
    Sliding window rate limiter using Redis.
    
    Args:
        request: FastAPI request object
        user_id: User identifier (from auth dependency)
        
    Raises:
        HTTPException: 429 if rate limit exceeded
    """
    if not r:
        # If Redis unavailable, skip rate limiting (fail open)
        return
    
    # Use user_id from request state (set by auth dependency)
    if not user_id and hasattr(request.state, "user_id"):
        user_id = request.state.user_id
    
    if not user_id:
        # Fallback to IP-based limiting
        user_id = request.client.host if request.client else "unknown"
    
    now = time.time()
    window_seconds = 60
    max_requests = settings.RATE_LIMIT_PER_MINUTE
    
    key = f"rate_limit:{user_id}"
    
    try:
        # Remove old entries outside the window
        r.zremrangebyscore(key, 0, now - window_seconds)
        
        # Count requests in current window
        current_count = r.zcard(key)
        
        if current_count >= max_requests:
            # Get oldest request timestamp to calculate retry_after
            oldest = r.zrange(key, 0, 0, withscores=True)
            if oldest:
                retry_after = int(oldest[0][1] + window_seconds - now) + 1
            else:
                retry_after = window_seconds
            
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "limit": max_requests,
                    "window_seconds": window_seconds,
                    "retry_after_seconds": retry_after
                },
                headers={
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(now + window_seconds)),
                    "Retry-After": str(retry_after)
                }
            )
        
        # Add current request
        r.zadd(key, {str(now): now})
        r.expire(key, window_seconds + 10)  # Cleanup after window + buffer
        
        # Set rate limit headers
        remaining = max_requests - current_count - 1
        
    except redis.RedisError as e:
        # If Redis fails, log and allow request (fail open)
        import logging
        logging.warning(f"Rate limiter Redis error: {e}")
        return