# Storage Service — Architecture Walkthrough

## 1. Architecture Overview

### Why Object Storage?

The previous filesystem-based upload system had critical production flaws:
- **No horizontal scaling**: Files stored on one instance's disk can't be accessed by other instances
- **Data loss on restart**: Instance failure means data loss
- **No CDN integration**: Can't serve files through a CDN for global performance
- **No access control**: Anyone with the file path could access files

Object storage solves these by providing:
1. **Shared access**: Any backend instance can read/write to the same files
2. **Durability**: Files survive instance failures (typically 99.99%+ durability)
3. **CDN-ready**: Can serve through CDN with signed URLs
4. **Access control**: Signed URLs with expiration for secure access

### Storage Backends

```
┌──────────────────────────────────────────────────────────────┐
│                    StorageService                            │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌───────────────────┐      ┌──────────────────┐            │
│   │  Supabase Storage │────▶│  S3-Compatible   │            │
│   │  (Production)     │      │  (AWS/GCS/Azure) │            │
│   └───────────────────┘      └──────────────────┘            │
│            │                                                 │
│            │ (fallback if not configured)                    │
│            ▼                                                 │
│   ┌──────────────────┐                                       │
│   │  Local Filesystem│  ← Dev mode only!                     │
│   │  (./uploads/)    │                                       │
│   └──────────────────┘                                       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Data Model

Files are stored with a consistent path structure:

```
datasets/{user_namespace}/{session_id}.jsonl
notebooks/{user_namespace}/{filename}.ipynb
```

**Path components:**
- `datasets` or `notebooks`: Bucket name
- `{user_namespace}`: Sanitized user ID (or "anonymous" for unauthenticated)
- `{session_id}`: UUID for the session
- `{filename}`: Original filename for notebooks

**User namespace rules:**
- Authenticated users: Sanitized user ID (alphanumeric + `_` `-`)
- Anonymous users: `"anonymous"`
- Special characters replaced with `_`
- Maximum 64 characters

---

## 2. Storage Service API

### Core Methods

```python
class StorageService:
    # Upload files
    async def upload_dataset(
        file_bytes: bytes,
        session_id: str,
        user_id: Optional[str] = None,
    ) -> str  # Returns storage path
    
    async def upload_notebook(
        file_bytes: bytes,
        session_id: str,
        user_id: Optional[str] = None,
        original_filename: Optional[str] = None,
    ) -> str  # Returns storage path
    
    # Access files
    async def get_signed_url(
        storage_path: str,
        expires_in: int = 3600,  # 1 hour default
    ) -> str  # Returns signed download URL
    
    async def download_file(storage_path: str) -> bytes
    
    # Delete files
    async def delete_file(storage_path: str) -> None
    
    # Check existence
    async def file_exists(storage_path: str) -> bool
```

### Upload Flow

```
Client                              Backend                          Storage
   |                                   |                                |
   |--- POST /upload ----------------->|                                |
   |   (multipart form data)           |                                |
   |                                   |                                |
   |                                   | 1. Validate size               |
   |                                   | 2. Build storage path          |
   |                                   | 3. Upload to Supabase/Local    |
   |                                   |                                |
   |<-- 200 {storage_path, url} -------|                                |
```

1. **Size validation**: Check against `settings.max_upload_bytes` (100MB default)
2. **Path building**: Construct path from session_id, user_id, and file type
3. **Upload**: Upload to Supabase Storage or local filesystem
4. **Return**: Return storage path for later reference

---

## 3. Supabase Storage Integration

### Bucket Configuration

Two buckets are required:

| Bucket | Purpose | ACL |
|--------|---------|-----|
| `datasets` | User-uploaded JSONL files | Private |
| `notebooks` | Generated Colab notebooks | Private |

**RLS Policies:**
- Users can only access files in their own namespace
- Service role can access all files (for cleanup jobs)

### Upload Implementation

```python
async def _upload_to_supabase(
    self,
    bucket: str,
    path: str,
    file_bytes: bytes,
    content_type: str,
) -> str:
    client = get_supabase_client()
    storage = client.storage
    
    # Convert bytes to file-like object
    file_obj = io.BytesIO(file_bytes)
    
    # Upload with upsert
    storage.from_(bucket).upload(
        path,
        file_obj,
        {"content-type": content_type},
        file_options={"upsert": True},
    )
    
    return path
```

### Signed URL Generation

```python
async def _get_supabase_signed_url(
    self,
    bucket: str,
    path: str,
    expires_in: int = 3600,
) -> str:
    client = get_supabase_client()
    storage = client.storage
    
    result = storage.from_(bucket).create_signed_url(
        path,
        expires_in,
    )
    
    return result.get("signedURL", "")
```

**Signed URL behavior:**
- URLs expire after `expires_in` seconds
- Maximum TTL: 24 hours (86400 seconds)
- Anyone with the URL can access the file until expiry

---

## 4. Local Fallback Mode

### When Used

Local fallback activates when:
1. `Supabase` is not configured (env vars missing)
2. `fallback_to_local=True` was passed to constructor

### Development Warning

```
WARNING: Supabase not configured. Using local filesystem storage. 
This is NOT recommended for production!
```

### Local Upload Implementation

```python
async def _upload_to_local(self, path: str, file_bytes: bytes) -> str:
    local_dir = Path(settings.upload_dir)
    local_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert storage path to local path
    local_path = local_dir / path
    local_path.parent.mkdir(parents=True, exist_ok=True)
    
    async with aiofiles.open(local_path, "wb") as f:
        await f.write(file_bytes)
    
    return path
```

### Local URL Format

In local mode, `get_signed_url()` returns an internal path:

```
/storage/local/{storage_path}
```

This path should be handled by a dedicated endpoint in `main.py`:

```python
@router.get("/storage/local/{path:path}")
async def serve_local_file(path: str):
    content, content_type = await storage.serve_local_file(path)
    return Response(content=content, media_type=content_type)
```

---

## 5. Security Considerations

### Path Traversal Prevention

All storage paths are validated before use:

```python
SAFE_PATH_RE = re.compile(r'^[a-zA-Z0-9_\-./]+$')

def _validate_path(path: str) -> None:
    if not path or ".." in path or not SAFE_PATH_RE.match(path):
        raise HTTPException(status_code=400, detail="Invalid storage path.")
```

**Blocked patterns:**
- `../` (directory traversal)
- `..` (anywhere in path)
- Special characters: `!@#$%^&*()+=[]{}|\\:"";<>?`
- Empty paths

### File Type Validation

Only specific extensions are allowed:

| File Type | Allowed Extensions |
|-----------|-------------------|
| Dataset | `.jsonl` |
| Notebook | `.ipynb` |

### Size Limits

- Maximum upload size: `settings.max_upload_bytes` (default 100MB)
- Rejected with HTTP 413 if exceeded

### Signed URL Expiration

- Default: 1 hour
- Maximum: 24 hours
- Prevents long-term exposure of URLs

---

## 6. Integration with Routers

### Upload Router

Updated to use `storage_service`:

```python
@router.post("/upload")
async def upload_file(...):
    # Read file bytes
    contents = await file.read()
    
    # Upload to storage
    storage_path = await storage_service.upload_dataset(
        file_bytes=contents,
        session_id=session_id,
        user_id=user.id if user else None,
    )
    
    # Update session with storage path
    session_store.update(session_id, dataset_storage_path=storage_path)
```

### Generate Router

Notebooks are uploaded to storage:

```python
@router.post("/generate-notebook")
async def generate_notebook(...):
    # Generate notebook
    notebook_bytes = generate_notebook(...)
    
    # Upload to storage
    notebook_path = await storage_service.upload_notebook(
        file_bytes=notebook_bytes,
        session_id=session_id,
        user_id=user.id if user else None,
        original_filename="training.ipynb",
    )
    
    # Get download URL
    download_url = await storage_service.get_signed_url(notebook_path)
```

### Preview/Analysis Routers

Files are loaded from storage when needed:

```python
@router.get("/preview/{session_id}")
async def preview_dataset(session_id: str, ...):
    # Get storage path from session
    session = session_store.get(session_id)
    storage_path = session.dataset_storage_path
    
    # Download from storage
    file_bytes = await storage_service.download_file(storage_path)
    
    # Process and return
    return process_preview(file_bytes)
```

---

## 7. Error Handling

### Error Codes

| Code | Scenario | Response |
|------|----------|----------|
| 400 | Invalid path or file type | `"Invalid storage path."` |
| 404 | File not found | `"File not found."` |
| 413 | File too large | `"File too large. Maximum size is X MB"` |
| 503 | Storage service unavailable | `"Storage service temporarily unavailable."` |

### Supabase Unavailable

If Supabase Storage is down:
1. Uploads return 503 with retry message
2. Downloads return 404 (file not accessible)
3. Signed URLs fail to generate

### Graceful Degradation

The service doesn't fail catastrophically:
- If one bucket fails, others still work
- If Supabase fails, local fallback can be used (with warning)
- Errors are logged for debugging

---

## 8. Configuration

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `UPLOAD_DIR` | `./uploads` | Local fallback directory |
| `MAX_UPLOAD_BYTES` | `104857600` (100MB) | Maximum file size |
| `SUPABASE_URL` | — | Supabase project URL |
| `SUPABASE_ANON_KEY` | — | Supabase anon key |
| `SUPABASE_SERVICE_ROLE_KEY` | — | Supabase service role |

### Settings Object

```python
class Settings(BaseSettings):
    upload_dir: str = "./uploads"
    max_upload_bytes: int = 100 * 1024 * 1024  # 100 MB
    
    # Supabase (optional)
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
```

---

## 9. Testing Strategy

### Unit Tests

Test individual methods with mocked backends:

```python
@pytest.mark.asyncio
async def test_local_upload():
    with tempfile.TemporaryDirectory() as tmpdir:
        mock_settings = MagicMock()
        mock_settings.upload_dir = tmpdir
        mock_settings.max_upload_bytes = 100 * 1024 * 1024
        
        with patch.object(storage_module, 'settings', mock_settings):
            with patch.object(storage_module, 'is_supabase_configured', return_value=False):
                service = StorageService(fallback_to_local=True)
                
                path = await service.upload_dataset(data, session_id, None)
                
                assert Path(tmpdir) / path exists
```

### Validation Tests

Test path validation, file type checking, and error cases:

```python
def test_validate_path_traversal():
    with pytest.raises(HTTPException) as exc_info:
        _validate_path("../etc/passwd")
    assert exc_info.value.status_code == 400
```

### Integration Tests

Test end-to-end workflows with real storage (when configured):

```python
@pytest.mark.integration
async def test_supabase_upload_flow():
    # Requires SUPABASE_* env vars
    service = StorageService(fallback_to_local=False)
    
    path = await service.upload_dataset(data, session_id, "user123")
    url = await service.get_signed_url(path)
    
    # Verify URL works
    response = requests.get(url)
    assert response.status_code == 200
```

---

## 10. Future Enhancements

### Planned Features

1. **Multipart uploads**: For files > 50MB, use multipart upload for reliability
2. **Upload progress**: Real-time progress via WebSocket/SSE
3. **CDN integration**: Serve files through Cloudflare/Fastly
4. **Automatic cleanup**: TTL-based cleanup of orphaned files
5. **Upload quotas**: Per-user storage limits

### Alternative Backends

The architecture supports adding other backends:

```python
class StorageBackend(Enum):
    SUPABASE = "supabase"
    S3 = "s3"
    GCS = "gcs"
    AZURE = "azure"
    LOCAL = "local"
```

Each backend implements the same interface, allowing transparent switching.

---

## 11. Migration Checklist

To migrate from filesystem to storage service:

- [x] Create `StorageService` class
- [x] Implement Supabase Storage operations
- [x] Implement local filesystem fallback
- [x] Update `upload.py` router
- [x] Update `generate.py` router
- [x] Update `preview.py` router
- [x] Update `analyze.py` router
- [x] Update `recommend.py` router
- [x] Create `serve_local_file` endpoint
- [x] Add path validation tests
- [x] Add upload/download tests
- [x] Add error handling tests
- [x] Create this documentation
