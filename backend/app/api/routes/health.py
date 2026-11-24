from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
def check_health():
    active_providers = []
    if settings.has_gemini_key:
        active_providers.append("gemini")
    if settings.has_groq_key:
        active_providers.append("groq")

    # Determine primary provider and model display
    if settings.has_gemini_key and settings.has_groq_key:
        primary_provider = "gemini+groq_fallback"
        primary_model = f"{settings.GEMINI_MODEL} (fallback: {settings.GROQ_MODEL})"
    elif settings.has_gemini_key:
        primary_provider = "gemini"
        primary_model = settings.GEMINI_MODEL
    elif settings.has_groq_key:
        primary_provider = "groq"
        primary_model = settings.GROQ_MODEL
    else:
        primary_provider = "none"
        primary_model = ""

    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "llm_provider": primary_provider,
        "llm_model": primary_model,
        "gemini_api_key_configured": settings.has_gemini_key,
        "groq_api_key_configured": settings.has_groq_key,
        "ai_provider_configured": settings.has_any_llm_key,
        "active_providers": active_providers,
        "gemini_model": settings.GEMINI_MODEL,
        "groq_model": settings.GROQ_MODEL,
        "demo_mode_available": True,
    }
