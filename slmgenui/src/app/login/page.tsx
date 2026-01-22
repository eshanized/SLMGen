/**
 * Login Page.
 * 
 * Email/password login with magic link and OAuth options.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

'use client'

import { Suspense, useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuth } from '@/contexts/auth-context'
import { Rocket, Mail, Lock, Github, ArrowRight, Loader2 } from '@/components/icons'

function LoginForm() {
    const router = useRouter()
    const searchParams = useSearchParams()
    const redirectTo = searchParams.get('redirectTo') || '/dashboard'

    const { signIn, signInWithMagicLink, signInWithOAuth } = useAuth()

    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [magicLinkSent, setMagicLinkSent] = useState(false)
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

    const handleEmailLogin = async (e: React.FormEvent) => {
        e.preventDefault()
        setIsLoading(true)
        setError(null)

        const { error } = await signIn(email, password)

        if (error) {
            setError(error.message)
            setIsLoading(false)
        } else {
            router.push(redirectTo)
        }
    }

    const handleMagicLink = async () => {
        if (!email) {
            setError('Please enter your email address')
            return
        }

        setIsLoading(true)
        setError(null)

        const { error } = await signInWithMagicLink(email)

        if (error) {
            setError(error.message)
        } else {
            setMagicLinkSent(true)
        }
        setIsLoading(false)
    }

    const handleOAuth = async (provider: 'github' | 'google') => {
        await signInWithOAuth(provider)
    }

    if (magicLinkSent) {
        return (
            <div className="max-w-md w-full text-center">
                <div className="w-16 h-16 mx-auto rounded-full bg-[#8ccf7e]/20 flex items-center justify-center mb-6">
                    <Mail className="w-8 h-8 text-[#8ccf7e]" />
                </div>
                <h1 className="text-2xl font-bold text-[#dadada] mb-2">Check your email</h1>
                <p className="text-[#8a9899] mb-6">
                    We sent a magic link to <strong className="text-[#dadada]">{email}</strong>
                </p>
                <button
                    onClick={() => setMagicLinkSent(false)}
                    className="text-[#8ccf7e] hover:underline"
                >
                    Use a different email
                </button>
            </div>
        )
    }

    return (
        <div className="max-w-md w-full">
            {/* Logo */}
            <Link href="/" className="flex items-center justify-center gap-2 mb-8">
                <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#8ccf7e] to-[#6cbfbf] flex items-center justify-center">
                    <Rocket className="w-5 h-5 text-[#141b1e]" />
                </div>
                <span className="text-2xl font-bold text-[#dadada] tracking-wide">SLMGEN</span>
            </Link>

            {/* Card */}
            <div className="bg-[#1e2528] border border-[#2d3437] rounded-2xl p-8">
                <h1 className="text-2xl font-bold text-[#dadada] text-center mb-2">
                    Welcome back
                </h1>
                <p className="text-[#8a9899] text-center mb-6">
                    Sign in to continue to your dashboard
                </p>

                {/* Error */}
                {error && (
                    <div className="mb-6 p-3 bg-[#e57474]/10 border border-[#e57474]/50 rounded-lg text-[#e57474] text-sm">
                        {error}
                    </div>
                )}

                {/* OAuth Buttons */}
                <div className="space-y-3 mb-6">
                    <button
                        onClick={() => handleOAuth('github')}
                        className="w-full flex items-center justify-center gap-3 px-4 py-3 bg-[#141b1e] border border-[#2d3437] rounded-xl text-[#dadada] font-medium hover:border-[#8ccf7e]/50 transition-all"
                    >
                        <Github className="w-5 h-5" />
                        Continue with GitHub
                    </button>
                </div>

                <div className="flex items-center gap-4 mb-6">
                    <div className="flex-1 h-px bg-[#2d3437]" />
                    <span className="text-sm text-[#8a9899]">or</span>
                    <div className="flex-1 h-px bg-[#2d3437]" />
                </div>

                {/* Email Form */}
                <form onSubmit={handleEmailLogin} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-[#dadada] mb-2">
                            Email
                        </label>
                        <div className="relative">
                            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#8a9899]" />
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="you@example.com"
                                required
                                className="w-full pl-10 pr-4 py-3 bg-[#141b1e] border border-[#2d3437] rounded-xl text-[#dadada] placeholder-[#8a9899] focus:outline-none focus:border-[#8ccf7e] transition-colors"
                            />
                        </div>
                    </div>

                    <div>
                        <div className="flex items-center justify-between mb-2">
                            <label className="text-sm font-medium text-[#dadada]">
                                Password
                            </label>
                            <Link href="/reset-password" className="text-sm text-[#8ccf7e] hover:underline">
                                Forgot?
                            </Link>
                        </div>
                        <div className="relative">
                            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#8a9899]" />
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="••••••••"
                                required
                                className="w-full pl-10 pr-4 py-3 bg-[#141b1e] border border-[#2d3437] rounded-xl text-[#dadada] placeholder-[#8a9899] focus:outline-none focus:border-[#8ccf7e] transition-colors"
                            />
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={isLoading}
                        className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-[#8ccf7e] to-[#6cbfbf] text-[#141b1e] font-semibold rounded-xl hover:shadow-lg hover:shadow-[#8ccf7e]/30 transition-all disabled:opacity-50"
                    >
                        {isLoading ? (
                            <Loader2 className="w-5 h-5 animate-spin" />
                        ) : (
                            <>
                                Sign in
                                <ArrowRight className="w-5 h-5" />
                            </>
                        )}
                    </button>

                    {/* Slow loading message */}
                    {showSlowMessage && (
                        <p className="flex items-center justify-center gap-2 text-center text-sm text-[#e5c76b] animate-pulse">
                            <Loader2 className="w-4 h-4 animate-spin" />
                            Server is warming up... This can take up to 30 seconds on first visit.
                        </p>
                    )}
                </form>

                {/* Magic Link */}
                <button
                    onClick={handleMagicLink}
                    disabled={isLoading}
                    className="w-full mt-4 text-center text-sm text-[#8a9899] hover:text-[#dadada] transition-colors"
                >
                    Or sign in with magic link
                </button>
            </div>

            {/* Sign up link */}
            <p className="text-center mt-6 text-[#8a9899]">
                Don&apos;t have an account?{' '}
                <Link href="/signup" className="text-[#8ccf7e] hover:underline">
                    Sign up
                </Link>
            </p>
        </div>
    )
}

function LoginFallback() {
    return (
        <div className="max-w-md w-full flex items-center justify-center">
            <Loader2 className="w-8 h-8 animate-spin text-[#8ccf7e]" />
        </div>
    )
}

export default function LoginPage() {
    return (
        <div className="min-h-screen bg-[#141b1e] flex items-center justify-center px-4">
            <Suspense fallback={<LoginFallback />}>
                <LoginForm />
            </Suspense>
        </div>
    )
}
