/**
 * Dashboard Page - Main Fine-tuning Wizard.
 * 
 * 4-step wizard: Upload → Configure → Recommend → Generate
 * Everblush themed with Lucide icons.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

'use client';

import { useState, useCallback } from 'react';
import Link from 'next/link';
import { useSession } from '@/hooks/use-session';
import { UploadZone } from '@/components/upload-zone';
import { StatsDisplay } from '@/components/stats-display';
import { TaskSelector } from '@/components/task-selector';
import { ModelCard } from '@/components/model-card';
import { NotebookReady } from '@/components/notebook-ready';
import { getRecommendation, generateNotebook, ApiError } from '@/lib/api';
import {
    Rocket,
    Upload,
    Settings,
    Target,
    Check,
    AlertTriangle,
    X,
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
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    // Get current step Index
    const currentStepIndex = STEPS.findIndex(s => s.key === session.currentStep);

    // Handle successful Upload
    const handleUpload = useCallback((sessionId: string, stats: typeof session.stats) => {
        if (stats) {
            session.setSession(sessionId, stats);
            setError(null);
        }
    }, [session]);

    // Handle configuration Complete
    const handleConfigComplete = useCallback(async (task: TaskType, deployment: DeploymentTarget) => {
        if (!session.sessionId) return;

        session.setTask(task);
        session.setDeployment(deployment);
        setIsLoading(true);
        setError(null);

        try {
            const recommendation = await getRecommendation(session.sessionId, task, deployment);
            session.setRecommendation(recommendation);
        } catch (err) {
            if (err instanceof ApiError) {
                setError(err.message);
            } else {
                setError('Failed to get recommendation');
            }
        } finally {
            setIsLoading(false);
        }
    }, [session]);

    // Handle notebook Generation
    const handleGenerateNotebook = useCallback(async (modelId?: string) => {
        if (!session.sessionId) return;

        setIsLoading(true);
        setError(null);

        try {
            const notebook = await generateNotebook(session.sessionId, modelId);
            session.setNotebook(notebook);
        } catch (err) {
            if (err instanceof ApiError) {
                setError(err.message);
            } else {
                setError('Failed to generate notebook');
            }
        } finally {
            setIsLoading(false);
        }
    }, [session]);

    // Handle Start over
    const handleStartOver = useCallback(() => {
        session.reset();
        setError(null);
    }, [session]);

    return (
        <div className="min-h-screen bg-[#141b1e]">
            {/* Header */}
            <header className="border-b border-[#2d3437]">
                <div className="container mx-auto px-4 py-4 flex items-center justify-between">
                    <Link href="/" className="flex items-center gap-2">
                        <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-[#8ccf7e] to-[#6cbfbf] flex items-center justify-center">
                            <Rocket className="w-5 h-5 text-[#141b1e]" />
                        </div>
                        <span className="text-xl font-bold text-[#dadada]">SLMGEN</span>
                    </Link>
                    <div className="flex items-center gap-4">
                        <Link href="/dashboard/history" className="text-sm text-[#8a9899] hover:text-[#dadada] transition-colors">
                            History
                        </Link>
                        <Link href="/dashboard/settings" className="text-sm text-[#8a9899] hover:text-[#dadada] transition-colors">
                            Settings
                        </Link>
                    </div>
                </div>
            </header>

            {/* Progress Bar */}
            <div className="border-b border-[#2d3437] bg-[#1e2528]/50">
                <div className="container mx-auto px-4 py-4">
                    <div className="flex items-center justify-between max-w-2xl mx-auto">
                        {STEPS.map((step, idx) => (
                            <div key={step.key} className="flex items-center">
                                {/* Step Circle */}
                                <div
                                    className={`
                                        flex items-center justify-center w-10 h-10 rounded-full font-medium transition-all
                                        ${idx < currentStepIndex
                                            ? 'bg-[#8ccf7e] text-[#141b1e]' // Completed
                                            : idx === currentStepIndex
                                                ? 'bg-gradient-to-br from-[#8ccf7e] to-[#6cbfbf] text-[#141b1e] shadow-lg shadow-[#8ccf7e]/30' // Current
                                                : 'bg-[#1e2528] text-[#8a9899] border border-[#2d3437]' // Future
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
                                <span className={`ml-2 hidden sm:inline ${idx === currentStepIndex ? 'text-[#dadada] font-medium' : 'text-[#8a9899]'
                                    }`}>
                                    {step.label}
                                </span>

                                {/* Connector Line */}
                                {idx < STEPS.length - 1 && (
                                    <div className={`w-8 sm:w-16 h-0.5 mx-2 sm:mx-4 ${idx < currentStepIndex ? 'bg-[#8ccf7e]' : 'bg-[#2d3437]'
                                        }`} />
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <main className="container mx-auto px-4 py-12">
                <div className="max-w-4xl mx-auto">
                    {/* Error Display */}
                    {error && (
                        <div className="mb-8 p-4 bg-[#e57474]/10 border border-[#e57474]/50 rounded-xl text-[#e57474]">
                            <div className="flex items-start gap-3">
                                <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                                <div className="flex-1">
                                    <p className="font-medium">Something went wrong</p>
                                    <p className="text-sm mt-1 opacity-80">{error}</p>
                                </div>
                                <button
                                    onClick={() => setError(null)}
                                    className="text-[#e57474] hover:text-[#dadada] transition-colors"
                                >
                                    <X className="w-5 h-5" />
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Step 1: Upload */}
                    {session.currentStep === 'upload' && (
                        <div className="space-y-8">
                            <div className="text-center">
                                <h1 className="text-3xl font-bold text-[#dadada]">Upload Your Dataset</h1>
                                <p className="text-[#8a9899] mt-2">
                                    Start by uploading your JSONL training data
                                </p>
                            </div>
                            <UploadZone onUpload={handleUpload} onError={setError} />

                            {/* Example Format */}
                            <div className="p-6 bg-[#1e2528]/80 rounded-xl border border-[#2d3437]">
                                <h3 className="font-medium text-[#dadada] mb-3">Expected Format</h3>
                                <pre className="text-sm text-[#8a9899] font-mono overflow-x-auto">
                                    {`{"messages": [{"role": "user", "content": "Hello!"}, {"role": "assistant", "content": "Hi there!"}]}
{"messages": [{"role": "system", "content": "You are helpful."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}`}
                                </pre>
                            </div>
                        </div>
                    )}

                    {/* Step 2: Configure */}
                    {session.currentStep === 'configure' && session.stats && (
                        <div className="space-y-8">
                            <StatsDisplay stats={session.stats} />
                            <TaskSelector onComplete={handleConfigComplete} />

                            {/* Loading state */}
                            {isLoading && (
                                <div className="text-center py-8">
                                    <div className="w-12 h-12 border-4 border-[#8ccf7e] border-t-transparent rounded-full animate-spin mx-auto" />
                                    <p className="text-[#8a9899] mt-4">Getting recommendations...</p>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Step 3: Recommend */}
                    {session.currentStep === 'recommend' && session.recommendation && (
                        <div className="space-y-8">
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
                                    className="inline-flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-[#8ccf7e] to-[#6cbfbf] text-[#141b1e] font-semibold rounded-xl text-lg hover:shadow-xl hover:shadow-[#8ccf7e]/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
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
                        </div>
                    )}

                    {/* Step 4: Generate */}
                    {session.currentStep === 'generate' && session.notebook && (
                        <NotebookReady
                            sessionId={session.sessionId!}
                            filename={session.notebook.notebook_filename}
                            colabUrl={session.notebook.colab_url}
                            onStartOver={handleStartOver}
                        />
                    )}
                </div>
            </main>
        </div>
    );
}
