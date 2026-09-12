/**
 * Dataset Preview Component.
 * 
 * Shows paginated preview of dataset examples with syntax highlighting.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

'use client'

import { useState, useEffect } from 'react'
import {
    ChevronLeft,
    ChevronRight,
    Eye,
    User,
    Bot,
    Settings,
    Loader2
} from '@/components/icons'
import { API_URL } from '@/lib/api'

interface Message {
    role: string
    content: string
}

interface Example {
    index: number
    messages: Message[]
    token_count: number
}

interface DatasetPreviewProps {
    sessionId: string
    apiUrl?: string
}

const ROLE_STYLES = {
    system: { icon: Settings, bg: 'bg-[#c47fd5]/10', text: 'text-[#c47fd5]', label: 'System' },
    user: { icon: User, bg: 'bg-[#67b0e8]/10', text: 'text-[#67b0e8]', label: 'User' },
    assistant: { icon: Bot, bg: 'bg-[#8ccf7e]/10', text: 'text-[#8ccf7e]', label: 'Assistant' },
}

export function DatasetPreview({ sessionId, apiUrl = API_URL }: DatasetPreviewProps) {
    const [examples, setExamples] = useState<Example[]>([])
    const [totalCount, setTotalCount] = useState(0)
    const [page, setPage] = useState(1)
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const pageSize = 3

    useEffect(() => {
        fetchPreview()
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [page, sessionId])

    const fetchPreview = async () => {
        setIsLoading(true)
        setError(null)

        try {
            const response = await fetch(
                `${apiUrl}/preview/${sessionId}?page=${page}&page_size=${pageSize}`
            )

            if (!response.ok) throw new Error('Failed to fetch preview')

            const data = await response.json()
            setExamples(data.examples)
            setTotalCount(data.total_count)
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred')
        } finally {
            setIsLoading(false)
        }
    }

    const totalPages = Math.ceil(totalCount / pageSize)

    if (isLoading) {
        return (
            <div className="flex items-center justify-center py-12">
                <Loader2 className="w-6 h-6 text-[#8ccf7e] animate-spin" />
            </div>
        )
    }

    if (error) {
        return (
            <div className="text-center py-8 text-[#e57474]">
                {error}
            </div>
        )
    }

    return (
        <div className="space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-[#dadada]">
                    <Eye className="w-5 h-5 text-[#8ccf7e]" />
                    <span className="font-medium">Dataset Preview</span>
                    <span className="text-sm text-[#8a9899]">
                        ({totalCount.toLocaleString()} examples)
                    </span>
                </div>

                {/* Pagination */}
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setPage(p => Math.max(1, p - 1))}
                        disabled={page === 1}
                        className="p-1.5 rounded-lg bg-[#1e2528] border border-[#2d3437] text-[#dadada] disabled:opacity-50 disabled:cursor-not-allowed hover:border-[#8ccf7e]/50 transition-colors"
                    >
                        <ChevronLeft className="w-4 h-4" />
                    </button>
                    <span className="text-sm text-[#8a9899]">
                        {page} / {totalPages}
                    </span>
                    <button
                        onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                        disabled={page === totalPages}
                        className="p-1.5 rounded-lg bg-[#1e2528] border border-[#2d3437] text-[#dadada] disabled:opacity-50 disabled:cursor-not-allowed hover:border-[#8ccf7e]/50 transition-colors"
                    >
                        <ChevronRight className="w-4 h-4" />
                    </button>
                </div>
            </div>

            {/* Examples */}
            <div className="space-y-4">
                {examples.map((example) => (
                    <div
                        key={example.index}
                        className="bg-[#1e2528] border border-[#2d3437] rounded-xl overflow-hidden"
                    >
                        {/* Example Header */}
                        <div className="flex items-center justify-between px-4 py-2 bg-[#141b1e] border-b border-[#2d3437]">
                            <span className="text-sm font-medium text-[#8a9899]">
                                Example #{example.index + 1}
                            </span>
                            <span className="text-xs text-[#8a9899]">
                                ~{example.token_count} tokens
                            </span>
                        </div>

                        {/* Messages */}
                        <div className="divide-y divide-[#2d3437]">
                            {example.messages.map((msg, msgIdx) => {
                                const style = ROLE_STYLES[msg.role as keyof typeof ROLE_STYLES] || ROLE_STYLES.user
                                const Icon = style.icon

                                return (
                                    <div key={msgIdx} className="p-4">
                                        <div className="flex items-start gap-3">
                                            <div className={`w-8 h-8 rounded-lg ${style.bg} flex items-center justify-center flex-shrink-0`}>
                                                <Icon className={`w-4 h-4 ${style.text}`} />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <span className={`text-xs font-medium ${style.text} uppercase`}>
                                                    {style.label}
                                                </span>
                                                <p className="mt-1 text-sm text-[#dadada] whitespace-pre-wrap break-words">
                                                    {msg.content.length > 500
                                                        ? msg.content.slice(0, 500) + '...'
                                                        : msg.content
                                                    }
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                )
                            })}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}
