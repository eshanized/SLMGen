/**
 * Failure Preview Component.
 * 
 * Shows potential failure cases before training.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

'use client'

import { useState, useEffect } from 'react'
import { AlertTriangle, ChevronRight, Lightbulb } from '@/components/icons'

interface FailureCase {
    category: string
    user_prompt: string
    bad_response: string
    why_it_fails: string
    likelihood: string
}

interface FailurePreviewProps {
    sessionId: string
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function FailurePreview({ sessionId }: FailurePreviewProps) {
    const [cases, setCases] = useState<FailureCase[]>([])
    const [loading, setLoading] = useState(true)
    const [expanded, setExpanded] = useState<number | null>(null)

    useEffect(() => {
        if (!sessionId) return

        fetch(`${API_URL}/failure-preview/${sessionId}`)
            .then(res => res.ok ? res.json() : Promise.reject('Failed'))
            .then(setCases)
            .catch(() => setCases([]))
            .finally(() => setLoading(false))
    }, [sessionId])

    if (loading || cases.length === 0) return null

    const getLikelihoodColor = (likelihood: string) => {
        switch (likelihood) {
            case 'high': return 'text-[#e67e80] bg-[#e67e80]/10'
            case 'medium': return 'text-[#e5c76b] bg-[#e5c76b]/10'
            default: return 'text-[#8ccf7e] bg-[#8ccf7e]/10'
        }
    }

    return (
        <div className="p-5 bg-[#1e2528] border border-[#2d3437] rounded-xl">
            {/* Header */}
            <div className="flex items-center gap-2 mb-4">
                <AlertTriangle className="w-5 h-5 text-[#e5c76b]" />
                <span className="text-[#dadada] font-medium">Potential Failure Modes</span>
                <span className="text-xs text-[#8a9899]">(before training)</span>
            </div>

            {/* Cases */}
            <div className="space-y-3">
                {cases.map((c, i) => (
                    <div
                        key={i}
                        className="border border-[#2d3437] rounded-lg overflow-hidden"
                    >
                        <button
                            onClick={() => setExpanded(expanded === i ? null : i)}
                            className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-[#141b1e]/50 transition-colors"
                        >
                            <div className="flex items-center gap-3">
                                <span className={`px-2 py-0.5 text-xs rounded ${getLikelihoodColor(c.likelihood)}`}>
                                    {c.likelihood}
                                </span>
                                <span className="text-sm text-[#dadada] capitalize">
                                    {c.category.replace('_', ' ')}
                                </span>
                            </div>
                            <ChevronRight className={`w-4 h-4 text-[#8a9899] transition-transform ${expanded === i ? 'rotate-90' : ''}`} />
                        </button>

                        {expanded === i && (
                            <div className="px-4 pb-4 space-y-3 text-sm animate-in slide-in-from-top-2">
                                <div>
                                    <span className="text-[#8a9899]">User:</span>
                                    <p className="text-[#dadada] mt-1 p-2 bg-[#141b1e] rounded">{c.user_prompt}</p>
                                </div>
                                <div>
                                    <span className="text-[#e67e80]">Bad Response:</span>
                                    <p className="text-[#8a9899] mt-1 p-2 bg-[#141b1e] rounded">{c.bad_response}</p>
                                </div>
                                <div className="flex items-center gap-2 text-[#e5c76b] text-xs p-2 bg-[#e5c76b]/5 rounded">
                                    <Lightbulb className="w-3.5 h-3.5 flex-shrink-0" />
                                    {c.why_it_fails}
                                </div>
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    )
}
