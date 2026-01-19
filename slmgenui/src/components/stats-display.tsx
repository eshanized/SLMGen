/**
 * Stats Display Component.
 * 
 * Shows dataset statistics after upload.
 * Everblush themed with Lucide icons.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

'use client';

import { BarChart3, FileText, Hash, Gauge, MessageSquare, Settings } from '@/components/icons';
import type { DatasetStats } from '@/lib/types';

interface StatsDisplayProps {
    stats: DatasetStats;
}

export function StatsDisplay({ stats }: StatsDisplayProps) {
    // Quality score color
    const getQualityColor = (score: number) => {
        if (score >= 0.8) return 'text-[#8ccf7e]';
        if (score >= 0.5) return 'text-[#e5c76b]';
        return 'text-[#e57474]';
    };

    return (
        <div className="bg-[#1e2528]/80 rounded-xl p-6 border border-[#2d3437]">
            <h3 className="flex items-center gap-2 text-lg font-semibold text-[#dadada] mb-4">
                <BarChart3 className="w-5 h-5 text-[#8ccf7e]" />
                Dataset Overview
            </h3>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
                <div className="text-center p-4 rounded-lg bg-[#141b1e]/50">
                    <FileText className="w-5 h-5 text-[#67b0e8] mx-auto mb-2" />
                    <div className="text-2xl font-bold text-[#67b0e8]">{stats.total_examples.toLocaleString()}</div>
                    <div className="text-sm text-[#8a9899]">Examples</div>
                </div>
                <div className="text-center p-4 rounded-lg bg-[#141b1e]/50">
                    <Hash className="w-5 h-5 text-[#c47fd5] mx-auto mb-2" />
                    <div className="text-2xl font-bold text-[#c47fd5]">{stats.total_tokens.toLocaleString()}</div>
                    <div className="text-sm text-[#8a9899]">Tokens</div>
                </div>
                <div className="text-center p-4 rounded-lg bg-[#141b1e]/50">
                    <BarChart3 className="w-5 h-5 text-[#6cbfbf] mx-auto mb-2" />
                    <div className="text-2xl font-bold text-[#6cbfbf]">{stats.avg_tokens_per_example}</div>
                    <div className="text-sm text-[#8a9899]">Avg per Example</div>
                </div>
                <div className="text-center p-4 rounded-lg bg-[#141b1e]/50">
                    <Gauge className="w-5 h-5 mx-auto mb-2" style={{ color: stats.quality_score >= 0.8 ? '#8ccf7e' : stats.quality_score >= 0.5 ? '#e5c76b' : '#e57474' }} />
                    <div className={`text-2xl font-bold ${getQualityColor(stats.quality_score)}`}>
                        {Math.round(stats.quality_score * 100)}%
                    </div>
                    <div className="text-sm text-[#8a9899]">Quality Score</div>
                </div>
            </div>

            {/* Turn Distribution */}
            <div className="flex items-center gap-3 mb-4">
                <div className="flex-1 h-2 bg-[#141b1e] rounded-full overflow-hidden">
                    <div
                        className="h-full bg-gradient-to-r from-[#67b0e8] to-[#c47fd5] rounded-full transition-all duration-500"
                        style={{ width: `${stats.single_turn_pct}%` }}
                    />
                </div>
                <span className="text-xs text-[#8a9899] w-32 text-right">
                    {stats.single_turn_pct}% single / {stats.multi_turn_pct}% multi
                </span>
            </div>

            {/* Quality Issues */}
            {stats.quality_issues.length > 0 && (
                <div className="mt-4 pt-4 border-t border-[#2d3437]">
                    <ul className="space-y-1">
                        {stats.quality_issues.map((issue, idx) => (
                            <li key={idx} className="text-sm text-[#e5c76b] flex items-start gap-2">
                                <span className="text-[#e5c76b]">•</span>
                                {issue}
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {/* Features */}
            <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-[#2d3437]">
                {stats.has_system_prompts && (
                    <span className="flex items-center gap-1.5 px-3 py-1.5 bg-[#67b0e8]/10 text-[#67b0e8] rounded-lg text-xs font-medium">
                        <Settings className="w-3.5 h-3.5" />
                        System Prompts
                    </span>
                )}
                {stats.multi_turn_pct > 50 && (
                    <span className="flex items-center gap-1.5 px-3 py-1.5 bg-[#c47fd5]/10 text-[#c47fd5] rounded-lg text-xs font-medium">
                        <MessageSquare className="w-3.5 h-3.5" />
                        Multi-turn Conversations
                    </span>
                )}
            </div>
        </div>
    );
}
