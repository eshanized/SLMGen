/**
 * Dashboard Header Navigation Component.
 * 
 * Navigation for authenticated dashboard pages.
 * Includes breadcrumb-style navigation and user actions.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
    Rocket,
    History,
    Settings,
    Home,
    ChevronRight,
    LogOut,
    User,
} from '@/components/icons';

import Image from 'next/image';

interface NavItem {
    label: string;
    href: string;
    icon: React.ComponentType<{ className?: string }>;
}

const DASHBOARD_NAV: NavItem[] = [
    { label: 'Dashboard', href: '/dashboard', icon: Home },
    { label: 'History', href: '/dashboard/history', icon: History },
    { label: 'Settings', href: '/dashboard/settings', icon: Settings },
];

interface DashboardHeaderProps {
    showBreadcrumb?: boolean;
}

export function DashboardHeader({ showBreadcrumb = false }: DashboardHeaderProps) {
    const pathname = usePathname();

    const isActive = (href: string) => {
        if (href === '/dashboard') return pathname === '/dashboard';
        return pathname.startsWith(href);
    };

    // Generate breadcrumb from pathname
    const getBreadcrumbs = () => {
        const parts = pathname.split('/').filter(Boolean);
        const breadcrumbs: { label: string; href: string }[] = [];

        let currentPath = '';
        parts.forEach((part) => {
            currentPath += `/${part}`;
            breadcrumbs.push({
                label: part.charAt(0).toUpperCase() + part.slice(1),
                href: currentPath,
            });
        });

        return breadcrumbs;
    };

    return (
        <header className="sticky top-0 z-50 backdrop-blur-xl bg-[#141b1e]/90 border-b border-[#2d3437]">
            <div className="container mx-auto px-4">
                {/* Main Navigation */}
                <nav className="flex items-center justify-between h-16">
                    {/* Logo */}
                    <Link href="/" className="flex items-center gap-2 group">
                        <div className="relative w-9 h-9">
                            <Image
                                src="/logo.svg"
                                alt="SLMGEN Logo"
                                fill
                                className="object-contain group-hover:scale-110 transition-transform"
                            />
                        </div>
                        <span className="text-xl font-bold text-[#dadada] tracking-wide">SLMGEN</span>
                    </Link>

                    {/* Center Navigation */}
                    <div className="hidden md:flex items-center gap-1 bg-[#1e2528]/50 rounded-xl p-1 border border-[#2d3437]/50">
                        {DASHBOARD_NAV.map((item) => (
                            <Link
                                key={item.label}
                                href={item.href}
                                className={`
                                    flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all
                                    ${isActive(item.href)
                                        ? 'bg-gradient-to-r from-[#8ccf7e]/20 to-[#6cbfbf]/20 text-[#8ccf7e] shadow-sm'
                                        : 'text-[#8a9899] hover:text-[#dadada] hover:bg-[#232a2d]'
                                    }
                                `}
                            >
                                <item.icon className="w-4 h-4" />
                                {item.label}
                            </Link>
                        ))}
                    </div>

                    {/* Mobile Navigation */}
                    <div className="flex md:hidden items-center gap-2">
                        {DASHBOARD_NAV.map((item) => (
                            <Link
                                key={item.label}
                                href={item.href}
                                className={`
                                    p-2 rounded-lg transition-all
                                    ${isActive(item.href)
                                        ? 'bg-[#8ccf7e]/10 text-[#8ccf7e]'
                                        : 'text-[#8a9899] hover:text-[#dadada] hover:bg-[#1e2528]'
                                    }
                                `}
                                title={item.label}
                            >
                                <item.icon className="w-5 h-5" />
                            </Link>
                        ))}
                    </div>

                    {/* Right Actions */}
                    <div className="flex items-center gap-2">
                        <button
                            className="hidden md:flex items-center gap-2 px-3 py-2 text-[#8a9899] hover:text-[#dadada] hover:bg-[#1e2528] rounded-lg transition-all text-sm"
                            title="Account"
                        >
                            <User className="w-4 h-4" />
                            <span className="hidden lg:inline">Account</span>
                        </button>
                        <Link
                            href="/"
                            className="flex items-center gap-2 px-3 py-2 text-[#8a9899] hover:text-[#e57474] hover:bg-[#e57474]/10 rounded-lg transition-all text-sm"
                            title="Exit Dashboard"
                        >
                            <LogOut className="w-4 h-4" />
                            <span className="hidden lg:inline">Exit</span>
                        </Link>
                    </div>
                </nav>

                {/* Breadcrumb */}
                {showBreadcrumb && (
                    <div className="flex items-center gap-2 py-2 text-sm overflow-x-auto">
                        <Link
                            href="/"
                            className="text-[#8a9899] hover:text-[#dadada] transition-colors whitespace-nowrap"
                        >
                            Home
                        </Link>
                        {getBreadcrumbs().map((crumb, idx) => (
                            <div key={crumb.href} className="flex items-center gap-2">
                                <ChevronRight className="w-4 h-4 text-[#2d3437]" />
                                <Link
                                    href={crumb.href}
                                    className={`
                                        transition-colors whitespace-nowrap
                                        ${idx === getBreadcrumbs().length - 1
                                            ? 'text-[#dadada] font-medium'
                                            : 'text-[#8a9899] hover:text-[#dadada]'
                                        }
                                    `}
                                >
                                    {crumb.label}
                                </Link>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </header>
    );
}
