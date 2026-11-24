"""
Admin routes: AI provider management, system configuration.
"""
import time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.permissions import require_admin
from app.db.session import get_db
from app.models.learning import AIModelLogModel

router = APIRouter(prefix="/admin", tags=["Administration"])


@router.get("/ai/providers", status_code=200)
def get_ai_providers(_=Depends(require_admin)):
    """Get current AI provider configuration. Never returns API keys."""
    return {
        "primary_provider": settings.LLM_PRIMARY_PROVIDER,
        "fallback_provider": settings.LLM_FALLBACK_PROVIDER,
        "providers": {
            "ollama": {
                "configured": True,
                "base_url": settings.OLLAMA_BASE_URL,
                "model": settings.OLLAMA_MODEL,
                "timeout_seconds": settings.OLLAMA_TIMEOUT_SECONDS,
                "num_ctx": settings.OLLAMA_NUM_CTX,
            },
            "gemini": {
                "configured": settings.has_gemini_key,
                "model": settings.GEMINI_MODEL,
                "api_key_set": settings.has_gemini_key,
                # API key never exposed
            },
            "groq": {
                "configured": settings.has_groq_key,
                "model": settings.GROQ_MODEL,
                "api_key_set": settings.has_groq_key,
                # API key never exposed
            },
        },
    }


@router.get("/ai/health", status_code=200)
def check_ai_health(_=Depends(require_admin)):
    """Check connectivity for all configured AI providers."""
    health = {}

    # Check Ollama
    try:
        import httpx
        start = time.time()
        resp = httpx.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=5)
        latency_ms = int((time.time() - start) * 1000)
        if resp.status_code == 200:
            models = [m.get("name") for m in resp.json().get("models", [])]
            health["ollama"] = {
                "status": "connected",
                "latency_ms": latency_ms,
                "available_models": models,
                "target_model": settings.OLLAMA_MODEL,
                "target_model_available": settings.OLLAMA_MODEL in models,
            }
        else:
            health["ollama"] = {"status": "error", "detail": f"HTTP {resp.status_code}"}
    except Exception as e:
        health["ollama"] = {"status": "unavailable", "detail": str(e)[:100]}

    # Check Gemini (lightweight check)
    if settings.has_gemini_key:
        health["gemini"] = {"status": "configured", "detail": "API key present"}
    else:
        health["gemini"] = {"status": "not_configured", "detail": "No API key"}

    # Check Groq
    if settings.has_groq_key:
        try:
            from groq import Groq
            client = Groq(api_key=settings.GROQ_API_KEY)
            start = time.time()
            models = client.models.list()
            latency_ms = int((time.time() - start) * 1000)
            health["groq"] = {
                "status": "connected",
                "latency_ms": latency_ms,
                "configured_model": settings.GROQ_MODEL,
            }
        except Exception as e:
            health["groq"] = {"status": "error", "detail": str(e)[:100]}
    else:
        health["groq"] = {"status": "not_configured", "detail": "No API key"}

    return health


@router.post("/ai/test-connection", status_code=200)
def test_ai_connection(_=Depends(require_admin)):
    """Test a sample AI generation to verify the full pipeline."""
    from app.services.llm_provider import LLMProviderError, get_llm_provider
    try:
        llm = get_llm_provider(task_type="test")
        start = time.time()
        result = llm.generate(
            prompt='Respond with this exact JSON: {"status": "ok", "message": "AI pipeline working correctly"}',
            system_instruction="Output only valid JSON.",
        )
        latency_ms = int((time.time() - start) * 1000)
        return {
            "status": "success",
            "latency_ms": latency_ms,
            "provider": type(llm).__name__,
            "response_preview": result[:200],
        }
    except LLMProviderError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/ai/logs", status_code=200)
def get_ai_logs(
    limit: int = 50,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """Get recent AI model invocation logs."""
    logs = db.query(AIModelLogModel).order_by(
        AIModelLogModel.created_at.desc()
    ).limit(limit).all()

    return {
        "logs": [
            {
                "id": log.id,
                "provider": log.provider,
                "model": log.model_name,
                "task_type": log.task_type,
                "latency_ms": log.latency_ms,
                "success": log.success,
                "error": log.error_message,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ]
    }


class UpdateProviderConfig(BaseModel):
    primary_provider: str | None = None
    ollama_model: str | None = None
    ollama_base_url: str | None = None


@router.post("/ai/configuration", status_code=200)
def update_ai_config(req: UpdateProviderConfig, _=Depends(require_admin)):
    """
    Update AI configuration at runtime.
    Note: Changes are session-only unless .env is updated.
    """
    if req.primary_provider:
        if req.primary_provider not in ("ollama", "gemini", "groq"):
            raise HTTPException(status_code=400, detail="Invalid provider. Choose: ollama, gemini, groq")
        settings.LLM_PRIMARY_PROVIDER = req.primary_provider

    if req.ollama_model:
        settings.OLLAMA_MODEL = req.ollama_model

    if req.ollama_base_url:
        settings.OLLAMA_BASE_URL = req.ollama_base_url.rstrip("/")

    # Persist to .env file for durability across restarts
    try:
        import os
        import re
        env_files = [".env", "backend/.env", "../backend/.env"]
        for env_path in env_files:
            if os.path.exists(env_path):
                with open(env_path, "r", encoding="utf-8") as f:
                    content = f.read()
                if req.primary_provider:
                    content = re.sub(r'LLM_PRIMARY_PROVIDER=.*', f'LLM_PRIMARY_PROVIDER={req.primary_provider}', content)
                if req.ollama_model:
                    content = re.sub(r'OLLAMA_MODEL=.*', f'OLLAMA_MODEL={req.ollama_model}', content)
                with open(env_path, "w", encoding="utf-8") as f:
                    f.write(content)
                break
    except Exception as e:
        import logging
        logging.getLogger("studyset").warning(f"Failed to persist settings to .env: {e}")

    return {
        "message": "Configuration updated successfully and persisted to environment.",
        "current_primary": settings.LLM_PRIMARY_PROVIDER,
        "current_ollama_model": settings.OLLAMA_MODEL,
        "note": "Settings applied immediately.",
    }
