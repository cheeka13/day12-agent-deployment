from fastapi import Header, HTTPException
from .config import settings
import hashlib


def verify_api_key(x_api_key: str = Header(..., description="API Key for authentication")) -> str:
    """
    Verify API key from X-API-Key header.
    
    Args:
        x_api_key: API key from request header
        
    Returns:
        user_id: Unique identifier for the user
        
    Raises:
        HTTPException: 401 if key is missing or invalid
    """
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Include header: X-API-Key: <your-key>",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    # Verify against configured API key
    if x_api_key != settings.AGENT_API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    # Generate user_id from API key (hash for privacy)
    # In production, you'd look up user_id from database
    user_id = hashlib.sha256(x_api_key.encode()).hexdigest()[:16]
    
    return user_id