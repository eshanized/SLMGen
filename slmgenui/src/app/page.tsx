/**
 * SLMGEN Landing Page.
 * 
 * Hero section with stats and CTA to dashboard.
 * Everblush themed with Lucide icons.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

import Link from 'next/link';
import {
  Rocket,
  ArrowRight,
  Upload,
  Settings,
  Target,
  Zap,
  Github,
  Mail,
  Diamond,
  Sparkles,
  Star,
  Hexagon,
  CircleDot,
} from '@/components/icons';

// Supported models to Showcase
const MODELS = [
  { name: 'Phi-4 Mini', size: '3.8B', Icon: Diamond, color: 'text-[#67b0e8]' },
  { name: 'Phi-3.5 Mini', size: '3.8B', Icon: Diamond, color: 'text-[#67b0e8]' },
  { name: 'Llama 3.2 3B', size: '3B', Icon: CircleDot, color: 'text-[#e5c76b]' },
  { name: 'Llama 3.2 1B', size: '1B', Icon: CircleDot, color: 'text-[#e5c76b]' },
  { name: 'Gemma 2', size: '2B', Icon: Sparkles, color: 'text-[#c47fd5]' },
  { name: 'Qwen 2.5', size: '3B', Icon: Star, color: 'text-[#8ccf7e]' },
  { name: 'Mistral', size: '7B', Icon: Hexagon, color: 'text-[#6cbfbf]' },
  { name: 'SmolLM2', size: '1.7B', Icon: Sparkles, color: 'text-[#e69875]' },
  { name: 'TinyLlama', size: '1.1B', Icon: CircleDot, color: 'text-[#8ccf7e]' },
  { name: 'DeepSeek Coder', size: '1.3B', Icon: Diamond, color: 'text-[#c47fd5]' },
  { name: 'StableLM', size: '3B', Icon: Hexagon, color: 'text-[#67b0e8]' },
];

// Key Stats - Reflecting actual SLMGEN capabilities
const STATS = [
  { value: '11', label: 'SLM Models', sublabel: 'from 1B to 7B' },
  { value: '6', label: 'Task Types', sublabel: 'classify to generation' },
  { value: '100%', label: 'Free', sublabel: 'runs on Colab T4' },
  { value: '6', label: 'Deploy Targets', sublabel: 'cloud to mobile' },
];

// How it works steps - Matching actual SLMGEN workflow
const STEPS = [
  { step: '1', title: 'Upload', desc: 'Drop your ChatML JSONL dataset', Icon: Upload },
  { step: '2', title: 'Analyze', desc: 'Auto-detect tokens, quality, format', Icon: Settings },
  { step: '3', title: 'Match', desc: 'AI scores models by task + deploy fit', Icon: Target },
  { step: '4', title: 'Generate', desc: 'Get your self-contained Colab notebook', Icon: Rocket },
];

export default function HomePage() {
  return (
    <div className="min-h-screen hero-gradient">
      {/* Header */}
      <header className="container mx-auto px-4 py-6">
        <nav className="flex items-center justify-between">
          <div className="flex items-center gap-8">
            {/* Logo */}
            <div className="flex items-center gap-2">
              <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-[#8ccf7e] to-[#6cbfbf] flex items-center justify-center">
                <Rocket className="w-5 h-5 text-[#141b1e]" />
              </div>
              <span className="text-xl font-bold text-[#dadada] tracking-wide">SLMGEN</span>
            </div>

            {/* Navigation Menu */}
            <div className="hidden md:flex items-center gap-6">
              <a href="#features" className="text-[#8a9899] hover:text-[#dadada] transition-colors text-sm font-medium">
                Features
              </a>
              <a href="#models" className="text-[#8a9899] hover:text-[#dadada] transition-colors text-sm font-medium">
                Models
              </a>
              <a href="#how-it-works" className="text-[#8a9899] hover:text-[#dadada] transition-colors text-sm font-medium">
                How It Works
              </a>
              <Link href="/about" className="text-[#8a9899] hover:text-[#dadada] transition-colors text-sm font-medium">
                About
              </Link>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <a
              href="https://github.com/eshanized/slmgen"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-[#8a9899] hover:text-[#dadada] transition-colors"
            >
              <Github className="w-5 h-5" />
              <span className="hidden sm:inline">GitHub</span>
            </a>
            <Link
              href="/dashboard"
              className="px-5 py-2.5 bg-gradient-to-r from-[#8ccf7e] to-[#6cbfbf] text-[#141b1e] rounded-lg font-semibold hover:shadow-lg hover:shadow-[#8ccf7e]/30 transition-all hover:-translate-y-0.5"
            >
              Get Started
            </Link>
          </div>
        </nav>
      </header>

      {/* Hero Section */}
      <main className="container mx-auto px-4 py-20">
        <div className="text-center max-w-4xl mx-auto">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-[#1e2528]/80 rounded-full border border-[#2d3437] mb-8">
            <span className="w-2 h-2 bg-[#8ccf7e] rounded-full animate-pulse" />
            <span className="text-sm text-[#8a9899]">Powered by Unsloth & LoRA</span>
          </div>

          {/* Headline */}
          <h1 className="text-5xl md:text-7xl font-bold text-[#dadada] mb-6 leading-tight">
            Your Data.<br />
            <span className="gradient-text">Best Model. Matched.</span>
          </h1>

          <p className="text-xl text-[#8a9899] max-w-2xl mx-auto mb-10">
            SLMGEN analyzes your dataset and scores 11 small language models
            to find the perfect fit for your task and deployment target.<br />
            <strong className="text-[#dadada]">One notebook. Zero setup. Ready to train.</strong>
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/dashboard"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-gradient-to-r from-[#8ccf7e] to-[#6cbfbf] text-[#141b1e] font-semibold rounded-xl text-lg hover:shadow-xl hover:shadow-[#8ccf7e]/30 hover:-translate-y-1 transition-all"
            >
              Start Fine-Tuning
              <ArrowRight className="w-5 h-5" />
            </Link>
            <a
              href="#how-it-works"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-[#1e2528] text-[#dadada] font-semibold rounded-xl text-lg border border-[#2d3437] hover:border-[#8ccf7e] hover:bg-[#232a2d] transition-all"
            >
              How it Works
            </a>
          </div>
        </div>

        {/* Stats / Features */}
        <div id="features" className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-20 max-w-4xl mx-auto">
          {STATS.map((stat) => (
            <div key={stat.label} className="text-center p-6 rounded-xl glass">
              <div className="text-4xl font-bold gradient-text">{stat.value}</div>
              <div className="text-[#dadada] font-medium mt-1">{stat.label}</div>
              <div className="text-sm text-[#8a9899]">{stat.sublabel}</div>
            </div>
          ))}
        </div>

        {/* Supported Models */}
        <div id="models" className="mt-24 text-center">
          <h2 className="text-2xl font-bold text-[#dadada] mb-8">Supported Models</h2>
          <div className="flex flex-wrap justify-center gap-4">
            {MODELS.map((model) => (
              <div
                key={model.name}
                className="flex items-center gap-3 px-5 py-3 bg-[#1e2528]/80 rounded-xl border border-[#2d3437] hover:border-[#8ccf7e]/50 transition-all hover:-translate-y-0.5"
              >
                <model.Icon className={`w-6 h-6 ${model.color}`} />
                <div className="text-left">
                  <div className="font-semibold text-[#dadada]">{model.name}</div>
                  <div className="text-sm text-[#8a9899]">{model.size}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* How it Works */}
        <div id="how-it-works" className="mt-24 max-w-5xl mx-auto">
          <h2 className="text-2xl font-bold text-[#dadada] mb-12 text-center">How It Works</h2>
          <div className="grid md:grid-cols-4 gap-6">
            {STEPS.map((item, idx) => (
              <div key={item.step} className="relative p-6 rounded-xl glass text-center group hover:-translate-y-1 transition-all">
                <div className="w-14 h-14 mx-auto mb-4 rounded-xl bg-gradient-to-br from-[#8ccf7e]/20 to-[#c47fd5]/20 flex items-center justify-center group-hover:from-[#8ccf7e]/30 group-hover:to-[#c47fd5]/30 transition-all">
                  <item.Icon className="w-7 h-7 text-[#8ccf7e]" />
                </div>
                <div className="text-lg font-semibold text-[#dadada] mb-2">{item.title}</div>
                <div className="text-sm text-[#8a9899]">{item.desc}</div>
                {idx < STEPS.length - 1 && (
                  <div className="hidden md:flex absolute top-1/2 -right-3 w-6 items-center justify-center text-[#2d3437]">
                    <ArrowRight className="w-4 h-4" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Features Section */}
        <div className="mt-24 max-w-5xl mx-auto">
          <h2 className="text-2xl font-bold text-[#dadada] mb-12 text-center">Why SLMGEN?</h2>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="p-6 rounded-xl glass-glow">
              <div className="w-12 h-12 rounded-lg bg-[#8ccf7e]/10 flex items-center justify-center mb-4">
                <Target className="w-6 h-6 text-[#8ccf7e]" />
              </div>
              <h3 className="text-lg font-semibold text-[#dadada] mb-2">100-Point Scoring</h3>
              <p className="text-[#8a9899] text-sm">
                AI scores each model: 50pts task fit, 30pts deployment, 20pts data characteristics. Best match wins.
              </p>
            </div>
            <div className="p-6 rounded-xl glass-glow">
              <div className="w-12 h-12 rounded-lg bg-[#67b0e8]/10 flex items-center justify-center mb-4">
                <Zap className="w-6 h-6 text-[#67b0e8]" />
              </div>
              <h3 className="text-lg font-semibold text-[#dadada] mb-2">Self-Contained Notebooks</h3>
              <p className="text-[#8a9899] text-sm">
                Your dataset is embedded directly in the notebook. One file. No uploads needed. Just run.
              </p>
            </div>
            <div className="p-6 rounded-xl glass-glow">
              <div className="w-12 h-12 rounded-lg bg-[#c47fd5]/10 flex items-center justify-center mb-4">
                <Sparkles className="w-6 h-6 text-[#c47fd5]" />
              </div>
              <h3 className="text-lg font-semibold text-[#dadada] mb-2">Cloud to Mobile</h3>
              <p className="text-[#8a9899] text-sm">
                Deploy anywhere: A100 cloud, local server, desktop, edge devices, mobile, or even browser.
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="container mx-auto px-4 py-8 mt-20 border-t border-[#2d3437]">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="text-[#8a9899] text-sm">
            © 2026 Eshan Roy. MIT License.
          </div>
          <div className="flex items-center gap-6 text-sm">
            <Link href="/terms" className="text-[#8a9899] hover:text-[#dadada] transition-colors">
              Terms
            </Link>
            <Link href="/privacy" className="text-[#8a9899] hover:text-[#dadada] transition-colors">
              Privacy
            </Link>
            <a href="https://github.com/eshanized/slmgen" className="flex items-center gap-2 text-[#8a9899] hover:text-[#dadada] transition-colors">
              <Github className="w-4 h-4" />
              GitHub
            </a>
            <a href="mailto:eshanized@proton.me" className="flex items-center gap-2 text-[#8a9899] hover:text-[#dadada] transition-colors">
              <Mail className="w-4 h-4" />
              Contact
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
