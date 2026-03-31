# Async Pipeline Architecture

This document describes the asynchronous job processing pipeline in SLMGEN.

## Overview

The async pipeline replaces synchronous API responses with background job processing:

```
Upload → Queue → Worker → Progress → Download
```

## Flow

1. **Upload** (`POST /upload`)
   - Receives file, saves to storage
   - Returns immediately with `session_id` and `stats: null`
   - Enqueues `ingest` job to RQ

2. **Job Processing** (Background)
   - Worker picks up job from Redis queue
   - Runs: ingest → analyze → recommend → generate
   - Updates session store with progress

3. **Status Polling** (`GET /pipeline/{session_id}/status`)
   - Returns current step, progress, and any completed data
   - Frontend polls every 2 seconds

4. **Frontend Updates**
   - `useSession` hook manages job state
   - `ProcessingStatusCard` shows progress
   - `TerminalSimulator` displays real-time status

## Frontend Components

### use-session.ts

The session hook manages async job state:

```typescript
interface SessionState {
    jobStatus: 'idle' | 'queued' | 'processing' | 'completed' | 'failed';
    jobProgress: number;        // 0-100
    currentPipelineStep: PipelineStep;
    jobError: string | null;
}

// Methods
setSession(sessionId, stats, filePreview, startPolling);
setJobStatus(response: JobStatusResponse);
startJobPolling(sessionId, onUpdate, onComplete, onError);
stopJobPolling();
```

### UploadZone

Updated to support async flow:

```typescript
interface UploadZoneProps {
    onUpload?: (sessionId, stats, filePreview) => void;  // Legacy sync
    onFileSelect?: (file: File) => Promise<void>;         // Async handler
    onError: (error: string) => void;
    isProcessing?: boolean;
}
```

### TaskSelector

Can be disabled while processing:

```typescript
<TaskSelector 
    onComplete={handleConfigComplete}
    disabled={session.isJobProcessing}
 />
```

### TerminalSimulator

Shows real-time job status:

```typescript
<TerminalSimulator
    currentStep={session.currentPipelineStep}
    progress={session.progressPercent}
/>
```

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/upload` | Upload file, returns session_id immediately |
| POST | `/pipeline/{id}/trigger/{step}` | Trigger a pipeline step |
| GET | `/pipeline/{id}/status` | Get job status |
| GET | `/pipeline/{id}/stream` | SSE stream for real-time updates |

## Backend Job System

See `docs/JOB_SYSTEM_ARCHITECTURE.md` for details on:
- RQ queues (high, default, low)
- Job tasks (ingest, analyze, recommend, generate)
- Worker process
- Idempotency checks

## Error Handling

- Job failures are stored in session with error message
- Frontend shows retry button on failure
- `handleRetry` triggers analysis again

## Testing

Frontend changes verified with:
- TypeScript compilation: `npx tsc --noEmit`
- ESLint: `npm run lint`
- Backend tests: `pytest tests/ -v` (194 passing)
