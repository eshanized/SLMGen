/**
 * Job History Page.
 * 
 * Displays all past fine-tuning jobs with filtering and actions.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useAuth } from '@/contexts/auth-context'
import { JobCard } from '@/components/job-card'
import {
    History,
    Plus,
    Loader2,
    Search,
    Filter,
    ArrowLeft
} from '@/components/icons'
import { API_URL } from '@/lib/api'

interface Job {
    id: string
    session_id: string
    dataset_filename: string
    total_examples: number
    total_tokens: number
    quality_score: number
    task_type: string
    deployment_target: string
    selected_model_name: string
    model_score: number
    notebook_filename?: string
    colab_url?: string
    status: string
    created_at: string
}

export default function HistoryPage() {
    const { session } = useAuth()
    const [jobs, setJobs] = useState<Job[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [searchTerm, setSearchTerm] = useState('')
    const [statusFilter, setStatusFilter] = useState<string>('all')

    useEffect(() => {
        if (session) {
            fetchJobs()
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [session])

    const fetchJobs = async () => {
        if (!session?.access_token) return

        setIsLoading(true)
        setError(null)

        try {
            const response = await fetch(`${API_URL}/jobs`, {
                headers: {
                    'Authorization': `Bearer ${session.access_token}`
                }
            })

            if (!response.ok) {
                throw new Error('Failed to fetch jobs')
            }

            const data = await response.json()
            setJobs(data)
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred')
        } finally {
            setIsLoading(false)
        }
    }

    const handleDelete = async (jobId: string) => {
        if (!session?.access_token) return

        const response = await fetch(`${API_URL}/jobs/${jobId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${session.access_token}`
            }
        })

        if (response.ok) {
            setJobs(jobs.filter(job => job.id !== jobId))
        }
    }

    // Filter jobs
    const filteredJobs = jobs.filter(job => {
        const matchesSearch = job.dataset_filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
            job.selected_model_name.toLowerCase().includes(searchTerm.toLowerCase())
        const matchesStatus = statusFilter === 'all' || job.status === statusFilter
        return matchesSearch && matchesStatus
    })

    return (
        <div className="min-h-screen bg-zinc-950">
            {/* Header */}
            <header className="border-b border-zinc-800 bg-zinc-900/50 backdrop-blur-sm sticky top-0 z-10">
                <div className="container mx-auto px-4 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <Link
                                href="/dashboard"
                                className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors"
                            >
                                <ArrowLeft className="w-5 h-5" />
                                <span className="hidden sm:inline">Back</span>
                            </Link>
                            <div className="flex items-center gap-2">
                                <History className="w-6 h-6 text-violet-400" />
                                <h1 className="text-xl font-bold text-white">Job History</h1>
                            </div>
                        </div>
                        <Link
                            href="/dashboard"
                            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white rounded-lg font-semibold hover:shadow-lg hover:shadow-violet-600/30 transition-all"
                        >
                            <Plus className="w-4 h-4" />
                            New Job
                        </Link>
                    </div>
                </div>
            </header>

            <main className="container mx-auto px-4 py-8">
                {/* Filters */}
                <div className="flex flex-col sm:flex-row gap-4 mb-6">
                    <div className="relative flex-1">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                        <input
                            type="text"
                            placeholder="Search jobs..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full pl-10 pr-4 py-2.5 bg-zinc-900 border border-zinc-800 rounded-xl text-white placeholder-zinc-500 focus:outline-none focus:border-violet-500 transition-colors"
                        />
                    </div>
                    <div className="relative">
                        <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                        <select
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                            className="pl-10 pr-8 py-2.5 bg-zinc-900 border border-zinc-800 rounded-xl text-white focus:outline-none focus:border-violet-500 transition-colors appearance-none cursor-pointer"
                        >
                            <option value="all">All Status</option>
                            <option value="created">Created</option>
                            <option value="processing">Processing</option>
                            <option value="completed">Completed</option>
                            <option value="failed">Failed</option>
                        </select>
                    </div>
                </div>

                {/* Content */}
                {isLoading ? (
                    <div className="flex items-center justify-center py-20">
                        <Loader2 className="w-8 h-8 text-violet-400 animate-spin" />
                    </div>
                ) : error ? (
                    <div className="text-center py-20">
                        <p className="text-red-400 mb-4">{error}</p>
                        <button
                            onClick={fetchJobs}
                            className="text-violet-400 hover:underline"
                        >
                            Try again
                        </button>
                    </div>
                ) : filteredJobs.length === 0 ? (
                    <div className="text-center py-20">
                        <History className="w-12 h-12 text-zinc-600 mx-auto mb-4" />
                        <h2 className="text-xl font-semibold text-white mb-2">
                            {jobs.length === 0 ? 'No jobs yet' : 'No matching jobs'}
                        </h2>
                        <p className="text-zinc-500 mb-6">
                            {jobs.length === 0
                                ? 'Start by creating your first fine-tuning job.'
                                : 'Try adjusting your search or filters.'
                            }
                        </p>
                        {jobs.length === 0 && (
                            <Link
                                href="/dashboard"
                                className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white rounded-xl font-semibold hover:shadow-lg hover:shadow-violet-600/30 transition-all"
                            >
                                <Plus className="w-5 h-5" />
                                Create Your First Job
                            </Link>
                        )}
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {filteredJobs.map((job) => (
                            <JobCard key={job.id} job={job} onDelete={handleDelete} />
                        ))}
                    </div>
                )}

                {/* Stats */}
                {jobs.length > 0 && (
                    <div className="mt-8 pt-6 border-t border-zinc-800">
                        <div className="flex flex-wrap gap-6 text-sm text-zinc-500">
                            <span>Total: <strong className="text-white">{jobs.length}</strong> jobs</span>
                            <span>Completed: <strong className="text-violet-400">{jobs.filter(j => j.status === 'completed').length}</strong></span>
                            <span>Processing: <strong className="text-amber-400">{jobs.filter(j => j.status === 'processing').length}</strong></span>
                        </div>
                    </div>
                )}
            </main>
        </div>
    )
}