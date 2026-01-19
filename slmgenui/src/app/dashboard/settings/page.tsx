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
            setFullName(profile.full_name || '')
            setAvatarUrl(profile.avatar_url || '')
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
                <h1 className="text-2xl font-bold text-[#dadada]">Profile</h1>
                <p className="text-[#8a9899] mt-1">Manage your public profile information</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
                {/* Avatar */}
                <div className="p-6 bg-[#1e2528] border border-[#2d3437] rounded-xl">
                    <label className="block text-sm font-medium text-[#dadada] mb-4">
                        Profile Picture
                    </label>
                    <div className="flex items-center gap-6">
                        <div className="relative">
                            <div className="w-24 h-24 rounded-full bg-gradient-to-br from-[#8ccf7e] to-[#6cbfbf] flex items-center justify-center text-[#141b1e] font-bold text-3xl overflow-hidden">
                                {avatarUrl ? (
                                    <img src={avatarUrl} alt="Avatar" className="w-full h-full object-cover" />
                                ) : (
                                    fullName?.[0]?.toUpperCase() || profile?.email?.[0]?.toUpperCase() || '?'
                                )}
                            </div>
                            <div className="absolute bottom-0 right-0 w-8 h-8 bg-[#2d3437] rounded-full flex items-center justify-center border-2 border-[#1e2528]">
                                <Camera className="w-4 h-4 text-[#8a9899]" />
                            </div>
                        </div>
                        <div className="flex-1">
                            <input
                                type="url"
                                value={avatarUrl}
                                onChange={(e) => setAvatarUrl(e.target.value)}
                                placeholder="https://example.com/avatar.jpg"
                                className="w-full px-4 py-3 bg-[#141b1e] border border-[#2d3437] rounded-xl text-[#dadada] placeholder-[#8a9899] focus:outline-none focus:border-[#8ccf7e] transition-colors"
                            />
                            <p className="mt-2 text-xs text-[#8a9899]">
                                Enter a URL for your profile picture
                            </p>
                        </div>
                    </div>
                </div>

                {/* Full Name */}
                <div className="p-6 bg-[#1e2528] border border-[#2d3437] rounded-xl">
                    <label className="block text-sm font-medium text-[#dadada] mb-2">
                        Full Name
                    </label>
                    <div className="relative">
                        <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#8a9899]" />
                        <input
                            type="text"
                            value={fullName}
                            onChange={(e) => setFullName(e.target.value)}
                            placeholder="Your full name"
                            className="w-full pl-10 pr-4 py-3 bg-[#141b1e] border border-[#2d3437] rounded-xl text-[#dadada] placeholder-[#8a9899] focus:outline-none focus:border-[#8ccf7e] transition-colors"
                        />
                    </div>
                    <p className="mt-2 text-xs text-[#8a9899]">
                        This name will be displayed on your profile
                    </p>
                </div>

                {/* Email (read-only) */}
                <div className="p-6 bg-[#1e2528] border border-[#2d3437] rounded-xl opacity-60">
                    <label className="block text-sm font-medium text-[#dadada] mb-2">
                        Email Address
                    </label>
                    <input
                        type="email"
                        value={profile?.email || ''}
                        disabled
                        className="w-full px-4 py-3 bg-[#141b1e] border border-[#2d3437] rounded-xl text-[#8a9899] cursor-not-allowed"
                    />
                    <p className="mt-2 text-xs text-[#8a9899]">
                        Email cannot be changed. Contact support if you need to update it.
                    </p>
                </div>

                {/* Error/Success */}
                {error && (
                    <div className="p-4 bg-[#e67e80]/10 border border-[#e67e80]/30 rounded-xl text-[#e67e80] text-sm">
                        {error}
                    </div>
                )}

                {success && (
                    <div className="p-4 bg-[#8ccf7e]/10 border border-[#8ccf7e]/30 rounded-xl text-[#8ccf7e] text-sm flex items-center gap-2">
                        <Check className="w-4 h-4" />
                        Profile updated successfully!
                    </div>
                )}

                {/* Submit */}
                <div className="flex justify-end">
                    <button
                        type="submit"
                        disabled={isLoading}
                        className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-[#8ccf7e] to-[#6cbfbf] text-[#141b1e] font-semibold rounded-xl hover:shadow-lg hover:shadow-[#8ccf7e]/30 transition-all disabled:opacity-50"
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
