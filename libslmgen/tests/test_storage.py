#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Storage Service.

Covers:
- Upload dataset / notebook
- Signed URL generation
- File deletion
- Failure scenarios
- Local fallback mode
- Path validation

Author: Eshan Roy <eshanized@proton.me>
License: MIT License
Copyright (c) 2026 Eshan Roy
"""

import json
import os
import tempfile
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from fastapi import HTTPException

# Import directly from storage module
import app.storage as storage_module
from app.storage import (
    StorageService,
    StorageBackend,
    FileType,
    _validate_path,
    _validate_file_type,
    _get_user_namespace,
    _build_storage_path,
    BUCKET_DATASETS,
    BUCKET_NOTEBOOKS,
)


# ============================================
# HELPERS
# ============================================

def valid_session_id():
    """Generate a valid UUID."""
    return str(uuid.uuid4())


def sample_jsonl_data():
    """Generate sample JSONL content."""
    entries = [
        {"messages": [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi!"}]},
        {"messages": [{"role": "user", "content": "How are you?"}, {"role": "assistant", "content": "I'm good!"}]},
    ]
    return "\n".join(json.dumps(e) for e in entries).encode("utf-8")


# ============================================
# VALIDATION TESTS
# ============================================

class TestPathValidation:
    """Test path validation functions."""

    def test_validate_path_valid(self):
        """Valid paths pass."""
        _validate_path("datasets/anonymous/abc123.jsonl")
        _validate_path("notebooks/user_id/file.ipynb")
        _validate_path("a/b/c/d.jsonl")

    def test_validate_path_traversal(self):
        """Path traversal attempts raise 400."""
        with pytest.raises(HTTPException) as exc_info:
            _validate_path("../etc/passwd")
        assert exc_info.value.status_code == 400
        
        with pytest.raises(HTTPException) as exc_info:
            _validate_path("datasets/../../etc/passwd")
        assert exc_info.value.status_code == 400

    def test_validate_path_empty(self):
        """Empty path raises 400."""
        with pytest.raises(HTTPException) as exc_info:
            _validate_path("")
        assert exc_info.value.status_code == 400

    def test_validate_path_special_chars(self):
        """Special characters raise 400."""
        with pytest.raises(HTTPException) as exc_info:
            _validate_path("datasets/../../../etc/passwd")
        assert exc_info.value.status_code == 400


class TestFileTypeValidation:
    """Test file type validation."""

    def test_valid_dataset_extension(self):
        """Valid .jsonl extension passes."""
        _validate_file_type("data.jsonl", FileType.DATASET)
        _validate_file_type("train.jsonl", FileType.DATASET)

    def test_valid_notebook_extension(self):
        """Valid .ipynb extension passes."""
        _validate_file_type("notebook.ipynb", FileType.NOTEBOOK)
        _validate_file_type("train.ipynb", FileType.NOTEBOOK)

    def test_invalid_extension(self):
        """Wrong extension raises 400."""
        with pytest.raises(HTTPException) as exc_info:
            _validate_file_type("data.txt", FileType.DATASET)
        assert exc_info.value.status_code == 400


class TestUserNamespace:
    """Test user namespace generation."""

    def test_authenticated_user(self):
        """Authenticated users get sanitized namespace."""
        ns = _get_user_namespace("user-123")
        assert ns == "user-123"

    def test_anonymous_user(self):
        """Anonymous users get 'anonymous' namespace."""
        assert _get_user_namespace(None) == "anonymous"
        assert _get_user_namespace("anonymous") == "anonymous"

    def test_sanitize_special_chars(self):
        """Special characters are sanitized."""
        ns = _get_user_namespace("user@example.com")
        assert "@" not in ns


class TestStoragePathBuilding:
    """Test storage path construction."""

    def test_dataset_path(self):
        """Dataset paths are correctly formatted."""
        sid = valid_session_id()
        path = _build_storage_path(FileType.DATASET, sid, None)
        assert path.startswith(f"{BUCKET_DATASETS}/anonymous/")
        assert path.endswith(".jsonl")

    def test_notebook_path(self):
        """Notebook paths are correctly formatted."""
        sid = valid_session_id()
        path = _build_storage_path(FileType.NOTEBOOK, sid, "user123")
        assert path.startswith(f"{BUCKET_NOTEBOOKS}/user123/")
        assert path.endswith(".ipynb")


# ============================================
# LOCAL FALLBACK TESTS
# ============================================

class TestLocalFallback:
    """Test local filesystem fallback."""

    @pytest.mark.asyncio
    async def test_local_upload(self):
        """Local upload works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_settings = MagicMock()
            mock_settings.upload_dir = tmpdir
            mock_settings.max_upload_bytes = 100 * 1024 * 1024
            
            with patch.object(storage_module, 'settings', mock_settings):
                with patch.object(storage_module, 'is_supabase_configured', return_value=False):
                    service = StorageService(fallback_to_local=True)
                    assert service._backend == StorageBackend.LOCAL
                    
                    sid = valid_session_id()
                    data = sample_jsonl_data()
                    
                    path = await service.upload_dataset(data, sid, None)
                    
                    # Verify file was created
                    file_path = Path(tmpdir) / path
                    assert file_path.exists()
                    assert file_path.read_bytes() == data

    @pytest.mark.asyncio
    async def test_local_signed_url(self):
        """Local signed URL returns internal path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_settings = MagicMock()
            mock_settings.upload_dir = tmpdir
            mock_settings.max_upload_bytes = 100 * 1024 * 1024
            
            with patch.object(storage_module, 'settings', mock_settings):
                with patch.object(storage_module, 'is_supabase_configured', return_value=False):
                    service = StorageService(fallback_to_local=True)
                    
                    sid = valid_session_id()
                    data = sample_jsonl_data()
                    path = await service.upload_dataset(data, sid, None)
                    
                    # Local signed URL returns internal path
                    url = await service.get_signed_url(path)
                    assert "/storage/local/" in url

    @pytest.mark.asyncio
    async def test_local_delete(self):
        """Local file deletion works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_settings = MagicMock()
            mock_settings.upload_dir = tmpdir
            mock_settings.max_upload_bytes = 100 * 1024 * 1024
            
            with patch.object(storage_module, 'settings', mock_settings):
                with patch.object(storage_module, 'is_supabase_configured', return_value=False):
                    service = StorageService(fallback_to_local=True)
                    
                    sid = valid_session_id()
                    data = sample_jsonl_data()
                    path = await service.upload_dataset(data, sid, None)
                    
                    # Verify file exists
                    file_path = Path(tmpdir) / path
                    assert file_path.exists()
                    
                    # Delete
                    await service.delete_file(path)
                    
                    # Verify file is gone
                    assert not file_path.exists()


# ============================================
# INTEGRATION-STYLE TESTS
# ============================================

class TestStorageWithSession:
    """Test storage integration with session workflow."""

    @pytest.mark.asyncio
    async def test_upload_updates_session_path(self):
        """After upload, session has dataset_path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_settings = MagicMock()
            mock_settings.upload_dir = tmpdir
            mock_settings.max_upload_bytes = 100 * 1024 * 1024
            
            with patch.object(storage_module, 'settings', mock_settings):
                with patch.object(storage_module, 'is_supabase_configured', return_value=False):
                    service = StorageService(fallback_to_local=True)
                    
                    sid = valid_session_id()
                    data = sample_jsonl_data()
                    
                    path = await service.upload_dataset(data, sid, "user123")
                    
                    # Path should be stored in session
                    assert path.startswith(f"{BUCKET_DATASETS}/user123/")

    @pytest.mark.asyncio
    async def test_download_after_upload(self):
        """Can download file after uploading."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_settings = MagicMock()
            mock_settings.upload_dir = tmpdir
            mock_settings.max_upload_bytes = 100 * 1024 * 1024
            
            with patch.object(storage_module, 'settings', mock_settings):
                with patch.object(storage_module, 'is_supabase_configured', return_value=False):
                    service = StorageService(fallback_to_local=True)
                    
                    sid = valid_session_id()
                    data = sample_jsonl_data()
                    
                    path = await service.upload_dataset(data, sid, None)
                    
                    # Download should return same data
                    downloaded = await service.download_file(path)
                    assert downloaded == data


# ============================================
# ERROR HANDLING TESTS
# ============================================

class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.asyncio
    async def test_file_too_large(self):
        """Oversized files are rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_settings = MagicMock()
            mock_settings.upload_dir = tmpdir
            mock_settings.max_upload_bytes = 100 * 1024 * 1024  # 100MB
            
            with patch.object(storage_module, 'settings', mock_settings):
                with patch.object(storage_module, 'is_supabase_configured', return_value=False):
                    service = StorageService(fallback_to_local=True)
                    
                    # Create data larger than max
                    large_data = b"x" * (101 * 1024 * 1024)
                    
                    with pytest.raises(HTTPException) as exc_info:
                        await service.upload_dataset(large_data, valid_session_id(), None)
                    
                    assert exc_info.value.status_code == 413

    @pytest.mark.asyncio
    async def test_file_not_found_on_download(self):
        """Missing file returns 404."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_settings = MagicMock()
            mock_settings.upload_dir = tmpdir
            mock_settings.max_upload_bytes = 100 * 1024 * 1024
            
            with patch.object(storage_module, 'settings', mock_settings):
                with patch.object(storage_module, 'is_supabase_configured', return_value=False):
                    service = StorageService(fallback_to_local=True)
                    
                    with pytest.raises(HTTPException) as exc_info:
                        await service.download_file("datasets/nonexistent/file.jsonl")
                    
                    assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_bucket_in_path(self):
        """Invalid bucket in path is rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_settings = MagicMock()
            mock_settings.upload_dir = tmpdir
            mock_settings.max_upload_bytes = 100 * 1024 * 1024
            
            with patch.object(storage_module, 'settings', mock_settings):
                with patch.object(storage_module, 'is_supabase_configured', return_value=False):
                    service = StorageService(fallback_to_local=True)
                    
                    # Path with unknown bucket should fail URL generation
                    with pytest.raises(HTTPException) as exc_info:
                        await service.get_signed_url("unknown_bucket/file.jsonl")
                    
                    assert exc_info.value.status_code == 400


# ============================================
# PERFORMANCE TESTS
# ============================================

class TestPerformance:
    """Test performance-related functionality."""

    def test_max_file_size_from_config(self):
        """Max file size comes from config."""
        # This test verifies the config is used
        from app.config import settings
        assert settings.max_upload_bytes == 100 * 1024 * 1024

    def test_signed_url_expiry_clamped(self):
        """Signed URL expiry is clamped to max."""
        from app.storage import MAX_SIGNED_URL_TTL
        assert MAX_SIGNED_URL_TTL == 86400  # 24 hours
