# Background Job System — Architecture Walkthrough

## 1. Why Background Jobs Are Required

### The Problem with Synchronous Execution

The original SLMGEN architecture executed all heavy operations inside HTTP request handlers:

```
Client → HTTP Request → Upload → Ingest → Analyze → Recommend → Generate → Response
         ↑                                                    ↑
         └──────────────── 60+ seconds wait ──────────────────┘
```

This causes several critical problems:

1. **Worker starvation**: A single request blocking a worker for 60s means that worker can't handle other requests. With 4 workers and 10 concurrent users, you can have 6 users waiting indefinitely.

2. **HTTP timeout**: Most clients timeout after 30-60 seconds. Long-running operations get aborted, leaving data in an inconsistent state.

3. **No progress visibility**: Users see a spinning loader with no indication of what's happening or how long it will take.

4. **No retry mechanism**: If a step fails (network blip, temporary API outage), the entire operation fails and the user must start over.

5. **Resource inefficiency**: Heavy operations (dataset parsing, notebook generation) consume memory and CPU while the HTTP connection is held open.

### The Solution: Background Jobs with Redis Queue

By moving heavy operations to background jobs, we achieve:

```
Client → HTTP Request → Upload → Response (immediate)
                                    ↓
                              Queue Job
                                    ↓
                        Worker Process (background)
                                    ↓
                              Progress Updates
                                    ↓
                         User Polls Status
```

Benefits:
- **Non-blocking**: HTTP response returns in < 1 second
- **Scalable**: Add more workers without changing code
- **Retryable**: Failed jobs can be automatically retried
- **Visible**: Users see real-time progress
- **Resilient**: Worker crash doesn't affect HTTP handlers

---

## 2. How the Job Queue Works Internally

### Architecture Overview

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   FastAPI    │────▶│    Redis     │◀────│   RQ Worker  │
│   Handler    │      │   (Queue)    │      │   Process    │
└──────────────┘      └──────────────┘      └──────────────┘
       │                    │                     │
       │  LPUSH job         │                     │
       │──────────────────▶│                     │
       │                    │                     │
       │                    │  BRPOP job          │
       │                    │◀───────────────────│
       │                    │                     │
       │                    │                     ▼
       │                    │              ┌──────────────┐
       │                    │              │   Execute    │
       │                    │              │   Task       │
       │                    │              └──────────────┘
       │                    │                     │
       │                    │   Store result      │
       │                    │◀───────────────────│
```

### Redis Data Structures

RQ uses two main Redis data structures:

1. **Lists** (job queue):
   ```
   rq:queue:default  → [job1_id, job2_id, job3_id, ...]
   ```
   Jobs are pushed with LPUSH and popped with BRPOP (blocking).

2. **Hashes** (job data):
   ```
   rq:job:{job_id}   → {
                          "data": "{serialized_args}",
                          "status": "queued|started|finished|failed",
                          "result": "{serialized_result}",
                          "exc_info": "{error_traceback}",
                          ...
                        }
   ```

### Job Lifecycle

```
     ┌─────────┐
     │ QUEUED  │ ← Job created, waiting for worker
     └────┬────┘
          │ Worker picks up job
          ▼
     ┌─────────┐
     │ STARTED │ ← Job is executing
     └────┬────┘
          │ Job completes successfully
          ▼
     ┌──────────┐
     │ FINISHED │ ← Result stored, available for retrieval
     └──────────┘

     ┌─────────┐
     │ STARTED │ ← Job is executing
     └────┬────┘
          │ Job raises exception
          ▼
     ┌────────┐
     │ FAILED │ ← Error stored, can be retried
     └────────┘
```

### Why RQ Over Celery?

| Factor | RQ | Celery |
|--------|----|----|
| Setup complexity | Simple | Complex (broker, results backend, serializers) |
| Dependencies | redis + rq only | redis + celery + kombu + ... |
| Code style | Decorator-based, Pythonic | Task registry, complex configuration |
| Horizontal scaling | Separate processes | Can fork workers |
| Features | Core features only | Everything including schedulers |
| Learning curve | Low | High |

For SLMGEN's use case (simple queue → execute → store result), RQ is the right choice.

---

## 3. Pipeline Execution Flow (Step-by-Step)

### Pipeline Steps

```
┌─────────┐     ┌─────────┐     ┌─────────────┐     ┌─────────┐
│ UPLOAD  │───▶│ INGEST  │───▶│  ANALYZE    │───▶│RECOMMEND│───▶ GENERATE
└─────────┘     └────┬────┘     └──────┬──────┘     └────┬────┘         │
                    │                │                │               │
                    ▼                ▼                ▼               ▼
              ┌─────────┐      ┌─────────┐      ┌─────────┐     ┌─────────┐
              │ Parse   │      │ Extract │      │ Score   │     │ Generate│
              │ JSONL   │      │ features│      │ models  │     │ Notebook│
              └─────────┘      └─────────┘      └─────────┘     └─────────┘
```

### Step 1: Upload

```python
# FastAPI handler (upload.py)
@router.post("/upload")
async def upload_dataset(file: UploadFile):
    # 1. Create session
    session_id = await session_store.create_session(owner_id=owner_id)
    
    # 2. Upload to storage
    dataset_path = await storage_service.upload_dataset(file_bytes, session_id)
    
    # 3. Initialize session state
    await session_store.update_session(session_id, {
        "dataset_path": dataset_path,
        "job_status": "queued",
        "progress": 0.0,
    })
    
    # 4. Enqueue job
    job_queue.enqueue_to_high("ingest_task", session_id=session_id)
    
    # 5. Return immediately
    return {"session_id": session_id, "status": "processing"}
```

**Time**: ~500ms (just file upload and queue)

### Step 2: Ingest Task

```python
# Worker executes (tasks.py)
def ingest_task(session_id: str):
    # 1. Check idempotency
    session = _get_session(session_id)
    if session["data"].get("ingest_done"):
        return  # Skip if already done
    
    # 2. Update progress
    _update_session(session_id, {"progress": 0.10, "current_step": "ingest"})
    
    # 3. Download from storage
    file_bytes = _download_from_storage(session["data"]["dataset_path"])
    
    # 4. Parse and validate
    data, stats, error = _parse_jsonl(file_bytes)
    if error:
        _update_session(session_id, {"job_status": "failed", "error": error})
        raise ValueError(error)
    
    # 5. Run quality checks
    quality_score, issues = _validate_quality(data)
    stats["quality_score"] = quality_score
    
    # 6. Update session with results
    _update_session(session_id, {
        "ingest_done": True,
        "raw_data": data,
        "stats": stats,
        "progress": 0.25,
    })
```

**Time**: ~5-30 seconds (depends on dataset size)

### Step 3: Analyze Task

```python
def analyze_task(session_id: str):
    # 1. Load data from session (already in Redis)
    session = _get_session(session_id)
    data = session["data"]["raw_data"]
    
    # 2. Extract characteristics
    characteristics = _analyze_dataset(data)
    
    # 3. Update session
    _update_session(session_id, {
        "analyze_done": True,
        "characteristics": characteristics,
        "progress": 0.50,
    })
```

**Time**: ~1-5 seconds

### Step 4: Recommend Task

```python
def recommend_task(session_id: str):
    session = _get_session(session_id)
    stats = session["data"]["stats"]
    chars = session["data"]["characteristics"]
    task_type = session["data"]["task_type"]
    deployment = session["data"]["deployment_target"]
    
    # Get recommendations from scoring engine
    recommendations = get_recommendations(task_type, deployment, stats, chars)
    
    _update_session(session_id, {
        "recommend_done": True,
        "selected_model_id": recommendations["primary"]["model_id"],
        "recommendations": recommendations,
        "progress": 0.75,
    })
```

**Time**: ~1 second

### Step 5: Generate Task

```python
def generate_notebook_task(session_id: str, model_id: str = None):
    session = _get_session(session_id)
    model_id = model_id or session["data"]["selected_model_id"]
    
    # Load dataset content
    dataset = _load_dataset_content(session["data"])
    
    # Generate notebook (CPU intensive)
    notebook_json = generate_notebook(dataset, model_id, ...)
    
    # Upload to storage
    notebook_path = _upload_notebook_to_storage(session_id, notebook_json)
    
    _update_session(session_id, {
        "notebook_path": notebook_path,
        "job_status": "completed",
        "progress": 1.0,
    })
```

**Time**: ~10-30 seconds (notebook generation)

---

## 4. How Retries and Failures Are Handled

### Automatic Retries

RQ supports automatic retries with configurable attempts:

```python
from rq import retry

@job(retries=3, retry_strategy=...)
def my_task():
    ...
```

Currently, SLMGEN uses RQ's default behavior (no automatic retries), but failure handling is implemented manually:

```python
def ingest_task(session_id: str):
    try:
        # ... task logic ...
        _update_session(session_id, {"job_status": "completed"})
    except Exception as e:
        # Mark as failed
        _update_session(session_id, {
            "job_status": "failed",
            "job_error": str(e),
        })
        # Re-raise so RQ marks job as failed
        raise
```

### Failure Recovery

1. **Failed jobs are stored in Redis**:
   - Job status = "failed"
   - Exception traceback stored in `exc_info` field
   - Job remains in Redis for investigation

2. **Manual retry via API**:
   ```python
   @router.post("/pipeline/{session_id}/run")
   async def rerun_pipeline(session_id: str):
       # Re-enqueue all pending tasks
       job_queue.enqueue("analyze_task", session_id=session_id)
       ...
   ```

3. **Idempotency ensures safe retry**:
   ```python
   def ingest_task(session_id: str):
       if session["data"].get("ingest_done"):
           return  # Skip, already done
       # ... do work ...
   ```

### Error Propagation

```
Worker Process
     │
     ▼
┌────────────────┐
│  ingest_task   │
│     try:       │
│       ...      │
│     except:    │
│       update   │──▶ Session: {"job_status": "failed", "error": "..."}
│       raise    │
└───────┬────────┘
        │
        ▼
┌────────────────┐
│  RQ Worker     │
│  except:       │──▶ Redis: rq:job:{id}.status = "failed"
│    handle      │              rq:job:{id}.exc_info = traceback
└───────┬────────┘
        │
        ▼
┌────────────────┐
│  User polls    │──▶ GET /pipeline/{session_id}/status
│  status        │         {"status": "failed", "error": "..."}
└────────────────┘
```

---

## 5. How Idempotency Is Ensured

### What Is Idempotency?

An idempotent operation produces the same result regardless of how many times it's executed. This is critical for:
- Safe retries after failure
- Preventing duplicate work
- Debugging without side effects

### Implementation Pattern

Every task checks its prerequisites before executing:

```python
def ingest_task(session_id: str):
    """Ingest is idempotent - checks if already done."""
    session = _get_session(session_id)
    
    # Idempotency check
    if session["data"].get("ingest_done"):
        logger.info(f"[{session_id}] Ingest already complete, skipping")
        return {"status": "skipped", "reason": "already_done"}
    
    # ... do work ...
```

### Session State Machine

```
    ┌──────────────────────────────────────────────────────┐
    │                                                      │
    ▼                                                      │
┌────────┐                                                 │
│QUEUED  │  (initial state after upload)                   │
└───┬────┘                                                 │
    │                                                      │
    ▼                                                      │
┌────────────┐                                             │
│PROCESSING  │  (one of the steps is running)              │
│ +progress  │                                             │
└─────┬──────┘                                             │
      │                                                    │
      ├───────────────────────────────────────────────┐    │
      │                                               │    │
      ▼                                               ▼    │
┌───────────┐  (success)                    ┌────────┐     │
│COMPLETED  │  (all steps done)             │FAILED  │     │
└───────────┘                               └────────┘     │
      ▲                                         │          │
      │                                         └──────────┘
      │                      (retry resets to QUEUED)
      │                                                    │
      └────────────────────────────────────────────────────┘

Step flags (within PROCESSING):
  ingest_done: true → false → true
  analyze_done: true → false → true
  recommend_done: true → false → true
  notebook_path: null → "/path/to/notebook.ipynb"
```

### Safe Retry Pattern

```python
# Step 1: First attempt fails
ingest_task("abc123")
# → Session updated with ingest_done=True (before failure)
# → Worker crashes during quality check
# → Job marked as failed

# Step 2: Retry
ingest_task("abc123")
# → Session checked: ingest_done=True
# → Function returns immediately
# → No duplicate work
```

---

## 6. System Behavior Under Load

### Worker Scaling

```
┌─────────────────────────────────────────────────────────┐
│                     Load Balancer                       │
└─────────────────┬───────────────────────┬───────────────┘
                  │                       │
        ┌─────────▼─────┐         ┌───────▼───────┐
        │   Worker 1    │         │   Worker 2    │
        │  (2 jobs)     │         │  (3 jobs)     │
        └───────┬───────┘         └───────┬───────┘
                │                         │
                ▼                         ▼
        ┌───────────────┐         ┌────────────────┐
        │ Queue: high   │         │ Queue: default │
        │ (1 pending)   │         │ (5 pending)    │
        └───────────────┘         └────────────────┘
                │                         │
                └────────────┬────────────┘
                             ▼
                    ┌─────────────────┐
                    │     Redis       │
                    │   (job store)   │
                    └─────────────────┘
```

### Queue Priority

Three queues with different priority levels:

| Queue | Purpose | Example Jobs |
|-------|---------|--------------|
| `high` | Critical operations | Ingest (after upload) |
| `default` | Standard operations | Analyze, recommend, generate |
| `low` | Background optimization | Cleanup, statistics |

Workers process jobs in order:
```bash
# Process high priority first
rq worker --queue high,default,low
```

### Memory Management

Jobs store only `session_id` in the queue:
```python
# Good - lightweight
job_queue.enqueue("ingest_task", session_id="abc-123")

# Bad - loads entire dataset into Redis
job_queue.enqueue("ingest_task", dataset=huge_list)  # DON'T DO THIS
```

Workers fetch data from Redis session store:
```python
def ingest_task(session_id):
    # Data loaded inside worker, not queued
    session = _get_session(session_id)
    dataset_path = session["data"]["dataset_path"]
    file_bytes = _download_from_storage(dataset_path)
```

### Concurrency

Each worker runs jobs sequentially (single-threaded), but multiple workers run in parallel:

```bash
# Start 4 workers (processes)
rq worker --workers 4 --url redis://...

# Or run 4 separate processes
terminal 1: rq worker high
terminal 2: rq worker high
terminal 3: rq worker default
terminal 4: rq worker default
```

---

## 7. Tradeoffs vs Synchronous Execution

### Comparison Table

| Factor | Synchronous | Background Jobs |
|--------|-------------|-----------------|
| Response time | 30-60s | < 1s |
| Scalability | Poor (workers blocked) | Excellent |
| Progress tracking | None | Real-time |
| Retry on failure | Manual restart | Automatic |
| Complexity | Simple | Medium |
| Debugging | Easy (stack trace) | Harder (separate process) |
| Resource usage | High (blocked workers) | Low |
| Timeout handling | Client-side only | Server-controlled |

### When to Use Each

**Use Synchronous** when:
- Operation completes in < 5 seconds
- No external dependencies
- Simple CRUD operations
- Immediate response required

**Use Background Jobs** when:
- Operation takes > 5 seconds
- External API calls involved
- Real-time progress needed
- Retry capability required
- High concurrency expected

### SLMGEN Use Case

SLMGEN operations are inherently slow:
- Dataset parsing: 5-30s (depending on size)
- Notebook generation: 10-30s
- Total pipeline: 30-90s

Background jobs are the correct choice.

### Fallback Behavior

When Redis/job queue is unavailable:

```python
if not job_queue.is_connected:
    # Run synchronously (blocks HTTP handler)
    ingest_task(session_id)
else:
    # Queue for background processing
    job_queue.enqueue("ingest_task", session_id=session_id)
```

This ensures the system still works in:
- Development mode (no Redis)
- Single-instance deployments
- Redis connection failures

---

## 8. Monitoring and Observability

### Key Metrics

1. **Queue depth**:
   ```bash
   rq info
   # Shows: high=0, default=5, low=2
   ```

2. **Worker status**:
   ```bash
   rq workers
   # Shows: worker-1 running, worker-2 idle
   ```

3. **Job success rate**:
   ```python
   # Query Redis
   redis-cli SCARD rq:finished:default  # Completed jobs
   redis-cli SCARD rq:failed:default    # Failed jobs
   ```

### Logging

Jobs log at each step:

```
2026-04-15 10:30:00 [INFO] [ingest_task] Starting for session abc-123
2026-04-15 10:30:05 [INFO] [ingest_task] Completed: 500 examples
2026-04-15 10:30:05 [INFO] [analyze_task] Starting for session abc-123
2026-04-15 10:30:06 [INFO] [analyze_task] Completed
...
```

### Health Checks

```python
@router.get("/health")
async def health_check():
    redis_healthy = await session_store.health_check()
    queue_stats = job_queue.get_queue_stats()
    
    return {
        "status": "healthy" if redis_healthy else "degraded",
        "redis": "connected" if redis_healthy else "disconnected",
        "queue": queue_stats,
    }
```

---

## 9. Security Considerations

### Job Data

Only `session_id` is passed in job arguments:
```python
job_queue.enqueue("ingest_task", session_id="abc-123")
```

All actual data stays in:
- Redis session store (protected by Redis auth)
- Object storage (protected by signed URLs)

### Access Control

Jobs execute with the same permissions as the uploading user:
```python
session = _get_session(session_id)
owner_id = session.get("owner_id")
# owner_id stored with session, validated on retrieval
```

### Rate Limiting

Job queue operations are rate-limited:
- Upload: 10/minute
- General: 60/minute

Workers process at their own pace, independent of client requests.

---

## 10. Migration Checklist

To add background jobs to an existing pipeline:

- [x] Create `app/jobs/` directory
- [x] Implement `queue.py` with Redis connection
- [x] Implement `tasks.py` with all job functions
- [x] Implement `worker.py` entry point
- [x] Update `upload.py` to enqueue jobs
- [x] Create `pipeline.py` with status endpoint
- [x] Update `main.py` to include pipeline router
- [x] Add idempotency checks to tasks
- [x] Add error handling with session updates
- [x] Create `tests/test_jobs.py`
- [x] Create this documentation

---

## 11. Future Enhancements

### Planned Features

1. **Webhook notifications**: POST to user URL when job completes
2. **Scheduled jobs**: Run analysis on a recurring schedule
3. **Job chaining**: Automatically trigger next step on completion
4. **Priority adjustment**: Allow users to upgrade/downgrade job priority
5. **Progress via WebSocket**: Real-time updates instead of polling
