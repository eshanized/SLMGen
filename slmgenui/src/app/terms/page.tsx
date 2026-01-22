/**
 * Terms of Service Page.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

import Link from 'next/link'
import { Metadata } from 'next'
import { ArrowLeft } from '@/components/icons'

export const metadata: Metadata = {
    title: 'Terms of Service',
    description: 'SLMGEN Terms of Service - Read our terms and conditions for using the platform.',
}

export default function TermsPage() {
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
                <h1 className="text-3xl font-bold text-[#dadada] mb-2">Terms of Service</h1>
                <p className="text-[#8a9899] mb-8">Last updated: January 19, 2026</p>

                <div className="prose prose-invert prose-headings:text-[#dadada] prose-p:text-[#8a9899] prose-strong:text-[#dadada] prose-a:text-[#8ccf7e] max-w-none space-y-8">
                    <section>
                        <h2 className="text-xl font-semibold text-[#dadada] mb-4">1. Acceptance of Terms</h2>
                        <p className="text-[#8a9899] leading-relaxed">
                            By accessing or using SLMGEN (&quot;the Service&quot;), you agree to be bound by these Terms of Service.
                            If you do not agree to these terms, please do not use the Service.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-[#dadada] mb-4">2. Description of Service</h2>
                        <p className="text-[#8a9899] leading-relaxed">
                            SLMGEN is a web application that enables users to generate fine-tuning notebooks for
                            Small Language Models (SLMs). The Service provides dataset analysis, model recommendation,
                            and Jupyter notebook generation for use with Google Colab.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-[#dadada] mb-4">3. User Responsibilities</h2>
                        <ul className="list-disc list-inside text-[#8a9899] space-y-2">
                            <li>You are responsible for the datasets you upload to the Service</li>
                            <li>You must not upload datasets containing illegal, harmful, or copyrighted content</li>
                            <li>You are responsible for securing your account credentials</li>
                            <li>You must comply with all applicable laws and regulations</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-[#dadada] mb-4">4. Intellectual Property</h2>
                        <p className="text-[#8a9899] leading-relaxed">
                            You retain all rights to your datasets. The generated notebooks are provided under the
                            MIT license. SLMGEN&apos;s source code, branding, and documentation remain the property
                            of Eshan Roy.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-[#dadada] mb-4">5. Limitation of Liability</h2>
                        <p className="text-[#8a9899] leading-relaxed">
                            The Service is provided &quot;as is&quot; without warranties of any kind. We are not liable for
                            any damages arising from the use of generated notebooks, training results, or model
                            outputs.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-[#dadada] mb-4">6. Data Handling</h2>
                        <p className="text-[#8a9899] leading-relaxed">
                            Uploaded datasets are processed temporarily and deleted after session expiration.
                            We do not store your training data permanently. See our Privacy Policy for more details.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-[#dadada] mb-4">7. Modifications</h2>
                        <p className="text-[#8a9899] leading-relaxed">
                            We reserve the right to modify these terms at any time. Continued use of the Service
                            after changes constitutes acceptance of the new terms.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-[#dadada] mb-4">8. Contact</h2>
                        <p className="text-[#8a9899] leading-relaxed">
                            For questions about these Terms, contact us at{' '}
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
