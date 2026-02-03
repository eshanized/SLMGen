"use client";

/**
 * Training Progress Component.
 * 
 * Displays real-time training progress from Colab notebooks.
 * Shows progress bar, loss chart, ETA, and training metrics.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
    Activity,
    Clock,
    TrendingDown,
    CheckCircle,
    XCircle,
    Loader2,
    BarChart3,
    Zap
} from "lucide-react";
import type { TrainingSessionStatus, TrainingEvent } from "@/lib/types";
import { getTrainingStatus, getTrainingEvents, subscribeToTraining } from "@/lib/api";

interface TrainingProgressProps {
    sessionId: string;
    onComplete?: (status: TrainingSessionStatus) => void;
}

export function TrainingProgress({ sessionId, onComplete }: TrainingProgressProps) {
    const [status, setStatus] = useState<TrainingSessionStatus | null>(null);
    const [events, setEvents] = useState<TrainingEvent[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    // Fetch initial status
    useEffect(() => {
        async function fetchInitial() {
            try {
                const [statusData, eventsData] = await Promise.all([
                    getTrainingStatus(sessionId),
                    getTrainingEvents(sessionId),
                ]);
                setStatus(statusData);
                setEvents(eventsData);
                setIsLoading(false);
            } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to load training status");
                setIsLoading(false);
            }
        }
        fetchInitial();
    }, [sessionId]);

    // Subscribe to SSE updates
    useEffect(() => {
        if (!sessionId) return;

        const unsubscribe = subscribeToTraining(
            sessionId,
            (newStatus) => {
                setStatus(newStatus);
                // Fetch new events
                getTrainingEvents(sessionId, status?.current_step).then(setEvents);
            },
            (finalStatus) => {
                setStatus(finalStatus);
                onComplete?.(finalStatus);
            },
            (errorMsg) => {
                setError(errorMsg);
            }
        );

        return unsubscribe;
    }, [sessionId, status?.current_step, onComplete]);

    // Status indicator component
    const StatusIndicator = useCallback(() => {
        if (!status) return null;

        const statusConfig = {
            pending: { icon: Clock, color: "text-yellow-400", bg: "bg-yellow-400/10", label: "Waiting to start" },
            running: { icon: Activity, color: "text-blue-400", bg: "bg-blue-400/10", label: "Training in progress" },
            completed: { icon: CheckCircle, color: "text-green-400", bg: "bg-green-400/10", label: "Training complete" },
            failed: { icon: XCircle, color: "text-red-400", bg: "bg-red-400/10", label: "Training failed" },
        };

        const config = statusConfig[status.status];
        const Icon = config.icon;

        return (
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${config.bg}`}>
                {status.status === "running" ? (
                    <Loader2 className={`w-4 h-4 ${config.color} animate-spin`} />
                ) : (
                    <Icon className={`w-4 h-4 ${config.color}`} />
                )}
                <span className={`text-sm font-medium ${config.color}`}>{config.label}</span>
            </div>
        );
    }, [status]);

    // Loading state
    if (isLoading) {
        return (
            <div className="flex items-center justify-center p-8">
                <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
            </div>
        );
    }

    // Error state
    if (error) {
        return (
            <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-6">
                <div className="flex items-center gap-3">
                    <XCircle className="w-6 h-6 text-red-400" />
                    <div>
                        <h3 className="font-semibold text-red-400">Error Loading Training Progress</h3>
                        <p className="text-sm text-gray-400">{error}</p>
                    </div>
                </div>
            </div>
        );
    }

    // No status available
    if (!status) {
        return (
            <div className="bg-gray-800/50 rounded-lg p-6 text-center">
                <p className="text-gray-400">No training session found</p>
            </div>
        );
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gray-900/80 backdrop-blur-xl rounded-xl border border-gray-800 p-6"
        >
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-500/10 rounded-lg">
                        <BarChart3 className="w-5 h-5 text-blue-400" />
                    </div>
                    <div>
                        <h2 className="text-lg font-semibold text-white">Training Progress</h2>
                        <p className="text-sm text-gray-400">{status.model_id}</p>
                    </div>
                </div>
                <StatusIndicator />
            </div>

            {/* Progress Bar */}
            <div className="mb-6">
                <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-400">
                        Step {status.current_step.toLocaleString()} / {status.total_steps.toLocaleString()}
                    </span>
                    <span className="text-sm font-medium text-white">
                        {status.progress_percent.toFixed(1)}%
                    </span>
                </div>
                <div className="h-3 bg-gray-800 rounded-full overflow-hidden">
                    <motion.div
                        className="h-full bg-gradient-to-r from-blue-500 to-purple-500"
                        initial={{ width: 0 }}
                        animate={{ width: `${status.progress_percent}%` }}
                        transition={{ duration: 0.5, ease: "easeOut" }}
                    />
                </div>
            </div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                {/* Current Epoch */}
                <div className="bg-gray-800/50 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-1">
                        <Zap className="w-4 h-4 text-yellow-400" />
                        <span className="text-xs text-gray-400 uppercase">Epoch</span>
                    </div>
                    <p className="text-xl font-semibold text-white">
                        {status.current_epoch} / {status.total_epochs}
                    </p>
                </div>

                {/* Latest Loss */}
                <div className="bg-gray-800/50 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-1">
                        <TrendingDown className="w-4 h-4 text-green-400" />
                        <span className="text-xs text-gray-400 uppercase">Loss</span>
                    </div>
                    <p className="text-xl font-semibold text-white">
                        {status.latest_loss !== undefined ? status.latest_loss.toFixed(4) : "--"}
                    </p>
                </div>

                {/* ETA */}
                <div className="bg-gray-800/50 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-1">
                        <Clock className="w-4 h-4 text-blue-400" />
                        <span className="text-xs text-gray-400 uppercase">ETA</span>
                    </div>
                    <p className="text-xl font-semibold text-white">
                        {status.eta_formatted || "--"}
                    </p>
                </div>

                {/* Events */}
                <div className="bg-gray-800/50 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-1">
                        <Activity className="w-4 h-4 text-purple-400" />
                        <span className="text-xs text-gray-400 uppercase">Events</span>
                    </div>
                    <p className="text-xl font-semibold text-white">
                        {status.event_count}
                    </p>
                </div>
            </div>

            {/* Loss Chart (Simple SVG) */}
            <AnimatePresence>
                {events.length > 1 && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        className="bg-gray-800/50 rounded-lg p-4"
                    >
                        <h3 className="text-sm font-medium text-gray-300 mb-3">Loss Curve</h3>
                        <LossChart events={events} />
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Error Message */}
            {status.error_message && (
                <div className="mt-4 bg-red-500/10 border border-red-500/20 rounded-lg p-4">
                    <p className="text-sm text-red-400">{status.error_message}</p>
                </div>
            )}
        </motion.div>
    );
}

// Simple Loss Chart Component
function LossChart({ events }: { events: TrainingEvent[] }) {
    if (events.length < 2) return null;

    const losses = events.map(e => e.loss);
    const minLoss = Math.min(...losses);
    const maxLoss = Math.max(...losses);
    const range = maxLoss - minLoss || 1;

    const width = 100;
    const height = 60;
    const padding = 5;

    const points = events.map((e, i) => {
        const x = padding + (i / (events.length - 1)) * (width - 2 * padding);
        const y = height - padding - ((e.loss - minLoss) / range) * (height - 2 * padding);
        return `${x},${y}`;
    }).join(" ");

    return (
        <svg
            viewBox={`0 0 ${width} ${height}`}
            className="w-full h-32"
            preserveAspectRatio="none"
        >
            {/* Grid lines */}
            <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding}
                stroke="rgb(55, 65, 81)" strokeWidth="0.5" />
            <line x1={padding} y1={padding} x2={padding} y2={height - padding}
                stroke="rgb(55, 65, 81)" strokeWidth="0.5" />

            {/* Loss line */}
            <motion.polyline
                points={points}
                fill="none"
                stroke="url(#lossGradient)"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 1, ease: "easeOut" }}
            />

            {/* Gradient definition */}
            <defs>
                <linearGradient id="lossGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#3b82f6" />
                    <stop offset="100%" stopColor="#a855f7" />
                </linearGradient>
            </defs>
        </svg>
    );
}
