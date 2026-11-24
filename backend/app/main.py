import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import (
    analytics,
    attempts,
    batches,
    documents,
    export,
    health,
    publications,
    quizzes,
)
from app.api.routes.auth import router as auth_router
from app.core.config import settings
from app.core.logging import logger
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing StudySet AI backend...")
    # Create upload directories
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "resumes"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "job_descriptions"), exist_ok=True)
    init_db()
    logger.info("Database initialized successfully.")
    yield
    # Shutdown
    logger.info("Shutting down StudySet AI backend.")


app = FastAPI(
    title="StudySet AI — Assessment & Interview Intelligence Platform",
    description=(
        "Intelligent Assessment. Personalized Interviews. Measurable Growth. "
        "Production-grade AI-powered academic and interview preparation platform."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}: "
        f"{type(exc).__name__} - {str(exc)[:120]}"
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected server error occurred. Please try again."},
    )


# --- Academic Assessment Routes (Existing — Preserved) ---
app.include_router(health.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(quizzes.router, prefix="/api")
app.include_router(attempts.router, prefix="/api")
app.include_router(export.router, prefix="/api")
app.include_router(batches.router, prefix="/api")
app.include_router(publications.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")

# --- New Authentication Routes ---
app.include_router(auth_router, prefix="/api")

# --- New Interview Intelligence Routes (registered after models are loaded) ---
try:
    from app.api.routes.resumes import router as resumes_router
    app.include_router(resumes_router, prefix="/api")
except ImportError:
    pass

try:
    from app.api.routes.job_descriptions import router as jd_router
    app.include_router(jd_router, prefix="/api")
except ImportError:
    pass

try:
    from app.api.routes.matching import router as matching_router
    app.include_router(matching_router, prefix="/api")
except ImportError:
    pass

try:
    from app.api.routes.interviews import router as interviews_router
    app.include_router(interviews_router, prefix="/api")
except ImportError:
    pass

try:
    from app.api.routes.interview_sessions import router as sessions_router
    app.include_router(sessions_router, prefix="/api")
except ImportError:
    pass

try:
    from app.api.routes.interview_analytics import router as interview_analytics_router
    app.include_router(interview_analytics_router, prefix="/api")
except ImportError:
    pass

try:
    from app.api.routes.admin import router as admin_router
    app.include_router(admin_router, prefix="/api")
except ImportError:
    pass


@app.get("/")
def root():
    return {
        "name": "StudySet AI",
        "version": "2.0.0",
        "tagline": "Intelligent Assessment. Personalized Interviews. Measurable Growth.",
        "docs_url": "/docs",
        "status": "online",
    }
