/**
 * Footer Navigation Component.
 * 
 * Reusable footer with links and social icons.
 * Everblush themed.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

import Image from 'next/image';
import Link from 'next/link';
import {
    Rocket,
    Github,
    Mail,
    FileText,
    Shield,
    Info,
    ExternalLink,
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
            <footer className="border-t border-[#2d3437] bg-[#141b1e]">
                <div className="container mx-auto px-4 py-4">
                    <div className="flex items-center justify-between text-sm text-[#8a9899]">
                        <span>© 2026 Eshan Roy</span>
                        <div className="flex items-center gap-4">
                            {SOCIAL_LINKS.map((link) => (
                                <a
                                    key={link.label}
                                    href={link.href}
                                    target={link.isExternal ? '_blank' : undefined}
                                    rel={link.isExternal ? 'noopener noreferrer' : undefined}
                                    className="hover:text-[#dadada] transition-colors"
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
        <footer className="border-t border-[#2d3437] bg-[#141b1e]">
            <div className="container mx-auto px-4 py-12">
                <div className="grid md:grid-cols-4 gap-8">
                    {/* Brand */}
                    <div className="md:col-span-2">
                        <Link href="/" className="flex items-center gap-2 group mb-4">
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
                        <p className="text-[#8a9899] text-sm max-w-md">
                            Fine-tune Small Language Models in minutes. Upload your dataset, get a ready-to-run Colab notebook. Powered by Unsloth & LoRA.
                        </p>
                    </div>

                    {/* Quick Links */}
                    <div>
                        <h3 className="text-[#dadada] font-semibold mb-4">Quick Links</h3>
                        <ul className="space-y-2">
                            {FOOTER_LINKS.map((link) => (
                                <li key={link.label}>
                                    <Link
                                        href={link.href}
                                        className="flex items-center gap-2 text-[#8a9899] hover:text-[#8ccf7e] transition-colors text-sm group"
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
                        <h3 className="text-[#dadada] font-semibold mb-4">Connect</h3>
                        <ul className="space-y-2">
                            {SOCIAL_LINKS.map((link) => (
                                <li key={link.label}>
                                    <a
                                        href={link.href}
                                        target={link.isExternal ? '_blank' : undefined}
                                        rel={link.isExternal ? 'noopener noreferrer' : undefined}
                                        className="flex items-center gap-2 text-[#8a9899] hover:text-[#8ccf7e] transition-colors text-sm group"
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
                <div className="mt-12 pt-6 border-t border-[#2d3437] flex flex-col md:flex-row items-center justify-between gap-4">
                    <p className="text-[#8a9899] text-sm">
                        © 2026 Eshan Roy. MIT License.
                    </p>
                    <div className="flex items-center gap-6">
                        <Link
                            href="/dashboard"
                            className="px-4 py-2 bg-gradient-to-r from-[#8ccf7e] to-[#6cbfbf] text-[#141b1e] rounded-lg font-semibold text-sm hover:shadow-lg hover:shadow-[#8ccf7e]/30 transition-all hover:-translate-y-0.5"
                        >
                            Get Started
                        </Link>
                    </div>
                </div>
            </div>
        </footer>
    );
}
