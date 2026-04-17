"""
YouTube Automation Pro — FastAPI Server
Main application entry point with CORS, auth, and route registration.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import env, OUTPUT_DIR
from .database import init_db
from .scheduler import start_scheduler, stop_scheduler

from .routes.channels import router as channels_router
from .routes.videos import router as videos_router
from .routes.pipeline import router as pipeline_router
from .routes.analytics import router as analytics_router
from .routes.ideas import router as ideas_router
from .routes.scheduler import router as scheduler_router

# ── Logging ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("youtube-auto-pro")


# ── Lifespan: init DB on startup ────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Initializing database...")
    init_db()
    logger.info("✅ Database ready. 6 channels loaded.")
    
    # Start APScheduler
    start_scheduler()
    
    yield
    
    # Shutdown APScheduler
    stop_scheduler()
    logger.info("🛑 Server shutting down.")


# ── App creation ─────────────────────────────────────────────
app = FastAPI(
    title="YouTube Automation Pro",
    description="Sistema automatizado de generación de videos YouTube por nicho",
    version="2.0.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Auth middleware ───────────────────────────────────────────
API_TOKEN = env("API_TOKEN", "yt-auto-pro-2026-secure")


async def verify_token(request: Request):
    """Simple token auth — skip for docs and health."""
    if request.url.path in ("/", "/health", "/docs", "/openapi.json", "/redoc"):
        return
    auth = request.headers.get("Authorization", "")
    token = request.query_params.get("token", "")
    if auth == f"Bearer {API_TOKEN}" or token == API_TOKEN:
        return
    # Allow during development
    if env("SKIP_AUTH", "true").lower() in {"1", "true", "yes"}:
        return
    raise HTTPException(status_code=401, detail="Invalid or missing API token")


# ── Routes ───────────────────────────────────────────────────
app.include_router(channels_router, prefix="/api/channels", tags=["Channels"])
app.include_router(videos_router, prefix="/api/videos", tags=["Videos"])
app.include_router(pipeline_router, prefix="/api/pipeline", tags=["Pipeline"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(ideas_router)
app.include_router(scheduler_router)

# ── Static files for generated videos ────────────────────────
app.mount("/media", StaticFiles(directory=str(OUTPUT_DIR)), name="media")


# ── Root & Health ────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "name": "YouTube Automation Pro",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"ok": True, "status": "healthy"}
