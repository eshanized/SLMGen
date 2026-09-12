/**
 * Field Distribution Component.
 * 
 * Displays bar charts and statistics for dataset field distribution.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

'use client'

import { useState, useEffect } from 'react'
import {
    BarChart3,
    Loader2,
    MessageSquare,
    Users,
    Settings,
    AlertTriangle,
    Check
} from '@/components/icons'
import { API_URL } from '@/lib/api'

interface Distribution {
    roles: Record<string, number>
    avg_message_length: number
    token_distribution: Record<string, number>
    has_system_prompts: boolean
    multi_turn_percentage: number
}

interface FieldDistributionProps {
    sessionId: string
    apiUrl?: string
}

export function FieldDistribution({ sessionId, apiUrl = API_URL }: FieldDistributionProps) {
    const [distribution, setDistribution] = useState<Distribution | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        fetchDistribution()
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [sessionId])

    const fetchDistribution = async () => {
        setIsLoading(true)
        setError(null)

        try {
            const response = await fetch(`${apiUrl}/preview/${sessionId}/distribution`)
            if (!response.ok) throw new Error('Failed to fetch distribution')

            const data = await response.json()
            setDistribution(data)
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred')
        } finally {
            setIsLoading(false)
        }
    }

    if (isLoading) {
        return (
            <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 text-[#8ccf7e] animate-spin" />
            </div>
        )
    }

    if (error || !distribution) {
        return (
            <div className="text-center py-6 text-[#e57474]">
                {error || 'No distribution data'}
            </div>
        )
    }

    const totalRoles = Object.values(distribution.roles).reduce((a, b) => a + b, 0)
    const maxTokenBucket = Math.max(...Object.values(distribution.token_distribution))

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center gap-2 text-[#dadada]">
                <BarChart3 className="w-5 h-5 text-[#8ccf7e]" />
                <span className="font-medium">Field Distribution</span>
            </div>

            {/* Role Distribution */}
            <div className="bg-[#1e2528] border border-[#2d3437] rounded-xl p-4">
                <h4 className="text-sm font-medium text-[#dadada] mb-3">Message Roles</h4>
                <div className="space-y-2">
                    {Object.entries(distribution.roles).map(([role, count]) => {
                        const percentage = (count / totalRoles) * 100
                        const colors: Record<string, string> = {
                            system: '#c47fd5',
                            user: '#67b0e8',
                            assistant: '#8ccf7e'
                        }
                        const color = colors[role] || '#8a9899'

                        return (
                            <div key={role} className="space-y-1">
                                <div className="flex items-center justify-between text-sm">
                                    <span className="text-[#8a9899] capitalize">{role}</span>
                                    <span className="text-[#dadada]">{count.toLocaleString()}</span>
                                </div>
                                <div className="h-2 bg-[#141b1e] rounded-full overflow-hidden">
                                    <div
                                        className="h-full rounded-full transition-all"
                                        style={{
                                            width: `${percentage}%`,
                                            backgroundColor: color
                                        }}
                                    />
                                </div>
                            </div>
                        )
                    })}
                </div>
            </div>

            {/* Token Distribution */}
            <div className="bg-[#1e2528] border border-[#2d3437] rounded-xl p-4">
                <h4 className="text-sm font-medium text-[#dadada] mb-3">Token Distribution</h4>
                <div className="flex items-end gap-2 h-24">
                    {Object.entries(distribution.token_distribution).map(([bucket, count]) => {
                        const height = (count / maxTokenBucket) * 100

                        return (
                            <div key={bucket} className="flex-1 flex flex-col items-center gap-1">
                                <div
                                    className="w-full bg-gradient-to-t from-[#8ccf7e] to-[#6cbfbf] rounded-t transition-all"
                                    style={{ height: `${Math.max(height, 5)}%` }}
                                />
                                <span className="text-xs text-[#8a9899]">{bucket}</span>
                            </div>
                        )
                    })}
                </div>
                <p className="text-xs text-[#8a9899] mt-2 text-center">tokens per example</p>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 gap-3">
                <div className="bg-[#1e2528] border border-[#2d3437] rounded-xl p-4">
                    <div className="flex items-center gap-2 mb-2">
                        <MessageSquare className="w-4 h-4 text-[#67b0e8]" />
                        <span className="text-xs text-[#8a9899]">Avg Message Length</span>
                    </div>
                    <p className="text-xl font-bold text-[#dadada]">
                        {distribution.avg_message_length.toLocaleString()} <span className="text-sm font-normal text-[#8a9899]">chars</span>
                    </p>
                </div>

                <div className="bg-[#1e2528] border border-[#2d3437] rounded-xl p-4">
                    <div className="flex items-center gap-2 mb-2">
                        <Users className="w-4 h-4 text-[#c47fd5]" />
                        <span className="text-xs text-[#8a9899]">Multi-turn</span>
                    </div>
                    <p className="text-xl font-bold text-[#dadada]">
                        {distribution.multi_turn_percentage}%
                    </p>
                </div>

                <div className="bg-[#1e2528] border border-[#2d3437] rounded-xl p-4 col-span-2">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Settings className="w-4 h-4 text-[#8a9899]" />
                            <span className="text-sm text-[#8a9899]">System Prompts</span>
                        </div>
                        {distribution.has_system_prompts ? (
                            <span className="flex items-center gap-1 text-sm text-[#8ccf7e]">
                                <Check className="w-4 h-4" /> Present
                            </span>
                        ) : (
                            <span className="flex items-center gap-1 text-sm text-[#e5c76b]">
                                <AlertTriangle className="w-4 h-4" /> Not found
                            </span>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}
