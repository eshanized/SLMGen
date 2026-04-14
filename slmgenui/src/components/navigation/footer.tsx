/**
 * Footer Navigation Component - V3.0.0.
 * 
 * Updated with fresh dark theme.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

import Image from 'next/image';
import Link from 'next/link';
import {
    Github,
    Mail,
    FileText,
    Shield,
    Info,
    ExternalLink,
    Sparkles,
} from '@/components/icons';

interface FooterLink {
    label: string;
    href: string;
    icon: React.ComponentType<{ className?: string }>;
    isExternal?: boolean;
}

const FOOTER_LINKS: FooterLink[] = [
    { label: 'About', href: '/about', icon: Info },
    { label: 'Terms', href: '/terms', icon: FileText },
    { label: 'Privacy', href: '/privacy', icon: Shield },
];

const SOCIAL_LINKS: FooterLink[] = [
    { label: 'GitHub', href: 'https://github.com/eshanized/slmgen', icon: Github, isExternal: true },
    { label: 'Contact', href: 'mailto:eshanized@proton.me', icon: Mail, isExternal: true },
];

interface FooterProps {
    variant?: 'default' | 'minimal';
}

export function Footer({ variant = 'default' }: FooterProps) {
    if (variant === 'minimal') {
        return (
            <footer className="border-t border-zinc-800 bg-zinc-950">
                <div className="container mx-auto px-4 py-4">
                    <div className="flex items-center justify-between text-sm text-zinc-500">
                        <span>© 2026 Eshan Roy</span>
                        <div className="flex items-center gap-4">
                            {SOCIAL_LINKS.map((link) => (
                                <a
                                    key={link.label}
                                    href={link.href}
                                    target={link.isExternal ? '_blank' : undefined}
                                    rel={link.isExternal ? 'noopener noreferrer' : undefined}
                                    className="hover:text-white transition-colors"
                                    title={link.label}
                                >
                                    <link.icon className="w-4 h-4" />
                                </a>
                            ))}
                        </div>
                    </div>
                </div>
            </footer>
        );
    }

    return (
        <footer className="border-t border-zinc-800 bg-zinc-950">
            <div className="container mx-auto px-4 py-12">
                <div className="grid md:grid-cols-4 gap-10">
                    {/* Brand */}
                    <div className="md:col-span-2">
                        <Link href="/" className="flex items-center gap-2.5 group mb-4">
                            <div className="relative w-8 h-8">
                                <Image
                                    src="/logo.svg"
                                    alt="SLMGEN"
                                    fill
                                    className="object-contain group-hover:scale-110 transition-transform"
                                />
                            </div>
                            <span className="text-lg font-bold tracking-wide">SLMGEN</span>
                            <span className="px-1.5 py-0.5 text-[10px] font-semibold bg-gradient-to-r from-violet-600 to-fuchsia-600 rounded-md text-white">
                                v3
                            </span>
                        </Link>
                        <p className="text-zinc-400 text-sm max-w-md leading-relaxed">
                            Fine-tune Small Language Models in seconds. 
                            Upload your dataset, get AI-matched model recommendations, and receive a ready-to-run Colab notebook.
                        </p>
                        <div className="flex items-center gap-2 mt-4 text-xs text-zinc-500">
                            <Sparkles className="w-3.5 h-3.5 text-violet-400" />
                            <span>Powered by Unsloth & LoRA</span>
                        </div>
                    </div>

                    {/* Quick Links */}
                    <div>
                        <h3 className="text-white font-semibold mb-4">Quick Links</h3>
                        <ul className="space-y-2.5">
                            {FOOTER_LINKS.map((link) => (
                                <li key={link.label}>
                                    <Link
                                        href={link.href}
                                        className="flex items-center gap-2 text-zinc-400 hover:text-violet-400 transition-colors text-sm group"
                                    >
                                        <link.icon className="w-4 h-4 group-hover:scale-110 transition-transform" />
                                        {link.label}
                                    </Link>
                                </li>
                            ))}
                        </ul>
                    </div>

                    {/* Connect */}
                    <div>
                        <h3 className="text-white font-semibold mb-4">Connect</h3>
                        <ul className="space-y-2.5">
                            {SOCIAL_LINKS.map((link) => (
                                <li key={link.label}>
                                    <a
                                        href={link.href}
                                        target={link.isExternal ? '_blank' : undefined}
                                        rel={link.isExternal ? 'noopener noreferrer' : undefined}
                                        className="flex items-center gap-2 text-zinc-400 hover:text-violet-400 transition-colors text-sm group"
                                    >
                                        <link.icon className="w-4 h-4 group-hover:scale-110 transition-transform" />
                                        {link.label}
                                        {link.isExternal && <ExternalLink className="w-3 h-3 opacity-50" />}
                                    </a>
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>

                {/* Bottom Bar */}
                <div className="mt-12 pt-6 border-t border-zinc-800 flex flex-col md:flex-row items-center justify-between gap-4">
                    <p className="text-zinc-500 text-sm">
                        © 2026 Eshan Roy. MIT License.
                    </p>
                    <div className="flex items-center gap-5">
                        <Link
                            href="/dashboard"
                            className="px-4 py-2.5 bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500 text-white rounded-lg font-semibold text-sm hover:shadow-lg hover:shadow-violet-600/20 transition-all"
                        >
                            Start Fine-Tuning Free
                        </Link>
                    </div>
                </div>
            </div>
        </footer>
    );
}