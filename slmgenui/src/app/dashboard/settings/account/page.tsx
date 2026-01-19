/**
 * Account Settings Page.
 * 
 * Password change and account deletion.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/auth-context'
import { Lock, AlertTriangle, Trash2, Check, Loader2 } from '@/components/icons'

export default function AccountSettingsPage() {
    const router = useRouter()
    const { updatePassword, signOut } = useAuth()

    // Password form
    const [newPassword, setNewPassword] = useState('')
    const [confirmPassword, setConfirmPassword] = useState('')
    const [passwordLoading, setPasswordLoading] = useState(false)
    const [passwordError, setPasswordError] = useState<string | null>(null)
    const [passwordSuccess, setPasswordSuccess] = useState(false)

    // Delete account
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
    const [deleteConfirmText, setDeleteConfirmText] = useState('')

    const handlePasswordChange = async (e: React.FormEvent) => {
        e.preventDefault()

        if (newPassword.length < 6) {
            setPasswordError('Password must be at least 6 characters')
            return
        }

        if (newPassword !== confirmPassword) {
            setPasswordError('Passwords do not match')
            return
        }

        setPasswordLoading(true)
        setPasswordError(null)

        const { error } = await updatePassword(newPassword)

        if (error) {
            setPasswordError(error.message)
        } else {
            setPasswordSuccess(true)
            setNewPassword('')
            setConfirmPassword('')
            setTimeout(() => setPasswordSuccess(false), 3000)
        }

        setPasswordLoading(false)
    }

    const handleDeleteAccount = async () => {
        if (deleteConfirmText !== 'DELETE') return

        // Sign out and redirect
        await signOut()
        router.push('/')

        // Note: Actual account deletion should be done via Supabase Edge Function
        // or backend API to properly clean up all user data
    }

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-[#dadada]">Account</h1>
                <p className="text-[#8a9899] mt-1">Manage your account security and settings</p>
            </div>

            {/* Change Password */}
            <form onSubmit={handlePasswordChange} className="p-6 bg-[#1e2528] border border-[#2d3437] rounded-xl space-y-4">
                <div className="flex items-center gap-2 mb-4">
                    <Lock className="w-5 h-5 text-[#8ccf7e]" />
                    <h2 className="text-lg font-semibold text-[#dadada]">Change Password</h2>
                </div>

                <div>
                    <label className="block text-sm font-medium text-[#dadada] mb-2">
                        New Password
                    </label>
                    <input
                        type="password"
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        placeholder="••••••••"
                        minLength={6}
                        required
                        className="w-full px-4 py-3 bg-[#141b1e] border border-[#2d3437] rounded-xl text-[#dadada] placeholder-[#8a9899] focus:outline-none focus:border-[#8ccf7e] transition-colors"
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-[#dadada] mb-2">
                        Confirm New Password
                    </label>
                    <input
                        type="password"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        placeholder="••••••••"
                        minLength={6}
                        required
                        className="w-full px-4 py-3 bg-[#141b1e] border border-[#2d3437] rounded-xl text-[#dadada] placeholder-[#8a9899] focus:outline-none focus:border-[#8ccf7e] transition-colors"
                    />
                </div>

                {passwordError && (
                    <div className="p-3 bg-[#e67e80]/10 border border-[#e67e80]/30 rounded-lg text-[#e67e80] text-sm">
                        {passwordError}
                    </div>
                )}

                {passwordSuccess && (
                    <div className="p-3 bg-[#8ccf7e]/10 border border-[#8ccf7e]/30 rounded-lg text-[#8ccf7e] text-sm flex items-center gap-2">
                        <Check className="w-4 h-4" />
                        Password updated successfully!
                    </div>
                )}

                <button
                    type="submit"
                    disabled={passwordLoading}
                    className="flex items-center gap-2 px-4 py-2 bg-[#2d3437] text-[#dadada] rounded-lg hover:bg-[#3d4447] transition-colors disabled:opacity-50"
                >
                    {passwordLoading ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                        'Update Password'
                    )}
                </button>
            </form>

            {/* Danger Zone */}
            <div className="p-6 bg-[#1e2528] border border-[#e67e80]/30 rounded-xl space-y-4">
                <div className="flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5 text-[#e67e80]" />
                    <h2 className="text-lg font-semibold text-[#e67e80]">Danger Zone</h2>
                </div>

                <p className="text-[#8a9899] text-sm">
                    Once you delete your account, there is no going back. All your data, including
                    datasets, training jobs, and notebooks will be permanently deleted.
                </p>

                {!showDeleteConfirm ? (
                    <button
                        onClick={() => setShowDeleteConfirm(true)}
                        className="flex items-center gap-2 px-4 py-2 border border-[#e67e80] text-[#e67e80] rounded-lg hover:bg-[#e67e80]/10 transition-colors"
                    >
                        <Trash2 className="w-4 h-4" />
                        Delete Account
                    </button>
                ) : (
                    <div className="p-4 bg-[#e67e80]/5 border border-[#e67e80]/30 rounded-lg space-y-4">
                        <p className="text-[#dadada] text-sm">
                            To confirm, type <strong>DELETE</strong> below:
                        </p>
                        <input
                            type="text"
                            value={deleteConfirmText}
                            onChange={(e) => setDeleteConfirmText(e.target.value)}
                            placeholder="DELETE"
                            className="w-full px-4 py-2 bg-[#141b1e] border border-[#2d3437] rounded-lg text-[#dadada] placeholder-[#8a9899] focus:outline-none focus:border-[#e67e80]"
                        />
                        <div className="flex gap-3">
                            <button
                                onClick={() => {
                                    setShowDeleteConfirm(false)
                                    setDeleteConfirmText('')
                                }}
                                className="px-4 py-2 text-[#8a9899] hover:text-[#dadada] transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleDeleteAccount}
                                disabled={deleteConfirmText !== 'DELETE'}
                                className="flex items-center gap-2 px-4 py-2 bg-[#e67e80] text-white rounded-lg hover:bg-[#d56d6f] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <Trash2 className="w-4 h-4" />
                                Permanently Delete
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
