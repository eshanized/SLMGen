/**
 * About Page.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

import Link from 'next/link'
import { Metadata } from 'next'
import { Rocket, BarChart3, Target, Zap, BookOpen, ArrowLeft } from '@/components/icons'

export const metadata: Metadata = {
    title: 'About',
    description: 'About SLMGEN - The open-source SLM fine-tuning platform.',
}

export default function AboutPage() {
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
                {/* Hero */}
                <div className="text-center mb-12">
                    <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-[#8ccf7e] to-[#6cbfbf] rounded-2xl mb-6">
                        <Rocket className="w-10 h-10 text-[#141b1e]" />
                    </div>
                    <h1 className="text-4xl font-bold text-[#dadada] mb-4">About SLMGEN</h1>
                    <p className="text-xl text-[#8a9899] max-w-2xl mx-auto">
                        The open-source platform for fine-tuning Small Language Models.
                        2x faster. 70% less VRAM. Completely free.
                    </p>
                </div>

                {/* Mission */}
                <section className="mb-12">
                    <h2 className="text-2xl font-bold text-[#dadada] mb-4">Our Mission</h2>
                    <p className="text-[#8a9899] leading-relaxed text-lg">
                        We believe everyone should have access to powerful AI fine-tuning tools, not just
                        big tech companies. SLMGEN democratizes SLM fine-tuning by providing an intuitive
                        interface that generates optimized training notebooks for free GPU resources.
                    </p>
                </section>

                {/* Features */}
                <section className="mb-12">
                    <h2 className="text-2xl font-bold text-[#dadada] mb-6">What We Offer</h2>
                    <div className="grid md:grid-cols-2 gap-4">
                        {[
                            { Icon: BarChart3, title: 'Dataset Intelligence', desc: 'Quality scoring, personality detection, and hallucination risk analysis' },
                            { Icon: Target, title: '100-Point Matching', desc: 'AI-powered model selection based on your data and deployment needs' },
                            { Icon: Zap, title: 'Unsloth Optimization', desc: '2x faster training with 70% less VRAM on free Colab GPUs' },
                            { Icon: BookOpen, title: 'Ready-to-Run Notebooks', desc: 'Self-contained Jupyter notebooks with embedded datasets' },
                        ].map((item) => (
                            <div key={item.title} className="p-4 bg-[#1e2528] border border-[#2d3437] rounded-xl flex gap-4 items-start">
                                <div className="p-2 bg-[#141b1e] rounded-lg border border-[#2d3437]">
                                    <item.Icon className="w-6 h-6 text-[#8ccf7e]" />
                                </div>
                                <div>
                                    <h3 className="text-[#dadada] font-semibold mb-1">{item.title}</h3>
                                    <p className="text-sm text-[#8a9899]">{item.desc}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </section>

                {/* Team / Contributors */}
                <section className="mb-12">
                    <h2 className="text-2xl font-bold text-[#dadada] mb-6">Team & Contributors</h2>
                    <div className="grid md:grid-cols-2 gap-6">
                        {/* Eshan - Creator */}
                        <div className="flex items-center gap-6 p-6 bg-[#1e2528] border border-[#2d3437] rounded-xl hover:border-[#8ccf7e]/30 transition-colors">
                            <div className="w-20 h-20 rounded-full bg-[#141b1e] overflow-hidden border-2 border-[#8ccf7e]/20 flex-shrink-0">
                                <img
                                    src="https://github.com/eshanized.png"
                                    alt="Eshan Roy"
                                    className="w-full h-full object-cover"
                                />
                            </div>
                            <div>
                                <h3 className="text-xl font-semibold text-[#dadada]">Eshan Roy</h3>
                                <p className="text-[#8a9899] mb-3">Creator & Maintainer</p>
                                <div className="flex gap-4">
                                    <a
                                        href="https://github.com/eshanized"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-[#8ccf7e] hover:underline text-sm flex items-center gap-1"
                                    >
                                        GitHub
                                    </a>
                                </div>
                            </div>
                        </div>

                        {/* Vedant - Contributor */}
                        <div className="flex items-center gap-6 p-6 bg-[#1e2528] border border-[#2d3437] rounded-xl hover:border-[#6cbfbf]/30 transition-colors">
                            <div className="w-20 h-20 rounded-full bg-[#141b1e] overflow-hidden border-2 border-[#6cbfbf]/20 flex-shrink-0">
                                <img
                                    src="https://github.com/vedanthq.png"
                                    alt="Vedant Singh Rajput"
                                    className="w-full h-full object-cover"
                                />
                            </div>
                            <div>
                                <h3 className="text-xl font-semibold text-[#dadada]">Vedant Singh Rajput</h3>
                                <p className="text-[#8a9899] mb-3">Contributor</p>
                                <div className="flex gap-4">
                                    <a
                                        href="https://github.com/vedanthq"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-[#6cbfbf] hover:underline text-sm flex items-center gap-1"
                                    >
                                        GitHub
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                {/* Open Source */}
                <section className="mb-12">
                    <h2 className="text-2xl font-bold text-[#dadada] mb-4">Open Source</h2>
                    <div className="p-6 bg-gradient-to-br from-[#8ccf7e]/10 to-[#6cbfbf]/10 border border-[#8ccf7e]/30 rounded-xl">
                        <p className="text-[#8a9899] mb-4">
                            SLMGEN is open source under the MIT License. Contributions are welcome!
                        </p>
                        <a
                            href="https://github.com/eshanized/SLMGen"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-2 px-4 py-2 bg-[#2d3437] text-[#dadada] rounded-lg hover:bg-[#3d4447] transition-colors"
                        >
                            ⭐ Star on GitHub
                        </a>
                    </div>
                </section>

                {/* Tech Stack */}
                <section>
                    <h2 className="text-2xl font-bold text-[#dadada] mb-4">Tech Stack</h2>
                    <div className="flex flex-wrap gap-2">
                        {['Next.js', 'FastAPI', 'Python', 'TypeScript', 'Supabase', 'Unsloth', 'LoRA', 'Tailwind CSS'].map((tech) => (
                            <span key={tech} className="px-3 py-1 bg-[#1e2528] border border-[#2d3437] rounded-full text-sm text-[#8a9899]">
                                {tech}
                            </span>
                        ))}
                    </div>
                </section>
            </main>
        </div>
    )
}
