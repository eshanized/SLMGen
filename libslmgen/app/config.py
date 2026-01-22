#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """App configuration loaded from Environment."""
    
    # CORS settings - where the frontend Lives
    # Comma-separated list of allowed origins
    allowed_origins: str = "http://localhost:3000,https://slmgen.vercel.app"
    
    # File storage stuff
    upload_dir: str = "./uploads"
    
    # Optional GitHub token for Gist creation
    # Leave empty if you don't want automatic Colab links
    github_token: str = ""
    
    # Session management
    max_sessions: int = 25
    session_ttl_minutes: int = 30
    
    # Security settings
    max_upload_bytes: int = 100 * 1024 * 1024  # 100 MB
    rate_limit_per_minute: int = 60  # General rate limit
    upload_rate_limit_per_minute: int = 10  # Stricter for uploads
    download_token_ttl_minutes: int = 60  # Download token validity
    
    # =========================================================================
    # Local Development Mode
    # =========================================================================
    # Hey there, local developer! 👋
    # 
    # If you just want to run SLMGEN locally without setting up Supabase,
    # set AUTH_DISABLED=true in your .env file (or as an environment variable).
    # 
    # What happens when auth is disabled:
    #   - No JWT verification needed - you'll be logged in as "local-dev-user"
    #   - The core workflow (upload → analyze → recommend → generate) works fine!
    #   - Job history endpoints will return a helpful 503 error since they need a database
    # 
    # This is great for:
    #   - Quick local testing
    #   - Contributing to the codebase without cloud setup
    #   - Running demos without external dependencies
    # =========================================================================
    auth_disabled: bool = False
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # ignore extra env Vars


# Global settings Instance
settings = Settings()

# Make sure upload directory Exists
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
