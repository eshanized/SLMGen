#!/usr/bin/env python3
"""
Application Configuration.

Handles env vars and settings for the SLMGEN backend.

This is the central place for all configuration. We use pydantic-settings
to automatically load values from environment variables or .env file.
If you're adding a new config option, just add it here and it'll be
picked up automatically!

Contributor: Vedant Singh Rajput <teleported0722@gmail.com>
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

from pathlib import Path

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """App configuration loaded from Environment."""

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # App version
    app_version: str = "3.0.0"

    # CORS settings - where the frontend Lives
    # Comma-separated list of allowed origins
    allowed_origins: str = "http://localhost:3000,https://slmgen.vercel.app"

    # File storage stuff
    upload_dir: str = "./uploads"

    # Optional GitHub token for Gist creation
    # Leave empty if you don't want automatic Colab links
    github_token: str = ""

    # Session management
    session_ttl_seconds: int = 1800  # 30 minutes

    # Security settings
    max_upload_bytes: int = 100 * 1024 * 1024  # 100 MB
    rate_limit_per_minute: int = 60  # General rate limit
    upload_rate_limit_per_minute: int = 10  # Stricter for uploads
    download_token_ttl_minutes: int = 60  # Download token validity

    # =========================================================================
    # Optional Authentication Mode
    # =========================================================================
    # By default, authentication is optional - anyone can generate notebooks!
    #
    # Set AUTH_DISABLED=false if you want to require login for all features.
    # When auth is enabled:
    #   - Job history endpoints require authentication
    #   - User profile features work
    #
    # When auth is disabled (default):
    #   - No JWT verification needed - anonymous users can use all features
    #   - The core workflow (upload → analyze → recommend → generate) works!
    #   - Job history returns 503 (requires database)
    #
    # This is great for:
    #   - Demos and quick testing
    #   - Public usage without account creation
    #   - Maximum accessibility
    # =========================================================================
    auth_disabled: bool = True


# Global settings Instance
settings = Settings()

# Make sure upload directory Exists
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
