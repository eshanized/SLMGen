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
import { motion } from 'framer-motion';
import { Navbar, Footer } from '@/components/navigation';
import {
  Rocket,
  ArrowRight,
  Zap,
  Sparkles,
  FileText,
  Gauge,
  Download,
  Wand2,
  Brain,
  Check,
  ChevronRight,
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

// Quick benefits list
const BENEFITS = [
  '2x faster training with Unsloth',
  '70% less GPU memory usage',
  'No setup required',
  'Runs on free Google Colab',
];

export default function HomePage() {
  return (
    <div className="min-h-screen bg-[#0a0a0b] text-white">
      <Navbar />
      
      {/* Hero Section - Two Column Layout */}
      <main className="container mx-auto px-4 pt-24 pb-16">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          
          {/* Left Column - Content */}
          <motion.div
            initial="hidden"
            animate="visible"
            variants={containerVariants}
          >
            {/* V3.0.0 Badge */}
            <motion.div variants={itemVariants} className="mb-6">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-violet-600/20 via-purple-600/20 to-fuchsia-600/20 border border-violet-500/30">
                <Sparkles className="w-4 h-4 text-violet-400" />
                <span className="text-sm font-medium text-violet-300">V3.0.0 Released</span>
              </div>
            </motion.div>

            {/* Headline */}
            <motion.h1 variants={fadeInUp} className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight mb-6">
              <span className="text-white">Fine-tune </span>
              <span className="bg-gradient-to-r from-violet-400 via-fuchsia-400 to-cyan-400 bg-clip-text text-transparent">
                SLMs
              </span>
              <span className="text-zinc-300"> in seconds</span>
            </motion.h1>

            {/* Description */}
            <motion.p variants={itemVariants} className="text-lg text-zinc-400 mb-8 leading-relaxed">
              Upload your dataset, get AI-matched model recommendations, and receive a ready-to-run 
              <span className="text-violet-400"> Google Colab notebook</span>. 
              Powered by <span className="text-cyan-400">Unsloth</span> for 2x faster, 70% less memory training.
            </motion.p>

            {/* Benefits List */}
            <motion.div variants={itemVariants} className="mb-8">
              <div className="flex flex-wrap gap-4">
                {BENEFITS.map((benefit) => (
                  <div key={benefit} className="flex items-center gap-2 text-zinc-300">
                    <Check className="w-4 h-4 text-violet-400" />
                    <span className="text-sm">{benefit}</span>
                  </div>
                ))}
              </div>
            </motion.div>

            {/* CTA Buttons */}
            <motion.div variants={itemVariants} className="flex flex-col sm:flex-row gap-4">
              <Link
                href="/dashboard"
                className="inline-flex items-center justify-center gap-2.5 px-8 py-4 bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500 text-white font-semibold rounded-xl text-base shadow-lg shadow-violet-600/25 hover:shadow-violet-500/40 transition-all duration-300"
              >
                <Rocket className="w-5 h-5" />
                Start Fine-Tuning Free
                <ArrowRight className="w-4 h-4" />
              </Link>
              <a
                href="#features"
                className="inline-flex items-center justify-center gap-2.5 px-8 py-4 bg-zinc-900/60 hover:bg-zinc-800/80 text-zinc-300 hover:text-white font-medium rounded-xl border border-zinc-700 hover:border-zinc-600 transition-all duration-300"
              >
                See Features
              </a>
            </motion.div>

            {/* Quick Stats */}
            <motion.div variants={itemVariants} className="mt-10 pt-8 border-t border-zinc-800">
              <div className="grid grid-cols-3 gap-6">
                <div>
                  <div className="text-2xl font-bold text-white">18</div>
                  <div className="text-xs text-zinc-500">Models</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-white">128K</div>
                  <div className="text-xs text-zinc-500">Context</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-white">4</div>
                  <div className="text-xs text-zinc-500">Presets</div>
                </div>
              </div>
            </motion.div>
          </motion.div>

          {/* Right Column - Visual/Notebook Mockup */}
          <motion.div
            initial={{ opacity: 0, x: 40 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.3 }}
            className="relative"
          >
            {/* Background glow */}
            <div className="absolute inset-0 bg-gradient-to-br from-violet-600/20 via-fuchsia-600/10 to-cyan-600/20 rounded-3xl blur-3xl" />
            
            {/* Notebook Mockup */}
            <div className="relative bg-zinc-900/90 border border-zinc-800 rounded-2xl overflow-hidden backdrop-blur-sm">
              {/* Terminal Header */}
              <div className="flex items-center gap-2 px-4 py-3 bg-zinc-950 border-b border-zinc-800">
                <div className="w-3 h-3 rounded-full bg-red-500" />
                <div className="w-3 h-3 rounded-full bg-yellow-500" />
                <div className="w-3 h-3 rounded-full bg-green-500" />
                <div className="ml-4 px-3 py-1 bg-zinc-800 rounded-md text-xs text-zinc-400 font-mono">
                  training.ipynb
                </div>
              </div>
              
              {/* Terminal Body */}
              <div className="p-4 font-mono text-sm">
                {/* Code lines */}
                <div className="space-y-2">
                  <div className="text-zinc-500"># SLMGEN Generated Notebook</div>
                  <div><span className="text-purple-400">from</span> <span className="text-yellow-300">unsloth</span> <span className="text-purple-400">import</span> FastChatModel</div>
                  <div><span className="text-purple-400">import</span> <span className="text-yellow-300">torch</span></div>
                  <div className="h-4" />
                  <div><span className="text-blue-400">model</span>, <span className="text-blue-400">tokenizer</span> = FastChatModel.from_pretrained(</div>
                  <div className="pl-4"><span className="text-green-300">&quot;Qwen/Qwen2.5-3B-Instruct&quot;</span>,</div>
                  <div className="pl-4">max_seq_length=<span className="text-orange-400">2048</span>,</div>
                  <div className="pl-4">load_in_4bit=<span className="text-blue-400">True</span></div>
                  <div>)</div>
                  <div className="h-4" />
                  <div><span className="text-purple-400">from</span> <span className="text-yellow-300">trl</span> <span className="text-purple-400">import</span> SFTTrainer</div>
                  <div className="h-2" />
                  <div className="flex items-center gap-2 text-zinc-400">
                    <span className="w-4 h-4 rounded-full bg-green-500" />
                    <span>Training started...</span>
                  </div>
                </div>

                {/* Live stats bar */}
                <div className="mt-6 p-3 bg-zinc-950 rounded-lg border border-zinc-800">
                  <div className="flex justify-between text-xs mb-2">
                    <span className="text-zinc-500">Step</span>
                    <span className="text-zinc-300">150/1000</span>
                  </div>
                  <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                    <div className="h-full w-[15%] bg-gradient-to-r from-violet-500 to-fuchsia-500 rounded-full" />
                  </div>
                  <div className="flex justify-between text-xs mt-2">
                    <span className="text-zinc-500">Loss: 0.84</span>
                    <span className="text-zinc-500">LR: 2e-4</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Floating elements */}
            <motion.div
              animate={{ y: [0, -8, 0] }}
              transition={{ duration: 3, repeat: Infinity }}
              className="absolute -bottom-6 -right-6 px-4 py-2 bg-zinc-900 border border-zinc-800 rounded-xl shadow-xl"
            >
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-amber-400" />
                <span className="text-sm text-zinc-300">Ready to run</span>
              </div>
            </motion.div>

            <motion.div
              animate={{ y: [0, 8, 0] }}
              transition={{ duration: 4, repeat: Infinity }}
              className="absolute -top-4 -left-4 px-3 py-1.5 bg-violet-600 rounded-lg"
            >
              <span className="text-xs font-medium text-white">V3.0.0</span>
            </motion.div>
          </motion.div>
        </div>
      </main>

      {/* Features Section */}
      <section id="features" className="py-16">
        <div className="container mx-auto px-4">
          <motion.div
            className="max-w-5xl mx-auto"
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold text-white mb-3">
                What&apos;s New in V3.0.0
              </h2>
              <p className="text-zinc-400">
                More models, more formats, more flexibility
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
              {FEATURES.map((feature) => (
                <motion.div
                  key={feature.title}
                  variants={itemVariants}
                  className={`p-5 rounded-2xl ${feature.bgColor} border ${feature.borderColor} backdrop-blur-sm hover:scale-[1.02] transition-transform`}
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
        </div>
      </section>

      {/* Models Showcase */}
      <section className="py-12 border-y border-zinc-800/50">
        <div className="container mx-auto px-4">
          <div className="flex flex-wrap justify-center gap-3">
            {MODELS.map((model) => (
              <div 
                key={model.name}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-zinc-900/60 border border-zinc-800"
              >
                <div className={`w-2 h-2 rounded-full ${model.color}`} />
                <span className="text-sm font-medium text-zinc-200">{model.name}</span>
                <span className="text-xs text-zinc-500">{model.size}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <motion.div
            className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto"
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
        </div>
      </section>

      {/* How It Works */}
      <section className="py-16 bg-zinc-900/20">
        <div className="container mx-auto px-4">
          <div className="max-w-5xl mx-auto">
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
                    <ChevronRight className="hidden md:block absolute top-1/2 -right-3 w-5 h-5 text-zinc-700 transform -translate-y-1/2" />
                  )}
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <motion.div
            className="text-center py-16 px-8 rounded-3xl bg-gradient-to-br from-violet-900/20 via-fuchsia-900/10 to-cyan-900/20 border border-violet-500/20"
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl font-bold text-white mb-4">
              Ready to fine-tune?
            </h2>
            <p className="text-zinc-400 mb-8 max-w-lg mx-auto">
              Start for free. No setup required. Runs on Google Colab with free GPU access.
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
        </div>
      </section>

      <Footer />
    </div>
  );
}