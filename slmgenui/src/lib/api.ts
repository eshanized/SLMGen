/**
 * API client for SLMGEN backend.
 * 
 * Handles all communication with the FastAPI backend.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

import type {
    UploadResponse,
    AnalyzeResponse,
    RecommendationResponse,
    NotebookResponse,
    TaskType,
    DeploymentTarget,
} from './types';

// Backend URL - can be overridden with env var
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Custom error class for API Errors.
 */
export class ApiError extends Error {
    constructor(public status: number, message: string) {
        super(message);
        this.name = 'ApiError';
    }
}

/**
 * Delay for a specified number of milliseconds.
 */
function delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Helper to make API Requests with retry logic.
 * Uses exponential backoff for transient failures.
 */
async function apiRequest<T>(
    endpoint: string,
    options: RequestInit = {},
    retries: number = 3
): Promise<T> {
    const url = `${API_URL}${endpoint}`;
    let lastError: Error | null = null;

    for (let attempt = 0; attempt < retries; attempt++) {
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Accept': 'application/json',
                    ...options.headers,
                },
            });

            if (!response.ok) {
                // Try to get error message from Response
                let errorMessage = `Request failed with status ${response.status}`;
                try {
                    const errorData = await response.json();
                    if (errorData.detail) {
                        errorMessage = errorData.detail;
                    }
                } catch {
                    // couldn't parse JSON, use default
                }

                // Don't retry client errors (4xx) except 429 (rate limit)
                if (response.status >= 400 && response.status < 500 && response.status !== 429) {
                    throw new ApiError(response.status, errorMessage);
                }

                // For 5xx errors and 429, retry with backoff
                lastError = new ApiError(response.status, errorMessage);
                if (attempt < retries - 1) {
                    const backoffMs = Math.pow(2, attempt) * 1000; // 1s, 2s, 4s
                    await delay(backoffMs);
                    continue;
                }
            } else {
                return response.json();
            }
        } catch (error) {
            if (error instanceof ApiError) {
                throw error;
            }
            // Network error - retry with backoff
            lastError = error instanceof Error ? error : new Error(String(error));
            if (attempt < retries - 1) {
                const backoffMs = Math.pow(2, attempt) * 1000;
                await delay(backoffMs);
                continue;
            }
        }
    }

    // All retries exhausted
    if (lastError instanceof ApiError) {
        throw lastError;
    }
    throw new ApiError(0, 'Failed to connect to server after multiple attempts. Is the backend running?');
}

/**
 * Upload a JSONL dataset File.
 */
export async function uploadDataset(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    return apiRequest<UploadResponse>('/upload', {
        method: 'POST',
        body: formData,
    });
}

/**
 * Get detailed analysis for a Session.
 */
export async function analyzeDataset(sessionId: string): Promise<AnalyzeResponse> {
    return apiRequest<AnalyzeResponse>('/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ session_id: sessionId }),
    });
}

/**
 * Get model recommendations for a Session.
 */
export async function getRecommendation(
    sessionId: string,
    task: TaskType,
    deployment: DeploymentTarget
): Promise<RecommendationResponse> {
    return apiRequest<RecommendationResponse>('/recommend', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            session_id: sessionId,
            task: task,
            deployment: deployment,
        }),
    });
}

/**
 * Generate a training Notebook.
 */
export async function generateNotebook(
    sessionId: string,
    modelId?: string
): Promise<NotebookResponse> {
    return apiRequest<NotebookResponse>('/generate-notebook', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            session_id: sessionId,
            model_id: modelId || null,
        }),
    });
}

/**
 * Get the download URL for a Notebook.
 */
export function getDownloadUrl(sessionId: string): string {
    return `${API_URL}/download/${sessionId}`;
}

/**
 * Health check to verify backend Connection.
 */
export async function healthCheck(): Promise<boolean> {
    try {
        await apiRequest<{ status: string }>('/health');
        return true;
    } catch {
        return false;
    }
}

/**
 * Validate a custom Hugging Face model ID.
 * Checks if the model exists and is compatible with Unsloth.
 */
export async function validateModel(modelId: string): Promise<{
    model_id: string;
    name: string;
    architecture: string;
    context_window: number;
    is_gated: boolean;
    downloads: number;
    likes: number;
    is_compatible: boolean;
    compatibility_reason: string;
    supported_architectures: string[];
}> {
    return apiRequest('/validate-model', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ model_id: modelId }),
    });
}

// =============================================================================
// Training Progress Tracking API
// =============================================================================

import type { TrainingSessionStatus, TrainingEvent } from './types';

/**
 * Get current training session status.
 */
export async function getTrainingStatus(sessionId: string): Promise<TrainingSessionStatus> {
    return apiRequest<TrainingSessionStatus>(`/training/${sessionId}/status`);
}

/**
 * Get all training events for a session.
 */
export async function getTrainingEvents(
    sessionId: string,
    sinceStep?: number
): Promise<TrainingEvent[]> {
    const query = sinceStep !== undefined ? `?since_step=${sinceStep}` : '';
    return apiRequest<TrainingEvent[]>(`/training/${sessionId}/events${query}`);
}

/**
 * Get the latest training event.
 */
export async function getLatestTrainingEvent(sessionId: string): Promise<TrainingEvent> {
    return apiRequest<TrainingEvent>(`/training/${sessionId}/latest`);
}

/**
 * Subscribe to training progress via Server-Sent Events.
 * Returns a function to unsubscribe.
 */
export function subscribeToTraining(
    sessionId: string,
    onUpdate: (status: TrainingSessionStatus) => void,
    onComplete: (status: TrainingSessionStatus) => void,
    onError: (error: string) => void
): () => void {
    const eventSource = new EventSource(`${API_URL}/training/${sessionId}/stream`);

    eventSource.onmessage = (event) => {
        try {
            const status = JSON.parse(event.data) as TrainingSessionStatus;
            onUpdate(status);
        } catch {
            // Ignore parse errors
        }
    };

    eventSource.addEventListener('complete', (event) => {
        try {
            const status = JSON.parse((event as MessageEvent).data) as TrainingSessionStatus;
            onComplete(status);
            eventSource.close();
        } catch {
            eventSource.close();
        }
    });

    eventSource.addEventListener('error', (event) => {
        if ((event as MessageEvent).data) {
            onError((event as MessageEvent).data);
        } else {
            onError('Connection lost');
        }
        eventSource.close();
    });

    eventSource.onerror = () => {
        eventSource.close();
    };

    // Return unsubscribe function
    return () => {
        eventSource.close();
    };
}

/**
 * List all active training sessions.
 */
export async function listTrainingSessions(): Promise<TrainingSessionStatus[]> {
    return apiRequest<TrainingSessionStatus[]>('/training/');
}

// =============================================================================
// Inference Playground API
// =============================================================================

import type {
    InferenceRequest,
    InferenceResponse,
    CompareRequest,
    ComparisonResponse,
    ListModelsResponse,
    JobStatusResponse,
    UploadResponseAsync,
} from './types';

/**
 * Run inference on a single model.
 */
export async function runInference(
    request: InferenceRequest,
    retries: number = 2
): Promise<InferenceResponse> {
    return apiRequest<InferenceResponse>('/inference/run', {
        method: 'POST',
        body: JSON.stringify(request),
        headers: {
            'Content-Type': 'application/json',
        },
    }, retries);
}

/**
 * Compare outputs from base and tuned models.
 */
export async function compareInference(
    request: CompareRequest,
    retries: number = 2
): Promise<ComparisonResponse> {
    return apiRequest<ComparisonResponse>('/inference/compare', {
        method: 'POST',
        body: JSON.stringify(request),
        headers: {
            'Content-Type': 'application/json',
        },
    }, retries);
}

/**
 * Get list of available models for inference.
 */
export async function listInferenceModels(): Promise<ListModelsResponse> {
    return apiRequest<ListModelsResponse>('/inference/models');
}

// =============================================================================
// Job Pipeline API (Async Processing)
// =============================================================================

/**
 * Upload dataset - returns immediately with queued status.
 * Backend processes asynchronously.
 */
export async function uploadDatasetAsync(file: File): Promise<UploadResponseAsync> {
    const formData = new FormData();
    formData.append('file', file);

    return apiRequest<UploadResponseAsync>('/upload', {
        method: 'POST',
        body: formData,
    });
}

/**
 * Get job status from pipeline endpoint.
 * Use for polling during async processing.
 */
export async function getJobStatus(sessionId: string): Promise<JobStatusResponse> {
    return apiRequest<JobStatusResponse>(`/pipeline/${sessionId}/status`);
}

/**
 * Trigger analysis step manually.
 */
export async function triggerAnalysis(sessionId: string): Promise<{ message: string; status: string }> {
    return apiRequest(`/pipeline/${sessionId}/analyze`, {
        method: 'POST',
    });
}

/**
 * Trigger recommendations step manually.
 */
export async function triggerRecommendations(
    sessionId: string,
    taskType: string = 'general',
    deployment: string = 'cloud'
): Promise<{ message: string; status: string }> {
    return apiRequest(`/pipeline/${sessionId}/recommend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task_type: taskType, deployment }),
    });
}

/**
 * Trigger notebook generation step manually.
 */
export async function triggerGeneration(
    sessionId: string,
    modelId?: string
): Promise<{ message: string; status: string }> {
    return apiRequest(`/pipeline/${sessionId}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_id: modelId }),
    });
}

/**
 * Run full pipeline (analyze → recommend → generate).
 */
export async function runPipeline(
    sessionId: string,
    taskType: string = 'general',
    deployment: string = 'cloud',
    modelId?: string
): Promise<{ message: string; tasks: number; status: string }> {
    return apiRequest(`/pipeline/${sessionId}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            task_type: taskType,
            deployment,
            model_id: modelId,
        }),
    });
}

/**
 * Subscribe to job status via polling.
 * Returns a cleanup function.
 */
export function pollJobStatus(
    sessionId: string,
    onUpdate: (status: JobStatusResponse) => void,
    onComplete: (status: JobStatusResponse) => void,
    onError: (error: string) => void,
    intervalMs: number = 2000,
    maxAttempts: number = 150  // 5 minutes max
): () => void {
    let attempts = 0;
    let stopped = false;

    const poll = async () => {
        if (stopped) return;

        try {
            const status = await getJobStatus(sessionId);
            onUpdate(status);

            if (status.status === 'completed') {
                stopped = true;
                onComplete(status);
                return;
            }

            if (status.status === 'failed') {
                stopped = true;
                onError(status.error || 'Job failed');
                return;
            }

            attempts++;
            if (attempts >= maxAttempts) {
                stopped = true;
                onError('Job timed out');
                return;
            }
        } catch (error) {
            if (!stopped) {
                onError(error instanceof Error ? error.message : 'Failed to poll status');
            }
        }
    };

    // Start polling
    const intervalId = setInterval(poll, intervalMs);
    poll(); // Initial poll

    // Return cleanup function
    return () => {
        stopped = true;
        clearInterval(intervalId);
    };
}
