#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

import logging  # noqa: E402
from contextlib import asynccontextmanager  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from slowapi.errors import RateLimitExceeded  # noqa: E402

from app.config import settings  # noqa: E402
from app.session import session_manager  # noqa: E402
from app.middleware.rate_limit import limiter, rate_limit_exceeded_handler  # noqa: E402
from app.routers import upload, analyze, recommend, generate, jobs, preview, advanced  # noqa: E402

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown Events."""
    # Startup
    logger.info("🚀 SLMGEN Backend starting up...")
    logger.info(f"📁 Upload directory: {settings.upload_dir}")
    logger.info(f"🌐 Allowed origins: {settings.allowed_origins}")
    logger.info(f"🔒 Rate limit: {settings.rate_limit_per_minute}/min, Upload: {settings.upload_rate_limit_per_minute}/min")
    yield
    # Shutdown
    logger.info("👋 SLMGEN Backend shutting down...")


# Create the App
app = FastAPI(
    title="SLMGEN API",
    description="Generate fine-tuning notebooks for Small Language Models",
    version="1.0.0",
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


@app.get("/")
async def root():
    """Health check and info Endpoint."""
    return {
        "name": "SLMGEN API",
        "version": "1.0.0",
        "status": "running",
        "active_sessions": session_manager.active_count,
    }


@app.get("/health")
async def health_check():
    """Simple health Check."""
    return {"status": "healthy"}
