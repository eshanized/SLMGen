/**
 * TypeScript type definitions for SLMGEN.
 * 
 * These match the backend Pydantic models exactly.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

// Task types supported for fine-tuning
export type TaskType = 'classify' | 'qa' | 'conversation' | 'generation' | 'extraction';

// Where the model will be Deployed
export type DeploymentTarget = 'cloud' | 'mobile' | 'edge' | 'browser' | 'desktop' | 'server';

// Dataset statistics from Upload
export interface DatasetStats {
    total_examples: number;
    total_tokens: number;
    avg_tokens_per_example: number;
    single_turn_pct: number;
    multi_turn_pct: number;
    has_system_prompts: boolean;
    quality_score: number;
    quality_issues: string[];
}

// Detailed dataset Characteristics
export interface DatasetCharacteristics {
    is_multilingual: boolean;
    avg_response_length: number;
    looks_like_json: boolean;
    is_multi_turn: boolean;
    has_system_prompts: boolean;
    dominant_language: string;
}

// Single model Recommendation
export interface ModelRecommendation {
    model_id: string;
    model_name: string;
    size: string;
    score: number;
    reasons: string[];
    context_window: number;
    is_gated: boolean;
}

// Full recommendation Response
export interface RecommendationResponse {
    primary: ModelRecommendation;
    alternatives: ModelRecommendation[];
}

// Upload Response
export interface UploadResponse {
    session_id: string;
    stats: DatasetStats;
    message: string;
}

// Analyze Response
export interface AnalyzeResponse {
    session_id: string;
    stats: DatasetStats;
    characteristics: DatasetCharacteristics;
}

// Notebook generation Response
export interface NotebookResponse {
    session_id: string;
    notebook_filename: string;
    download_url: string;
    colab_url: string | null;
    message: string;
}

// Wizard step tracking
export type WizardStep = 'upload' | 'configure' | 'recommend' | 'generate';

// Task option for UI
export interface TaskOption {
    value: TaskType;
    label: string;
    description: string;
}

// Deployment option for UI
export interface DeploymentOption {
    value: DeploymentTarget;
    label: string;
    description: string;
}

// Custom model validation response from HuggingFace
export interface ValidateModelResponse {
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
}

// =============================================================================
// Training Progress Tracking Types
// =============================================================================

// Training session status
export type TrainingStatus = 'pending' | 'running' | 'completed' | 'failed';

// Single training event
export interface TrainingEvent {
    step: number;
    loss: number;
    epoch: number;
    learning_rate: number;
    timestamp: string;
    grad_norm?: number;
    tokens_per_second?: number;
    gpu_memory_used?: number;
}

// Training session status response
export interface TrainingSessionStatus {
    session_id: string;
    job_id: string;
    model_id: string;
    status: TrainingStatus;
    total_steps: number;
    total_epochs: number;
    current_step: number;
    current_epoch: number;
    progress_percent: number;
    latest_loss?: number;
    eta_seconds?: number;
    eta_formatted?: string;
    created_at: string;
    started_at?: string;
    completed_at?: string;
    error_message?: string;
    event_count: number;
}

// =============================================================================
// Inference Playground Types
// =============================================================================

// Inference request payload
export interface InferenceRequest {
    model_id: string;
    prompt: string;
    system_prompt?: string;
    temperature?: number;
    max_tokens?: number;
}

// Inference response
export interface InferenceResponse {
    model_id: string;
    output: string;
    latency_ms: number;
    tokens: number;
    finish_reason: string;
    error?: string;
}

// Comparison request payload
export interface CompareRequest {
    base_model_id: string;
    tuned_model_id?: string;
    prompt: string;
    system_prompt?: string;
    temperature?: number;
    max_tokens?: number;
}

// Comparison metrics
export interface ComparisonMetrics {
    base_latency_ms: number;
    tuned_latency_ms: number;
    latency_delta_ms: number;
    base_tokens: number;
    tuned_tokens: number;
    token_delta: number;
    similarity_score: number;
    base_risk_score: number;
    tuned_risk_score: number;
    base_risk_level: string;
    tuned_risk_level: string;
    quality_score: number;
}

// Comparison response
export interface ComparisonResponse {
    base_model_id: string;
    tuned_model_id?: string;
    base_output: string;
    tuned_output: string;
    base_latency_ms: number;
    tuned_latency_ms: number;
    metrics: ComparisonMetrics;
    error?: string;
}

// Model info for inference
export interface ModelInfo {
    model_id: string;
    name: string;
    size: string;
    is_gated: boolean;
    context_window: number;
}

// List models response
export interface ListModelsResponse {
    models: ModelInfo[];
}

// Prompt history item
export interface PromptHistoryItem {
    id: string;
    prompt: string;
    systemPrompt?: string;
    timestamp: Date;
}
