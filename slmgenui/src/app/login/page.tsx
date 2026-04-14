/**
 * Login Page - V3.0.0.
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

    useEffect(() => {
        if (isLoading) {
            const timer = setTimeout(() => {}, 3000)
            return () => clearTimeout(timer)
        }
    }, [isLoading])

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
                <div className="w-16 h-16 mx-auto rounded-full bg-violet-500/20 flex items-center justify-center mb-6">
                    <Mail className="w-8 h-8 text-violet-400" />
                </div>
                <h1 className="text-2xl font-bold text-white mb-2">Check your email</h1>
                <p className="text-zinc-400 mb-6">
                    We sent a magic link to <strong className="text-white">{email}</strong>
                </p>
                <button
                    onClick={() => setMagicLinkSent(false)}
                    className="text-violet-400 hover:underline"
                >
                    Use a different email
                </button>
            </div>
        )
    }

    return (
        <div className="max-w-md w-full">
            <Link href="/" className="flex items-center justify-center gap-2.5 mb-8">
                <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-violet-600 to-fuchsia-600 flex items-center justify-center">
                    <Rocket className="w-5 h-5 text-white" />
                </div>
                <span className="text-2xl font-bold tracking-wide">SLMGEN</span>
            </Link>

            <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-8">
                <h1 className="text-2xl font-bold text-white text-center mb-2">
                    Welcome back
                </h1>
                <p className="text-zinc-400 text-center mb-6">
                    Sign in to continue
                </p>

                {error && (
                    <div className="mb-6 p-3 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400 text-sm">
                        {error}
                    </div>
                )}

                <div className="space-y-3 mb-6">
                    <button
                        onClick={() => handleOAuth('github')}
                        className="w-full flex items-center justify-center gap-3 px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-xl text-white font-medium hover:border-violet-500/50 transition-all"
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

                <form onSubmit={handleEmailLogin} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-white mb-2">Email</label>
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
                        <div className="flex items-center justify-between mb-2">
                            <label className="text-sm font-medium text-white">Password</label>
                            <Link href="/reset-password" className="text-sm text-violet-400 hover:underline">
                                Forgot?
                            </Link>
                        </div>
                        <div className="relative">
                            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="••••••••"
                                required
                                className="w-full pl-10 pr-4 py-3 bg-zinc-950 border border-zinc-800 rounded-xl text-white placeholder-zinc-500 focus:outline-none focus:border-violet-500 transition-colors"
                            />
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={isLoading}
                        className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white font-semibold rounded-xl hover:shadow-lg hover:shadow-violet-600/20 transition-all disabled:opacity-50"
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
                </form>

                <button
                    onClick={handleMagicLink}
                    disabled={isLoading}
                    className="w-full mt-4 text-center text-sm text-zinc-400 hover:text-white transition-colors"
                >
                    Or sign in with magic link
                </button>
            </div>

            <p className="text-center mt-6 text-zinc-400">
                Don&apos;t have an account?{' '}
                <Link href="/signup" className="text-violet-400 hover:underline">
                    Sign up
                </Link>
            </p>
        </div>
    )
}

function LoginFallback() {
    return (
        <div className="max-w-md w-full flex items-center justify-center">
            <Loader2 className="w-8 h-8 animate-spin text-violet-400" />
        </div>
    )
}

export default function LoginPage() {
    return (
        <div className="min-h-screen bg-zinc-950 flex items-center justify-center px-4">
            <Suspense fallback={<LoginFallback />}>
                <LoginForm />
            </Suspense>
        </div>
    )
}