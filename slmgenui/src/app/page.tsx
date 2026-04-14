/**
 * SLMGEN V3.0.0 Landing Page.
 * 
 * Completely redesigned with a fresh, modern look.
 * V3.0.0 banner, new hero, feature highlights.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

'use client';

import Link from 'next/link';
import { motion, Variants } from 'framer-motion';
import { Navbar, Footer } from '@/components/navigation';
import {
  Rocket,
  ArrowRight,
  Upload,
  Settings,
  Target,
  Zap,
  Sparkles,
  FileText,
  Gauge,
  Download,
  Wand2,
  Brain,
  Cpu,
  Layers,
  Terminal,
  Cloud,
  Server,
} from '@/components/icons';

// Animation variants
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.08, delayChildren: 0.15 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 25 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5 } },
};

const fadeInUp = {
  hidden: { opacity: 0, y: 40 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.7 } },
};

const floatVariant = {
  initial: { y: 0 },
  animate: { y: [0, -12, 0], transition: { duration: 3, repeat: Infinity } }
};

// V3.0.0 Features
const FEATURES = [
  {
    icon: FileText,
    title: 'Dataset Converter',
    description: 'CSV, TSV, JSON, Alpaca, ShareGPT → ChatML',
    color: 'from-blue-500 to-cyan-500',
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-500/30',
  },
  {
    icon: Gauge,
    title: 'Training Presets',
    description: 'Quick Demo, Production, Edge Optimize',
    color: 'from-purple-500 to-pink-500',
    bgColor: 'bg-purple-500/10',
    borderColor: 'border-purple-500/30',
  },
  {
    icon: Download,
    title: 'Export Pipeline',
    description: 'Ollama, GGUF, vLLM, HuggingFace',
    color: 'from-emerald-500 to-teal-500',
    bgColor: 'bg-emerald-500/10',
    borderColor: 'border-emerald-500/30',
  },
  {
    icon: Brain,
    title: '18 Models',
    description: 'Up to 84B params, 128K context',
    color: 'from-amber-500 to-orange-500',
    bgColor: 'bg-amber-500/10',
    borderColor: 'border-amber-500/30',
  },
];

// Models showcase
const MODELS = [
  { name: 'Qwen 3.5', size: '32B', color: 'bg-green-500' },
  { name: 'Llama 3.3', size: '8B', color: 'bg-yellow-500' },
  { name: 'DeepSeek V3', size: '84B', color: 'bg-purple-500' },
  { name: 'Mistral Small 3', size: '24B', color: 'bg-cyan-500' },
  { name: 'Gemma 3', size: '4B', color: 'bg-pink-500' },
  { name: 'SmolLM3', size: '3B', color: 'bg-orange-500' },
];

// Stats
const STATS = [
  { value: '18', label: 'SLM Models', desc: 'Latest 2026 models' },
  { value: '128K', label: 'Max Context', desc: 'Token context window' },
  { value: '4', label: 'Presets', desc: 'Quick to Production' },
  { value: '4', label: 'Export Formats', desc: 'Ollama, GGUF, vLLM, HF' },
];

// How it works
const STEPS = [
  { num: '01', title: 'Upload', desc: 'Drop your dataset or convert from CSV/JSON' },
  { num: '02', title: 'Analyze', desc: 'Auto-detect quality, format, characteristics' },
  { num: '03', title: 'Match', desc: 'AI scores 18 models for your task & data' },
  { num: '04', title: 'Generate', desc: 'Get ready-to-run Colab notebook' },
];

export default function HomePage() {
  return (
    <div className="min-h-screen bg-[#0a0a0b] text-white">
      <Navbar />
      
      {/* V3.0.0 Banner */}
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="pt-20 px-4 text-center"
      >
        <div className="inline-flex items-center gap-3 px-5 py-2.5 rounded-full bg-gradient-to-r from-violet-600/20 via-purple-600/20 to-fuchsia-600/20 border border-violet-500/30 backdrop-blur-sm">
          <Sparkles className="w-4 h-4 text-violet-400" />
          <span className="text-sm font-medium bg-gradient-to-r from-violet-300 to-fuchsia-300 bg-clip-text text-transparent">
            New in V3.0.0
          </span>
          <span className="text-xs text-zinc-400">Dataset Converter • Training Presets • Export Pipeline</span>
        </div>
      </motion.div>

      {/* Hero Section */}
      <main className="container mx-auto px-4 py-16 relative">
        {/* Background glow effects */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-1/4 -left-32 w-96 h-96 bg-violet-600/20 rounded-full blur-[128px]" />
          <div className="absolute top-1/3 -right-32 w-96 h-96 bg-cyan-600/15 rounded-full blur-[128px]" />
        </div>

        <motion.div
          className="text-center max-w-4xl mx-auto relative z-10"
          initial="hidden"
          animate="visible"
          variants={containerVariants}
        >
          {/* Main Headline */}
          <motion.h1 
            variants={fadeInUp}
            className="text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight mb-6"
          >
            <span className="text-white">Fine-tune </span>
            <span className="bg-gradient-to-r from-violet-400 via-fuchsia-400 to-cyan-400 bg-clip-text text-transparent">
              SLMs
            </span>
            <br />
            <span className="text-zinc-300">in seconds.</span>
          </motion.h1>

          <motion.p 
            variants={itemVariants}
            className="text-lg md:text-xl text-zinc-400 max-w-2xl mx-auto mb-10 leading-relaxed"
          >
            Upload your dataset, get AI-matched model recommendations, and receive a ready-to-run 
            <span className="text-violet-400"> Google Colab notebook</span>. 
            Powered by <span className="text-cyan-400">Unsloth</span> for 2x faster, 70% less memory training.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div 
            variants={itemVariants}
            className="flex flex-col sm:flex-row gap-4 justify-center mb-16"
          >
            <Link
              href="/dashboard"
              className="group inline-flex items-center justify-center gap-2.5 px-8 py-4 bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500 text-white font-semibold rounded-xl text-base shadow-lg shadow-violet-600/25 hover:shadow-violet-500/40 transition-all duration-300"
            >
              <Rocket className="w-5 h-5" />
              Start Fine-Tuning Free
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>
            <a
              href="#features"
              className="inline-flex items-center justify-center gap-2.5 px-8 py-4 bg-zinc-900/60 hover:bg-zinc-800/80 text-zinc-300 hover:text-white font-medium rounded-xl border border-zinc-700 hover:border-zinc-600 transition-all duration-300"
            >
              See What's New
            </a>
          </motion.div>

          {/* Floating model cards */}
          <motion.div 
            variants={floatVariant}
            initial="initial"
            animate="animate"
            className="flex justify-center gap-3 mb-16"
          >
            {MODELS.map((model) => (
              <div 
                key={model.name}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-zinc-900/80 border border-zinc-800 backdrop-blur-sm"
              >
                <div className={`w-2 h-2 rounded-full ${model.color}`} />
                <span className="text-sm font-medium text-zinc-200">{model.name}</span>
                <span className="text-xs text-zinc-500">{model.size}</span>
              </div>
            ))}
          </motion.div>
        </motion.div>

        {/* V3.0.0 Features Grid */}
        <motion.div
          id="features"
          className="max-w-5xl mx-auto mt-20"
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-white mb-3">
              V3.0.0 Features
            </h2>
            <p className="text-zinc-400">
              More models, more formats, more flexibility
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            {FEATURES.map((feature, idx) => (
              <motion.div
                key={feature.title}
                variants={itemVariants}
                className={`p-5 rounded-2xl ${feature.bgColor} border ${feature.borderColor} backdrop-blur-sm`}
              >
                <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${feature.color} flex items-center justify-center mb-4`}>
                  <feature.icon className="w-5 h-5 text-white" />
                </div>
                <h3 className="text-base font-semibold text-white mb-1.5">{feature.title}</h3>
                <p className="text-sm text-zinc-400 leading-relaxed">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Stats Section */}
        <motion.div
          className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto mt-16"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.2 }}
        >
          {STATS.map((stat) => (
            <div 
              key={stat.label}
              className="text-center p-5 rounded-xl bg-zinc-900/40 border border-zinc-800"
            >
              <div className="text-3xl font-bold bg-gradient-to-r from-white to-zinc-400 bg-clip-text text-transparent">
                {stat.value}
              </div>
              <div className="text-sm font-medium text-zinc-300 mt-1">{stat.label}</div>
              <div className="text-xs text-zinc-500">{stat.desc}</div>
            </div>
          ))}
        </motion.div>

        {/* How It Works */}
        <div className="max-w-5xl mx-auto mt-24">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-white mb-3">
              How It Works
            </h2>
            <p className="text-zinc-400">
              Four simple steps to your fine-tuned model
            </p>
          </div>

          <div className="grid md:grid-cols-4 gap-6">
            {STEPS.map((step, idx) => (
              <motion.div
                key={step.num}
                className="relative p-6 rounded-2xl bg-zinc-900/40 border border-zinc-800 text-center"
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: idx * 0.1 }}
              >
                <div className="text-5xl font-bold text-zinc-700/50 mb-3">{step.num}</div>
                <h3 className="text-lg font-semibold text-white mb-2">{step.title}</h3>
                <p className="text-sm text-zinc-400 leading-relaxed">{step.desc}</p>
                {idx < STEPS.length - 1 && (
                  <ArrowRight className="hidden md:block absolute top-1/2 -right-3 w-5 h-5 text-zinc-700 transform -translate-y-1/2" />
                )}
              </motion.div>
            ))}
          </div>
        </div>

        {/* CTA Section */}
        <motion.div
          className="text-center mt-24 py-16"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to fine-tune?
          </h2>
          <p className="text-zinc-400 mb-8">
            Start for free. No setup required. Runs on Google Colab.
          </p>
          <Link
            href="/dashboard"
            className="inline-flex items-center justify-center gap-2.5 px-8 py-4 bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500 text-white font-semibold rounded-xl shadow-lg shadow-violet-600/25 transition-all"
          >
            <Wand2 className="w-5 h-5" />
            Start Fine-Tuning Now
            <ArrowRight className="w-4 h-4" />
          </Link>
        </motion.div>
      </main>

      <Footer />
    </div>
  );
}