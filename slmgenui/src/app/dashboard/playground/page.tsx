'use client';

/**
 * Inference Playground Page.
 * 
 * Real-time prompt testing and model comparison interface.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

import { useState, useEffect, useCallback } from 'react';
import { 
    Play, 
    Copy, 
    Check, 
    Clock, 
    Zap, 
    Target,
    AlertTriangle,
    MessageSquare,
    Bot,
    Loader2
} from 'lucide-react';
import { 
    runInference, 
    compareInference, 
    listInferenceModels,
    ApiError 
} from '@/lib/api';
import type { 
    ModelInfo, 
    InferenceResponse, 
    ComparisonResponse, 
    PromptHistoryItem,
    ComparisonMetrics 
} from '@/lib/types';
import { toast } from 'sonner';

// Risk level colors
const RISK_COLORS = {
    low: { bg: 'bg-emerald-500', text: 'text-emerald-400', icon: '✓' },
    medium: { bg: 'bg-amber-500', text: 'text-amber-400', icon: '!' },
    high: { bg: 'bg-red-500', text: 'text-red-400', icon: '✗' },
};

export default function PlaygroundPage() {
    // State
    const [models, setModels] = useState<ModelInfo[]>([]);
    const [baseModel, setBaseModel] = useState<string>('');
    const [tunedModel, setTunedModel] = useState<string>('');
    const [prompt, setPrompt] = useState<string>('');
    const [systemPrompt, setSystemPrompt] = useState<string>('');
    const [temperature, setTemperature] = useState<number>(0.7);
    const [maxTokens, setMaxTokens] = useState<number>(512);
    const [history, setHistory] = useState<PromptHistoryItem[]>([]);
    
    // Output state
    const [isRunning, setIsRunning] = useState<boolean>(false);
    const [isComparing, setIsComparing] = useState<boolean>(false);
    const [singleResult, setSingleResult] = useState<InferenceResponse | null>(null);
    const [comparisonResult, setComparisonResult] = useState<ComparisonResponse | null>(null);
    const [copiedId, setCopiedId] = useState<string | null>(null);

    // Load models on mount
    useEffect(() => {
        async function loadModels() {
            try {
                const response = await listInferenceModels();
                setModels(response.models);
                // Default to Phi-4 Mini
                const phiModel = response.models.find(m => m.model_id.includes('Phi'));
                if (phiModel) {
                    setBaseModel(phiModel.model_id);
                }
            } catch (error) {
                console.error('Failed to load models:', error);
                toast.error('Failed to load available models');
            }
        }
        loadModels();
    }, []);

    // Run single inference
    const handleRun = useCallback(async () => {
        if (!prompt.trim()) {
            toast.error('Please enter a prompt');
            return;
        }
        if (!baseModel) {
            toast.error('Please select a base model');
            return;
        }

        setIsRunning(true);
        setSingleResult(null);
        setComparisonResult(null);

        try {
            const result = await runInference({
                model_id: baseModel,
                prompt: prompt.trim(),
                system_prompt: systemPrompt.trim() || undefined,
                temperature,
                max_tokens: maxTokens,
            });

            setSingleResult(result);
            
            // Add to history
            addToHistory(prompt.trim(), systemPrompt.trim());
            
            if (result.error) {
                toast.warning(result.error);
            } else {
                toast.success('Inference complete');
            }
        } catch (error) {
            console.error('Inference failed:', error);
            toast.error(error instanceof ApiError ? error.message : 'Inference failed');
        } finally {
            setIsRunning(false);
        }
    }, [prompt, systemPrompt, baseModel, temperature, maxTokens]);

    // Run comparison
    const handleCompare = useCallback(async () => {
        if (!prompt.trim()) {
            toast.error('Please enter a prompt');
            return;
        }
        if (!baseModel) {
            toast.error('Please select a base model');
            return;
        }

        setIsComparing(true);
        setSingleResult(null);
        setComparisonResult(null);

        try {
            const result = await compareInference({
                base_model_id: baseModel,
                tuned_model_id: tunedModel || undefined,
                prompt: prompt.trim(),
                system_prompt: systemPrompt.trim() || undefined,
                temperature,
                max_tokens: maxTokens,
            });

            setComparisonResult(result);
            
            // Add to history
            addToHistory(prompt.trim(), systemPrompt.trim());
            
            if (result.error) {
                toast.warning(result.error);
            } else {
                toast.success('Comparison complete');
            }
        } catch (error) {
            console.error('Comparison failed:', error);
            toast.error(error instanceof ApiError ? error.message : 'Comparison failed');
        } finally {
            setIsComparing(false);
        }
    }, [prompt, systemPrompt, baseModel, tunedModel, temperature, maxTokens]);

    // Add prompt to history
    const addToHistory = (promptText: string, systemText: string) => {
        const newItem: PromptHistoryItem = {
            id: Date.now().toString(),
            prompt: promptText,
            systemPrompt: systemText || undefined,
            timestamp: new Date(),
        };
        setHistory(prev => [newItem, ...prev.slice(0, 4)]);
    };

    // Load from history
    const loadFromHistory = (item: PromptHistoryItem) => {
        setPrompt(item.prompt);
        if (item.systemPrompt) {
            setSystemPrompt(item.systemPrompt);
        }
    };

    // Copy to clipboard
    const copyToClipboard = async (text: string, id: string) => {
        try {
            await navigator.clipboard.writeText(text);
            setCopiedId(id);
            setTimeout(() => setCopiedId(null), 2000);
        } catch {
            toast.error('Failed to copy');
        }
    };

    return (
        <div className="min-h-screen bg-[#141b1e] text-[#dadada]">
            <div className="max-w-6xl mx-auto px-4 py-8">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-2xl font-bold flex items-center gap-3">
                        <Zap className="w-6 h-6 text-[#8ccf7e]" />
                        Inference Playground
                    </h1>
                    <p className="text-[#8a9899] mt-2">
                        Test prompts against models and compare outputs in real-time
                    </p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Input Section */}
                    <div className="lg:col-span-1 space-y-6">
                        {/* Model Selection */}
                        <div className="bg-[#1e2528] border border-[#2d3437] rounded-xl p-5">
                            <h3 className="font-medium mb-4 flex items-center gap-2">
                                <Bot className="w-4 h-4 text-[#8ccf7e]" />
                                Model Selection
                            </h3>
                            
                            {/* Base Model */}
                            <div className="mb-4">
                                <label className="text-sm text-[#8a9899] mb-2 block">
                                    Base Model
                                </label>
                                <select
                                    value={baseModel}
                                    onChange={(e) => setBaseModel(e.target.value)}
                                    className="w-full bg-[#141b1e] border border-[#2d3437] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8ccf7e]"
                                >
                                    <option value="">Select model...</option>
                                    {models.map((model) => (
                                        <option key={model.model_id} value={model.model_id}>
                                            {model.name} ({model.size})
                                        </option>
                                    ))}
                                </select>
                            </div>

                            {/* Tuned Model (optional) */}
                            <div>
                                <label className="text-sm text-[#8a9899] mb-2 block">
                                    Tuned Model (optional)
                                </label>
                                <select
                                    value={tunedModel}
                                    onChange={(e) => setTunedModel(e.target.value)}
                                    className="w-full bg-[#141b1e] border border-[#2d3437] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8ccf7e]"
                                >
                                    <option value="">None (single inference)</option>
                                    {models.map((model) => (
                                        <option key={model.model_id} value={model.model_id}>
                                            {model.name} ({model.size})
                                        </option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        {/* Prompt Input */}
                        <div className="bg-[#1e2528] border border-[#2d3437] rounded-xl p-5">
                            <h3 className="font-medium mb-4 flex items-center gap-2">
                                <MessageSquare className="w-4 h-4 text-[#8ccf7e]" />
                                Prompt
                            </h3>
                            
                            {/* System Prompt */}
                            <div className="mb-4">
                                <label className="text-sm text-[#8a9899] mb-2 block">
                                    System Prompt (optional)
                                </label>
                                <textarea
                                    value={systemPrompt}
                                    onChange={(e) => setSystemPrompt(e.target.value)}
                                    placeholder="You are a helpful assistant..."
                                    className="w-full bg-[#141b1e] border border-[#2d3437] rounded-lg px-3 py-2 text-sm h-20 resize-none focus:outline-none focus:border-[#8ccf7e]"
                                />
                            </div>

                            {/* User Prompt */}
                            <div className="mb-4">
                                <label className="text-sm text-[#8a9899] mb-2 block">
                                    User Prompt
                                </label>
                                <textarea
                                    value={prompt}
                                    onChange={(e) => setPrompt(e.target.value)}
                                    placeholder="What is machine learning?"
                                    className="w-full bg-[#141b1e] border border-[#2d3437] rounded-lg px-3 py-2 text-sm h-32 resize-none focus:outline-none focus:border-[#8ccf7e]"
                                />
                            </div>

                            {/* Parameters */}
                            <div className="grid grid-cols-2 gap-4 mb-4">
                                <div>
                                    <label className="text-sm text-[#8a9899] mb-2 block">
                                        Temperature: {temperature}
                                    </label>
                                    <input
                                        type="range"
                                        min="0"
                                        max="2"
                                        step="0.1"
                                        value={temperature}
                                        onChange={(e) => setTemperature(parseFloat(e.target.value))}
                                        className="w-full"
                                    />
                                </div>
                                <div>
                                    <label className="text-sm text-[#8a9899] mb-2 block">
                                        Max Tokens: {maxTokens}
                                    </label>
                                    <input
                                        type="range"
                                        min="64"
                                        max="2048"
                                        step="64"
                                        value={maxTokens}
                                        onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                                        className="w-full"
                                    />
                                </div>
                            </div>

                            {/* Run Buttons */}
                            <div className="flex gap-2">
                                <button
                                    onClick={handleRun}
                                    disabled={isRunning || isComparing}
                                    className="flex-1 bg-[#8ccf7e] text-[#141b1e] font-medium py-2 px-4 rounded-lg hover:bg-[#8ccf7e]/90 disabled:opacity-50 flex items-center justify-center gap-2"
                                >
                                    {isRunning ? (
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                    ) : (
                                        <Play className="w-4 h-4" />
                                    )}
                                    Run
                                </button>
                                <button
                                    onClick={handleCompare}
                                    disabled={isRunning || isComparing}
                                    className="flex-1 bg-[#67b0e8] text-white font-medium py-2 px-4 rounded-lg hover:bg-[#67b0e8]/90 disabled:opacity-50 flex items-center justify-center gap-2"
                                >
                                    {isComparing ? (
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                    ) : (
                                        <Target className="w-4 h-4" />
                                    )}
                                    Compare
                                </button>
                            </div>
                        </div>

                        {/* History */}
                        {history.length > 0 && (
                            <div className="bg-[#1e2528] border border-[#2d3437] rounded-xl p-5">
                                <h3 className="font-medium mb-4 text-[#8a9899]">
                                    Recent Prompts
                                </h3>
                                <div className="space-y-2">
                                    {history.map((item) => (
                                        <button
                                            key={item.id}
                                            onClick={() => loadFromHistory(item)}
                                            className="w-full text-left p-3 bg-[#141b1e] rounded-lg hover:bg-[#141b1e]/80 transition-colors"
                                        >
                                            <p className="text-sm truncate">{item.prompt}</p>
                                            <p className="text-xs text-[#8a9899] mt-1">
                                                {item.timestamp.toLocaleTimeString()}
                                            </p>
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Output Section */}
                    <div className="lg:col-span-2 space-y-6">
                        {/* Single Result */}
                        {singleResult && !comparisonResult && (
                            <OutputCard
                                title={singleResult.model_id}
                                output={singleResult.output}
                                latency_ms={singleResult.latency_ms}
                                tokens={singleResult.tokens}
                                error={singleResult.error}
                                onCopy={() => copyToClipboard(singleResult.output, 'single')}
                                copied={copiedId === 'single'}
                                riskScore={0.3}
                                riskLevel="low"
                            />
                        )}

                        {/* Comparison Results */}
                        {comparisonResult && (
                            <div className="space-y-6">
                                {/* Metrics */}
                                <MetricsCard metrics={comparisonResult.metrics} />

                                {/* Base Model Output */}
                                <OutputCard
                                    title={`Base: ${comparisonResult.base_model_id.split('/').pop()}`}
                                    output={comparisonResult.base_output}
                                    latency_ms={comparisonResult.base_latency_ms}
                                    tokens={comparisonResult.metrics.base_tokens}
                                    onCopy={() => copyToClipboard(comparisonResult.base_output, 'base')}
                                    copied={copiedId === 'base'}
                                    riskScore={comparisonResult.metrics.base_risk_score}
                                    riskLevel={comparisonResult.metrics.base_risk_level}
                                    color="border-[#67b0e8]"
                                />

                                {/* Tuned Model Output */}
                                {comparisonResult.tuned_output && (
                                    <OutputCard
                                        title={`Tuned: ${comparisonResult.tuned_model_id?.split('/').pop()}`}
                                        output={comparisonResult.tuned_output}
                                        latency_ms={comparisonResult.tuned_latency_ms}
                                        tokens={comparisonResult.metrics.tuned_tokens}
                                        onCopy={() => copyToClipboard(comparisonResult.tuned_output, 'tuned')}
                                        copied={copiedId === 'tuned'}
                                        riskScore={comparisonResult.metrics.tuned_risk_score}
                                        riskLevel={comparisonResult.metrics.tuned_risk_level}
                                        color="border-[#8ccf7e]"
                                    />
                                )}
                            </div>
                        )}

                        {/* Empty State */}
                        {!singleResult && !comparisonResult && (
                            <div className="bg-[#1e2528] border border-[#2d3437] rounded-xl p-12 text-center">
                                <Zap className="w-12 h-12 text-[#8a9899] mx-auto mb-4" />
                                <h3 className="text-lg font-medium mb-2">Ready to Test</h3>
                                <p className="text-[#8a9899]">
                                    Enter a prompt and click Run or Compare to see results
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

// Output Card Component
function OutputCard({
    title,
    output,
    latency_ms,
    tokens,
    error,
    onCopy,
    copied,
    riskScore,
    riskLevel,
    color = 'border-[#2d3437]',
}: {
    title: string;
    output: string;
    latency_ms: number;
    tokens: number;
    error?: string;
    onCopy: () => void;
    copied: boolean;
    riskScore: number;
    riskLevel: string;
    color?: string;
}) {
    const riskColor = RISK_COLORS[riskLevel as keyof typeof RISK_COLORS] || RISK_COLORS.medium;

    return (
        <div className={`bg-[#1e2528] border ${color} rounded-xl overflow-hidden`}>
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-[#2d3437]">
                <h3 className="font-medium truncate">{title}</h3>
                <div className="flex items-center gap-3 text-sm text-[#8a9899]">
                    <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {latency_ms.toFixed(0)}ms
                    </span>
                    <span>{tokens} tokens</span>
                    <button
                        onClick={onCopy}
                        className="p-1 hover:bg-[#2d3437] rounded transition-colors"
                    >
                        {copied ? (
                            <Check className="w-4 h-4 text-[#8ccf7e]" />
                        ) : (
                            <Copy className="w-4 h-4" />
                        )}
                    </button>
                </div>
            </div>

            {/* Output */}
            <div className="p-4">
                {error ? (
                    <div className="flex items-start gap-2 text-amber-400">
                        <AlertTriangle className="w-4 h-4 mt-0.5" />
                        <span className="text-sm">{error}</span>
                    </div>
                ) : (
                    <div className="prose prose-invert prose-sm max-w-none">
                        <p className="whitespace-pre-wrap text-[#dadada]">{output}</p>
                    </div>
                )}
            </div>

            {/* Footer - Risk Indicator */}
            {!error && (
                <div className="px-4 py-3 bg-[#141b1e] border-t border-[#2d3437] flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${riskColor.bg}`} />
                    <span className="text-xs text-[#8a9899]">Risk:</span>
                    <span className={`text-xs font-medium ${riskColor.text}`}>
                        {riskLevel.charAt(0).toUpperCase() + riskLevel.slice(1)}
                    </span>
                    <span className="text-xs text-[#8a9899]">
                        ({(riskScore * 100).toFixed(0)}%)
                    </span>
                </div>
            )}
        </div>
    );
}

// Metrics Card Component
function MetricsCard({ metrics }: { metrics: ComparisonMetrics }) {
    return (
        <div className="bg-[#1e2528] border border-[#2d3437] rounded-xl p-5">
            <h3 className="font-medium mb-4 flex items-center gap-2">
                <Target className="w-4 h-4 text-[#8ccf7e]" />
                Comparison Metrics
            </h3>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {/* Latency */}
                <MetricBox
                    label="Latency Delta"
                    value={`${metrics.latency_delta_ms > 0 ? '+' : ''}${metrics.latency_delta_ms.toFixed(0)}ms`}
                    sublabel="vs base"
                    positive={metrics.latency_delta_ms < 0}
                />

                {/* Token Delta */}
                <MetricBox
                    label="Token Delta"
                    value={`${metrics.token_delta > 0 ? '+' : ''}${metrics.token_delta}`}
                    sublabel="tokens"
                    positive={metrics.token_delta > 0}
                />

                {/* Similarity */}
                <MetricBox
                    label="Similarity"
                    value={`${(metrics.similarity_score * 100).toFixed(0)}%`}
                    sublabel="output match"
                    positive={metrics.similarity_score > 0.5}
                />

                {/* Quality */}
                <MetricBox
                    label="Quality"
                    value={`${(metrics.quality_score * 100).toFixed(0)}%`}
                    sublabel="composite"
                    positive={metrics.quality_score > 0.5}
                />
            </div>
        </div>
    );
}

// Metric Box Component
function MetricBox({
    label,
    value,
    sublabel,
    positive,
}: {
    label: string;
    value: string;
    sublabel: string;
    positive: boolean;
}) {
    return (
        <div className="bg-[#141b1e] rounded-lg p-3">
            <p className="text-xs text-[#8a9899] mb-1">{label}</p>
            <p className={`text-xl font-bold ${positive ? 'text-[#8ccf7e]' : 'text-[#e67e80]'}`}>
                {value}
            </p>
            <p className="text-xs text-[#8a9899]">{sublabel}</p>
        </div>
    );
}
