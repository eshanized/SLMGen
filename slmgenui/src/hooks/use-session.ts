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
 * @author Eshan Roy <eshanized@proton.me>
 * @contributor Vedant Singh Rajput <teleported0722@gmail.com>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

'use client';

import { useState, useCallback, useEffect } from 'react';
import type {
    WizardStep,
    DatasetStats,
    TaskType,
    DeploymentTarget,
    RecommendationResponse,
    NotebookResponse,
} from '@/lib/types';

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
        return saved ? JSON.parse(saved) : initialState;
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
            sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
        }
    }, [state]);

    // ========================================================================
    // SETTERS - These are the functions components call to update state
    // ========================================================================

    /**
     * Called after successful upload.
     * Now includes filePreview for the chat bubble component!
     */
    const setSession = useCallback((sessionId: string, stats: DatasetStats, filePreview?: string) => {
        setState(prev => ({
            ...prev,
            sessionId,
            stats,
            filePreview: filePreview || null,
            currentStep: 'configure',
        }));
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
        setState(initialState);
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

    // ========================================================================
    // RETURN
    // ========================================================================

    return {
        // Spread all state values
        ...state,
        // Setters
        setSession,
        setTask,
        setDeployment,
        setRecommendation,
        setNotebook,
        goToStep,
        reset,
        // Computed
        canProceedFromConfigure,
    };
}
