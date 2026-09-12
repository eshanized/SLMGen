#!/usr/bin/env python3
"""
SLMGEN FastAPI Application.

Main entry point for the backend API.
Handles CORS, routing, rate limiting, and lifecycle events.
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

# Load environment variables first (before any other imports)
from dotenv import load_dotenv

load_dotenv()

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.middleware.rate_limit import limiter, rate_limit_exceeded_handler
from app.routers import (
    advanced,
    analyze,
    convert,
    export,
    generate,
    jobs,
    presets,
    preview,
    recommend,
    training,
    upload,
)
from app.session_store import session_store
from app.storage import serve_local_file, storage_service
from app.training_store import training_store

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    logger.info("🚀 SLMGEN Backend starting up...")
    logger.info(f"📁 Upload directory: {settings.upload_dir}")
    logger.info(f"🌐 Allowed origins: {settings.allowed_origins}")
    logger.info(f"🔒 Rate limit: {settings.rate_limit_per_minute}/min, Upload: {settings.upload_rate_limit_per_minute}/min")

    # Initialize in-memory session store
    session_store.start()
    logger.info(f"🗄️ In-memory session store started (TTL: {settings.session_ttl_seconds}s)")

    # Initialize training store
    training_store.start()
    logger.info("📊 Training store started")

    yield

    # Shutdown
    logger.info("👋 SLMGEN Backend shutting down...")
    session_store.stop()
    training_store.stop()


# Create the App
app = FastAPI(
    title="SLMGEN API",
    description="Generate fine-tuning notebooks for Small Language Models",
    version=settings.app_version,
    lifespan=lifespan,
)

# Add rate limiter state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Configure CORS with restricted methods and headers
origins = [origin.strip() for origin in settings.allowed_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Requested-With",
    ],
)

# Include Routers
app.include_router(upload.router, tags=["Upload"])
app.include_router(analyze.router, tags=["Analysis"])
app.include_router(recommend.router, tags=["Recommendation"])
app.include_router(generate.router, tags=["Generation"])
app.include_router(jobs.router)
app.include_router(preview.router)
app.include_router(advanced.router, tags=["Advanced Features"])
app.include_router(training.router)
app.include_router(convert.router, tags=["Converter"])
app.include_router(export.router, tags=["Export"])
app.include_router(presets.router)


@app.get("/")
async def root():
    """Health check and info endpoint."""
    active_sessions = await session_store.get_active_count()
    return {
        "name": "SLMGEN API",
        "version": "3.0.0",
        "status": "running",
        "active_sessions": active_sessions,
    }


@app.get("/health")
async def health_check():
    """Simple health check."""
    return {
        "status": "healthy",
        "storage": "local",
    }


@app.get("/storage/local/{path:path}")
async def get_local_file(path: str):
    """Serve files from local storage."""
    if storage_service.is_local:
        try:
            content, content_type = await serve_local_file(path)
            return Response(content=content, media_type=content_type)
        except Exception:
            return JSONResponse(
                status_code=404,
                content={"detail": "File not found."},
            )
    else:
        return JSONResponse(
            status_code=404,
            content={"detail": "Local file serving not available."},
        )
