#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Production-Grade Storage Service.

Provides unified object storage with Supabase Storage as primary backend,
falling back to local filesystem for development.

Architecture:
    - Primary: Supabase Storage (S3-compatible)
    - Fallback: Local filesystem (dev mode only)
    - All operations are async-safe
    - Signed URLs for secure access
    - Metadata tracking in session store

Why Object Storage:
    1. Horizontal scaling - any instance can access files
    2. Persistence - files survive restarts and instance failures
    3. CDN-ready - can serve through CDN with signed URLs
    4. Cost-effective - pay per GB vs instance storage

Storage Structure:
    datasets/{user_id}/{session_id}.jsonl
    notebooks/{user_id}/{session_id}.ipynb

For anonymous users: use "anonymous" as user_id prefix.

Author: Eshan Roy <eshanized@proton.me>
License: MIT License
Copyright (c) 2026 Eshan Roy
"""

import io
import logging
import os
import re
from enum import Enum
from pathlib import Path
from typing import Optional

import aiofiles
from fastapi import HTTPException

from .config import settings
from .supabase import is_supabase_configured

logger = logging.getLogger(__name__)

# File type definitions
class FileType(str, Enum):
    DATASET = "dataset"
    NOTEBOOK = "notebook"


# Allowed extensions by file type
ALLOWED_EXTENSIONS = {
    FileType.DATASET: {".jsonl"},
    FileType.NOTEBOOK: {".ipynb"},
}

# Bucket names
BUCKET_DATASETS = "datasets"
BUCKET_NOTEBOOKS = "notebooks"

# Signed URL expiry defaults (seconds)
DEFAULT_SIGNED_URL_TTL = 3600  # 1 hour
MAX_SIGNED_URL_TTL = 86400  # 24 hours

# Path validation regex - prevents traversal
SAFE_PATH_RE = re.compile(r'^[a-zA-Z0-9_\-./]+$')


def _validate_path(path: str) -> None:
    """
    Validate storage path to prevent traversal attacks.
    
    Args:
        path: Storage path to validate
        
    Raises:
        HTTPException(400): If path contains dangerous patterns
    """
    if not path or ".." in path or not SAFE_PATH_RE.match(path):
        raise HTTPException(
            status_code=400,
            detail="Invalid storage path.",
        )


def _validate_file_type(filename: str, file_type: FileType) -> None:
    """
    Validate file extension matches expected type.
    
    Args:
        filename: Original filename
        file_type: Expected file type
        
    Raises:
        HTTPException(400): If extension doesn't match
    """
    ext = Path(filename).suffix.lower()
    allowed = ALLOWED_EXTENSIONS.get(file_type, set())
    
    if ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Expected: {', '.join(allowed)}",
        )


def _get_user_namespace(user_id: Optional[str]) -> str:
    """
    Get namespace for file storage based on user.
    
    For authenticated users: uses their user_id
    For anonymous: uses "anonymous"
    """
    if not user_id or user_id == "anonymous":
        return "anonymous"
    # Sanitize user_id
    return re.sub(r'[^a-zA-Z0-9_\-]', '_', user_id)[:64]


def _build_storage_path(
    file_type: FileType,
    session_id: str,
    user_id: Optional[str],
    original_filename: Optional[str] = None,
) -> str:
    """
    Build the storage path for a file.
    
    Format: {bucket}/{user_namespace}/{session_id}[_{filename}]
    """
    namespace = _get_user_namespace(user_id)
    
    if file_type == FileType.DATASET:
        return f"{BUCKET_DATASETS}/{namespace}/{session_id}.jsonl"
    else:
        filename = original_filename or f"{session_id}.ipynb"
        return f"{BUCKET_NOTEBOOKS}/{namespace}/{filename}"


class StorageBackend(Enum):
    """Available storage backends."""
    SUPABASE = "supabase"
    LOCAL = "local"


class StorageService:
    """
    Unified storage service with Supabase as primary backend.
    
    Provides:
    - Async file uploads
    - Signed URL generation
    - Secure access patterns
    - Graceful fallback to local storage
    
    Usage:
        service = StorageService()
        
        # Upload
        path = await service.upload_dataset(file_bytes, session_id, user_id)
        
        # Get download URL
        url = await service.get_signed_url(path)
        
        # Delete
        await service.delete_file(path)
    """

    def __init__(
        self,
        fallback_to_local: bool = True,
    ):
        """
        Initialize storage service.
        
        Args:
            fallback_to_local: If True, fall back to local filesystem
                             when Supabase is not configured.
        """
        self._fallback_to_local = fallback_to_local and not is_supabase_configured()
        self._backend = StorageBackend.SUPABASE if is_supabase_configured() else StorageBackend.LOCAL
        
        if self._backend == StorageBackend.LOCAL:
            logger.warning(
                "⚠️  Supabase not configured. Using local filesystem storage. "
                "This is NOT recommended for production!"
            )
        
        logger.info(f"Storage backend: {self._backend.value}")

    @property
    def is_using_supabase(self) -> bool:
        """Check if using Supabase storage."""
        return self._backend == StorageBackend.SUPABASE

    @property
    def is_local_fallback(self) -> bool:
        """Check if using local filesystem fallback."""
        return self._backend == StorageBackend.LOCAL

    # =============================================================================
    # Supabase Storage Operations
    # =============================================================================

    async def _upload_to_supabase(
        self,
        bucket: str,
        path: str,
        file_bytes: bytes,
        content_type: str,
    ) -> str:
        """
        Upload file to Supabase Storage.
        
        Args:
            bucket: Bucket name
            path: Storage path
            file_bytes: File content
            content_type: MIME type
            
        Returns:
            Storage path
            
        Raises:
            HTTPException(503): If upload fails
        """
        try:
            from supabase import Client
            
            # Import here to avoid circular imports
            from .supabase import get_supabase_client
            
            client: Client = get_supabase_client()
            storage = client.storage
            
            # Convert bytes to file-like object
            file_obj = io.BytesIO(file_bytes)
            
            storage.from_(bucket).upload(
                path,
                file_obj,
                {"content-type": content_type},
                # Upsert if exists
                file_options={"upsert": True},
            )
            
            logger.info(f"Uploaded to Supabase: {bucket}/{path}")
            return path
            
        except Exception as e:
            logger.error(f"Supabase upload failed: {e}")
            raise HTTPException(
                status_code=503,
                detail="Storage service temporarily unavailable. Please try again later.",
            )

    async def _get_supabase_signed_url(
        self,
        bucket: str,
        path: str,
        expires_in: int = DEFAULT_SIGNED_URL_TTL,
    ) -> str:
        """
        Generate signed URL from Supabase Storage.
        
        Args:
            bucket: Bucket name
            path: Storage path
            expires_in: Expiration in seconds
            
        Returns:
            Signed download URL
        """
        try:
            from .supabase import get_supabase_client
            
            client = get_supabase_client()
            storage = client.storage
            
            result = storage.from_(bucket).create_signed_url(
                path,
                expires_in,
            )
            
            return result.get("signedURL", "")
            
        except Exception as e:
            logger.error(f"Failed to create signed URL: {e}")
            raise HTTPException(
                status_code=503,
                detail="Failed to generate download URL.",
            )

    async def _delete_from_supabase(self, bucket: str, path: str) -> None:
        """
        Delete file from Supabase Storage.
        
        Args:
            bucket: Bucket name
            path: Storage path
        """
        try:
            from .supabase import get_supabase_client
            
            client = get_supabase_client()
            storage = client.storage
            
            storage.from_(bucket).remove([path])
            logger.info(f"Deleted from Supabase: {bucket}/{path}")
            
        except Exception as e:
            logger.error(f"Failed to delete from Supabase: {e}")
            # Don't raise - deletion failures are non-critical

    # =============================================================================
    # Local Filesystem Fallback
    # =============================================================================

    async def _upload_to_local(
        self,
        path: str,
        file_bytes: bytes,
    ) -> str:
        """
        Upload file to local filesystem.
        
        Used only for development when Supabase is not configured.
        
        Args:
            path: Local file path (relative)
            file_bytes: File content
            
        Returns:
            Storage path
        """
        local_dir = Path(settings.upload_dir)
        local_dir.mkdir(parents=True, exist_ok=True)
        
        # Convert storage path to local path
        # datasets/user/session.jsonl -> upload_dir/datasets/user/session.jsonl
        local_path = local_dir / path
        
        # Create parent directories
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        async with aiofiles.open(local_path, "wb") as f:
            await f.write(file_bytes)
        
        logger.info(f"Uploaded to local: {local_path}")
        return path

    async def _get_local_signed_url(
        self,
        path: str,
        expires_in: int = DEFAULT_SIGNED_URL_TTL,
    ) -> str:
        """
        Get local file URL (development only).
        
        In local mode, returns a path that can be served directly.
        NOT suitable for production.
        
        Args:
            path: Storage path
            expires_in: Ignored in local mode
            
        Returns:
            Local file path
        """
        local_path = Path(settings.upload_dir) / path
        if not local_path.exists():
            raise HTTPException(
                status_code=404,
                detail="File not found.",
            )
        return f"/storage/local/{path}"

    async def _delete_from_local(self, path: str) -> None:
        """
        Delete file from local filesystem.
        
        Args:
            path: Storage path
        """
        local_path = Path(settings.upload_dir) / path
        if local_path.exists():
            local_path.unlink()
            logger.info(f"Deleted from local: {local_path}")

    # =============================================================================
    # Public API
    # =============================================================================

    async def upload_dataset(
        self,
        file_bytes: bytes,
        session_id: str,
        user_id: Optional[str] = None,
        original_filename: Optional[str] = None,
    ) -> str:
        """
        Upload dataset file to storage.
        
        Args:
            file_bytes: File content
            session_id: Session UUID
            user_id: Optional user ID for namespacing
            original_filename: Original filename (for notebooks)
            
        Returns:
            Storage path (e.g., "datasets/anonymous/uuid.jsonl")
            
        Raises:
            HTTPException(400): If file is too large or invalid type
            HTTPException(503): If storage service fails
        """
        # Validate size
        if len(file_bytes) > settings.max_upload_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {settings.max_upload_bytes // (1024*1024)}MB",
            )
        
        # Build path
        storage_path = _build_storage_path(
            FileType.DATASET,
            session_id,
            user_id,
        )
        
        _validate_path(storage_path)
        
        # Upload
        if self._backend == StorageBackend.SUPABASE:
            await self._upload_to_supabase(
                BUCKET_DATASETS,
                storage_path,
                file_bytes,
                "application/jsonl",
            )
        else:
            await self._upload_to_local(storage_path, file_bytes)
        
        return storage_path

    async def upload_notebook(
        self,
        file_bytes: bytes,
        session_id: str,
        user_id: Optional[str] = None,
        original_filename: Optional[str] = None,
    ) -> str:
        """
        Upload notebook file to storage.
        
        Args:
            file_bytes: File content
            session_id: Session UUID
            user_id: Optional user ID for namespacing
            original_filename: Original filename
            
        Returns:
            Storage path (e.g., "notebooks/anonymous/uuid.ipynb")
            
        Raises:
            HTTPException(400): If file is invalid type
            HTTPException(503): If storage service fails
        """
        # Validate file type
        if original_filename:
            _validate_file_type(original_filename, FileType.NOTEBOOK)
        
        # Build path
        storage_path = _build_storage_path(
            FileType.NOTEBOOK,
            session_id,
            user_id,
            original_filename,
        )
        
        _validate_path(storage_path)
        
        # Upload
        if self._backend == StorageBackend.SUPABASE:
            await self._upload_to_supabase(
                BUCKET_NOTEBOOKS,
                storage_path,
                file_bytes,
                "application/json",
            )
        else:
            await self._upload_to_local(storage_path, file_bytes)
        
        return storage_path

    async def get_signed_url(
        self,
        storage_path: str,
        expires_in: int = DEFAULT_SIGNED_URL_TTL,
    ) -> str:
        """
        Get signed download URL for a stored file.
        
        Args:
            storage_path: Path returned from upload (e.g., "datasets/.../file.jsonl")
            expires_in: URL expiration in seconds (max 24 hours)
            
        Returns:
            Signed download URL
            
        Raises:
            HTTPException(404): If file not found
            HTTPException(503): If URL generation fails
        """
        _validate_path(storage_path)
        
        # Clamp expiry
        expires_in = min(expires_in, MAX_SIGNED_URL_TTL)
        
        # Determine bucket from path
        if storage_path.startswith(BUCKET_DATASETS + "/"):
            bucket = BUCKET_DATASETS
            path_in_bucket = storage_path[len(BUCKET_DATASETS) + 1:]
        elif storage_path.startswith(BUCKET_NOTEBOOKS + "/"):
            bucket = BUCKET_NOTEBOOKS
            path_in_bucket = storage_path[len(BUCKET_NOTEBOOKS) + 1:]
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid storage path.",
            )
        
        if self._backend == StorageBackend.SUPABASE:
            return await self._get_supabase_signed_url(bucket, path_in_bucket, expires_in)
        else:
            return await self._get_local_signed_url(storage_path, expires_in)

    async def delete_file(self, storage_path: str) -> None:
        """
        Delete a file from storage.
        
        Args:
            storage_path: Path returned from upload
        """
        _validate_path(storage_path)
        
        if storage_path.startswith(BUCKET_DATASETS + "/"):
            bucket = BUCKET_DATASETS
        elif storage_path.startswith(BUCKET_NOTEBOOKS + "/"):
            bucket = BUCKET_NOTEBOOKS
        else:
            logger.warning(f"Unknown bucket for path: {storage_path}")
            return
        
        if self._backend == StorageBackend.SUPABASE:
            await self._delete_from_supabase(bucket, storage_path)
        else:
            await self._delete_from_local(storage_path)

    async def download_file(self, storage_path: str) -> bytes:
        """
        Download file content from storage.
        
        Args:
            storage_path: Path returned from upload
            
        Returns:
            File bytes
            
        Raises:
            HTTPException(404): If file not found
            HTTPException(503): If download fails
        """
        _validate_path(storage_path)
        
        if storage_path.startswith(BUCKET_DATASETS + "/"):
            bucket = BUCKET_DATASETS
        elif storage_path.startswith(BUCKET_NOTEBOOKS + "/"):
            bucket = BUCKET_NOTEBOOKS
        else:
            raise HTTPException(status_code=400, detail="Invalid storage path.")
        
        if self._backend == StorageBackend.SUPABASE:
            try:
                from .supabase import get_supabase_client
                
                client = get_supabase_client()
                storage = client.storage
                
                result = storage.from_(bucket).download(storage_path)
                return result
                
            except Exception as e:
                logger.error(f"Failed to download from Supabase: {e}")
                raise HTTPException(
                    status_code=404,
                    detail="File not found.",
                )
        else:
            local_path = Path(settings.upload_dir) / storage_path
            if not local_path.exists():
                raise HTTPException(status_code=404, detail="File not found.")
            
            async with aiofiles.open(local_path, "rb") as f:
                return await f.read()

    async def file_exists(self, storage_path: str) -> bool:
        """
        Check if a file exists in storage.
        
        Args:
            storage_path: Path to check
            
        Returns:
            True if file exists
        """
        _validate_path(storage_path)
        
        if self._backend == StorageBackend.SUPABASE:
            try:
                from .supabase import get_supabase_client
                
                client = get_supabase_client()
                storage = client.storage
                
                # Try to get signed URL - if it fails, file doesn't exist
                if storage_path.startswith(BUCKET_DATASETS + "/"):
                    bucket = BUCKET_DATASETS
                else:
                    bucket = BUCKET_NOTEBOOKS
                
                result = storage.from_(bucket).create_signed_url(storage_path, 1)
                return bool(result.get("signedURL"))
                
            except Exception:
                return False
        else:
            local_path = Path(settings.upload_dir) / storage_path
            return local_path.exists()


# =============================================================================
# Local File Server Endpoint (Development Only)
# =============================================================================

async def serve_local_file(storage_path: str) -> tuple[bytes, str]:
    """
    Serve a file from local storage (development only).
    
    Args:
        storage_path: Path within local storage
        
    Returns:
        Tuple of (file_bytes, content_type)
        
    Raises:
        HTTPException(404): If file not found
    """
    _validate_path(storage_path)
    
    local_path = Path(settings.upload_dir) / storage_path
    
    if not local_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")
    
    # Determine content type
    ext = local_path.suffix.lower()
    if ext == ".jsonl":
        content_type = "application/jsonl"
    elif ext == ".ipynb":
        content_type = "application/json"
    else:
        content_type = "application/octet-stream"
    
    async with aiofiles.open(local_path, "rb") as f:
        content = await f.read()
    
    return content, content_type


# =============================================================================
# Global singleton instance
# =============================================================================
storage_service = StorageService()
