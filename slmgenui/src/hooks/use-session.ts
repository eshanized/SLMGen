/**
 * Session management hook.
 * 
 * This hook is the "brain" of the wizard. It stores all the state
 * as the user moves through: Upload → Configure → Recommend → Generate.
 * 
 * We persist to sessionStorage so the user can refresh the page
 * without losing their progress. This is really important for UX!
 * 
 * What we store:
 * - sessionId: The backend session identifier
 * - stats: Dataset statistics from the upload
 * - filePreview: First ~10KB of the file for the chat preview
 * - task: Selected task type (classification, QA, etc.)
 * - deployment: Where the model will run (cloud, mobile, etc.)
 * - recommendation: The AI's model recommendation
 * - notebook: Generated notebook info
 * - currentStep: Which step of the wizard we're on
 * 
 * ASYNC JOB STATE:
 * - jobStatus: Current job processing status
 * - jobProgress: Progress through pipeline (0-100)
 * - currentPipelineStep: Current step being processed
 * - jobError: Error message if job failed
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @contributor Vedant Singh Rajput <teleported0722@gmail.com>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import type {
    WizardStep,
    DatasetStats,
    TaskType,
    DeploymentTarget,
    RecommendationResponse,
    NotebookResponse,
    JobStatus,
    PipelineStep,
    JobStatusResponse,
} from '@/lib/types';
import { pollJobStatus } from '@/lib/api';

// ============================================================================
// TYPES
// ============================================================================

/**
 * The complete session state.
 * Everything we need to track as the user goes through the wizard.
 */
export interface SessionState {
    sessionId: string | null;
    stats: DatasetStats | null;
    /** NEW: The first ~10KB of the uploaded file for preview */
    filePreview: string | null;
    task: TaskType | null;
    deployment: DeploymentTarget | null;
    recommendation: RecommendationResponse | null;
    notebook: NotebookResponse | null;
    currentStep: WizardStep;
    /** Async job state */
    jobStatus: JobStatus;
    jobProgress: number;
    currentPipelineStep: PipelineStep;
    jobError: string | null;
    /** Cleanup function for polling */
    _pollCleanup: (() => void) | null;
}

// ============================================================================
// INITIAL STATE
// ============================================================================

const initialState: SessionState = {
    sessionId: null,
    stats: null,
    filePreview: null,
    task: null,
    deployment: null,
    recommendation: null,
    notebook: null,
    currentStep: 'upload',
    jobStatus: 'idle',
    jobProgress: 0,
    currentPipelineStep: 'ingest',
    jobError: null,
    _pollCleanup: null,
};

const STORAGE_KEY = 'slmgen-session';

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Try to load session state from sessionStorage.
 * 
 * We use sessionStorage (not localStorage) because:
 * 1. It clears when the browser tab closes (fresh start next time)
 * 2. It's isolated per tab (can have multiple sessions in different tabs)
 * 
 * @returns The saved state or initial state if nothing saved
 */
function loadFromStorage(): SessionState {
    // Server-side rendering check - window doesn't exist on server
    if (typeof window === 'undefined') return initialState;

    try {
        const saved = sessionStorage.getItem(STORAGE_KEY);
        if (saved) {
            const parsed = JSON.parse(saved);
            // Clean up polling state when restoring
            if (parsed._pollCleanup) {
                parsed._pollCleanup = null;
            }
            return { ...initialState, ...parsed };
        }
        return initialState;
    } catch {
        // JSON parse failed or storage is corrupted
        return initialState;
    }
}

// ============================================================================
// THE HOOK
// ============================================================================

export function useSession() {
    const [state, setState] = useState<SessionState>(loadFromStorage);

    // Persist to sessionStorage whenever state changes
    // This is like an "auto-save" feature
    useEffect(() => {
        if (typeof window !== 'undefined') {
            // Don't persist internal cleanup functions
            const { _pollCleanup, ...persistable } = state;
            sessionStorage.setItem(STORAGE_KEY, JSON.stringify(persistable));
        }
    }, [state]);

    // Cleanup polling on unmount
    useEffect(() => {
        return () => {
            if (state._pollCleanup) {
                state._pollCleanup();
            }
        };
    }, []);

    // ========================================================================
    // SETTERS - These are the functions components call to update state
    // ========================================================================

    /**
     * Called after successful upload.
     * Now includes filePreview for the chat bubble component!
     * Also starts job status polling.
     */
    const setSession = useCallback((
        sessionId: string,
        stats: DatasetStats | null,
        filePreview?: string,
        startPolling: boolean = true
    ) => {
        setState(prev => {
            // Clean up existing polling if any
            if (prev._pollCleanup) {
                prev._pollCleanup();
            }
            return {
                ...prev,
                sessionId,
                stats,
                filePreview: filePreview || null,
                currentStep: 'configure',
                jobStatus: startPolling ? 'queued' : 'idle',
                jobProgress: 0,
                currentPipelineStep: 'ingest',
                jobError: null,
                _pollCleanup: null,
            };
        });
    }, []);

    /**
     * Set job status from polling response.
     */
    const setJobStatus = useCallback((response: JobStatusResponse) => {
        setState(prev => {
            // Check if this response indicates completion
            if (response.status === 'completed' && prev._pollCleanup) {
                prev._pollCleanup();
            }

            return {
                ...prev,
                jobStatus: response.status,
                jobProgress: Math.round(response.progress * 100),
                currentPipelineStep: response.current_step,
                jobError: response.error || null,
                stats: response.stats || prev.stats,
                recommendation: response.recommendations || prev.recommendation,
                notebook: response.notebook_path ? {
                    session_id: prev.sessionId || '',
                    notebook_filename: 'training.ipynb',
                    download_url: `/download/${prev.sessionId}`,
                    colab_url: null,
                    message: 'Notebook ready',
                } : prev.notebook,
            };
        });
    }, []);

    /**
     * Start polling for job status.
     */
    const startJobPolling = useCallback((
        sessionId: string,
        onComplete?: (status: JobStatusResponse) => void,
        onError?: (error: string) => void
    ) => {
        // Clean up existing polling
        setState(prev => {
            if (prev._pollCleanup) {
                prev._pollCleanup();
            }
            return { ...prev, _pollCleanup: null };
        });

        const cleanup = pollJobStatus(
            sessionId,
            (status) => setJobStatus(status),
            (status) => {
                setJobStatus(status);
                onComplete?.(status);
            },
            (error) => {
                setState(prev => ({
                    ...prev,
                    jobStatus: 'failed',
                    jobError: error,
                }));
                onError?.(error);
            },
            2000, // Poll every 2 seconds
            150   // Max 5 minutes
        );

        setState(prev => ({
            ...prev,
            jobStatus: 'processing',
            _pollCleanup: cleanup,
        }));
    }, [setJobStatus]);

    /**
     * Stop polling for job status.
     */
    const stopJobPolling = useCallback(() => {
        setState(prev => {
            if (prev._pollCleanup) {
                prev._pollCleanup();
            }
            return { ...prev, _pollCleanup: null };
        });
    }, []);

    /** Set the selected task type */
    const setTask = useCallback((task: TaskType) => {
        setState(prev => ({ ...prev, task }));
    }, []);

    /** Set the deployment target */
    const setDeployment = useCallback((deployment: DeploymentTarget) => {
        setState(prev => ({ ...prev, deployment }));
    }, []);

    /** Set the model recommendation (moves to recommend step) */
    const setRecommendation = useCallback((recommendation: RecommendationResponse) => {
        setState(prev => ({
            ...prev,
            recommendation,
            currentStep: 'recommend',
        }));
    }, []);

    /** Set the generated notebook (moves to generate step) */
    const setNotebook = useCallback((notebook: NotebookResponse) => {
        setState(prev => ({
            ...prev,
            notebook,
            currentStep: 'generate',
        }));
    }, []);

    /** Jump to a specific step (used for navigation) */
    const goToStep = useCallback((step: WizardStep) => {
        setState(prev => ({ ...prev, currentStep: step }));
    }, []);

    /** Reset everything - starts fresh */
    const reset = useCallback(() => {
        setState(prev => {
            // Clean up polling if any
            if (prev._pollCleanup) {
                prev._pollCleanup();
            }
            return initialState;
        });
        if (typeof window !== 'undefined') {
            sessionStorage.removeItem(STORAGE_KEY);
        }
    }, []);

    // ========================================================================
    // COMPUTED VALUES
    // ========================================================================

    // Can we proceed from the configure step?
    // Only if user has selected both task and deployment
    const canProceedFromConfigure = state.task !== null && state.deployment !== null;

    // Is the job still processing?
    const isJobProcessing = state.jobStatus === 'queued' || state.jobStatus === 'processing';

    // Progress percentage for display
    const progressPercent = Math.round(state.jobProgress);

    // ========================================================================
    // RETURN
    // ========================================================================

    return {
        // Spread all state values
        ...state,
        // Setters
        setSession,
        setJobStatus,
        startJobPolling,
        stopJobPolling,
        setTask,
        setDeployment,
        setRecommendation,
        setNotebook,
        goToStep,
        reset,
        // Computed
        canProceedFromConfigure,
        isJobProcessing,
        progressPercent,
    };
}
