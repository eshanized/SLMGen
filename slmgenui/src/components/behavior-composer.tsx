/**
 * Behavior Composer Component.
 * 
 * Sliders to compose a custom system prompt.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

'use client'

import { useState, useCallback } from 'react'
import { Settings, Copy, Check } from '@/components/icons'

interface BehaviorConfig {
    tone: number
    depth: number
    risk_tolerance: number
    creativity: number
}

interface ComposedBehavior {
    system_prompt: string
    explanation: string
    traits_summary: string
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const SLIDERS = [
    { key: 'tone', label: 'Tone', leftLabel: 'Casual', rightLabel: 'Formal' },
    { key: 'depth', label: 'Depth', leftLabel: 'Concise', rightLabel: 'Thorough' },
    { key: 'risk_tolerance', label: 'Risk', leftLabel: 'Safe', rightLabel: 'Bold' },
    { key: 'creativity', label: 'Creativity', leftLabel: 'Factual', rightLabel: 'Creative' },
] as const

export function BehaviorComposer() {
    const [config, setConfig] = useState<BehaviorConfig>({
        tone: 50,
        depth: 50,
        risk_tolerance: 30,
        creativity: 50,
    })
    const [result, setResult] = useState<ComposedBehavior | null>(null)
    const [loading, setLoading] = useState(false)
    const [copied, setCopied] = useState(false)

    const handleChange = useCallback((key: keyof BehaviorConfig, value: number) => {
        setConfig(prev => ({ ...prev, [key]: value }))
    }, [])

    const handleCompose = useCallback(async () => {
        setLoading(true)
        try {
            const res = await fetch(`${API_URL}/behavior/compose`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config),
            })
            if (res.ok) {
                const data = await res.json()
                setResult(data)
            }
        } catch (e) {
            console.error(e)
        } finally {
            setLoading(false)
        }
    }, [config])

    const handleCopy = useCallback(() => {
        if (result) {
            navigator.clipboard.writeText(result.system_prompt)
            setCopied(true)
            setTimeout(() => setCopied(false), 2000)
        }
    }, [result])

    return (
        <div className="p-5 bg-[#1e2528] border border-[#2d3437] rounded-xl space-y-5">
            {/* Header */}
            <div className="flex items-center gap-2">
                <Settings className="w-5 h-5 text-[#8ccf7e]" />
                <span className="text-[#dadada] font-medium">Behavior Composer</span>
            </div>

            {/* Sliders */}
            <div className="space-y-4">
                {SLIDERS.map(({ key, label, leftLabel, rightLabel }) => (
                    <div key={key}>
                        <div className="flex justify-between text-xs text-[#8a9899] mb-1">
                            <span>{leftLabel}</span>
                            <span className="text-[#dadada]">{label}</span>
                            <span>{rightLabel}</span>
                        </div>
                        <input
                            type="range"
                            min={0}
                            max={100}
                            value={config[key]}
                            onChange={(e) => handleChange(key, Number(e.target.value))}
                            className="w-full h-2 bg-[#141b1e] rounded-lg appearance-none cursor-pointer accent-[#8ccf7e]"
                        />
                    </div>
                ))}
            </div>

            {/* Compose Button */}
            <button
                onClick={handleCompose}
                disabled={loading}
                className="w-full py-2.5 bg-gradient-to-r from-[#8ccf7e] to-[#6cbfbf] text-[#141b1e] font-semibold rounded-lg hover:shadow-lg transition-all disabled:opacity-50"
            >
                {loading ? 'Composing...' : 'Generate System Prompt'}
            </button>

            {/* Result */}
            {result && (
                <div className="space-y-3">
                    <div className="flex items-center justify-between">
                        <span className="text-sm text-[#8a9899]">
                            Traits: <span className="text-[#dadada]">{result.traits_summary}</span>
                        </span>
                        <button
                            onClick={handleCopy}
                            className="flex items-center gap-1 text-xs text-[#8a9899] hover:text-[#dadada]"
                        >
                            {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                            {copied ? 'Copied!' : 'Copy'}
                        </button>
                    </div>
                    <pre className="p-4 bg-[#141b1e] rounded-lg text-xs text-[#dadada] whitespace-pre-wrap overflow-auto max-h-[200px]">
                        {result.system_prompt}
                    </pre>
                    <p className="text-xs text-[#8a9899]">{result.explanation}</p>
                </div>
            )}
        </div>
    )
}
