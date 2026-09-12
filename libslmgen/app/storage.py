#!/usr/bin/env python3
"""
Simple Local Storage Service.

Provides basic file storage for uploads using local filesystem.
For the core MVP workflow, data is embedded in notebooks,
so this is used primarily for caching uploaded datasets.

Author: Eshan Roy <eshanized@proton.me>
License: MIT License
Copyright (c) 2026 Eshan Roy
"""

import logging
import re
from pathlib import Path

from fastapi import HTTPException

from .config import settings

logger = logging.getLogger(__name__)

# Path validation regex - prevents traversal
SAFE_PATH_RE = re.compile(r'^[a-zA-Z0-9_\-./]+$')


def _validate_path(path: str) -> None:
    """Validate storage path to prevent traversal attacks."""
    if not path or ".." in path or not SAFE_PATH_RE.match(path):
        raise HTTPException(
            status_code=400,
            detail="Invalid storage path.",
        )


class SimpleStorageService:
    """
    Simple local file storage.

    Stores uploaded files in local filesystem.
    For production with multiple instances, consider Supabase Storage.
    """

    def __init__(self):
        self._storage_dir = Path(settings.upload_dir)
        self._storage_dir.mkdir(parents=True, exist_ok=True)

    @property
    def is_local(self) -> bool:
        """Always local for simplified version."""
        return True

    async def upload_dataset(
        self,
        file_bytes: bytes,
        session_id: str,
        user_id: str | None = None,
        original_filename: str | None = None,
    ) -> str:
        """Upload dataset file."""
        if len(file_bytes) > settings.max_upload_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {settings.max_upload_bytes // (1024*1024)}MB",
            )

        # Build path: datasets/{session_id}.jsonl
        storage_path = f"datasets/{session_id}.jsonl"
        _validate_path(storage_path)

        # Ensure directory exists
        local_path = self._storage_dir / storage_path
        local_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        local_path.write_bytes(file_bytes)

        logger.info(f"Uploaded dataset: {storage_path}")
        return storage_path

    async def upload_notebook(
        self,
        file_bytes: bytes,
        session_id: str,
        user_id: str | None = None,
        original_filename: str | None = None,
    ) -> str:
        """Upload notebook file."""
        filename = original_filename or f"{session_id}.ipynb"
        storage_path = f"notebooks/{filename}"
        _validate_path(storage_path)

        local_path = self._storage_dir / storage_path
        local_path.parent.mkdir(parents=True, exist_ok=True)

        local_path.write_bytes(file_bytes)

        logger.info(f"Uploaded notebook: {storage_path}")
        return storage_path

    async def get_signed_url(self, storage_path: str, expires_in: int = 3600) -> str:
        """Get file URL (returns local path)."""
        _validate_path(storage_path)

        local_path = self._storage_dir / storage_path
        if not local_path.exists():
            raise HTTPException(
                status_code=404,
                detail="File not found.",
            )

        return f"/storage/local/{storage_path}"

    async def delete_file(self, storage_path: str) -> None:
        """Delete a file."""
        _validate_path(storage_path)

        local_path = self._storage_dir / storage_path
        if local_path.exists():
            local_path.unlink()
            logger.info(f"Deleted: {storage_path}")

    async def download_file(self, storage_path: str) -> bytes:
        """Download file content."""
        _validate_path(storage_path)

        local_path = self._storage_dir / storage_path
        if not local_path.exists():
            raise HTTPException(
                status_code=404,
                detail="File not found.",
            )

        return local_path.read_bytes()

    async def file_exists(self, storage_path: str) -> bool:
        """Check if file exists."""
        _validate_path(storage_path)

        local_path = self._storage_dir / storage_path
        return local_path.exists()


async def serve_local_file(storage_path: str) -> tuple[bytes, str]:
    """Serve a file from local storage."""
    _validate_path(storage_path)

    storage = SimpleStorageService()
    local_path = storage._storage_dir / storage_path

    if not local_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")

    ext = local_path.suffix.lower()
    if ext == ".jsonl":
        content_type = "application/jsonl"
    elif ext == ".ipynb":
        content_type = "application/json"
    else:
        content_type = "application/octet-stream"

    return local_path.read_bytes(), content_type


# Global singleton
storage_service = SimpleStorageService()
