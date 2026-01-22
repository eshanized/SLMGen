/**
 * SLMGEN Landing Page.
 * 
 * Hero section with stats and CTA to dashboard.
 * Everblush themed with Lucide icons.
 * Enhanced with Framer Motion animations and text diffusion effects.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @contributor Vedant Singh Rajput <teleported0722@gmail.com>
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

// Key Stats
const STATS = [
  { value: '11', label: 'SLM Models', sublabel: 'from 1B to 7B' },
  { value: '6', label: 'Task Types', sublabel: 'classify to generation' },
  { value: '100%', label: 'Free', sublabel: 'runs on Colab T4' },
  { value: '6', label: 'Deploy Targets', sublabel: 'cloud to mobile' },
];

// How it works steps
const STEPS = [
  { step: '1', title: 'Upload', desc: 'Drop your ChatML JSONL dataset', Icon: Upload },
  { step: '2', title: 'Analyze', desc: 'Auto-detect tokens, quality, format', Icon: Settings },
  { step: '3', title: 'Match', desc: 'AI scores models by task + deploy fit', Icon: Target },
  { step: '4', title: 'Generate', desc: 'Get your self-contained Colab notebook', Icon: Rocket },
];

// Animation variants
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5 }
  },
};

const diffusionVariant: Variants = {
  hidden: { filter: 'blur(12px)', opacity: 0, y: 10 },
  visible: {
    filter: 'blur(0px)',
    opacity: 1,
    y: 0,
    transition: { duration: 1.2, ease: "easeOut" }
  }
};

export default function HomePage() {
  return (
    <div className="min-h-screen hero-gradient overflow-hidden selection:bg-[#8ccf7e] selection:text-[#141b1e]">
      {/* Navigation */}
      <Navbar />

      {/* Hero Section */}
      <main className="container mx-auto px-4 py-20 relative z-10">
        <motion.div
          className="text-center max-w-4xl mx-auto"
          initial="hidden"
          animate="visible"
          variants={containerVariants}
        >
          {/* Badge */}
          <motion.div variants={itemVariants} className="inline-flex items-center gap-2 px-4 py-2 bg-[#1e2528]/80 rounded-full border border-[#2d3437] mb-8 backdrop-blur-sm">
            <span className="w-2 h-2 bg-[#8ccf7e] rounded-full animate-pulse" />
            <span className="text-sm text-[#8a9899]">Powered by Unsloth & LoRA</span>
          </motion.div>

          {/* Headline with Diffusion Effect */}
          <motion.h1 className="text-5xl md:text-6xl lg:text-7xl font-bold text-[#dadada] mb-6 leading-[1.1] tracking-tight">
            <motion.span variants={diffusionVariant} className="inline-block">Your Data.</motion.span><br />
            <motion.span
              variants={diffusionVariant}
              className="gradient-text text-glow inline-block"
            >
              Best Model. Matched.
            </motion.span>
          </motion.h1>

          <motion.p variants={itemVariants} className="text-xl text-[#8a9899] max-w-2xl mx-auto mb-10 leading-relaxed">
            SLMGEN analyzes your dataset and scores 11 small language models
            to find the perfect fit for your task and deployment target.<br />
            <strong className="text-[#dadada]">One notebook. Zero setup. Ready to train.</strong>
          </motion.p>

          {/* CTA Buttons */}
          <motion.div variants={itemVariants} className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/dashboard"
              className="group inline-flex items-center justify-center gap-2 px-8 py-4 bg-gradient-to-r from-[#8ccf7e] to-[#6cbfbf] text-[#141b1e] font-bold rounded-xl text-lg shadow-lg shadow-[#8ccf7e]/20 hover:shadow-[#8ccf7e]/40 hover:-translate-y-1 transition-all duration-300"
            >
              Start Fine-Tuning
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Link>
            <a
              href="#how-it-works"
              className="group inline-flex items-center justify-center gap-2 px-8 py-4 bg-[#1e2528]/80 text-[#dadada] font-semibold rounded-xl text-lg border border-[#2d3437] hover:border-[#8ccf7e] hover:bg-[#232a2d] transition-all duration-300"
            >
              How it Works
            </a>
          </motion.div>
        </motion.div>

        {/* Stats / Features */}
        <motion.div
          id="features"
          className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6 mt-24 max-w-5xl mx-auto"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.2 }}
        >
          {STATS.map((stat) => (
            <motion.div
              key={stat.label}
              className="text-center p-6 rounded-2xl glass-interactive"
              whileHover={{ scale: 1.05 }}
            >
              <div className="text-4xl font-bold gradient-text mb-2">{stat.value}</div>
              <div className="text-[#dadada] font-medium text-lg">{stat.label}</div>
              <div className="text-sm text-[#8a9899] mt-1">{stat.sublabel}</div>
            </motion.div>
          ))}
        </motion.div>

        {/* Supported Models */}
        <div id="models" className="mt-32 text-center">
          <motion.h2
            className="text-3xl font-bold text-[#dadada] mb-10"
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
          >
            Supported Models
          </motion.h2>
          <motion.div
            className="flex flex-wrap justify-center gap-4 max-w-6xl mx-auto"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            variants={containerVariants}
          >
            {MODELS.map((model) => (
              <motion.div
                key={model.name}
                variants={itemVariants}
                className="flex items-center gap-3 px-5 py-3 bg-[#1e2528]/60 rounded-xl border border-[#2d3437] hover:border-[#8ccf7e]/50 hover:bg-[#1e2528]/80 transition-all cursor-default"
                whileHover={{ scale: 1.05, y: -2 }}
              >
                <model.Icon className={`w-5 h-5 ${model.color}`} />
                <div className="text-left">
                  <div className="font-semibold text-[#dadada]">{model.name}</div>
                  <div className="text-xs text-[#8a9899] font-mono">{model.size}</div>
                </div>
              </motion.div>
            ))}
          </motion.div>
        </div>

        {/* How it Works */}
        <div id="how-it-works" className="mt-32 max-w-6xl mx-auto">
          <motion.h2
            className="text-3xl font-bold text-[#dadada] mb-16 text-center"
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
          >
            How It Works
          </motion.h2>
          <div className="grid md:grid-cols-4 gap-6">
            {STEPS.map((item, idx) => (
              <motion.div
                key={item.step}
                className="relative p-8 rounded-2xl glass-interactive text-center group"
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: idx * 0.1 }}
                whileHover={{ y: -5 }}
              >
                <div className="w-16 h-16 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-[#8ccf7e]/10 to-[#c47fd5]/10 flex items-center justify-center group-hover:from-[#8ccf7e]/20 group-hover:to-[#c47fd5]/20 transition-all border border-[#2d3437] group-hover:border-[#8ccf7e]/30">
                  <item.Icon className="w-8 h-8 text-[#8ccf7e]" />
                </div>
                <div className="text-xl font-bold text-[#dadada] mb-3">{item.title}</div>
                <div className="text-[#8a9899] leading-relaxed">{item.desc}</div>
                {idx < STEPS.length - 1 && (
                  <div className="hidden md:flex absolute top-1/2 -right-3 w-6 items-center justify-center text-[#2d3437] transform -translate-y-1/2 z-10">
                    <ArrowRight className="w-5 h-5" />
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </div>

        {/* Features Section */}
        <div className="mt-32 max-w-6xl mx-auto mb-20">
          <motion.h2
            className="text-3xl font-bold text-[#dadada] mb-16 text-center"
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
          >
            Why SLMGEN?
          </motion.h2>
          <div className="grid md:grid-cols-3 gap-8">
            <motion.div
              className="p-8 rounded-2xl glass-glow"
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.1 }}
            >
              <div className="w-14 h-14 rounded-2xl bg-[#8ccf7e]/10 flex items-center justify-center mb-6">
                <Target className="w-7 h-7 text-[#8ccf7e]" />
              </div>
              <h3 className="text-xl font-bold text-[#dadada] mb-3">100-Point Scoring</h3>
              <p className="text-[#8a9899] leading-relaxed">
                AI scores each model based on 3 distinct factors: <span className="text-[#dadada]">Task Fit (50pts)</span>, <span className="text-[#dadada]">Deployment Target (30pts)</span>, and <span className="text-[#dadada]">Data Characteristics (20pts)</span>.
              </p>
            </motion.div>

            <motion.div
              className="p-8 rounded-2xl glass-glow"
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.2 }}
            >
              <div className="w-14 h-14 rounded-2xl bg-[#67b0e8]/10 flex items-center justify-center mb-6">
                <Zap className="w-7 h-7 text-[#67b0e8]" />
              </div>
              <h3 className="text-xl font-bold text-[#dadada] mb-3">Self-Contained Notebooks</h3>
              <p className="text-[#8a9899] leading-relaxed">
                No messy uploads. Your dataset is <span className="text-[#dadada]">base64-embedded</span> directly into the generated notebook. Just open in Colab and hit &quot;Run All&quot;.
              </p>
            </motion.div>

            <motion.div
              className="p-8 rounded-2xl glass-glow"
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.3 }}
            >
              <div className="w-14 h-14 rounded-2xl bg-[#c47fd5]/10 flex items-center justify-center mb-6">
                <Sparkles className="w-7 h-7 text-[#c47fd5]" />
              </div>
              <h3 className="text-xl font-bold text-[#dadada] mb-3">Cloud to Mobile</h3>
              <p className="text-[#8a9899] leading-relaxed">
                Optimized export targets for <span className="text-[#dadada]">GGUF (Llama.cpp)</span>, <span className="text-[#dadada]">Ollama</span>, and <span className="text-[#dadada]">vLLM</span>. Deploy anywhere from A100s to edge devices.
              </p>
            </motion.div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <Footer />
    </div>
  );
}
