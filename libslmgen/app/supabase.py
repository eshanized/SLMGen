#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supabase Client Configuration.

Provides Supabase client factories for both service-level and user-level access.
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

import os
import logging
from functools import lru_cache
from typing import Optional

from supabase import create_client, Client

logger = logging.getLogger(__name__)


@lru_cache()
def get_supabase_url() -> str:
    """Get Supabase project URL."""
    url = os.environ.get("SUPABASE_URL")
    if not url:
        raise ValueError("SUPABASE_URL environment variable is required")
    return url


@lru_cache()
def get_supabase_anon_key() -> str:
    """Get Supabase anonymous/public key."""
    key = os.environ.get("SUPABASE_ANON_KEY")
    if not key:
        raise ValueError("SUPABASE_ANON_KEY environment variable is required")
    return key


@lru_cache()
def get_supabase_service_key() -> str:
    """Get Supabase service role key (server-side only)."""
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not key:
        raise ValueError("SUPABASE_SERVICE_KEY environment variable is required")
    return key


@lru_cache()
def get_jwt_secret() -> str:
    """
    Get Supabase JWT secret for token verification.
    
    Note: Supabase JWT secrets are raw strings used directly with HS256.
    They should NOT be base64 decoded.
    """
    secret = os.environ.get("SUPABASE_JWT_SECRET")
    if not secret:
        raise ValueError("SUPABASE_JWT_SECRET environment variable is required")
    logger.debug(f"JWT secret loaded: {len(secret)} chars")
    return secret


def get_supabase_client() -> Client:
    """
    Get Supabase client with service role key.
    
    Use this for server-side operations that bypass RLS.
    """
    return create_client(get_supabase_url(), get_supabase_service_key())


def get_supabase_anon_client() -> Client:
    """
    Get Supabase client with anon key.
    
    Use this for operations that should respect RLS.
    """
    return create_client(get_supabase_url(), get_supabase_anon_key())


def get_user_client(access_token: str) -> Client:
    """
    Get Supabase client authenticated as a specific user.
    
    Args:
        access_token: User's JWT access token
        
    Returns:
        Supabase client with user's context
    """
    client = create_client(get_supabase_url(), get_supabase_anon_key())
    # Set the user's session
    client.auth.set_session(access_token, "")
    return client


# Storage helpers
def get_storage_url() -> str:
    """Get Supabase storage URL."""
    return os.environ.get(
        "SUPABASE_STORAGE_URL",
        f"{get_supabase_url()}/storage/v1"
    )


async def upload_to_storage(
    bucket: str,
    path: str,
    file_content: bytes,
    content_type: str = "application/octet-stream",
    user_id: Optional[str] = None
) -> str:
    """
    Upload file to Supabase Storage.
    
    Args:
        bucket: Storage bucket name
        path: File path within bucket
        file_content: File bytes
        content_type: MIME type
        user_id: Optional user ID to prepend to path
        
    Returns:
        Full storage path
    """
    client = get_supabase_client()
    
    # Prepend user_id to path for RLS
    if user_id:
        full_path = f"{user_id}/{path}"
    else:
        full_path = path
    
    result = client.storage.from_(bucket).upload(
        full_path,
        file_content,
        {"content-type": content_type}
    )
    
    logger.info(f"Uploaded file to {bucket}/{full_path}")
    return full_path


async def get_signed_url(bucket: str, path: str, expires_in: int = 3600) -> str:
    """
    Get a signed URL for private file access.
    
    Args:
        bucket: Storage bucket name
        path: File path within bucket
        expires_in: URL expiration in seconds
        
    Returns:
        Signed download URL
    """
    client = get_supabase_client()
    result = client.storage.from_(bucket).create_signed_url(path, expires_in)
    return result["signedURL"]


async def delete_from_storage(bucket: str, paths: list[str]) -> None:
    """
    Delete files from Supabase Storage.
    
    Args:
        bucket: Storage bucket name
        paths: List of file paths to delete
    """
    client = get_supabase_client()
    client.storage.from_(bucket).remove(paths)
    logger.info(f"Deleted {len(paths)} files from {bucket}")
