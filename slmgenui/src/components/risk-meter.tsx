/**
 * Risk Meter Component.
 * 
 * Visual meter showing hallucination risk level.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

'use client'

import { useState, useEffect } from 'react'
import { AlertTriangle, Check, Info, Lightbulb } from '@/components/icons'

interface RiskData {
    score: number
    level: string
    factors: string[]
    recommendation: string
}

interface RiskMeterProps {
    sessionId: string
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function RiskMeter({ sessionId }: RiskMeterProps) {
    const [risk, setRisk] = useState<RiskData | null>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        if (!sessionId) return

        fetch(`${API_URL}/risk/${sessionId}`)
            .then(res => res.ok ? res.json() : Promise.reject('Failed'))
            .then(setRisk)
            .catch(() => { })
            .finally(() => setLoading(false))
    }, [sessionId])

    if (loading || !risk) {
        return null
    }

    const colors = {
        low: { bg: 'bg-[#8ccf7e]', text: 'text-[#8ccf7e]', Icon: Check },
        medium: { bg: 'bg-[#e5c76b]', text: 'text-[#e5c76b]', Icon: Info },
        high: { bg: 'bg-[#e67e80]', text: 'text-[#e67e80]', Icon: AlertTriangle },
    }

    const { bg, text, Icon } = colors[risk.level as keyof typeof colors] || colors.medium

    return (
        <div className="p-5 bg-[#1e2528] border border-[#2d3437] rounded-xl">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <Icon className={`w-5 h-5 ${text}`} />
                    <span className="text-[#dadada] font-medium">Hallucination Risk</span>
                </div>
                <span className={`text-sm font-semibold ${text} uppercase`}>
                    {risk.level}
                </span>
            </div>

            {/* Meter */}
            <div className="h-3 bg-[#141b1e] rounded-full overflow-hidden mb-4">
                <div
                    className={`h-full ${bg} transition-all duration-500`}
                    style={{ width: `${risk.score * 100}%` }}
                />
            </div>

            {/* Factors */}
            {risk.factors.length > 0 && (
                <ul className="space-y-1 mb-4">
                    {risk.factors.map((factor, i) => (
                        <li key={i} className="text-sm text-[#8a9899] flex items-start gap-2">
                            <span className="text-[#8a9899]">•</span>
                            {factor}
                        </li>
                    ))}
                </ul>
            )}

            {/* Recommendation */}
            <div className="flex items-center gap-2 text-sm text-[#8a9899] p-3 bg-[#141b1e] rounded-lg">
                <Lightbulb className="w-4 h-4 text-[#e5c76b] flex-shrink-0" />
                {risk.recommendation}
            </div>
        </div>
    )
}
