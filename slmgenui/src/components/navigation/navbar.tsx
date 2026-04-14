/**
 * Main Navigation Bar Component - V3.0.0.
 * 
 * Updated with fresh dark theme and V3.0.0 branding.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
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
    const [isScrolled, setIsScrolled] = useState(false);
    const pathname = usePathname();

    const isActive = (href: string) => {
        if (href === '/') return pathname === '/';
        if (href.startsWith('/#')) return pathname === '/';
        return pathname.startsWith(href);
    };

    useEffect(() => {
        const handleScroll = () => {
            setIsScrolled(window.scrollY > 20);
        };
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    return (
        <motion.header
            className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${isScrolled ? 'py-2' : 'py-0'}`}
        >
            <div className="container mx-auto px-4">
                <motion.nav
                    layout
                    className={`
                        flex items-center justify-between transition-all duration-300
                        ${isScrolled
                            ? 'h-14 bg-zinc-900/80 backdrop-blur-xl border border-zinc-800 rounded-2xl shadow-2xl shadow-black/30 px-5 max-w-5xl mx-auto'
                            : 'h-18 bg-transparent border-b border-zinc-800/50 px-0 max-w-none'
                        }
                    `}
                >
                    {/* Logo */}
                    <Link href="/" className="flex items-center gap-2.5 group mr-8">
                        <motion.div
                            className="relative w-8 h-8"
                            whileHover={{ rotate: 180 }}
                            transition={{ duration: 0.5 }}
                        >
                            <Image
                                src="/logo.svg"
                                alt="SLMGEN"
                                fill
                                className="object-contain"
                            />
                        </motion.div>
                        <span className="text-lg font-bold tracking-wide group-hover:text-white transition-colors">
                            SLMGEN
                        </span>
                        <span className="hidden sm:inline-block px-1.5 py-0.5 text-[10px] font-semibold bg-gradient-to-r from-violet-600 to-fuchsia-600 rounded-md text-white">
                            v3
                        </span>
                    </Link>

                    {/* Desktop Navigation */}
                    <div className="hidden md:flex items-center gap-1">
                        {NAV_ITEMS.map((item) => {
                            const active = isActive(item.href);
                            return (
                                <Link
                                    key={item.label}
                                    href={item.href}
                                    className="relative px-3.5 py-2 text-sm font-medium transition-colors"
                                >
                                    {active && (
                                        <motion.div
                                            layoutId="nav-pill"
                                            className="absolute inset-0 bg-zinc-800/60 rounded-lg border border-zinc-700"
                                            transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                                        />
                                    )}
                                    <span className={`relative z-10 flex items-center gap-2 ${active ? 'text-violet-400' : 'text-zinc-400 hover:text-white'}`}>
                                        <item.icon className={`w-4 h-4 ${active ? 'text-violet-400' : 'text-zinc-400'}`} />
                                        {item.label}
                                    </span>
                                </Link>
                            );
                        })}
                    </div>

                    {/* Right Actions */}
                    <div className="flex items-center gap-3 md:ml-auto">
                        <a
                            href="https://github.com/eshanized/slmgen"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="hidden md:flex items-center gap-2 px-3.5 py-2 text-zinc-400 hover:text-white hover:bg-zinc-800/50 border border-transparent hover:border-zinc-700 rounded-lg transition-all text-sm font-medium"
                        >
                            <Github className="w-4 h-4" />
                            <span>GitHub</span>
                        </a>

                        <div className="w-px h-6 bg-zinc-800 hidden md:block mx-1" />

                        <Link
                            href="/dashboard"
                            className="px-5 py-2.5 bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500 text-white rounded-lg font-semibold hover:shadow-lg hover:shadow-violet-600/20 transition-all hover:-translate-y-0.5 text-sm"
                        >
                            Start Fine-Tuning
                        </Link>

                        <button
                            onClick={() => setIsOpen(!isOpen)}
                            className="md:hidden p-2 text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors"
                            aria-label={isOpen ? 'Close menu' : 'Open menu'}
                        >
                            {isOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
                        </button>
                    </div>
                </motion.nav>

                {/* Mobile Navigation */}
                <AnimatePresence>
                    {isOpen && (
                        <motion.div
                            initial={{ opacity: 0, y: -20, height: 0 }}
                            animate={{ opacity: 1, y: 0, height: 'auto' }}
                            exit={{ opacity: 0, y: -20, height: 0 }}
                            className="md:hidden overflow-hidden"
                        >
                            <div className="mt-2 bg-zinc-900/95 backdrop-blur-xl rounded-2xl p-2 border border-zinc-800 shadow-2xl">
                                <div className="flex flex-col gap-1">
                                    {NAV_ITEMS.map((item) => (
                                        <Link
                                            key={item.label}
                                            href={item.href}
                                            onClick={() => setIsOpen(false)}
                                            className={`
                                                flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all
                                                ${isActive(item.href)
                                                    ? 'bg-zinc-800 text-violet-400'
                                                    : 'text-zinc-400 hover:text-white hover:bg-zinc-800/50'
                                                }
                                            `}
                                        >
                                            <item.icon className="w-5 h-5" />
                                            {item.label}
                                        </Link>
                                    ))}
                                    <hr className="border-zinc-800 my-2" />
                                    <a
                                        href="https://github.com/eshanized/slmgen"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-zinc-400 hover:text-white hover:bg-zinc-800/50 transition-all"
                                    >
                                        <Github className="w-5 h-5" />
                                        GitHub
                                    </a>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </motion.header>
    );
}