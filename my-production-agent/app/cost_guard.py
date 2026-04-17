import redis
from datetime import datetime
from fastapi import HTTPException, Request
from .config import settings

# Redis connection
try:
    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
except Exception:
    r = None


def check_budget(request: Request, user_id: str = None):
    """
    Check monthly spending budget per user.
    
    Args:
        request: FastAPI request object
        user_id: User identifier (from auth dependency)
        
    Raises:
        HTTPException: 402 Payment Required if budget exceeded
    """
    if not r:
        # If Redis unavailable, skip cost guard (fail open)
        return
    
    # Use user_id from request state (set by auth dependency)
    if not user_id and hasattr(request.state, "user_id"):
        user_id = request.state.user_id
    
    if not user_id:
        return
    
    # Get current month key
    month_key = datetime.now().strftime("%Y-%m")
    key = f"budget:{user_id}:{month_key}"
    
    # Estimated cost per request (adjust based on your LLM usage)
    estimated_cost = 0.01  # $0.01 per request
    
    try:
        # Get current spending
        current_spending = float(r.get(key) or 0)
        
        # Check if adding this request would exceed budget
        if current_spending + estimated_cost > settings.MONTHLY_BUDGET_USD:
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "Monthly budget exceeded",
                    "budget_usd": settings.MONTHLY_BUDGET_USD,
                    "spent_usd": current_spending,
                    "remaining_usd": max(0, settings.MONTHLY_BUDGET_USD - current_spending),
                    "message": "Please upgrade your plan or wait until next month"
                },
                headers={
                    "X-Budget-Limit": str(settings.MONTHLY_BUDGET_USD),
                    "X-Budget-Spent": str(current_spending),
                    "X-Budget-Remaining": str(max(0, settings.MONTHLY_BUDGET_USD - current_spending))
                }
            )
        
        # Increment spending
        r.incrbyfloat(key, estimated_cost)
        
        # Set expiry to 32 days (covers longest month + buffer)
        r.expire(key, 32 * 24 * 3600)
        
    except redis.RedisError as e:
        # If Redis fails, log and allow request (fail open)
        import logging
        logging.warning(f"Cost guard Redis error: {e}")
        return