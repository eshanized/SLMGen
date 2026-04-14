/**
 * Profile Settings Page.
 * 
 * Edit user profile information.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

'use client'

import { useState, useEffect } from 'react'
import Image from 'next/image'
import { useAuth } from '@/contexts/auth-context'
import { User, Check, Loader2, Camera } from '@/components/icons'

export default function ProfileSettingsPage() {
    const { profile, updateProfile, refreshProfile } = useAuth()

    const [fullName, setFullName] = useState('')
    const [avatarUrl, setAvatarUrl] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const [success, setSuccess] = useState(false)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        if (profile) {
            const t = setTimeout(() => {
                setFullName(profile.full_name || '')
                setAvatarUrl(profile.avatar_url || '')
            }, 0)
            return () => clearTimeout(t)
        }
    }, [profile])

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setIsLoading(true)
        setError(null)
        setSuccess(false)

        const { error } = await updateProfile({
            full_name: fullName,
            avatar_url: avatarUrl || undefined,
        })

        if (error) {
            setError(error.message)
        } else {
            setSuccess(true)
            await refreshProfile()
            setTimeout(() => setSuccess(false), 3000)
        }

        setIsLoading(false)
    }

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-white">Profile</h1>
                <p className="text-zinc-500 mt-1">Manage your public profile information</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
                {/* Avatar */}
                <div className="p-6 bg-zinc-900 border border-zinc-800 rounded-xl">
                    <label className="block text-sm font-medium text-white mb-4">
                        Profile Picture
                    </label>
                    <div className="flex items-center gap-6">
                        <div className="relative">
                            <div className="w-24 h-24 rounded-full bg-gradient-to-br from-violet-600 to-fuchsia-600 flex items-center justify-center text-white font-bold text-3xl overflow-hidden">
                                {avatarUrl ? (
                                    <Image src={avatarUrl} alt="Avatar" fill className="object-cover" unoptimized />
                                ) : (
                                    fullName?.[0]?.toUpperCase() || profile?.email?.[0]?.toUpperCase() || '?'
                                )}
                            </div>
                            <div className="absolute bottom-0 right-0 w-8 h-8 bg-zinc-800 rounded-full flex items-center justify-center border-2 border-zinc-900">
                                <Camera className="w-4 h-4 text-zinc-500" />
                            </div>
                        </div>
                        <div className="flex-1">
                            <input
                                type="url"
                                value={avatarUrl}
                                onChange={(e) => setAvatarUrl(e.target.value)}
                                placeholder="https://example.com/avatar.jpg"
                                className="w-full px-4 py-3 bg-zinc-950 border border-zinc-800 rounded-xl text-white placeholder-zinc-500 focus:outline-none focus:border-violet-500 transition-colors"
                            />
                            <p className="mt-2 text-xs text-zinc-500">
                                Enter a URL for your profile picture
                            </p>
                        </div>
                    </div>
                </div>

                {/* Full Name */}
                <div className="p-6 bg-zinc-900 border border-zinc-800 rounded-xl">
                    <label className="block text-sm font-medium text-white mb-2">
                        Full Name
                    </label>
                    <div className="relative">
                        <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                        <input
                            type="text"
                            value={fullName}
                            onChange={(e) => setFullName(e.target.value)}
                            placeholder="Your full name"
                            className="w-full pl-10 pr-4 py-3 bg-zinc-950 border border-zinc-800 rounded-xl text-white placeholder-zinc-500 focus:outline-none focus:border-violet-500 transition-colors"
                        />
                    </div>
                    <p className="mt-2 text-xs text-zinc-500">
                        This name will be displayed on your profile
                    </p>
                </div>

                {/* Email (read-only) */}
                <div className="p-6 bg-zinc-900 border border-zinc-800 rounded-xl opacity-60">
                    <label className="block text-sm font-medium text-white mb-2">
                        Email Address
                    </label>
                    <input
                        type="email"
                        value={profile?.email || ''}
                        disabled
                        className="w-full px-4 py-3 bg-zinc-950 border border-zinc-800 rounded-xl text-zinc-500 cursor-not-allowed"
                    />
                    <p className="mt-2 text-xs text-zinc-500">
                        Email cannot be changed. Contact support if you need to update it.
                    </p>
                </div>

                {/* Error/Success */}
                {error && (
                    <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm">
                        {error}
                    </div>
                )}

                {success && (
                    <div className="p-4 bg-violet-500/10 border border-violet-500/30 rounded-xl text-violet-400 text-sm flex items-center gap-2">
                        <Check className="w-4 h-4" />
                        Profile updated successfully!
                    </div>
                )}

                {/* Submit */}
                <div className="flex justify-end">
                    <button
                        type="submit"
                        disabled={isLoading}
                        className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white font-semibold rounded-xl hover:shadow-lg hover:shadow-violet-600/30 transition-all disabled:opacity-50"
                    >
                        {isLoading ? (
                            <Loader2 className="w-5 h-5 animate-spin" />
                        ) : (
                            <>
                                <Check className="w-5 h-5" />
                                Save Changes
                            </>
                        )}
                    </button>
                </div>
            </form>
        </div>
    )
}