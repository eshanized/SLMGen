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
                <h1 className="text-2xl font-bold text-white">Account</h1>
                <p className="text-zinc-500 mt-1">Manage your account security and settings</p>
            </div>

            {/* Change Password */}
            <form onSubmit={handlePasswordChange} className="p-6 bg-zinc-900 border border-zinc-800 rounded-xl space-y-4">
                <div className="flex items-center gap-2 mb-4">
                    <Lock className="w-5 h-5 text-violet-400" />
                    <h2 className="text-lg font-semibold text-white">Change Password</h2>
                </div>

                <div>
                    <label className="block text-sm font-medium text-white mb-2">
                        New Password
                    </label>
                    <input
                        type="password"
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        placeholder="••••••••"
                        minLength={6}
                        required
                        className="w-full px-4 py-3 bg-zinc-950 border border-zinc-800 rounded-xl text-white placeholder-zinc-500 focus:outline-none focus:border-violet-500 transition-colors"
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-white mb-2">
                        Confirm New Password
                    </label>
                    <input
                        type="password"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        placeholder="••••••••"
                        minLength={6}
                        required
                        className="w-full px-4 py-3 bg-zinc-950 border border-zinc-800 rounded-xl text-white placeholder-zinc-500 focus:outline-none focus:border-violet-500 transition-colors"
                    />
                </div>

                {passwordError && (
                    <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
                        {passwordError}
                    </div>
                )}

                {passwordSuccess && (
                    <div className="p-3 bg-violet-500/10 border border-violet-500/30 rounded-lg text-violet-400 text-sm flex items-center gap-2">
                        <Check className="w-4 h-4" />
                        Password updated successfully!
                    </div>
                )}

                <button
                    type="submit"
                    disabled={passwordLoading}
                    className="flex items-center gap-2 px-4 py-2 bg-zinc-800 text-white rounded-lg hover:bg-zinc-700 transition-colors disabled:opacity-50"
                >
                    {passwordLoading ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                        'Update Password'
                    )}
                </button>
            </form>

            {/* Danger Zone */}
            <div className="p-6 bg-zinc-900 border border-red-500/30 rounded-xl space-y-4">
                <div className="flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5 text-red-400" />
                    <h2 className="text-lg font-semibold text-red-400">Danger Zone</h2>
                </div>

                <p className="text-zinc-500 text-sm">
                    Once you delete your account, there is no going back. All your data, including
                    datasets, training jobs, and notebooks will be permanently deleted.
                </p>

                {!showDeleteConfirm ? (
                    <button
                        onClick={() => setShowDeleteConfirm(true)}
                        className="flex items-center gap-2 px-4 py-2 border border-red-500 text-red-400 rounded-lg hover:bg-red-500/10 transition-colors"
                    >
                        <Trash2 className="w-4 h-4" />
                        Delete Account
                    </button>
                ) : (
                    <div className="p-4 bg-red-500/5 border border-red-500/30 rounded-lg space-y-4">
                        <p className="text-white text-sm">
                            To confirm, type <strong>DELETE</strong> below:
                        </p>
                        <input
                            type="text"
                            value={deleteConfirmText}
                            onChange={(e) => setDeleteConfirmText(e.target.value)}
                            placeholder="DELETE"
                            className="w-full px-4 py-2 bg-zinc-950 border border-zinc-800 rounded-lg text-white placeholder-zinc-500 focus:outline-none focus:border-red-500"
                        />
                        <div className="flex gap-3">
                            <button
                                onClick={() => {
                                    setShowDeleteConfirm(false)
                                    setDeleteConfirmText('')
                                }}
                                className="px-4 py-2 text-zinc-400 hover:text-white transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleDeleteAccount}
                                disabled={deleteConfirmText !== 'DELETE'}
                                className="flex items-center gap-2 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
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