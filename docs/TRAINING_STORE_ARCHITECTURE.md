# Redis Streams Training Store — Architecture Walkthrough

## 1. Architecture Overview

### Why Redis Streams?

The previous in-memory `TrainingTracker` singleton had critical production flaws:
- **Data loss on restart**: All training progress lost when the backend restarts
- **No horizontal scaling**: A dict in one process can't be shared across multiple instances
- **No event history**: Couldn't replay events for debugging or analytics
- **Blocking I/O**: Thread locks blocked async FastAPI handlers

Redis Streams solves these by providing:
1. **Durability**: Events survive restarts (persisted to Redis)
2. **Shared state**: Any backend instance can read/write to the same streams
3. **Event log**: Complete history for debugging and replay
4. **Non-blocking**: Async operations don't block the event loop

### Data Model

Each training session has two Redis keys:

```
training:{session_id}:events   → Redis Stream (append-only event log)
training:{session_id}:state   → Redis String (JSON snapshot)
```

**Stream structure:**
- Append-only log using XADD
- Capped at MAXLEN=1000 entries (oldest events evicted automatically)
- Each event has a Redis-generated ID (timestamp-based: `{ms}-{seq}`)

**State snapshot:**
- Updated on every event (progress, ETA, step count)
- Fast reads without scanning the stream
- Includes metadata (job_id, model_id, total_steps)

### Event Schema

```json
{
  "event": "start | progress | complete | error",
  "timestamp": "2026-04-15T10:30:00.000000+00:00",
  "step": 100,
  "loss": 0.5234,
  "epoch": 0,
  "learning_rate": 0.0002,
  "grad_norm": 1.234,
  "tokens_per_second": 1500.5,
  "gpu_memory_used": 12.5,
  "meta": {}
}
```

---

## 2. Event Lifecycle

### Phase 1: Session Start

```
Colab Notebook                          Backend                           Redis
      |                                   |                                |
      |--- POST /training/start --------->|                                |
      |   {session_id, job_id, model_id,  |                                |
      |    total_steps, total_epochs}     |                                |
      |                                   |                                |
      |                                   | XADD :events {init: started}   |
      |                                   | SET :state {status: running}   |
      |                                   | EXPIRE :events 7200            |
      |                                   | EXPIRE :state 7200             |
      |                                   |                                |
      |<-- 200 {status: running} ---------|                                |
```

1. Colab calls `/training/start` before training begins
2. Backend creates a Redis Stream with an init event
3. Backend creates a JSON state snapshot with initial values
4. Both keys get 2-hour TTL (auto-cleanup)

### Phase 2: Training Progress

```
Colab Notebook                          Backend                           Redis
      |                                   |                                |
      |--- POST /training/webhook ------->|                                |
      |   {session_id, step, loss, ...}   |                                |
      |                                   |                                |
      |                                   | XADD :events {step, loss, ...} |
      |                                   | XRANGE :events - + LIMIT 20    |
      |                                   | SET :state {progress, eta}     |
      |                                   |                                |
      |                                   | XADD :events {complete, ...}   |
      |                                   | SET :state {status: complete}  |
      |                                   |                                |
      |<-- 200 {received: true} ----------|                                |
```

1. Colab calls `/training/webhook` every N steps (configurable)
2. Backend appends event to stream (XADD with MAXLEN=1000)
3. Backend reads recent events to calculate ETA
4. Backend updates state snapshot (fast reads, no stream scan)
5. On completion/failure, final event written to stream

### Phase 3: SSE Streaming

```
Frontend                                Backend                           Redis
    |                                       |                                |
    |--- GET /training/{id}/stream -------->|                                |
    |                                       |                                |
    |                                       | GET :state                     |  (initial state)
    |<-- event: status\ndata: {...} --------|                                |
    |                                       |                                |
    |                                       | XREAD BLOCK :events $ 2000     |
    |                                       |                                |
    |  (Colab sends webhook)                |                                |
    |                                       | XREAD returns new event        |
    |<-- data: {type: event, step: 100} ----|                                |
    |                                       |                                |
    |  ... more events ...                  |                                |
    |                                       |                                |
    |  (training completes)                 |                                |
    |<-- event: complete\ndata: {...} ------|                                |
```

1. Frontend connects to SSE endpoint
2. Backend immediately returns current state
3. Backend calls XREAD with BLOCK=2000ms (2 second timeout)
4. On new event: returns it to frontend immediately
5. On timeout: sends heartbeat to keep connection alive
6. On completion/failure: sends final event and closes

---

## 3. Internal SSE Implementation

### How XREAD BLOCK Works

```python
# Pseudocode for stream_events()
while True:
    # BLOCK 2000 means: wait up to 2 seconds for new data
    result = await redis.xread(
        {events_key: last_seen_id},
        block=2000,  # milliseconds
        count=100
    )
    
    if result:
        for event in result:
            yield event
            last_seen_id = event.id
    else:
        # Timeout - no new events
        yield {"type": "heartbeat"}
```

**Benefits of XREAD BLOCK:**
- No polling loop (CPU efficient)
- Returns immediately when new data arrives
- Falls back to heartbeat on timeout
- Non-blocking for other async operations

### SSE Format

```
event: status
data: {"session_id":"...","status":"running","progress_percent":45.5,...}

data: {"type":"event","step":100,"loss":0.5,"epoch":0,...}

event: complete
data: {"session_id":"...","status":"completed","progress_percent":100.0,...}
```

**Message types:**
- `event: status` - Initial state snapshot
- `data: {...}` - Individual training events
- `event: complete` - Training finished (success or failure)
- `event: error` - Error occurred
- `: heartbeat` - Keep-alive (no data)

---

## 4. Snapshot + Stream Relationship

### Why Both?

| Aspect | Stream | Snapshot |
|--------|--------|----------|
| Purpose | Event log / audit trail | Fast state reads |
| Access pattern | Sequential, newest-first | Random, single read |
| Update frequency | Append-only | Updated every event |
| Use case | SSE streaming, debugging | `/status` endpoint, ETA calc |

### Write Flow

```
1. Receive event from Colab webhook
2. XADD event to stream (append)
3. XREVRANGE last 20 events (for ETA)
4. Calculate ETA from recent events
5. Read current snapshot
6. Update snapshot with:   - current_step
   - current_epoch
   - latest_loss
   - progress_percent
   - eta_seconds
7. SET updated snapshot
```

### Read Flow (Status Endpoint)

```
1. GET :state  → Instant, no stream scan
2. Parse JSON
3. Return to client
```

### Read Flow (Events Endpoint)

```
1. XREVRANGE :events + - COUNT 100  → Stream scan
2. Parse events
3. Return to client
```

---

## 5. Failure Scenarios

### Redis Down During Webhook

```
Colab                      Backend                      Redis
   |                           |                           |
   | POST /webhook             |                           |
   |-------------------------->|                           |
   |                           | XADD                      |
   |                           |------------------------X  |
   |                           |  (connection refused)     |
   |                           |                           |
   |                           | HTTP 503 + log error      |
   |<--------------------------|                           |
   | 503 Service Unavailable   |                           |
```

**Behavior:**
- Returns HTTP 503 to Colab
- Colab should retry (idempotent webhook)
- No data corruption (Redis is source of truth)

### Redis Down During SSE

```
Frontend                   Backend                      Redis
   |                          |                           |
   | GET /stream              |                           |
   |------------------------->|                           |
   |                          | XREAD BLOCK               |
   |                          |------------------------X  |
   |                          |                           |
   |                          | Yields error event        |
   |<-------------------------|                           |
   | event: error             |                           |
```

**Behavior:**
- Yields error event to frontend
- Frontend should reconnect
- SSE connection closes

### Partial Event (Colab Crash)

```
Colab                      Backend                      Redis
   |                           |                           |
   | POST /webhook             |                           |
   | (partial data)            |                           |
   |-------------------------->|                           |
   |                           | XADD (partial event)      |
   |                           |-------------------------->|
   |                           |                           |
   |                           | Validation fails          |
   |                           | (missing step/loss)       |
   |                           |                           |
   |                           | Logs error, continues     |
   |<--------------------------|                           |
   | 200 (received: false)     |                           |
```

**Behavior:**
- If validation fails: returns 200 but `received: false`
- Colab should resend on next step
- Partial events don't corrupt stream

### Session Not Found

```
Colab                      Backend                      Redis
   |                           |                           |
   | POST /webhook             |                           |
   | {session_id: bad-uuid}    |                           |
   |-------------------------->|                           |
   |                           | EXISTS :state             |
   |                           |-------------------------> |
   |                           | 0 (not found)             |
   |                           |                           |
   |<--------------------------|                           |
   | 200 (received: false)     |                           |
```

**Behavior:**
- Returns 200 with `received: false`
- Doesn't block Colab training
- Colab should call `/training/start` first

---

## 6. Scaling Behavior

### Single Instance

```
                  ┌──────────────────┐
                  │   FastAPI        │
                  │   Backend        │
                  │                  │
  Colab ───────▶ │                  │
                  │                  │
  Frontend ─────▶│  training_store  │────────▶ Redis
                  │                  │
                  └──────────────────┘
```

Simple, direct access to Redis.

### Multiple Instances (Horizontal Scaling)

```
                    ┌─────────────────┐
                    │   FastAPI       │
  Colab ──────────▶│   Instance 1    │─────────┐
                    └─────────────────┘         │
                                                ▼
                    ┌─────────────────┐     ┌─────────┐
                    │   FastAPI       │     │         │
  Frontend ───────▶│   Instance 2    │───▶│  Redis  │
                    └─────────────────┘     │         │
                                            └─────────┘
                    ┌─────────────────┐
                    │   FastAPI       │
                    │   Instance N    │
                    └─────────────────┘
```

**How it works:**
- Any instance can receive webhook from Colab
- Any instance can stream SSE to Frontend
- All share same Redis (source of truth)
- XREAD BLOCK on any instance connects to same Redis

**Benefits:**
- Horizontal scaling: add more backend instances
- High availability: one instance down, others serve
- Load balancing: distribute webhook calls

### Consumer Groups (Future Enhancement)

For advanced scenarios (multiple frontends, distributed processing):

```
Stream: training:{id}:events
  └─▶ Consumer Group: "frontend-clients"
       ├─▶ Client 1 (Frontend A)
       ├─▶ Client 2 (Frontend B)
       └─▶ Client 3 (Frontend C)

XPENDING → Shows unacknowledged messages
XACK     → Mark message as processed
```

**Current implementation:**
- Uses XREAD without consumer groups
- Each SSE client reads from stream independently
- Idempotent: same events delivered to all clients

---

## 7. Tradeoffs vs In-Memory System

| Aspect | In-Memory (Old) | Redis Streams (New) |
|--------|-----------------|-------------------|
| **Durability** | ❌ Lost on restart | ✅ Persisted |
| **Scaling** | ❌ Single instance | ✅ Multi-instance |
| **Latency** | ✅ Fastest | ⚠️ ~1-5ms overhead |
| **Complexity** | ✅ Simple dict | ⚠️ Requires Redis |
| **Debugging** | ❌ No history | ✅ Full event log |
| **Cost** | ✅ Free | ⚠️ Redis instance |

### When to Choose Redis Streams

**Use Redis Streams when:**
- Training sessions need to survive restarts
- Multiple backend instances (horizontal scaling)
- Need event history for debugging
- Building production-grade monitoring

**Stick with in-memory when:**
- Simple local development
- Single-instance deployment only
- Minimal latency is critical
- No Redis infrastructure available

---

## 8. Key Implementation Details

### UUID Validation

All session IDs are validated as UUID v4 before using in Redis keys:

```python
_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
```

**Why?** Prevents key injection attacks where malicious input could access other Redis keys.

### Bytes/String Handling

Fakeredis may return bytes keys/values while real Redis returns strings:

```python
# Normalize to string keys
normalized = {}
for k, v in data.items():
    if isinstance(k, bytes):
        k = k.decode("utf-8")
    normalized[k] = v
```

### Sliding TTL

Session TTL refreshed on every operation:

```python
# On get: refresh TTL
await r.expire(key, ttl_seconds)

# On update: refresh TTL
await r.set(key, data, ex=ttl_seconds)
```

### ETA Calculation

ETA estimated from last 20 events:

```python
def _estimate_eta(current_step, total_steps, events):
    if len(events) < 2:
        return None
    
    recent = events[-20:]
    # Calculate steps/second from recent events
    time_diff = (t_last - t_first).total_seconds()
    steps_diff = last["step"] - first["step"]
    
    steps_per_second = steps_diff / time_diff
    remaining = total_steps - current_step
    eta_seconds = remaining / steps_per_second
    
    return {"seconds": eta_seconds, "formatted": "2m 30s"}
```

---

## 9. API Quick Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/training/start` | POST | Initialize session |
| `/training/webhook` | POST | Receive events |
| `/training/complete` | POST | Mark done/failed |
| `/training/{id}/status` | GET | Fast state read |
| `/training/{id}/events` | GET | Event history |
| `/training/{id}/latest` | GET | Most recent event |
| `/training/{id}/stream` | GET | SSE real-time stream |
| `/training/` | GET | List all sessions |

---

## 10. Production Checklist

Before deploying to production:

- [ ] Redis 7.0+ running (Streams require Redis 5.0+)
- [ ] `REDIS_URL` environment variable configured
- [ ] Redis persistence enabled (AOF or RDB)
- [ ] Connection pooling configured (max_connections=20)
- [ ] TTL appropriate for workload (default 2 hours)
- [ ] Monitoring: Redis memory, CPU, connections
- [ ] Alerting: Redis connection failures
- [ ] Backup strategy for Redis data
- [ ] Security: Redis password, network isolation
