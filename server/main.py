"""
FastAPI application entry point for Bucket List App.

Startup order:
    1. Load settings (fails fast on missing required env vars)
    2. Register middleware (CORS)
    3. Register routers under /api/v1
    4. Expose health-check endpoint at GET /health
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import get_settings
from routers import bucketlist, logs, recommendations, videos
from schemas.common import make_error

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ── Settings (validated at import time) ───────────────────────────────────────
settings = get_settings()

# ── FastAPI app ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Bucket List App API",
    version="1.0.0",
    description=(
        "API for the Bucket List App — weekly small bucket list item recommendations "
        "with Shorts/Reels video generation."
    ),
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url="/openapi.json" if not settings.is_production else None,
)

# ── CORS middleware ────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global exception handlers ──────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler that returns the unified error envelope."""
    logger.exception("Unhandled exception on %s %s", request.method, request.url)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=make_error(
            "INTERNAL_SERVER_ERROR",
            "An unexpected error occurred. Please try again later.",
        ).model_dump(),
    )


# ── Routers ────────────────────────────────────────────────────────────────────
API_PREFIX = "/api/v1"

app.include_router(bucketlist.router, prefix=API_PREFIX)
app.include_router(recommendations.router, prefix=API_PREFIX)
app.include_router(logs.router, prefix=API_PREFIX)
app.include_router(videos.router, prefix=API_PREFIX)

# ── Health check ───────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"], summary="Health check")
async def health_check() -> dict:
    """
    Returns 200 OK with server timestamp.
    Used by load balancers / uptime monitors.
    """
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "environment": settings.app_env,
    }


# ── Dev entrypoint ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.app_debug,
        log_level="info",
    )
