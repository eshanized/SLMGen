/**
 * Model Recommendation Card Component.
 * 
 * Displays model info with score ring and reasons.
 * Everblush themed with Lucide icons.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

'use client';

import { motion } from 'framer-motion';
import { Star, Lock } from '@/components/icons';
import type { ModelRecommendation } from '@/lib/types';
import { Skeleton } from '@/components/ui/skeleton';

interface ModelCardProps {
    model: ModelRecommendation;
    isPrimary?: boolean;
    onSelect?: () => void;
}

export function ModelCard({ model, isPrimary = false, onSelect }: ModelCardProps) {
    // Calculate score ring - SVG circle math
    const radius = 40;
    const circumference = 2 * Math.PI * radius;
    const scorePercent = model.score / 100;
    const strokeDashoffset = circumference * (1 - scorePercent);

    // Score color based on Value (Everblush)
    const getScoreColor = (score: number) => {
        if (score >= 80) return 'text-[#8ccf7e]';
        if (score >= 60) return 'text-[#e5c76b]';
        return 'text-[#e69875]';
    };

    const getScoreStroke = (score: number) => {
        if (score >= 80) return 'stroke-[#8ccf7e]';
        if (score >= 60) return 'stroke-[#e5c76b]';
        return 'stroke-[#e69875]';
    };

    return (
        <motion.div
            layout
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            whileHover={onSelect ? { scale: 1.02, y: -4 } : { y: -2 }}
            transition={{ type: "spring", stiffness: 300, damping: 25 }}
            className={`
                relative rounded-2xl p-6 glass-interactive
                ${isPrimary
                    ? 'bg-gradient-to-br from-[#8ccf7e]/10 to-[#c47fd5]/10 border-2 border-[#8ccf7e]/50 shadow-xl shadow-[#8ccf7e]/10'
                    : 'bg-[#1e2528]/80 border border-[#2d3437] hover:border-[#8ccf7e]/50'
                }
                ${onSelect ? 'cursor-pointer' : ''}
            `}
            onClick={onSelect}
        >
            {/* Primary Badge */}
            {isPrimary && (
                <div className="absolute -top-3 left-6 flex items-center gap-1.5 px-3 py-1 bg-gradient-to-r from-[#8ccf7e] to-[#6cbfbf] rounded-full text-sm font-semibold text-[#141b1e] shadow-lg shadow-[#8ccf7e]/30 z-10">
                    <Star className="w-4 h-4" />
                    Best Match
                </div>
            )}

            <div className="flex items-start gap-6">
                {/* Score Ring */}
                <div className="relative flex-shrink-0">
                    <svg className="w-24 h-24 -rotate-90">
                        {/* Background circle */}
                        <circle
                            cx="48"
                            cy="48"
                            r={radius}
                            strokeWidth="8"
                            className="fill-none stroke-[#2d3437]"
                        />
                        {/* Score circle */}
                        <motion.circle
                            cx="48"
                            cy="48"
                            r={radius}
                            strokeWidth="8"
                            strokeDasharray={circumference}
                            initial={{ strokeDashoffset: circumference }}
                            animate={{ strokeDashoffset: strokeDashoffset }}
                            transition={{ duration: 1.5, ease: "easeOut", delay: 0.2 }}
                            strokeLinecap="round"
                            className={`fill-none ${getScoreStroke(model.score)}`}
                        />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                        <span className={`text-2xl font-bold ${getScoreColor(model.score)}`}>
                            {Math.round(model.score)}
                        </span>
                    </div>
                </div>

                {/* Model Info */}
                <div className="flex-1 min-w-0">
                    <h3 className="text-xl font-bold text-[#dadada] truncate">{model.model_name}</h3>

                    <div className="flex flex-wrap gap-2 mt-2">
                        <span className="px-2 py-1 bg-[#141b1e] rounded-md text-sm text-[#8a9899] border border-[#2d3437]">
                            {model.size}
                        </span>
                        <span className="px-2 py-1 bg-[#141b1e] rounded-md text-sm text-[#8a9899] border border-[#2d3437]">
                            {(model.context_window / 1000).toFixed(0)}K context
                        </span>
                        {model.is_gated && (
                            <span className="flex items-center gap-1 px-2 py-1 bg-[#e5c76b]/10 text-[#e5c76b] rounded-md text-sm">
                                <Lock className="w-3.5 h-3.5" />
                                Gated
                            </span>
                        )}
                    </div>

                    {/* Reasons */}
                    <ul className="mt-4 space-y-1">
                        {model.reasons.map((reason, idx) => (
                            <li key={idx} className="text-sm text-[#8a9899] flex items-start gap-2">
                                <span className="text-[#8ccf7e] flex-shrink-0">•</span>
                                {reason.replace(/^[✅💪⚡🎯]+\s*/, '')}
                            </li>
                        ))}
                    </ul>
                </div>
            </div>

            {/* Model ID */}
            <div className="mt-4 pt-4 border-t border-[#2d3437]">
                <code className="text-xs text-[#8a9899] font-mono break-all">{model.model_id}</code>
            </div>
        </motion.div>
    );
}

export function ModelCardSkeleton() {
    return (
        <div className="rounded-2xl p-6 bg-[#1e2528]/80 border border-[#2d3437]">
            <div className="flex items-start gap-6">
                {/* Score Ring Skeleton */}
                <Skeleton className="w-24 h-24 rounded-full flex-shrink-0" />

                <div className="flex-1 space-y-4">
                    {/* Title */}
                    <Skeleton className="h-8 w-3/4" />

                    {/* Tags */}
                    <div className="flex gap-2">
                        <Skeleton className="h-6 w-16" />
                        <Skeleton className="h-6 w-24" />
                    </div>

                    {/* Reasons */}
                    <div className="space-y-2 mt-4">
                        <Skeleton className="h-4 w-full" />
                        <Skeleton className="h-4 w-5/6" />
                        <Skeleton className="h-4 w-4/6" />
                    </div>
                </div>
            </div>

            {/* Footer */}
            <div className="mt-4 pt-4 border-t border-[#2d3437]">
                <Skeleton className="h-4 w-1/2" />
            </div>
        </div>
    )
}
