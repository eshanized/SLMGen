/**
 * Signup Page.
 * 
 * New user registration with email/password.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

'use client'

// Force dynamic rendering to avoid SSG issues with Supabase
export const dynamic = 'force-dynamic'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useAuth } from '@/contexts/auth-context'
import { Rocket, Mail, Lock, User, Github, ArrowRight, Loader2, Check } from '@/components/icons'

export default function SignupPage() {
    const { signUp, signInWithOAuth } = useAuth()

    const [fullName, setFullName] = useState('')
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [success, setSuccess] = useState(false)
    const [showSlowMessage, setShowSlowMessage] = useState(false)

    // Show slow loading message after 3 seconds
    useEffect(() => {
        if (isLoading) {
            const timer = setTimeout(() => setShowSlowMessage(true), 3000)
            return () => clearTimeout(timer)
        } else if (showSlowMessage) {
            const timer = setTimeout(() => setShowSlowMessage(false), 0)
            return () => clearTimeout(timer)
        }
    }, [isLoading, showSlowMessage])

    const handleSignup = async (e: React.FormEvent) => {
        e.preventDefault()

        if (password.length < 6) {
            setError('Password must be at least 6 characters')
            return
        }

        setIsLoading(true)
        setError(null)

        const { error } = await signUp(email, password, fullName)

        if (error) {
            setError(error.message)
            setIsLoading(false)
        } else {
            setSuccess(true)
            setIsLoading(false)
        }
    }

    const handleOAuth = async (provider: 'github' | 'google') => {
        await signInWithOAuth(provider)
    }

    if (success) {
        return (
            <div className="min-h-screen bg-zinc-950 flex items-center justify-center px-4">
                <div className="max-w-md w-full text-center">
                    <div className="w-16 h-16 mx-auto rounded-full bg-violet-600/20 flex items-center justify-center mb-6">
                        <Check className="w-8 h-8 text-violet-400" />
                    </div>
                    <h1 className="text-2xl font-bold text-white mb-2">Check your email</h1>
                    <p className="text-zinc-400 mb-6">
                        We sent a confirmation link to <strong className="text-white">{email}</strong>
                    </p>
                    <p className="text-sm text-zinc-500">
                        Click the link in the email to activate your account.
                    </p>
                    <Link
                        href="/login"
                        className="inline-block mt-6 text-violet-400 hover:text-violet-300 hover:underline"
                    >
                        Back to login
                    </Link>
                </div>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-zinc-950 flex items-center justify-center px-4">
            <div className="max-w-md w-full">
                {/* Logo */}
                <Link href="/" className="flex items-center justify-center gap-2 mb-8">
                    <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-violet-600 to-fuchsia-600 flex items-center justify-center">
                        <Rocket className="w-5 h-5 text-white" />
                    </div>
                    <span className="text-2xl font-bold text-white tracking-wide">SLMGEN</span>
                </Link>

                {/* Card */}
                <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-8">
                    <h1 className="text-2xl font-bold text-white text-center mb-2">
                        Create your account
                    </h1>
                    <p className="text-zinc-400 text-center mb-6">
                        Start fine-tuning models in minutes
                    </p>

                    {/* Error */}
                    {error && (
                        <div className="mb-6 p-3 bg-red-900/20 border border-red-500/50 rounded-lg text-red-400 text-sm">
                            {error}
                        </div>
                    )}

                    {/* OAuth Buttons */}
                    <div className="space-y-3 mb-6">
                        <button
                            onClick={() => handleOAuth('github')}
                            className="w-full flex items-center justify-center gap-3 px-4 py-3 bg-zinc-950 border border-zinc-800 rounded-xl text-white font-medium hover:border-violet-500/30 hover:bg-zinc-900/50 transition-all"
                        >
                            <Github className="w-5 h-5" />
                            Continue with GitHub
                        </button>
                    </div>

                    <div className="flex items-center gap-4 mb-6">
                        <div className="flex-1 h-px bg-zinc-800" />
                        <span className="text-sm text-zinc-500">or</span>
                        <div className="flex-1 h-px bg-zinc-800" />
                    </div>

                    {/* Signup Form */}
                    <form onSubmit={handleSignup} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-white mb-2">
                                Full name
                            </label>
                            <div className="relative">
                                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                                <input
                                    type="text"
                                    value={fullName}
                                    onChange={(e) => setFullName(e.target.value)}
                                    placeholder="John Doe"
                                    className="w-full pl-10 pr-4 py-3 bg-zinc-950 border border-zinc-800 rounded-xl text-white placeholder-zinc-500 focus:outline-none focus:border-violet-500 transition-colors"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-white mb-2">
                                Email
                            </label>
                            <div className="relative">
                                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    placeholder="you@example.com"
                                    required
                                    className="w-full pl-10 pr-4 py-3 bg-zinc-950 border border-zinc-800 rounded-xl text-white placeholder-zinc-500 focus:outline-none focus:border-violet-500 transition-colors"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-white mb-2">
                                Password
                            </label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="••••••••"
                                    required
                                    minLength={6}
                                    className="w-full pl-10 pr-4 py-3 bg-zinc-950 border border-zinc-800 rounded-xl text-white placeholder-zinc-500 focus:outline-none focus:border-violet-500 transition-colors"
                                />
                            </div>
                            <p className="mt-1 text-xs text-zinc-500">Minimum 6 characters</p>
                        </div>

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white font-semibold rounded-xl hover:shadow-lg hover:shadow-violet-600/30 transition-all disabled:opacity-50"
                        >
                            {isLoading ? (
                                <Loader2 className="w-5 h-5 animate-spin" />
                            ) : (
                                <>
                                    Create account
                                    <ArrowRight className="w-5 h-5" />
                                </>
                            )}
                        </button>

                        {/* Slow loading message */}
                        {showSlowMessage && (
                            <p className="flex items-center justify-center gap-2 text-center text-sm text-amber-400 animate-pulse">
                                <Loader2 className="w-4 h-4 animate-spin" />
                                Server is warming up... This can take up to 30 seconds on first visit.
                            </p>
                        )}
                    </form>

                    <p className="mt-4 text-xs text-center text-zinc-500">
                        By signing up, you agree to our{' '}
                        <Link href="/terms" className="text-violet-400 hover:underline">Terms of Service</Link>
                        {' '}and{' '}
                        <Link href="/privacy" className="text-violet-400 hover:underline">Privacy Policy</Link>.
                    </p>
                </div>

                {/* Login link */}
                <p className="text-center mt-6 text-zinc-400">
                    Already have an account?{' '}
                    <Link href="/login" className="text-violet-400 hover:text-violet-300 hover:underline">
                        Sign in
                    </Link>
                </p>
            </div>
        </div>
    )
}