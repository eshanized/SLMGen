/**
 * Personality Display Component.
 * 
 * Shows dataset personality analysis in a human-readable format.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

'use client'

import { useState, useEffect } from 'react'
import { User, Sparkles, MessageSquare, Settings } from '@/components/icons'

interface Personality {
    tone: string
    verbosity: string
    technicality: string
    strictness: string
    confidence: number
    summary: string
}

interface PersonalityDisplayProps {
    sessionId: string
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function PersonalityDisplay({ sessionId }: PersonalityDisplayProps) {
    const [personality, setPersonality] = useState<Personality | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        if (!sessionId) return

        fetch(`${API_URL}/personality/${sessionId}`)
            .then(res => res.ok ? res.json() : Promise.reject('Failed to load'))
            .then(setPersonality)
            .catch(e => setError(String(e)))
            .finally(() => setLoading(false))
    }, [sessionId])

    if (loading) {
        return (
            <div className="p-4 bg-[#1e2528] border border-[#2d3437] rounded-xl animate-pulse">
                <div className="h-4 bg-[#2d3437] rounded w-3/4"></div>
            </div>
        )
    }

    if (error || !personality) {
        return null
    }

    const traits = [
        { label: 'Tone', value: personality.tone, Icon: MessageSquare },
        { label: 'Verbosity', value: personality.verbosity, Icon: Settings },
        { label: 'Technicality', value: personality.technicality, Icon: Sparkles },
        { label: 'Strictness', value: personality.strictness, Icon: User },
    ]

    return (
        <div className="p-5 bg-[#1e2528] border border-[#2d3437] rounded-xl">
            {/* Summary */}
            <p className="text-[#dadada] font-medium mb-4">
                {personality.summary}
            </p>

            {/* Traits */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {traits.map(({ label, value, Icon }) => (
                    <div key={label} className="flex items-center gap-2 text-sm">
                        <Icon className="w-4 h-4 text-[#8ccf7e]" />
                        <span className="text-[#8a9899]">{label}:</span>
                        <span className="text-[#dadada] capitalize">{value}</span>
                    </div>
                ))}
            </div>

            {/* Confidence */}
            <div className="mt-4 flex items-center gap-2 text-xs text-[#8a9899]">
                <span>Confidence:</span>
                <div className="flex-1 h-1.5 bg-[#141b1e] rounded-full max-w-[100px]">
                    <div
                        className="h-full bg-[#8ccf7e] rounded-full"
                        style={{ width: `${personality.confidence * 100}%` }}
                    />
                </div>
                <span>{Math.round(personality.confidence * 100)}%</span>
            </div>
        </div>
    )
}
