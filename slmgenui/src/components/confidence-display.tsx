/**
 * Confidence Display Component.
 * 
 * Shows dataset confidence score and breakdown.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

'use client'

import { useState, useEffect } from 'react'
import { Shield, Check, AlertTriangle } from '@/components/icons'

interface Confidence {
    score: number
    level: string
    coverage: number
    redundancy: number
    diversity: number
    explanation: string
}

interface ConfidenceDisplayProps {
    sessionId: string
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function ConfidenceDisplay({ sessionId }: ConfidenceDisplayProps) {
    const [confidence, setConfidence] = useState<Confidence | null>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        if (!sessionId) return

        fetch(`${API_URL}/confidence/${sessionId}`)
            .then(res => res.ok ? res.json() : Promise.reject('Failed'))
            .then(setConfidence)
            .catch(() => { })
            .finally(() => setLoading(false))
    }, [sessionId])

    if (loading || !confidence) return null

    const levelColors = {
        high: 'text-[#8ccf7e]',
        medium: 'text-[#e5c76b]',
        low: 'text-[#e67e80]',
    }

    const metrics = [
        { label: 'Coverage', value: confidence.coverage, good: confidence.coverage > 0.5 },
        { label: 'Redundancy', value: 1 - confidence.redundancy, good: confidence.redundancy < 0.1 },
        { label: 'Diversity', value: confidence.diversity, good: confidence.diversity > 0.5 },
    ]

    return (
        <div className="p-5 bg-[#1e2528] border border-[#2d3437] rounded-xl">
            {/* Header with Score */}
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <Shield className="w-5 h-5 text-[#8ccf7e]" />
                    <span className="text-[#dadada] font-medium">Training Confidence</span>
                </div>
                <div className="flex items-center gap-2">
                    <span className={`text-2xl font-bold ${levelColors[confidence.level as keyof typeof levelColors]}`}>
                        {Math.round(confidence.score * 100)}%
                    </span>
                    <span className={`text-xs uppercase ${levelColors[confidence.level as keyof typeof levelColors]}`}>
                        {confidence.level}
                    </span>
                </div>
            </div>

            {/* Metrics */}
            <div className="grid grid-cols-3 gap-4 mb-4">
                {metrics.map(({ label, value, good }) => (
                    <div key={label} className="text-center">
                        <div className={`text-lg font-semibold ${good ? 'text-[#8ccf7e]' : 'text-[#e5c76b]'}`}>
                            {Math.round(value * 100)}%
                        </div>
                        <div className="text-xs text-[#8a9899]">{label}</div>
                    </div>
                ))}
            </div>

            {/* Explanation */}
            <p className="text-sm text-[#8a9899] p-3 bg-[#141b1e] rounded-lg">
                {confidence.explanation}
            </p>
        </div>
    )
}
