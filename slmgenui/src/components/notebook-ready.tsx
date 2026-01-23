/**
 * Notebook Ready Component.
 * 
 * This is the victory screen! When the user gets here, their notebook
 * is ready for download. We want to make them feel accomplished, so
 * we've added:
 * - A big green checkmark
 * - Confetti explosion (because why not?)
 * - Clear download buttons
 * - Next steps instructions
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @contributor Vedant Singh Rajput <teleported0722@gmail.com>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

'use client';

import { Check, Download, ExternalLink, ClipboardList, ArrowLeft, Sparkles } from '@/components/icons';
import { Confetti } from '@/components/confetti';

interface NotebookReadyProps {
    filename: string;
    downloadUrl: string;
    colabUrl?: string | null;
    onStartOver: () => void;
}

export function NotebookReady({ filename, downloadUrl, colabUrl, onStartOver }: NotebookReadyProps) {
    // const downloadUrl = getDownloadUrl(sessionId); // Deprecated: Backend provides full URL with token

    return (
        <div className="text-center space-y-8">
            {/* Confetti celebration! */}
            <Confetti />
            {/* Success Icon */}
            <div className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-gradient-to-br from-[#8ccf7e] to-[#6cbfbf] shadow-xl shadow-[#8ccf7e]/30">
                <Check className="w-12 h-12 text-[#141b1e]" strokeWidth={3} />
            </div>

            <div>
                <h2 className="flex items-center justify-center gap-2 text-3xl font-bold text-[#dadada]">
                    Your Notebook is Ready!
                    <Sparkles className="w-7 h-7 text-[#e5c76b]" />
                </h2>
                <p className="text-[#8a9899] mt-2">Everything is set up for fine-tuning</p>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
                {/* Download Button */}
                <a
                    href={downloadUrl}
                    download={filename}
                    className="inline-flex items-center justify-center gap-3 px-8 py-4 bg-gradient-to-r from-[#8ccf7e] to-[#6cbfbf] text-[#141b1e] font-semibold rounded-xl hover:shadow-xl hover:shadow-[#8ccf7e]/30 hover:-translate-y-0.5 transition-all"
                >
                    <Download className="w-5 h-5" />
                    Download Notebook
                </a>

                {/* Colab Link if Available (and NOT localhost) */}
                {colabUrl && !colabUrl.includes('localhost') && !colabUrl.includes('127.0.0.1') ? (
                    <a
                        href={colabUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center justify-center gap-3 px-8 py-4 bg-[#e69875] text-[#141b1e] font-semibold rounded-xl hover:shadow-lg hover:shadow-[#e69875]/30 hover:-translate-y-0.5 transition-all"
                    >
                        <ExternalLink className="w-5 h-5" />
                        Open in Colab
                    </a>
                ) : colabUrl ? (
                    // Localhost fallback
                    <div className="flex flex-col items-center gap-2 text-sm text-[#e69875] bg-[#e69875]/10 px-4 py-2 rounded-lg border border-[#e69875]/20 max-w-xs">
                        <p className="font-semibold flex items-center gap-2">
                            <ExternalLink className="w-4 h-4" />
                            Running Locally?
                        </p>
                        <p className="opacity-80">
                            Google Colab cannot access localhost. Please download the notebook and upload it manually.
                        </p>
                        <a
                            href="https://colab.research.google.com"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="underline hover:text-[#dadada]"
                        >
                            Go to Google Colab
                        </a>
                    </div>
                ) : null}
            </div>

            {/* Instructions */}
            <div className="max-w-xl mx-auto bg-[#1e2528]/80 rounded-xl p-6 text-left border border-[#2d3437]">
                <h3 className="flex items-center gap-2 font-semibold text-[#dadada] mb-4">
                    <ClipboardList className="w-5 h-5 text-[#8ccf7e]" />
                    Next Steps
                </h3>
                <ol className="space-y-3 text-[#8a9899]">
                    <li className="flex gap-3">
                        <span className="flex-shrink-0 w-6 h-6 rounded-full bg-[#141b1e] border border-[#2d3437] flex items-center justify-center text-sm font-semibold text-[#dadada]">1</span>
                        <span>Open the notebook in Google Colab</span>
                    </li>
                    <li className="flex gap-3">
                        <span className="flex-shrink-0 w-6 h-6 rounded-full bg-[#141b1e] border border-[#2d3437] flex items-center justify-center text-sm font-semibold text-[#dadada]">2</span>
                        <span>Set runtime to <strong className="text-[#dadada]">T4 GPU</strong> (Runtime → Change runtime type)</span>
                    </li>
                    <li className="flex gap-3">
                        <span className="flex-shrink-0 w-6 h-6 rounded-full bg-[#141b1e] border border-[#2d3437] flex items-center justify-center text-sm font-semibold text-[#dadada]">3</span>
                        <span>Click <strong className="text-[#dadada]">Runtime → Run all</strong></span>
                    </li>
                    <li className="flex gap-3">
                        <span className="flex-shrink-0 w-6 h-6 rounded-full bg-[#141b1e] border border-[#2d3437] flex items-center justify-center text-sm font-semibold text-[#dadada]">4</span>
                        <span>Wait ~15 minutes for training to complete</span>
                    </li>
                    <li className="flex gap-3">
                        <span className="flex-shrink-0 w-6 h-6 rounded-full bg-[#141b1e] border border-[#2d3437] flex items-center justify-center text-sm font-semibold text-[#dadada]">5</span>
                        <span>Download your LoRA adapter from the Files panel</span>
                    </li>
                </ol>
            </div>

            {/* Start Over */}
            <button
                onClick={onStartOver}
                className="inline-flex items-center gap-2 text-[#8a9899] hover:text-[#dadada] transition-colors"
            >
                <ArrowLeft className="w-4 h-4" />
                Start over with new data
            </button>
        </div>
    );
}
