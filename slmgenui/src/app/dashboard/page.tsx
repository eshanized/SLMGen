/**
 * Dashboard Page - Main Fine-tuning Wizard.
 * 
 * This is the heart of SLMGen! It guides users through 4 steps:
 * Upload → Configure → Recommend → Generate
 * 
 * Each step has its own UI, and we use framer-motion for smooth transitions.
 * The session hook tracks all the state as users progress.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @contributor Vedant Singh Rajput <teleported0722@gmail.com>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

'use client';

import { useState, useCallback } from 'react';
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
import { getRecommendation, generateNotebook, ApiError } from '@/lib/api';
import {
    Rocket,
    Upload,
    Settings,
    Target,
    Check,
    ArrowRight,
} from '@/components/icons';
import type { TaskType, DeploymentTarget } from '@/lib/types';

// Wizard step Labels
const STEPS = [
    { key: 'upload', label: 'Upload', Icon: Upload },
    { key: 'configure', label: 'Configure', Icon: Settings },
    { key: 'recommend', label: 'Recommend', Icon: Target },
    { key: 'generate', label: 'Generate', Icon: Rocket },
] as const;

export default function DashboardPage() {
    const session = useSession();
    const [isLoading, setIsLoading] = useState(false);

    // Get current step Index
    const currentStepIndex = STEPS.findIndex(s => s.key === session.currentStep);

    // Handle configuration Complete
    const handleConfigComplete = useCallback(async (task: TaskType, deployment: DeploymentTarget) => {
        if (!session.sessionId) return;

        session.setTask(task);
        session.setDeployment(deployment);
        setIsLoading(true);

        try {
            const recommendation = await getRecommendation(session.sessionId, task, deployment);
            session.setRecommendation(recommendation);
        } catch (err) {
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
            const notebook = await generateNotebook(session.sessionId, modelId);
            session.setNotebook(notebook);
            toast.success('Notebook generated successfully!', { id: toastId });
        } catch (err) {
            if (err instanceof ApiError) {
                toast.error(err.message, { id: toastId });
            } else {
                toast.error('Failed to generate notebook', { id: toastId });
            }
        } finally {
            setIsLoading(false);
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
                                        session.setSession(sessionId, stats, preview);
                                        toast.success('Dataset processed successfully!');
                                    }}
                                    onError={(msg) => toast.error(msg)}
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

                                {/* NEW: Chat preview of the uploaded data */}
                                {session.filePreview && (
                                    <DataPreview fileContent={session.filePreview} maxExamples={3} />
                                )}

                                <TaskSelector onComplete={handleConfigComplete} />

                                {/* Loading state */}
                                {isLoading && (
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
                                        disabled={isLoading}
                                        className="inline-flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-[#8ccf7e] to-[#6cbfbf] text-[#141b1e] font-semibold rounded-xl text-lg hover:shadow-xl hover:shadow-[#8ccf7e]/30 hover:-translate-y-1 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        {isLoading ? (
                                            <>
                                                <div className="w-5 h-5 border-2 border-[#141b1e] border-t-transparent rounded-full animate-spin" />
                                                Generating...
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
                                {isLoading && (
                                    <TerminalSimulator />
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
                                    disabled={isLoading}
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
                                    sessionId={session.sessionId!}
                                    filename={session.notebook.notebook_filename}
                                    colabUrl={session.notebook.colab_url}
                                    onStartOver={handleStartOver}
                                />
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </main >
        </div >
    );
}
