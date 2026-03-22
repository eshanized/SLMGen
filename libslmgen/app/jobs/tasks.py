#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Background Job Tasks.

Implements all background job functions for the SLMGEN pipeline.
Each task is designed to be:
- Idempotent: Check if already completed before running
- Fault-tolerant: Handle errors gracefully with retries
- Progress-aware: Update session status throughout execution

Job Pipeline:
    upload → ingest → analyze → recommend → generate

Author: Eshan Roy <eshanized@proton.me>
License: MIT License
Copyright (c) 2026 Eshan Roy
"""

import json
import logging
from typing import Optional, Callable

import redis

from app.config import settings

logger = logging.getLogger(__name__)

# Redis connection for synchronous tasks (RQ workers run sync code)
_redis_client: Optional[redis.Redis] = None


def _get_redis() -> redis.Redis:
    """Get synchronous Redis client for tasks."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.redis_url,
            decode_responses=False,
        )
    return _redis_client


def _serialize(data: dict) -> bytes:
    """Serialize session data."""
    import orjson
    return orjson.dumps(data, option=orjson.OPT_NON_STR_KEYS)


def _deserialize(raw: bytes) -> dict:
    """Deserialize session data."""
    import orjson
    return orjson.loads(raw)


def _get_session(session_id: str) -> Optional[dict]:
    """Get session from Redis."""
    r = _get_redis()
    key = f"session:{session_id}"
    raw = r.get(key)
    if raw is None:
        return None
    return _deserialize(raw)


def _update_session(session_id: str, updates: dict) -> None:
    """Update session in Redis."""
    r = _get_redis()
    key = f"session:{session_id}"
    raw = r.get(key)
    if raw is None:
        raise ValueError(f"Session {session_id} not found")
    
    session = _deserialize(raw)
    session["updated_at"] = _get_timestamp()
    
    if "data" not in session:
        session["data"] = {}
    session["data"].update(updates)
    
    r.set(key, _serialize(session), ex=settings.session_ttl_seconds)


def _get_timestamp() -> str:
    """Get current UTC timestamp."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def get_task_function(func_name: str) -> Optional[Callable]:
    """
    Get a task function by name.
    
    Args:
        func_name: Name of the task function
        
    Returns:
        Task function or None if not found
    """
    tasks = {
        "ingest_task": ingest_task,
        "analyze_task": analyze_task,
        "recommend_task": recommend_task,
        "generate_notebook_task": generate_notebook_task,
    }
    return tasks.get(func_name)


# =============================================================================
# Pipeline Stage: Ingest
# =============================================================================

def ingest_task(session_id: str) -> dict:
    """
    Ingest and validate a dataset.
    
    This task:
    1. Loads dataset from storage
    2. Validates JSONL format
    3. Runs quality checks
    4. Updates session with stats
    
    Idempotent: Skips if analysis_done is already True.
    
    Args:
        session_id: Session UUID
        
    Returns:
        Dict with status and results
    """
    logger.info(f"[ingest_task] Starting for session {session_id}")
    
    # Idempotency check
    session = _get_session(session_id)
    if session is None:
        raise ValueError(f"Session {session_id} not found")
    
    session_data = session.get("data", {})
    if session_data.get("ingest_done"):
        logger.info(f"[ingest_task] Already completed for {session_id}, skipping")
        return {"status": "skipped", "reason": "already_done"}
    
    # Update status to processing
    _update_session(session_id, {
        "job_status": "processing",
        "current_step": "ingest",
        "progress": 0.10,
    })
    
    try:
        # Get dataset from storage
        dataset_path = session_data.get("dataset_path")
        if not dataset_path:
            raise ValueError("No dataset_path in session")
        
        # Download from storage (sync version for RQ)
        file_bytes = _download_from_storage(dataset_path)
        
        # Parse and validate
        data, stats, error = _parse_jsonl(file_bytes)
        
        if error:
            _update_session(session_id, {
                "job_status": "failed",
                "job_error": error,
                "current_step": "ingest",
                "progress": 0.0,
            })
            raise ValueError(error)
        
        # Run quality checks
        quality_score, quality_issues = _validate_quality(data)
        stats["quality_score"] = quality_score
        stats["quality_issues"] = quality_issues
        
        # Update session with results
        _update_session(session_id, {
            "ingest_done": True,
            "raw_data": data,
            "stats": stats,
            "job_status": "processing",
            "current_step": "ingest",
            "progress": 0.25,
        })
        
        logger.info(f"[ingest_task] Completed for {session_id}: {stats.get('total_examples', 0)} examples")
        
        return {
            "status": "success",
            "examples": stats.get("total_examples", 0),
            "quality_score": quality_score,
        }
        
    except Exception as e:
        logger.error(f"[ingest_task] Failed for {session_id}: {e}")
        _update_session(session_id, {
            "job_status": "failed",
            "job_error": str(e),
            "current_step": "ingest",
            "progress": 0.0,
        })
        raise


# =============================================================================
# Pipeline Stage: Analyze
# =============================================================================

def analyze_task(session_id: str) -> dict:
    """
    Analyze dataset characteristics.
    
    This task:
    1. Loads data from session (already ingested)
    2. Runs analysis for model selection hints
    3. Updates session with characteristics
    
    Idempotent: Skips if characteristics already computed.
    
    Args:
        session_id: Session UUID
        
    Returns:
        Dict with analysis results
    """
    logger.info(f"[analyze_task] Starting for session {session_id}")
    
    # Idempotency check
    session = _get_session(session_id)
    if session is None:
        raise ValueError(f"Session {session_id} not found")
    
    session_data = session.get("data", {})
    
    # Ensure ingest was done first
    if not session_data.get("ingest_done"):
        raise ValueError("Ingest not complete. Run ingest_task first.")
    
    if session_data.get("analyze_done"):
        logger.info(f"[analyze_task] Already completed for {session_id}, skipping")
        return {"status": "skipped", "reason": "already_done"}
    
    # Update status
    _update_session(session_id, {
        "job_status": "processing",
        "current_step": "analyze",
        "progress": 0.30,
    })
    
    try:
        # Get data from session
        data = session_data.get("raw_data", [])
        if not data:
            # Try to reload from storage
            dataset_path = session_data.get("dataset_path")
            if dataset_path:
                file_bytes = _download_from_storage(dataset_path)
                data, _, _ = _parse_jsonl(file_bytes)
            else:
                raise ValueError("No data available for analysis")
        
        # Run analysis
        characteristics = _analyze_dataset(data)
        
        # Update session
        _update_session(session_id, {
            "analyze_done": True,
            "characteristics": characteristics,
            "job_status": "processing",
            "current_step": "analyze",
            "progress": 0.50,
        })
        
        logger.info(f"[analyze_task] Completed for {session_id}")
        
        return {
            "status": "success",
            "characteristics": characteristics,
        }
        
    except Exception as e:
        logger.error(f"[analyze_task] Failed for {session_id}: {e}")
        _update_session(session_id, {
            "job_status": "failed",
            "job_error": str(e),
            "current_step": "analyze",
        })
        raise


# =============================================================================
# Pipeline Stage: Recommend
# =============================================================================

def recommend_task(session_id: str) -> dict:
    """
    Generate model recommendations.
    
    This task:
    1. Gets task type and deployment target from session
    2. Generates model recommendations
    3. Updates session with selected model
    
    Idempotent: Skips if already recommended.
    
    Args:
        session_id: Session UUID
        
    Returns:
        Dict with recommendation results
    """
    logger.info(f"[recommend_task] Starting for session {session_id}")
    
    # Idempotency check
    session = _get_session(session_id)
    if session is None:
        raise ValueError(f"Session {session_id} not found")
    
    session_data = session.get("data", {})
    
    # Ensure previous stages done
    if not session_data.get("analyze_done"):
        raise ValueError("Analyze not complete. Run analyze_task first.")
    
    if session_data.get("recommend_done"):
        logger.info(f"[recommend_task] Already completed for {session_id}, skipping")
        return {"status": "skipped", "reason": "already_done"}
    
    # Update status
    _update_session(session_id, {
        "job_status": "processing",
        "current_step": "recommend",
        "progress": 0.55,
    })
    
    try:
        # Get parameters
        task_type = session_data.get("task_type")
        deployment_target = session_data.get("deployment_target")
        stats = session_data.get("stats", {})
        characteristics = session_data.get("characteristics", {})
        
        if not task_type or not deployment_target:
            raise ValueError("task_type and deployment_target required in session")
        
        # Generate recommendations
        from core import get_recommendations
        from app.models import TaskType, DeploymentTarget
        
        recommendations = get_recommendations(
            task=TaskType(task_type),
            deployment=DeploymentTarget(deployment_target),
            stats=stats,
            characteristics=characteristics,
        )
        
        # Update session with recommendation
        _update_session(session_id, {
            "recommend_done": True,
            "selected_model_id": recommendations["primary"]["model_id"],
            "recommendations": recommendations,
            "job_status": "processing",
            "current_step": "recommend",
            "progress": 0.75,
        })
        
        logger.info(f"[recommend_task] Completed for {session_id}: {recommendations['primary']['model_name']}")
        
        return {
            "status": "success",
            "primary_model": recommendations["primary"]["model_id"],
        }
        
    except Exception as e:
        logger.error(f"[recommend_task] Failed for {session_id}: {e}")
        _update_session(session_id, {
            "job_status": "failed",
            "job_error": str(e),
            "current_step": "recommend",
        })
        raise


# =============================================================================
# Pipeline Stage: Generate
# =============================================================================

def generate_notebook_task(session_id: str, model_id: Optional[str] = None) -> dict:
    """
    Generate the training notebook.
    
    This task:
    1. Loads dataset from session or storage
    2. Generates notebook with Jinja2 template
    3. Uploads notebook to storage
    4. Updates session with notebook path
    
    Idempotent: Skips if notebook already generated.
    
    Args:
        session_id: Session UUID
        model_id: Optional model override
        
    Returns:
        Dict with notebook results
    """
    logger.info(f"[generate_notebook_task] Starting for session {session_id}")
    
    # Idempotency check
    session = _get_session(session_id)
    if session is None:
        raise ValueError(f"Session {session_id} not found")
    
    session_data = session.get("data", {})
    
    # Ensure previous stage done
    if not session_data.get("recommend_done"):
        raise ValueError("Recommend not complete. Run recommend_task first.")
    
    if session_data.get("notebook_path") and not model_id:
        logger.info(f"[generate_notebook_task] Notebook already generated for {session_id}, skipping")
        return {"status": "skipped", "reason": "already_done"}
    
    # Update status
    _update_session(session_id, {
        "job_status": "processing",
        "current_step": "generate",
        "progress": 0.80,
    })
    
    try:
        # Get parameters
        selected_model_id = model_id or session_data.get("selected_model_id")
        if not selected_model_id:
            raise ValueError("No model selected")
        
        # Get model info
        from core.recommender import MODELS
        model_info = None
        for spec in MODELS.values():
            if spec.model_id == selected_model_id:
                model_info = (spec.name, spec.size, spec.is_gated)
                break
        
        if model_info is None:
            raise ValueError(f"Invalid model_id: {selected_model_id}")
        
        model_name, model_size, is_gated = model_info
        
        # Load dataset
        dataset_content = _load_dataset_content(session_data)
        
        # Get task type
        task_type = session_data.get("task_type", "general")
        stats = session_data.get("stats", {})
        
        # Generate notebook
        from core import generate_notebook
        notebook_json = generate_notebook(
            dataset_jsonl=dataset_content,
            model_id=selected_model_id,
            model_name=model_name,
            model_size=model_size,
            task_type=task_type,
            num_examples=stats.get("total_examples", 0),
            is_gated=is_gated,
        )
        
        # Upload to storage
        notebook_path = _upload_notebook_to_storage(
            session_id=session_id,
            notebook_content=notebook_json,
            model_name=model_name,
        )
        
        # Update session
        _update_session(session_id, {
            "notebook_path": notebook_path,
            "job_status": "completed",
            "current_step": "generate",
            "progress": 1.0,
        })
        
        logger.info(f"[generate_notebook_task] Completed for {session_id}")
        
        return {
            "status": "success",
            "notebook_path": notebook_path,
        }
        
    except Exception as e:
        logger.error(f"[generate_notebook_task] Failed for {session_id}: {e}")
        _update_session(session_id, {
            "job_status": "failed",
            "job_error": str(e),
            "current_step": "generate",
        })
        raise


# =============================================================================
# Helper Functions
# =============================================================================

def _download_from_storage(storage_path: str) -> bytes:
    """
    Download file from storage synchronously.
    
    For RQ workers, we use synchronous redis client for file operations.
    """
    # Check if using local or supabase
    from app.storage import storage_service, BUCKET_DATASETS, BUCKET_NOTEBOOKS
    
    if storage_service.is_local_fallback:
        # Local filesystem
        from app.config import settings
        from pathlib import Path
        local_path = Path(settings.upload_dir) / storage_path
        return local_path.read_bytes()
    else:
        # Supabase Storage
        from supabase import Client
        from app.supabase import get_supabase_client
        
        client: Client = get_supabase_client()
        storage = client.storage
        
        # Determine bucket
        if storage_path.startswith(BUCKET_DATASETS + "/"):
            bucket = BUCKET_DATASETS
        elif storage_path.startswith(BUCKET_NOTEBOOKS + "/"):
            bucket = BUCKET_NOTEBOOKS
        else:
            raise ValueError(f"Unknown bucket in path: {storage_path}")
        
        return storage.from_(bucket).download(storage_path)


def _upload_notebook_to_storage(
    session_id: str,
    notebook_content: str,
    model_name: str,
) -> str:
    """Upload notebook to storage synchronously."""
    from app.storage import storage_service, BUCKET_NOTEBOOKS
    import time
    
    filename = f"finetune_{model_name.lower().replace(' ', '_')}_{session_id[:8]}_{int(time.time())}.ipynb"
    
    if storage_service.is_local_fallback:
        # Local filesystem
        from app.config import settings
        from pathlib import Path
        
        local_dir = Path(settings.upload_dir) / BUCKET_NOTEBOOKS
        local_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = local_dir / filename
        file_path.write_bytes(notebook_content.encode("utf-8"))
        
        return f"{BUCKET_NOTEBOOKS}/{filename}"
    else:
        # Supabase Storage
        from app.supabase import get_supabase_client
        
        client = get_supabase_client()
        storage = client.storage
        
        storage.from_(BUCKET_NOTEBOOKS).upload(
            f"{BUCKET_NOTEBOOKS}/{filename}",
            notebook_content.encode("utf-8"),
            {"content-type": "application/json"},
            file_options={"upsert": True},
        )
        
        return f"{BUCKET_NOTEBOOKS}/{filename}"


def _parse_jsonl(file_bytes: bytes) -> tuple[list[dict], dict, Optional[str]]:
    """
    Parse and validate JSONL data.
    
    Returns:
        - data: List of valid conversation dicts
        - stats: Stats dict
        - error: Error message if failed
    """
    MIN_EXAMPLES = 50
    
    def estimate_tokens(text: str) -> int:
        return max(1, len(text) // 4)
    
    def validate_message(msg: dict) -> tuple[bool, str]:
        if not isinstance(msg, dict):
            return False, "message must be a dict"
        role = msg.get("role")
        content = msg.get("content")
        if role not in ("user", "assistant", "system"):
            return False, f"invalid role: {role}"
        if not isinstance(content, str):
            return False, "content must be a string"
        return True, ""
    
    def validate_conversation(entry: dict, idx: int) -> tuple[bool, str]:
        if not isinstance(entry, dict):
            return False, f"Line {idx}: must be a JSON object"
        messages = entry.get("messages")
        if not isinstance(messages, list):
            return False, f"Line {idx}: missing or invalid 'messages' array"
        if len(messages) < 2:
            return False, f"Line {idx}: need at least 2 messages"
        has_user = False
        has_assistant = False
        for i, msg in enumerate(messages):
            valid, err = validate_message(msg)
            if not valid:
                return False, f"Line {idx}, message {i}: {err}"
            if msg.get("role") == "user":
                has_user = True
            elif msg.get("role") == "assistant":
                has_assistant = True
        if not has_user:
            return False, f"Line {idx}: must have at least one user message"
        if not has_assistant:
            return False, f"Line {idx}: must have at least one assistant message"
        return True, ""
    
    data: list[dict] = []
    errors: list[str] = []
    total_tokens = 0
    single_turn = 0
    multi_turn = 0
    has_system = False
    
    content = file_bytes.decode("utf-8")
    lines = content.strip().split("\n")
    
    for line_num, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue
        
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as e:
            errors.append(f"Line {line_num}: Invalid JSON - {e}")
            continue
        
        valid, err = validate_conversation(entry, line_num)
        if not valid:
            errors.append(err)
            continue
        
        messages = entry["messages"]
        data.append(entry)
        
        for msg in messages:
            total_tokens += estimate_tokens(msg.get("content", ""))
            if msg.get("role") == "system":
                has_system = True
        
        non_system = [m for m in messages if m.get("role") != "system"]
        if len(non_system) == 2:
            single_turn += 1
        else:
            multi_turn += 1
    
    if len(data) < MIN_EXAMPLES:
        return [], {}, (
            f"Need at least {MIN_EXAMPLES} examples. "
            f"You only have {len(data)}. Maybe try adding more data?"
        )
    
    total = len(data)
    single_pct = int((single_turn / total) * 100) if total > 0 else 0
    multi_pct = 100 - single_pct
    avg_tokens = total_tokens // total if total > 0 else 0
    
    stats = {
        "total_examples": total,
        "total_tokens": total_tokens,
        "avg_tokens_per_example": avg_tokens,
        "single_turn_pct": single_pct,
        "multi_turn_pct": multi_pct,
        "has_system_prompts": has_system,
        "quality_score": 1.0,
        "quality_issues": [],
    }
    
    return data, stats, None


def _validate_quality(data: list[dict]) -> tuple[float, list[str]]:
    """Run quality checks on dataset."""
    from core import validate_quality
    return validate_quality(data)


def _analyze_dataset(data: list[dict]) -> dict:
    """Analyze dataset characteristics."""
    from core import analyze_dataset
    result = analyze_dataset(data)
    return result.model_dump()


def _load_dataset_content(session_data: dict) -> str:
    """Load dataset content from session or storage."""
    raw_data = session_data.get("raw_data")
    if raw_data and isinstance(raw_data, list):
        lines = []
        for entry in raw_data:
            lines.append(json.dumps(entry))
        return "\n".join(lines)
    
    dataset_path = session_data.get("dataset_path")
    if dataset_path:
        file_bytes = _download_from_storage(dataset_path)
        return file_bytes.decode("utf-8")
    
    raise ValueError("Dataset not available")
