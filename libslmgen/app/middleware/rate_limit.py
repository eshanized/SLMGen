#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rate Limiting Middleware.

Protects API endpoints from abuse with configurable rate limits.
Uses slowapi for in-memory rate limiting.
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings


def get_real_client_ip(request: Request) -> str:
    """
    Get the real client IP, handling reverse proxies.
    
    Checks X-Forwarded-For header for proxied requests,
    falls back to direct connection IP.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take the first IP in the chain (original client)
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


# Create limiter instance
limiter = Limiter(key_func=get_real_client_ip)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Custom handler for rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Try again in a few seconds.",
            "retry_after": exc.detail,
        }
    )


# Rate limit decorators for different endpoint types
def general_limit():
    """Standard rate limit for most endpoints."""
    return limiter.limit(f"{settings.rate_limit_per_minute}/minute")


def upload_limit():
    """Stricter rate limit for upload endpoints."""
    return limiter.limit(f"{settings.upload_rate_limit_per_minute}/minute")
