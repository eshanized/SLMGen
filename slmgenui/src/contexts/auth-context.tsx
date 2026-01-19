/**
 * Authentication Context.
 * 
 * Provides auth state and methods throughout the app.
 * SSG-safe implementation that lazily initializes Supabase client.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

'use client'

import { createContext, useContext, useEffect, useState, useCallback, useMemo, type ReactNode } from 'react'
import { User, Session, AuthError, SupabaseClient } from '@supabase/supabase-js'
import { createClient } from '@/lib/supabase'
import type { Profile } from '@/lib/database.types'

interface AuthContextType {
    // State
    user: User | null
    session: Session | null
    profile: Profile | null
    loading: boolean
    isConfigured: boolean

    // Auth methods
    signIn: (email: string, password: string) => Promise<{ error: AuthError | null }>
    signUp: (email: string, password: string, fullName?: string) => Promise<{ error: AuthError | null }>
    signOut: () => Promise<void>
    signInWithMagicLink: (email: string) => Promise<{ error: AuthError | null }>
    signInWithOAuth: (provider: 'github' | 'google') => Promise<void>
    resetPassword: (email: string) => Promise<{ error: AuthError | null }>
    updatePassword: (password: string) => Promise<{ error: AuthError | null }>

    // Profile
    updateProfile: (data: Partial<Profile>) => Promise<{ error: Error | null }>
    refreshProfile: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface AuthProviderProps {
    children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
    const [user, setUser] = useState<User | null>(null)
    const [session, setSession] = useState<Session | null>(null)
    const [profile, setProfile] = useState<Profile | null>(null)
    const [loading, setLoading] = useState(true)
    const [supabase, setSupabase] = useState<SupabaseClient | null>(null)
    const [isConfigured, setIsConfigured] = useState(false)

    // Initialize Supabase client on mount (client-side only)
    useEffect(() => {
        if (supabase) return

        try {
            const client = createClient()
            setTimeout(() => {
                setSupabase(client)
                setIsConfigured(true)
            }, 0)
        } catch (e) {
            console.warn('Supabase not configured:', e)
            setTimeout(() => {
                setLoading(false)
                setIsConfigured(false)
            }, 0)
        }
    }, [supabase])

    // Fetch user profile - creates one if missing
    const fetchProfile = useCallback(async (userId: string, client: SupabaseClient) => {
        const { data, error } = await client
            .from('profiles')
            .select('*')
            .eq('id', userId)
            .single()

        if (error) {
            // PGRST116 = "no rows returned" - profile doesn't exist yet
            if (error.code === 'PGRST116') {
                // Get user data to create profile
                const { data: { user } } = await client.auth.getUser()
                if (user) {
                    // Create missing profile
                    const newProfile = {
                        id: userId,
                        email: user.email || '',
                        full_name: user.user_metadata?.full_name || user.user_metadata?.name || '',
                        avatar_url: user.user_metadata?.avatar_url || user.user_metadata?.picture || '',
                    }

                    const { data: createdProfile, error: createError } = await client
                        .from('profiles')
                        .insert(newProfile)
                        .select()
                        .single()

                    if (!createError && createdProfile) {
                        setProfile(createdProfile as Profile)
                    } else {
                        console.warn('Failed to create profile:', createError?.message)
                    }
                }
            } else {
                console.warn('Error fetching profile:', error.message)
            }
        } else if (data) {
            setProfile(data as Profile)
        }
    }, [])

    // Initialize auth state when Supabase is ready
    useEffect(() => {
        if (!supabase) return

        const initAuth = async () => {
            const { data: { session } } = await supabase.auth.getSession()
            setSession(session)
            setUser(session?.user ?? null)

            if (session?.user) {
                await fetchProfile(session.user.id, supabase)
            }

            setLoading(false)
        }

        initAuth()

        // Listen for auth changes
        const { data: { subscription } } = supabase.auth.onAuthStateChange(
            async (_event: string, session: Session | null) => {
                setSession(session)
                setUser(session?.user ?? null)

                if (session?.user) {
                    await fetchProfile(session.user.id, supabase)
                } else {
                    setProfile(null)
                }
            }
        )

        return () => subscription.unsubscribe()
    }, [supabase, fetchProfile])

    // Sign in with email/password
    const signIn = useCallback(async (email: string, password: string) => {
        if (!supabase) return { error: { message: 'Not configured' } as AuthError }
        const { error } = await supabase.auth.signInWithPassword({ email, password })
        return { error }
    }, [supabase])

    // Sign up with email/password
    const signUp = useCallback(async (email: string, password: string, fullName?: string) => {
        if (!supabase) return { error: { message: 'Not configured' } as AuthError }
        const { error } = await supabase.auth.signUp({
            email,
            password,
            options: {
                data: { full_name: fullName }
            }
        })
        return { error }
    }, [supabase])

    // Sign out
    const signOut = useCallback(async () => {
        if (!supabase) return
        await supabase.auth.signOut()
        setProfile(null)
    }, [supabase])

    // Sign in with magic link
    const signInWithMagicLink = useCallback(async (email: string) => {
        if (!supabase) return { error: { message: 'Not configured' } as AuthError }
        const { error } = await supabase.auth.signInWithOtp({
            email,
            options: {
                emailRedirectTo: `${window.location.origin}/auth/callback`
            }
        })
        return { error }
    }, [supabase])

    // Sign in with OAuth
    const signInWithOAuth = useCallback(async (provider: 'github' | 'google') => {
        if (!supabase) return
        await supabase.auth.signInWithOAuth({
            provider,
            options: {
                redirectTo: `${window.location.origin}/auth/callback`
            }
        })
    }, [supabase])

    // Reset password
    const resetPassword = useCallback(async (email: string) => {
        if (!supabase) return { error: { message: 'Not configured' } as AuthError }
        const { error } = await supabase.auth.resetPasswordForEmail(email, {
            redirectTo: `${window.location.origin}/auth/update-password`
        })
        return { error }
    }, [supabase])

    // Update password
    const updatePassword = useCallback(async (password: string) => {
        if (!supabase) return { error: { message: 'Not configured' } as AuthError }
        const { error } = await supabase.auth.updateUser({ password })
        return { error }
    }, [supabase])

    // Update profile
    const updateProfile = useCallback(async (data: Partial<Profile>) => {
        if (!user || !supabase) {
            return { error: new Error('Not authenticated') }
        }

        const { error } = await supabase
            .from('profiles')
            .update({
                full_name: data.full_name ?? undefined,
                avatar_url: data.avatar_url ?? undefined,
                updated_at: new Date().toISOString(),
            })
            .eq('id', user.id)

        if (!error) {
            setProfile(prev => prev ? { ...prev, ...data } : null)
        }

        return { error: error ? new Error(error.message) : null }
    }, [user, supabase])

    // Refresh profile
    const refreshProfile = useCallback(async () => {
        if (user && supabase) {
            await fetchProfile(user.id, supabase)
        }
    }, [user, supabase, fetchProfile])

    const value = useMemo<AuthContextType>(() => ({
        user,
        session,
        profile,
        loading,
        isConfigured,
        signIn,
        signUp,
        signOut,
        signInWithMagicLink,
        signInWithOAuth,
        resetPassword,
        updatePassword,
        updateProfile,
        refreshProfile,
    }), [
        user, session, profile, loading, isConfigured,
        signIn, signUp, signOut, signInWithMagicLink, signInWithOAuth,
        resetPassword, updatePassword, updateProfile, refreshProfile
    ])

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    )
}

export function useAuth() {
    const context = useContext(AuthContext)
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider')
    }
    return context
}

// Helper hook for protected content
export function useRequireAuth() {
    const { user, loading, isConfigured } = useAuth()

    return {
        user,
        loading,
        isConfigured,
        isAuthenticated: !!user,
    }
}
