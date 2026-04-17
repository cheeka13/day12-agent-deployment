import json
import logging
import redis
from fastapi import FastAPI, Depends, HTTPException, Request
from pydantic import BaseModel
from .config import settings
from .auth import verify_api_key
from .rate_limiter import check_rate_limit
from .cost_guard import check_budget

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger(__name__)

# Redis connection
try:
    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
except Exception as e:
    logger.warning(f"Redis connection failed: {e}. Running without Redis.")
    r = None

app = FastAPI(
    title="Production AI Agent",
    version="1.0.0",
    description="Production-ready AI agent with auth, rate limiting, and cost guard"
)


class AskRequest(BaseModel):
    question: str
    user_id: str = None


@app.get("/")
def root():
    return {
        "app": "Production AI Agent",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "status": "running"
    }


@app.get("/health")
def health():
    """
    Liveness probe: Agent còn sống không?
    Platform restart nếu trả về non-200.
    """
    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT
    }


@app.get("/ready")
def ready():
    """
    Readiness probe: Agent sẵn sàng nhận traffic chưa?
    Check Redis connection.
    """
    if r is None:
        raise HTTPException(
            status_code=503,
            detail="Redis not available"
        )
    
    try:
        r.ping()
        return {"status": "ready", "redis": "connected"}
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Redis connection failed: {str(e)}"
        )


@app.post("/ask")
async def ask(
    request: Request,
    body: AskRequest,
    user_id: str = Depends(verify_api_key),
    _rate_limit: None = Depends(check_rate_limit),
    _budget: None = Depends(check_budget)
):
    """
    Protected endpoint: Trả lời câu hỏi với conversation history.
    Requires: X-API-Key header
    Rate limited: 10 req/min per user
    Cost guarded: $10/month per user
    """
    question = body.question
    
    if not question or not question.strip():
        raise HTTPException(status_code=422, detail="Question cannot be empty")
    
    # Log request (không log sensitive data)
    logger.info(json.dumps({
        "event": "agent_request",
        "user_id": user_id,
        "question_length": len(question),
        "client_ip": request.client.host if request.client else "unknown"
    }))
    
    # 1. Get conversation history from Redis
    history_key = f"history:{user_id}"
    history = []
    if r:
        try:
            history_raw = r.lrange(history_key, -5, -1)  # Last 5 messages
            history = [json.loads(msg) for msg in history_raw]
        except Exception as e:
            logger.warning(f"Failed to get history: {e}")
    
    # 2. Call LLM (mock for now)
    # TODO: Replace with real OpenAI call if OPENAI_API_KEY is set
    if settings.OPENAI_API_KEY:
        # Real OpenAI call would go here
        answer = f"[Real LLM] Answer to: {question}"
    else:
        # Mock response
        answer = f"Mock response: I received your question '{question}'. This is a demo response."
    
    # 3. Save to Redis
    if r:
        try:
            conversation = json.dumps({"question": question, "answer": answer})
            r.rpush(history_key, conversation)
            r.expire(history_key, 86400)  # Expire after 24 hours
        except Exception as e:
            logger.warning(f"Failed to save history: {e}")
    
    # Log response
    logger.info(json.dumps({
        "event": "agent_response",
        "user_id": user_id,
        "answer_length": len(answer)
    }))
    
    # 4. Return response
    return {
        "question": question,
        "answer": answer,
        "user_id": user_id,
        "model": settings.LLM_MODEL,
        "history_count": len(history)
    }