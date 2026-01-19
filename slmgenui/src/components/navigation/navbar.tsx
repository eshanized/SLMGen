/**
 * Main Navigation Bar Component.
 * 
 * Desktop and mobile responsive navigation with icons.
 * Everblush themed.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
    Github,
    Menu,
    X,
    Sparkles,
    Box,
    Zap,
    Info,
    Home,
} from '@/components/icons';

import Image from 'next/image';

interface NavItem {
    label: string;
    href: string;
    icon: React.ComponentType<{ className?: string }>;
    isExternal?: boolean;
}

const NAV_ITEMS: NavItem[] = [
    { label: 'Home', href: '/', icon: Home },
    { label: 'Features', href: '/#features', icon: Sparkles },
    { label: 'Models', href: '/#models', icon: Box },
    { label: 'How It Works', href: '/#how-it-works', icon: Zap },
    { label: 'About', href: '/about', icon: Info },
];

export function Navbar() {
    const [isOpen, setIsOpen] = useState(false);
    const pathname = usePathname();

    const isActive = (href: string) => {
        if (href === '/') return pathname === '/';
        if (href.startsWith('/#')) return pathname === '/';
        return pathname.startsWith(href);
    };

    return (
        <header className="sticky top-0 z-50 backdrop-blur-xl bg-[#141b1e]/80 border-b border-[#2d3437]">
            <div className="container mx-auto px-4">
                <nav className="flex items-center justify-between h-20">
                    {/* Logo */}
                    <Link href="/" className="flex items-center gap-2 group mr-8">
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

                    {/* Desktop Navigation - Centered Pill Design */}
                    <div className="hidden md:flex items-center gap-2">
                        {NAV_ITEMS.map((item) => (
                            <Link
                                key={item.label}
                                href={item.href}
                                className={`
                                    flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 border border-transparent
                                    ${isActive(item.href)
                                        ? 'bg-[#1e2528] text-[#8ccf7e] border-[#2d3437]'
                                        : 'text-[#8a9899] hover:text-[#dadada] hover:bg-[#1e2528]/50 hover:border-[#2d3437]/50'
                                    }
                                `}
                            >
                                <item.icon className={`w-4 h-4 ${isActive(item.href) ? 'text-[#8ccf7e]' : 'text-[#8a9899] group-hover:text-[#dadada]'}`} />
                                {item.label}
                            </Link>
                        ))}
                    </div>

                    {/* Right Side Actions */}
                    <div className="flex items-center gap-3 ml-auto">
                        <a
                            href="https://github.com/eshanized/slmgen"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="hidden md:flex items-center gap-2 px-4 py-2.5 text-[#8a9899] hover:text-[#dadada] hover:bg-[#1e2528] border border-transparent hover:border-[#2d3437] rounded-xl transition-all text-sm font-medium"
                        >
                            <Github className="w-4 h-4" />
                            <span>GitHub</span>
                        </a>

                        <div className="w-px h-8 bg-[#2d3437] hidden md:block mx-1" />

                        <Link
                            href="/dashboard"
                            className="px-5 py-2.5 bg-gradient-to-r from-[#8ccf7e] to-[#6cbfbf] text-[#141b1e] rounded-xl font-bold hover:shadow-lg hover:shadow-[#8ccf7e]/20 transition-all hover:-translate-y-0.5 text-sm"
                        >
                            Get Started
                        </Link>

                        {/* Mobile Menu Button */}
                        <button
                            onClick={() => setIsOpen(!isOpen)}
                            className="md:hidden p-2 text-[#8a9899] hover:text-[#dadada] hover:bg-[#1e2528] rounded-xl transition-colors border border-transparent hover:border-[#2d3437]"
                            aria-label={isOpen ? 'Close menu' : 'Open menu'}
                        >
                            {isOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
                        </button>
                    </div>
                </nav>

                {/* Mobile Navigation */}
                {isOpen && (
                    <div className="md:hidden pb-4 animate-in slide-in-from-top-2 duration-200">
                        <div className="flex flex-col gap-1 bg-[#1e2528] rounded-2xl p-2 border border-[#2d3437] shadow-xl">
                            {NAV_ITEMS.map((item) => (
                                <Link
                                    key={item.label}
                                    href={item.href}
                                    onClick={() => setIsOpen(false)}
                                    className={`
                                        flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all
                                        ${isActive(item.href)
                                            ? 'bg-[#2d3437] text-[#8ccf7e]'
                                            : 'text-[#8a9899] hover:text-[#dadada] hover:bg-[#232a2d]'
                                        }
                                    `}
                                >
                                    <item.icon className="w-5 h-5" />
                                    {item.label}
                                </Link>
                            ))}
                            <hr className="border-[#2d3437] my-2" />
                            <a
                                href="https://github.com/eshanized/slmgen"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-[#8a9899] hover:text-[#dadada] hover:bg-[#232a2d] transition-all"
                            >
                                <Github className="w-5 h-5" />
                                GitHub
                            </a>
                        </div>
                    </div>
                )}
            </div>
        </header>
    );
}
