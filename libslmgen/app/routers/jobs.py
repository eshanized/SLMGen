"""
Jobs Router.

CRUD operations for fine-tuning jobs with Supabase storage.

These endpoints require a Supabase database connection to store job history.
When running with AUTH_DISABLED=true (local dev mode), these endpoints will
return a 503 error with a helpful message explaining how to enable them.

The core workflow (upload → analyze → recommend → generate) works fine
without Supabase - only job history persistence needs the database.

Contributor: Vedant Singh Rajput <teleported0722@gmail.com>

@author Eshan Roy <eshanized@proton.me>
@license MIT
@copyright 2026 Eshan Roy
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timezone

from app.middleware.auth import get_current_user, AuthenticatedUser
from app.supabase import get_supabase_client, is_supabase_configured

router = APIRouter(prefix="/jobs", tags=["jobs"])


# ============================================
# HELPER FUNCTIONS
# ============================================

def _require_supabase():
    """
    Check if Supabase is configured, raise helpful error if not.
    
    This is called at the start of each jobs endpoint. If you're running
    locally with AUTH_DISABLED=true, you probably don't have Supabase set up,
    and that's totally fine! This returns a friendly error explaining the situation.
    
    Why 503 (Service Unavailable)?
        It's the right status code for "this feature exists but isn't available right now"
        The client can retry later when Supabase is configured.
    
    Raises:
        HTTPException: 503 if Supabase is not configured
    """
    if not is_supabase_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Job history requires Supabase database connection. "
                "To enable: set SUPABASE_URL, SUPABASE_ANON_KEY, and SUPABASE_SERVICE_KEY "
                "environment variables. See docs/SUPABASE.md for setup instructions. "
                "The core workflow (upload → analyze → recommend → generate) works without this!"
            )
        )


# ============================================
# MODELS
# ============================================

class JobCreate(BaseModel):
    session_id: str
    dataset_filename: str
    dataset_path: str
    total_examples: int
    total_tokens: int
    quality_score: float
    task_type: str
    deployment_target: str
    selected_model_id: str
    selected_model_name: str
    model_score: float
    training_config: dict = {}


class JobUpdate(BaseModel):
    notebook_filename: Optional[str] = None
    notebook_path: Optional[str] = None
    colab_url: Optional[str] = None
    status: Optional[str] = None
    training_config: Optional[dict] = None


class JobResponse(BaseModel):
    id: str
    user_id: str
    session_id: str
    dataset_filename: str
    dataset_path: str
    total_examples: int
    total_tokens: int
    quality_score: float
    task_type: str
    deployment_target: str
    selected_model_id: str
    selected_model_name: str
    model_score: float
    training_config: dict
    notebook_filename: Optional[str] = None
    notebook_path: Optional[str] = None
    colab_url: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime


# ============================================
# ENDPOINTS
# ============================================

@router.get("", response_model=List[JobResponse])
async def list_jobs(
    user: AuthenticatedUser = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0
):
    """
    List all jobs for the current user.
    
    Returns a paginated list of the user's fine-tuning jobs, newest first.
    Each job contains the full configuration and status.
    
    Note: Requires Supabase database connection. Returns 503 in local dev mode.
    """
    _require_supabase()
    
    supabase = get_supabase_client()
    
    response = supabase.table("jobs") \
        .select("*") \
        .eq("user_id", user.id) \
        .order("created_at", desc=True) \
        .range(offset, offset + limit - 1) \
        .execute()
    
    return response.data


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """Get a specific job by ID."""
    _require_supabase()
    supabase = get_supabase_client()
    
    response = supabase.table("jobs") \
        .select("*") \
        .eq("id", job_id) \
        .eq("user_id", user.id) \
        .single() \
        .execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    return response.data


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job: JobCreate,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """Create a new job record."""
    _require_supabase()
    supabase = get_supabase_client()
    
    job_data = {
        **job.model_dump(),
        "user_id": user.id,
        "status": "created"
    }
    
    response = supabase.table("jobs") \
        .insert(job_data) \
        .execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create job"
        )
    
    return response.data[0]


@router.patch("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: str,
    updates: JobUpdate,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """Update a job record."""
    _require_supabase()
    supabase = get_supabase_client()
    
    # Filter out None values
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update fields provided"
        )
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    response = supabase.table("jobs") \
        .update(update_data) \
        .eq("id", job_id) \
        .eq("user_id", user.id) \
        .execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    return response.data[0]


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: str,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """Delete a job and its associated files."""
    _require_supabase()
    supabase = get_supabase_client()
    
    # Get job first to check ownership and get file paths
    job_response = supabase.table("jobs") \
        .select("*") \
        .eq("id", job_id) \
        .eq("user_id", user.id) \
        .single() \
        .execute()
    
    if not job_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    job = job_response.data
    
    # Delete associated files from storage
    try:
        if job.get("dataset_path"):
            supabase.storage.from_("datasets").remove([job["dataset_path"]])
        if job.get("notebook_path"):
            supabase.storage.from_("notebooks").remove([job["notebook_path"]])
    except Exception:
        pass  # Continue even if file deletion fails
    
    # Delete job record
    supabase.table("jobs") \
        .delete() \
        .eq("id", job_id) \
        .eq("user_id", user.id) \
        .execute()
    
    return None


@router.get("/session/{session_id}", response_model=JobResponse)
async def get_job_by_session(
    session_id: str,
    user: AuthenticatedUser = Depends(get_current_user)
):
    """Get a job by session ID."""
    _require_supabase()
    supabase = get_supabase_client()
    
    response = supabase.table("jobs") \
        .select("*") \
        .eq("session_id", session_id) \
        .eq("user_id", user.id) \
        .single() \
        .execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    return response.data
