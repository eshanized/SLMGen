/**
 * Settings Layout.
 * 
 * Sidebar navigation for user settings pages.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAuth } from '@/contexts/auth-context'
import { User, Lock, ArrowLeft, Settings } from '@/components/icons'

const settingsNav = [
    { href: '/dashboard/settings', label: 'Profile', icon: User },
    { href: '/dashboard/settings/account', label: 'Account', icon: Lock },
]

export default function SettingsLayout({
    children,
}: {
    children: React.ReactNode
}) {
    const pathname = usePathname()
    const { profile } = useAuth()

    return (
        <div className="min-h-screen bg-[#141b1e]">
            {/* Header */}
            <header className="border-b border-[#2d3437] bg-[#1e2528]/80 backdrop-blur-sm sticky top-0 z-50">
                <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Link
                            href="/dashboard"
                            className="flex items-center gap-2 text-[#8a9899] hover:text-[#dadada] transition-colors"
                        >
                            <ArrowLeft className="w-5 h-5" />
                            <span>Back to Dashboard</span>
                        </Link>
                    </div>
                    <div className="flex items-center gap-2">
                        <Settings className="w-5 h-5 text-[#8ccf7e]" />
                        <span className="text-[#dadada] font-medium">Settings</span>
                    </div>
                </div>
            </header>

            <div className="max-w-6xl mx-auto px-6 py-8">
                <div className="flex gap-8">
                    {/* Sidebar */}
                    <aside className="w-64 flex-shrink-0">
                        {/* User info */}
                        <div className="p-4 bg-[#1e2528] border border-[#2d3437] rounded-xl mb-6">
                            <div className="flex items-center gap-3">
                                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-[#8ccf7e] to-[#6cbfbf] flex items-center justify-center text-[#141b1e] font-bold text-lg">
                                    {profile?.full_name?.[0]?.toUpperCase() || profile?.email?.[0]?.toUpperCase() || '?'}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="text-[#dadada] font-medium truncate">
                                        {profile?.full_name || 'User'}
                                    </p>
                                    <p className="text-sm text-[#8a9899] truncate">
                                        {profile?.email}
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Navigation */}
                        <nav className="space-y-1">
                            {settingsNav.map((item) => {
                                const isActive = pathname === item.href
                                const Icon = item.icon
                                return (
                                    <Link
                                        key={item.href}
                                        href={item.href}
                                        className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-colors ${isActive
                                                ? 'bg-[#8ccf7e]/10 text-[#8ccf7e] border border-[#8ccf7e]/30'
                                                : 'text-[#8a9899] hover:text-[#dadada] hover:bg-[#1e2528]'
                                            }`}
                                    >
                                        <Icon className="w-5 h-5" />
                                        <span>{item.label}</span>
                                    </Link>
                                )
                            })}
                        </nav>
                    </aside>

                    {/* Main content */}
                    <main className="flex-1 min-w-0">
                        {children}
                    </main>
                </div>
            </div>
        </div>
    )
}
