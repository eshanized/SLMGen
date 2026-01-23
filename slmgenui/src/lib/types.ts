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
