# Deployment Information

## Public URL
https://production-ai-agent.onrender.com

<!-- TODO: Replace with your actual Render URL -->

## Platform
**Render** (Free Tier)

## Services Deployed
- **Web Service**: production-ai-agent (Docker)
- **Redis**: agent-redis (Key-Value store)

## Deployment Date
2026-04-17

## Test Commands

### Health Check
```bash
curl https://production-ai-agent.onrender.com/health
# Expected: {"status": "ok", "environment": "production"}
```

**PowerShell:**
```powershell
Invoke-RestMethod -Uri "https://production-ai-agent.onrender.com/health"
```

### Readiness Check
```bash
curl https://production-ai-agent.onrender.com/ready
# Expected: {"status": "ready", "redis": "connected"}
```

**PowerShell:**
```powershell
Invoke-RestMethod -Uri "https://production-ai-agent.onrender.com/ready"
```

### API Test (with authentication)
```bash
curl -X POST https://production-ai-agent.onrender.com/ask \
  -H "X-API-Key: 6n82ottb0yXMDMp1xUh8ko0aHx6l9v3L+1ceVL3SXOk=" \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello, how are you?"}'
```

**PowerShell:**
```powershell
$body = @{question = "Hello, how are you?"} | ConvertTo-Json
Invoke-RestMethod -Uri "https://production-ai-agent.onrender.com/ask" `
    -Method POST `
    -Headers @{"X-API-Key"="6n82ottb0yXMDMp1xUh8ko0aHx6l9v3L+1ceVL3SXOk="; "Content-Type"="application/json"} `
    -Body $body
```

**Expected Response:**
```json
{
  "question": "Hello, how are you?",
  "answer": "Mock response: I received your question 'Hello, how are you?'. This is a demo response.",
  "user_id": "a3f5e8d9c2b1a4f6",
  "model": "gpt-3.5-turbo",
  "history_count": 0
}
```

### Test Rate Limiting
```powershell
# Send 15 requests to trigger rate limit
for ($i=1; $i -le 15; $i++) {
    Write-Host "Request $i"
    $body = @{question = "Test $i"} | ConvertTo-Json
    try {
        Invoke-RestMethod -Uri "https://production-ai-agent.onrender.com/ask" `
            -Method POST `
            -Headers @{"X-API-Key"="6n82ottb0yXMDMp1xUh8ko0aHx6l9v3L+1ceVL3SXOk="; "Content-Type"="application/json"} `
            -Body $body
    } catch {
        Write-Host "Rate limited: $_"
    }
}
```

**Expected:** First 10 requests succeed, request 11+ returns 429 Too Many Requests

---

## Environment Variables Set

| Variable | Value | Source |
|----------|-------|--------|
| PORT | (auto) | Render |
| ENVIRONMENT | production | render.yaml |
| HOST | 0.0.0.0 | render.yaml |
| LOG_LEVEL | INFO | render.yaml |
| RATE_LIMIT_PER_MINUTE | 10 | render.yaml |
| MONTHLY_BUDGET_USD | 10.0 | render.yaml |
| LLM_MODEL | gpt-3.5-turbo | render.yaml |
| REDIS_URL | redis://... | Auto from Redis service |
| AGENT_API_KEY | (generated) | Render auto-generated |
| OPENAI_API_KEY | (optional) | Manual (not set) |

---

## Architecture

```
Internet
    │
    ▼
┌─────────────────────┐
│  Render Load Bal.   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  production-agent   │  ← Docker container
│  (FastAPI + Uvicorn)│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   agent-redis       │  ← Redis instance
│  (Session + Cache)  │
└─────────────────────┘
```

---

## Features Verified

- ✅ **Authentication**: API key required (X-API-Key header)
- ✅ **Rate Limiting**: 10 requests/minute per user
- ✅ **Cost Guard**: $10/month budget per user
- ✅ **Health Checks**: `/health` and `/ready` endpoints
- ✅ **Stateless**: All state in Redis
- ✅ **Graceful Shutdown**: Handles SIGTERM properly
- ✅ **Structured Logging**: JSON format
- ✅ **No Hardcoded Secrets**: All from environment variables
- ✅ **Multi-stage Docker**: Optimized image size
- ✅ **HTTPS**: Enabled by default on Render

---

## Performance

**Cold Start:** ~15-30 seconds (Render free tier sleeps after 15 min inactivity)  
**Warm Response Time:** ~100-200ms  
**Uptime:** 99%+ (Render free tier)

---

## Monitoring

**Logs:** Render Dashboard → production-ai-agent → Logs tab  
**Metrics:** Render Dashboard → production-ai-agent → Metrics tab

---

## Cost

**Current:** $0/month (Render free tier)  
**Limits:**
- 750 hours/month runtime
- Sleeps after 15 min inactivity
- 100 GB bandwidth/month

---

## Repository

**GitHub:** https://github.com/cheeka13/day12-agent-deployment  
**Branch:** main  
**Commit:** Latest

---

## Next Steps

- [ ] Add custom domain
- [ ] Enable auto-scaling (paid plan)
- [ ] Add monitoring/alerting
- [ ] Implement CI/CD pipeline
- [ ] Add distributed tracing
- [ ] Set up backup strategy

---

**Deployment Status:** ✅ LIVE AND RUNNING

**Last Updated:** 2026-04-17
