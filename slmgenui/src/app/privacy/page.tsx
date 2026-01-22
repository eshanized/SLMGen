/**
 * Privacy Policy Page.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

import Link from 'next/link'
import { Metadata } from 'next'
import { ArrowLeft } from '@/components/icons'

export const metadata: Metadata = {
    title: 'Privacy Policy',
    description: 'SLMGEN Privacy Policy - Learn how we handle your data.',
}

export default function PrivacyPage() {
    return (
        <div className="min-h-screen bg-[#141b1e]">
            {/* Header */}
            <header className="border-b border-[#2d3437] bg-[#1e2528]/80 backdrop-blur-sm">
                <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
                    <Link href="/" className="flex items-center gap-2 text-[#dadada] hover:text-[#8ccf7e] transition-colors">
                        <ArrowLeft className="w-4 h-4" />
                        Back to Home
                    </Link>
                </div>
            </header>

            <main className="max-w-4xl mx-auto px-6 py-12">
                <h1 className="text-3xl font-bold text-[#dadada] mb-2">Privacy Policy</h1>
                <p className="text-[#8a9899] mb-8">Last updated: January 19, 2026</p>

                <div className="space-y-8">
                    <section>
                        <h2 className="text-xl font-semibold text-[#dadada] mb-4">1. Information We Collect</h2>
                        <div className="text-[#8a9899] space-y-4">
                            <p><strong className="text-[#dadada]">Account Information:</strong> Email address, name, and avatar URL when you create an account.</p>
                            <p><strong className="text-[#dadada]">Dataset Data:</strong> JSONL files you upload for processing. These are stored temporarily and deleted after your session expires.</p>
                            <p><strong className="text-[#dadada]">Usage Data:</strong> Information about how you use the Service, including job history and preferences.</p>
                        </div>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-[#dadada] mb-4">2. How We Use Your Information</h2>
                        <ul className="list-disc list-inside text-[#8a9899] space-y-2">
                            <li>To provide and maintain the Service</li>
                            <li>To analyze datasets and generate training notebooks</li>
                            <li>To improve the Service and user experience</li>
                            <li>To communicate with you about your account</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-[#dadada] mb-4">3. Data Retention</h2>
                        <div className="p-4 bg-[#8ccf7e]/10 border border-[#8ccf7e]/30 rounded-xl text-[#8a9899]">
                            <p className="text-[#8ccf7e] font-semibold mb-2">Key Point:</p>
                            <p>
                                Uploaded datasets are automatically deleted after 30 minutes of inactivity.
                                We do not permanently store your training data on our servers.
                            </p>
                        </div>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-[#dadada] mb-4">4. Data Security</h2>
                        <p className="text-[#8a9899] leading-relaxed">
                            We implement industry-standard security measures to protect your data, including:
                        </p>
                        <ul className="list-disc list-inside text-[#8a9899] space-y-2 mt-4">
                            <li>HTTPS encryption for all data in transit</li>
                            <li>Secure authentication via Supabase</li>
                            <li>Automatic session expiration and data cleanup</li>
                            <li>No permanent storage of uploaded datasets</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-[#dadada] mb-4">5. Third-Party Services</h2>
                        <p className="text-[#8a9899] leading-relaxed">We use the following third-party services:</p>
                        <ul className="list-disc list-inside text-[#8a9899] space-y-2 mt-4">
                            <li><strong className="text-[#dadada]">Supabase:</strong> Authentication and database</li>
                            <li><strong className="text-[#dadada]">Vercel:</strong> Frontend hosting</li>
                            <li><strong className="text-[#dadada]">Render:</strong> Backend hosting</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-[#dadada] mb-4">6. Your Rights</h2>
                        <p className="text-[#8a9899] leading-relaxed">You have the right to:</p>
                        <ul className="list-disc list-inside text-[#8a9899] space-y-2 mt-4">
                            <li>Access your personal data</li>
                            <li>Correct inaccurate data</li>
                            <li>Delete your account and associated data</li>
                            <li>Export your data</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-[#dadada] mb-4">7. Cookies</h2>
                        <p className="text-[#8a9899] leading-relaxed">
                            We use essential cookies for authentication and session management.
                            We do not use tracking or advertising cookies.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-[#dadada] mb-4">8. Contact</h2>
                        <p className="text-[#8a9899] leading-relaxed">
                            For privacy-related inquiries, contact us at{' '}
                            <a href="mailto:eshanized@proton.me" className="text-[#8ccf7e] hover:underline">
                                eshanized@proton.me
                            </a>
                        </p>
                    </section>
                </div>
            </main>
        </div>
    )
}
