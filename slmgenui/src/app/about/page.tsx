/**
 * About Page - V3.0.0.
 * 
 * Updated with fresh dark theme and V3 features.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

import Link from 'next/link';
import { Metadata } from 'next';
import Image from 'next/image';
import { 
    Rocket, 
    BarChart3, 
    Target, 
    Zap, 
    BookOpen, 
    ArrowLeft,
    Sparkles,
    FileText,
    Download,
    Gauge,
    Layers,
} from '@/components/icons';

export const metadata: Metadata = {
    title: 'About - SLMGEN V3.0.0',
    description: 'About SLMGEN - The open-source SLM fine-tuning platform.',
};

export default function AboutPage() {
    return (
        <div className="min-h-screen bg-zinc-950 text-white">
            {/* Header */}
            <header className="border-b border-zinc-800 bg-zinc-900/50 backdrop-blur-sm">
                <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
                    <Link href="/" className="flex items-center gap-2 text-zinc-300 hover:text-white transition-colors">
                        <ArrowLeft className="w-4 h-4" />
                        Back to Home
                    </Link>
                    <span className="px-2 py-1 text-xs font-semibold bg-gradient-to-r from-violet-600 to-fuchsia-600 rounded-md text-white">
                        v3.0.0
                    </span>
                </div>
            </header>

            <main className="max-w-4xl mx-auto px-6 py-12">
                {/* Hero */}
                <div className="text-center mb-14">
                    <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-violet-600 to-fuchsia-600 rounded-2xl mb-6">
                        <Rocket className="w-10 h-10 text-white" />
                    </div>
                    <h1 className="text-4xl font-bold mb-4">About SLMGEN</h1>
                    <p className="text-xl text-zinc-400 max-w-2xl mx-auto">
                        The open-source platform for fine-tuning Small Language Models.
                        2x faster. 70% less VRAM. Completely free.
                    </p>
                </div>

                {/* Mission */}
                <section className="mb-14">
                    <h2 className="text-2xl font-bold mb-4">Our Mission</h2>
                    <p className="text-zinc-400 leading-relaxed text-lg">
                        We believe everyone should have access to powerful AI fine-tuning tools, 
                        not just big tech companies. SLMGEN democratizes SLM fine-tuning by providing 
                        an intuitive interface that generates optimized training notebooks for free GPU resources.
                    </p>
                </section>

                {/* V3.0.0 Features */}
                <section className="mb-14">
                    <h2 className="text-2xl font-bold mb-6">
                        <span className="bg-gradient-to-r from-violet-400 to-fuchsia-400 bg-clip-text text-transparent">
                            V3.0.0
                        </span>
                        {' '}What&apos;s New
                    </h2>
                    <div className="grid md:grid-cols-2 gap-4">
                        {[
                            { Icon: FileText, title: 'Dataset Converter', desc: 'CSV, TSV, JSON, Alpaca, ShareGPT → ChatML' },
                            { Icon: Gauge, title: 'Training Presets', desc: 'Quick Demo, Production, Edge Optimize, Code Fine-tune' },
                            { Icon: Download, title: 'Export Pipeline', desc: 'Ollama Modelfile, GGUF, vLLM, HuggingFace' },
                            { Icon: Layers, title: '18 Models', desc: 'Up to 84B params with 128K context window' },
                        ].map((item) => (
                            <div key={item.title} className="p-5 bg-zinc-900/50 border border-zinc-800 rounded-xl flex gap-4 items-start hover:border-violet-500/30 transition-colors">
                                <div className="p-2.5 bg-zinc-800 rounded-lg border border-zinc-700">
                                    <item.Icon className="w-5 h-5 text-violet-400" />
                                </div>
                                <div>
                                    <h3 className="text-white font-semibold mb-1.5">{item.title}</h3>
                                    <p className="text-sm text-zinc-500">{item.desc}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </section>

                {/* What We Offer */}
                <section className="mb-14">
                    <h2 className="text-2xl font-bold mb-6">What We Offer</h2>
                    <div className="grid md:grid-cols-2 gap-4">
                        {[
                            { Icon: BarChart3, title: 'Dataset Intelligence', desc: 'Quality scoring, personality detection, and hallucination risk analysis' },
                            { Icon: Target, title: '100-Point Matching', desc: 'AI-powered model selection based on your data and deployment needs' },
                            { Icon: Zap, title: 'Unsloth Optimization', desc: '2x faster training with 70% less VRAM on free Colab GPUs' },
                            { Icon: BookOpen, title: 'Ready-to-Run Notebooks', desc: 'Self-contained Jupyter notebooks with embedded datasets' },
                        ].map((item) => (
                            <div key={item.title} className="p-4 bg-zinc-900/50 border border-zinc-800 rounded-xl flex gap-4 items-start">
                                <div className="p-2 bg-zinc-800 rounded-lg border border-zinc-700">
                                    <item.Icon className="w-5 h-5 text-emerald-400" />
                                </div>
                                <div>
                                    <h3 className="text-white font-semibold mb-1">{item.title}</h3>
                                    <p className="text-sm text-zinc-500">{item.desc}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </section>

                {/* Team */}
                <section className="mb-14">
                    <h2 className="text-2xl font-bold mb-6">Team & Contributors</h2>
                    <div className="grid md:grid-cols-2 gap-6">
                        <div className="flex items-center gap-5 p-5 bg-zinc-900/50 border border-zinc-800 rounded-xl hover:border-violet-500/30 transition-colors">
                            <div className="w-16 h-16 rounded-full bg-zinc-800 overflow-hidden border-2 border-violet-500/20 flex-shrink-0 relative">
                                <Image
                                    src="https://github.com/eshanized.png"
                                    alt="Eshan Roy"
                                    fill
                                    className="object-cover"
                                />
                            </div>
                            <div>
                                <h3 className="text-lg font-semibold text-white">Eshan Roy</h3>
                                <p className="text-zinc-500 mb-3">Creator & Maintainer</p>
                                <a
                                    href="https://github.com/eshanized"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-violet-400 hover:underline text-sm flex items-center gap-1"
                                >
                                    GitHub
                                </a>
                            </div>
                        </div>

                        <div className="flex items-center gap-5 p-5 bg-zinc-900/50 border border-zinc-800 rounded-xl hover:border-cyan-500/30 transition-colors">
                            <div className="w-16 h-16 rounded-full bg-zinc-800 overflow-hidden border-2 border-cyan-500/20 flex-shrink-0 relative">
                                <Image
                                    src="https://github.com/vedanthq.png"
                                    alt="Vedant Singh Rajput"
                                    fill
                                    className="object-cover"
                                />
                            </div>
                            <div>
                                <h3 className="text-lg font-semibold text-white">Vedant Singh Rajput</h3>
                                <p className="text-zinc-500 mb-3">Contributor</p>
                                <a
                                    href="https://github.com/vedanthq"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-cyan-400 hover:underline text-sm flex items-center gap-1"
                                >
                                    GitHub
                                </a>
                            </div>
                        </div>
                    </div>
                </section>

                {/* Open Source */}
                <section className="mb-14">
                    <h2 className="text-2xl font-bold mb-4">Open Source</h2>
                    <div className="p-6 bg-gradient-to-br from-violet-600/10 to-fuchsia-600/10 border border-violet-500/30 rounded-xl">
                        <p className="text-zinc-400 mb-5">
                            SLMGEN is open source under the MIT License. Contributions are welcome!
                        </p>
                        <a
                            href="https://github.com/eshanized/SLMGen"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-2 px-4 py-2.5 bg-zinc-800 text-white rounded-lg hover:bg-zinc-700 transition-colors"
                        >
                            <Sparkles className="w-4 h-4" />
                            ⭐ Star on GitHub
                        </a>
                    </div>
                </section>

                {/* Tech Stack */}
                <section>
                    <h2 className="text-2xl font-bold mb-4">Tech Stack</h2>
                    <div className="flex flex-wrap gap-2">
                        {['Next.js 16', 'FastAPI', 'Python 3.11', 'TypeScript', 'Supabase', 'Unsloth', 'LoRA', 'Tailwind CSS 4'].map((tech) => (
                            <span key={tech} className="px-3 py-1.5 bg-zinc-900/50 border border-zinc-800 rounded-full text-sm text-zinc-400">
                                {tech}
                            </span>
                        ))}
                    </div>
                </section>
            </main>
        </div>
    );
}