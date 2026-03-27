/**
 * Dashboard Page - Main Fine-tuning Wizard.
 * 
 * This is the heart of SLMGen! It guides users through 4 steps:
 * Upload → Configure → Recommend → Generate
 * 
 * Each step has its own UI, and we use framer-motion for smooth transitions.
 * The session hook tracks all the state as users progress.
 * 
 * ASYNC PIPELINE:
 * - After upload, the backend processes data asynchronously
 * - We poll for job status every 2 seconds
 * - Progress bar shows current step and completion percentage
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @contributor Vedant Singh Rajput <teleported0722@gmail.com>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

'use client';

import { useState, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSession } from '@/hooks/use-session';
import { DashboardHeader } from '@/components/navigation';
import { UploadZone } from '@/components/upload-zone';
import { StatsDisplay } from '@/components/stats-display';
import { TaskSelector } from '@/components/task-selector';
import { toast } from 'sonner';
import { ModelCard, ModelCardSkeleton } from '@/components/model-card';
import { NotebookReady } from '@/components/notebook-ready';
import { DataPreview } from '@/components/data-preview';
import { TerminalSimulator } from '@/components/terminal-simulator';
import { CustomModelInput } from '@/components/custom-model-input';
import { 
    uploadDatasetAsync, 
    getRecommendation, 
    generateNotebook, 
    getJobStatus,
    runPipeline,
    triggerAnalysis,
    triggerRecommendations,
    triggerGeneration,
    ApiError 
} from '@/lib/api';
import {
    Rocket,
    Upload,
    Settings,
    Target,
    Check,
    ArrowRight,
    AlertCircle,
    RefreshCw,
    Loader2,
} from '@/components/icons';
import type { TaskType, DeploymentTarget, JobStatusResponse } from '@/lib/types';

// Wizard step Labels
const STEPS = [
    { key: 'upload', label: 'Upload', Icon: Upload },
    { key: 'configure', label: 'Configure', Icon: Settings },
    { key: 'recommend', label: 'Recommend', Icon: Target },
    { key: 'generate', label: 'Generate', Icon: Rocket },
] as const;

// Pipeline step labels for display
const PIPELINE_STEPS = {
    ingest: 'Ingesting Dataset',
    analyze: 'Analyzing Data',
    recommend: 'Finding Models',
    generate: 'Generating Notebook',
};

export default function DashboardPage() {
    const session = useSession();
    const [isLoading, setIsLoading] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);

    // Get current step Index
    const currentStepIndex = STEPS.findIndex(s => s.key === session.currentStep);

    // Handle file upload with async processing
    const handleUpload = useCallback(async (file: File) => {
        setIsProcessing(true);
        const toastId = toast.loading('Uploading dataset...');

        try {
            const response = await uploadDatasetAsync(file);
            
            // Set session with stats (may be null if still processing)
            session.setSession(response.session_id, response.stats, undefined, true);
            
            // Start polling for job status
            session.startJobPolling(response.session_id, 
                (status) => {
                    // On complete
                    if (status.stats) {
                        toast.success('Dataset processed successfully!', { id: toastId });
                    }
                },
                (error) => {
                    toast.error(`Processing failed: ${error}`, { id: toastId });
                }
            );

            toast.info('Dataset uploaded! Processing in background...', { id: toastId });

        } catch (err) {
            toast.dismiss(toastId);
            if (err instanceof ApiError) {
                toast.error(err.message);
            } else {
                toast.error('Failed to upload dataset');
            }
        } finally {
            setIsProcessing(false);
        }
    }, [session]);

    // Handle configuration complete (task + deployment selection)
    const handleConfigComplete = useCallback(async (task: TaskType, deployment: DeploymentTarget) => {
        if (!session.sessionId) return;

        session.setTask(task);
        session.setDeployment(deployment);

        // If job is still processing, we need to wait
        if (session.isJobProcessing) {
            toast.info('Waiting for dataset processing to complete...');
            
            // Poll until we can proceed
            const checkStatus = async () => {
                const status = await getJobStatus(session.sessionId!);
                session.setJobStatus(status);
                
                if (status.status === 'completed' || status.status === 'failed') {
                    return status;
                }
                
                // Wait and retry
                return new Promise<JobStatusResponse>((resolve) => {
                    setTimeout(async () => {
                        const result = await checkStatus();
                        resolve(result);
                    }, 2000);
                });
            };
            
            try {
                const finalStatus = await checkStatus();
                if (finalStatus.status === 'failed') {
                    toast.error(finalStatus.error || 'Processing failed');
                    return;
                }
            } catch (err) {
                toast.error('Failed to check processing status');
                return;
            }
        }

        setIsLoading(true);
        const toastId = toast.loading('Getting recommendations...');

        try {
            // Trigger recommendations via pipeline
            await triggerRecommendations(session.sessionId, task, deployment);
            
            // Poll for completion
            session.startJobPolling(session.sessionId,
                () => {},
                (status) => {
                    if (status.recommendations) {
                        session.setRecommendation(status.recommendations);
                        toast.success('Recommendations ready!', { id: toastId });
                    }
                },
                (error) => {
                    toast.error(`Failed: ${error}`, { id: toastId });
                }
            );

        } catch (err) {
            toast.dismiss(toastId);
            if (err instanceof ApiError) {
                toast.error(err.message);
            } else {
                toast.error('Failed to get recommendation');
            }
        } finally {
            setIsLoading(false);
        }
    }, [session]);

    // Handle notebook Generation
    const handleGenerateNotebook = useCallback(async (modelId?: string) => {
        if (!session.sessionId) return;

        setIsLoading(true);
        const toastId = toast.loading('Generating notebook...');

        try {
            // Trigger generation via pipeline
            await triggerGeneration(session.sessionId, modelId);
            
            // Poll for completion
            session.startJobPolling(session.sessionId,
                () => {},
                (status) => {
                    if (status.notebook_path) {
                        session.setNotebook({
                            session_id: session.sessionId!,
                            notebook_filename: 'training.ipynb',
                            download_url: `/download/${session.sessionId}`,
                            colab_url: null,
                            message: 'Notebook ready!',
                        });
                        toast.success('Notebook generated successfully!', { id: toastId });
                    }
                },
                (error) => {
                    toast.error(`Failed: ${error}`, { id: toastId });
                }
            );

        } catch (err) {
            toast.dismiss(toastId);
            if (err instanceof ApiError) {
                toast.error(err.message);
            } else {
                toast.error('Failed to generate notebook');
            }
        } finally {
            setIsLoading(false);
        }
    }, [session]);

    // Handle retry failed job
    const handleRetry = useCallback(async () => {
        if (!session.sessionId) return;

        setIsProcessing(true);
        try {
            await triggerAnalysis(session.sessionId);
            session.startJobPolling(session.sessionId,
                () => {},
                (status) => {
                    toast.success('Processing complete!');
                },
                (error) => {
                    toast.error(`Retry failed: ${error}`);
                }
            );
        } catch (err) {
            toast.error('Failed to retry processing');
        } finally {
            setIsProcessing(false);
        }
    }, [session]);

    // Handle Start over
    const handleStartOver = useCallback(() => {
        session.reset();
    }, [session]);

    return (
        <div className="min-h-screen bg-[#141b1e] selection:bg-[#8ccf7e] selection:text-[#141b1e]">
            {/* Header */}
            <DashboardHeader />

            {/* Progress Bar */}
            <div className="border-b border-[#2d3437] bg-[#1e2528]/50 backdrop-blur-sm sticky top-0 z-20">
                <div className="container mx-auto px-4 py-4">
                    <div className="flex items-center justify-between max-w-2xl mx-auto">
                        {STEPS.map((step, idx) => (
                            <div key={step.key} className="flex items-center relative group">
                                {/* Step Circle */}
                                <div
                                    className={`
                                        flex items-center justify-center w-10 h-10 rounded-full font-medium transition-all duration-300
                                        ${idx < currentStepIndex
                                            ? 'bg-[#8ccf7e] text-[#141b1e] scale-100' // Completed
                                            : idx === currentStepIndex
                                                ? 'bg-gradient-to-br from-[#8ccf7e] to-[#6cbfbf] text-[#141b1e] shadow-lg shadow-[#8ccf7e]/30 scale-110 ring-4 ring-[#8ccf7e]/10' // Current
                                                : 'bg-[#1e2528] text-[#8a9899] border border-[#2d3437] group-hover:border-[#8ccf7e]/50 group-hover:text-[#dadada]' // Future
                                        }
                                    `}
                                >
                                    {idx < currentStepIndex ? (
                                        <Check className="w-5 h-5" />
                                    ) : (
                                        <step.Icon className="w-5 h-5" />
                                    )}
                                </div>

                                {/* Label */}
                                <span className={`ml-3 hidden sm:inline transition-colors duration-300 ${idx === currentStepIndex ? 'text-[#dadada] font-medium' : 'text-[#8a9899] group-hover:text-[#dadada]'
                                    }`}>
                                    {step.label}
                                </span>

                                {/* Connector Line */}
                                {idx < STEPS.length - 1 && (
                                    <div className="w-8 sm:w-16 h-0.5 mx-2 sm:mx-4 bg-[#2d3437] relative overflow-hidden rounded-full">
                                        <div
                                            className={`absolute inset-0 bg-[#8ccf7e] transition-transform duration-500 ease-out origin-left ${idx < currentStepIndex ? 'scale-x-100' : 'scale-x-0'
                                                }`}
                                        />
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>

                    {/* Job Progress Bar */}
                    {session.isJobProcessing && (
                        <div className="mt-4 max-w-2xl mx-auto">
                            <div className="flex items-center justify-between mb-1">
                                <span className="text-sm text-[#8a9899]">
                                    {PIPELINE_STEPS[session.currentPipelineStep]}...
                                </span>
                                <span className="text-sm text-[#8ccf7e] font-medium">
                                    {session.progressPercent}%
                                </span>
                            </div>
                            <div className="h-1.5 bg-[#141b1e] rounded-full overflow-hidden">
                                <motion.div
                                    className="h-full bg-gradient-to-r from-[#8ccf7e] to-[#67b0e8]"
                                    initial={{ width: 0 }}
                                    animate={{ width: `${session.progressPercent}%` }}
                                    transition={{ duration: 0.5 }}
                                />
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Main Content */}
            <main className="container mx-auto px-4 py-12">
                <div className="max-w-4xl mx-auto">
                    <AnimatePresence mode="wait">
                        {/* Step 1: Upload */}
                        {session.currentStep === 'upload' && (
                            <motion.div
                                key="upload"
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -20 }}
                                transition={{ duration: 0.3 }}
                                className="space-y-8"
                            >
                                <div className="text-center">
                                    <h1 className="text-3xl font-bold text-[#dadada]">Upload Your Dataset</h1>
                                    <p className="text-[#8a9899] mt-2">
                                        Start by uploading your JSONL training data
                                    </p>
                                </div>
                                <UploadZone
                                    onUpload={(sessionId, stats, preview) => {
                                        // This is the old synchronous callback
                                        // We now use the async handleUpload instead
                                    }}
                                    onError={(msg) => toast.error(msg)}
                                    onFileSelect={handleUpload}
                                    isProcessing={isProcessing}
                                />

                                {/* Example Format */}
                                <div className="p-6 bg-[#1e2528]/80 rounded-xl border border-[#2d3437]">
                                    <h3 className="font-medium text-[#dadada] mb-3">Expected Format</h3>
                                    <pre className="text-sm text-[#8a9899] font-mono overflow-x-auto">
                                        {`{"messages": [{"role": "user", "content": "Hello!"}, {"role": "assistant", "content": "Hi there!"}]}
{"messages": [{"role": "system", "content": "You are helpful."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}`}
                                    </pre>
                                </div>
                            </motion.div>
                        )}

                        {/* Step 2: Configure */}
                        {session.currentStep === 'configure' && session.stats && (
                            <motion.div
                                key="configure"
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -20 }}
                                transition={{ duration: 0.3 }}
                                className="space-y-8"
                            >
                                <StatsDisplay stats={session.stats} />

                                {/* Processing Status */}
                                {session.isJobProcessing && (
                                    <ProcessingStatusCard
                                        status={session.jobStatus}
                                        progress={session.progressPercent}
                                        currentStep={session.currentPipelineStep}
                                        error={session.jobError}
                                        onRetry={handleRetry}
                                    />
                                )}

                                {/* Chat preview */}
                                {session.filePreview && (
                                    <DataPreview fileContent={session.filePreview} maxExamples={3} />
                                )}

                                {/* Task selector - disabled while processing */}
                                <TaskSelector 
                                    onComplete={handleConfigComplete}
                                    disabled={session.isJobProcessing}
                                />

                                {/* Loading state */}
                                {(isLoading || (session.isJobProcessing && session.jobStatus === 'queued')) && (
                                    <div className="grid gap-4 animate-in fade-in zoom-in-95 duration-500">
                                        <ModelCardSkeleton />
                                        <ModelCardSkeleton />
                                        <ModelCardSkeleton />
                                    </div>
                                )}
                            </motion.div>
                        )}

                        {/* Step 3: Recommend */}
                        {session.currentStep === 'recommend' && session.recommendation && (
                            <motion.div
                                key="recommend"
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -20 }}
                                transition={{ duration: 0.3 }}
                                className="space-y-8"
                            >
                                <div className="text-center">
                                    <h1 className="text-3xl font-bold text-[#dadada]">Model Recommendation</h1>
                                    <p className="text-[#8a9899] mt-2">
                                        Based on your data and requirements, here&apos;s what we suggest
                                    </p>
                                </div>

                                {/* Primary Recommendation */}
                                <ModelCard model={session.recommendation.primary} isPrimary />

                                {/* Generate Button */}
                                <div className="text-center">
                                    <button
                                        onClick={() => handleGenerateNotebook()}
                                        disabled={isLoading || session.isJobProcessing}
                                        className="inline-flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-[#8ccf7e] to-[#6cbfbf] text-[#141b1e] font-semibold rounded-xl text-lg hover:shadow-xl hover:shadow-[#8ccf7e]/30 hover:-translate-y-1 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        {isLoading || session.isJobProcessing ? (
                                            <>
                                                <Loader2 className="w-5 h-5 animate-spin" />
                                                Processing...
                                            </>
                                        ) : (
                                            <>
                                                Generate Colab Notebook
                                                <ArrowRight className="w-5 h-5" />
                                            </>
                                        )}
                                    </button>
                                </div>

                                {/* Terminal Simulator - shows during generation */}
                                {(isLoading || session.isJobProcessing) && (
                                    <TerminalSimulator 
                                        currentStep={session.currentPipelineStep}
                                        progress={session.progressPercent}
                                    />
                                )}

                                {/* Alternative Models */}
                                {session.recommendation.alternatives.length > 0 && (
                                    <div>
                                        <h2 className="text-xl font-semibold text-[#dadada] mb-4">Alternatives</h2>
                                        <div className="grid gap-4">
                                            {session.recommendation.alternatives.map((model) => (
                                                <ModelCard
                                                    key={model.model_id}
                                                    model={model}
                                                    onSelect={() => handleGenerateNotebook(model.model_id)}
                                                />
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Custom Model Input */}
                                <CustomModelInput
                                    onSelect={(id) => handleGenerateNotebook(id)}
                                    disabled={isLoading || session.isJobProcessing}
                                />
                            </motion.div>
                        )}

                        {/* Step 4: Generate */}
                        {session.currentStep === 'generate' && session.notebook && (
                            <motion.div
                                key="generate"
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -20 }}
                                transition={{ duration: 0.3 }}
                            >
                                <NotebookReady
                                    filename={session.notebook.notebook_filename}
                                    downloadUrl={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${session.notebook.download_url}`}
                                    colabUrl={session.notebook.colab_url}
                                    onStartOver={handleStartOver}
                                />
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </main>
        </div>
    );
}

// Processing Status Card Component
function ProcessingStatusCard({
    status,
    progress,
    currentStep,
    error,
    onRetry,
}: {
    status: string;
    progress: number;
    currentStep: string;
    error: string | null;
    onRetry: () => void;
}) {
    const isQueued = status === 'queued';
    const isProcessing = status === 'processing';
    const isFailed = status === 'failed';

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`p-5 rounded-xl border ${
                isFailed 
                    ? 'bg-red-500/10 border-red-500/30' 
                    : 'bg-[#1e2528] border-[#2d3437]'
            }`}
        >
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                    {isFailed ? (
                        <AlertCircle className="w-5 h-5 text-red-400" />
                    ) : isQueued ? (
                        <Loader2 className="w-5 h-5 text-[#67b0e8] animate-spin" />
                    ) : (
                        <Loader2 className="w-5 h-5 text-[#8ccf7e] animate-spin" />
                    )}
                    <span className="font-medium text-[#dadada]">
                        {isQueued && 'Queued for processing...'}
                        {isProcessing && PIPELINE_STEPS[currentStep as keyof typeof PIPELINE_STEPS] + '...'}
                        {isFailed && 'Processing failed'}
                    </span>
                </div>
                {isFailed && (
                    <button
                        onClick={onRetry}
                        className="flex items-center gap-2 px-3 py-1.5 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg text-sm transition-colors"
                    >
                        <RefreshCw className="w-4 h-4" />
                        Retry
                    </button>
                )}
            </div>

            {/* Progress bar */}
            {!isFailed && (
                <div className="mb-3">
                    <div className="h-2 bg-[#141b1e] rounded-full overflow-hidden">
                        <motion.div
                            className="h-full bg-gradient-to-r from-[#8ccf7e] to-[#67b0e8]"
                            initial={{ width: 0 }}
                            animate={{ width: `${progress}%` }}
                            transition={{ duration: 0.5 }}
                        />
                    </div>
                </div>
            )}

            {/* Error message */}
            {error && (
                <p className="text-sm text-red-400 mt-2">{error}</p>
            )}

            {/* Hint */}
            {!isFailed && (
                <p className="text-xs text-[#8a9899] mt-2">
                    You can continue configuring while processing happens in the background.
                </p>
            )}
        </motion.div>
    );
}
