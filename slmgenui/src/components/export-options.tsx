/**
 * Export Options Component.
 * 
 * Export format selector for HuggingFace, ONNX, and Ollama.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

'use client'

import { useState } from 'react'
import {
    Download,
    Check,
    Smile,
    Zap,
    Box,
    Hammer
} from 'lucide-react'

interface ExportOption {
    id: string
    name: string
    description: string
    Icon: React.ElementType
    color: string
}

const EXPORT_OPTIONS: ExportOption[] = [
    {
        id: 'huggingface',
        name: 'HuggingFace Hub',
        description: 'Push to HF model repository',
        Icon: Smile,
        color: '#FFD21E'
    },
    {
        id: 'onnx',
        name: 'ONNX Format',
        description: 'For edge deployment',
        Icon: Zap,
        color: '#67b0e8'
    },
    {
        id: 'ollama',
        name: 'Ollama Modelfile',
        description: 'Run locally with Ollama',
        Icon: Box,
        color: '#8ccf7e'
    },
    {
        id: 'gguf',
        name: 'GGUF Quantized',
        description: 'For llama.cpp inference',
        Icon: Hammer,
        color: '#c47fd5'
    }
]

interface ExportOptionsProps {
    onExport: (format: string, config: Record<string, string>) => Promise<void>
    isExporting?: boolean
}

export function ExportOptions({ onExport, isExporting }: ExportOptionsProps) {
    const [selectedFormat, setSelectedFormat] = useState<string | null>(null)
    const [hfRepoName, setHfRepoName] = useState('')
    const [showConfig, setShowConfig] = useState(false)

    const handleExport = async () => {
        if (!selectedFormat) return

        const config: Record<string, string> = {}
        if (selectedFormat === 'huggingface' && hfRepoName) {
            config.repo_name = hfRepoName
        }

        await onExport(selectedFormat, config)
    }

    return (
        <div className="space-y-4">
            {/* Header */}
            <div className="flex items-center gap-2 text-[#dadada]">
                <Download className="w-5 h-5 text-[#8ccf7e]" />
                <span className="font-medium">Export Options</span>
            </div>

            {/* Format Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {EXPORT_OPTIONS.map((option) => {
                    const isSelected = selectedFormat === option.id

                    return (
                        <button
                            key={option.id}
                            onClick={() => {
                                setSelectedFormat(option.id)
                                setShowConfig(option.id === 'huggingface')
                            }}
                            className={`p-4 rounded-xl border text-left transition-all ${isSelected
                                ? 'bg-[#8ccf7e]/10 border-[#8ccf7e]'
                                : 'bg-[#1e2528] border-[#2d3437] hover:border-[#8ccf7e]/50'
                                }`}
                        >
                            <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-3 ${isSelected ? 'bg-[#8ccf7e]/20 text-[#8ccf7e]' : 'bg-[#141b1e] text-[#8a9899]'}`}>
                                <option.Icon className="w-5 h-5" />
                            </div>
                            <h4 className="font-medium text-[#dadada] text-sm">{option.name}</h4>
                            <p className="text-xs text-[#8a9899] mt-1">{option.description}</p>
                            {isSelected && (
                                <Check className="w-4 h-4 text-[#8ccf7e] absolute top-2 right-2" />
                            )}
                        </button>
                    )
                })}
            </div>

            {/* HuggingFace Config */}
            {showConfig && selectedFormat === 'huggingface' && (
                <div className="p-4 bg-[#1e2528] border border-[#2d3437] rounded-xl animate-in slide-in-from-top-2">
                    <label className="block text-sm text-[#8a9899] mb-2">
                        Repository Name (optional)
                    </label>
                    <input
                        type="text"
                        value={hfRepoName}
                        onChange={(e) => setHfRepoName(e.target.value)}
                        placeholder="username/model-name"
                        className="w-full px-3 py-2 bg-[#141b1e] border border-[#2d3437] rounded-lg text-[#dadada] placeholder-[#8a9899] focus:outline-none focus:border-[#8ccf7e]"
                    />
                </div>
            )}

            {/* Export Button */}
            {selectedFormat && (
                <button
                    onClick={handleExport}
                    disabled={isExporting}
                    className="flex items-center justify-center gap-2 w-full px-4 py-3 bg-gradient-to-r from-[#8ccf7e] to-[#6cbfbf] text-[#141b1e] font-semibold rounded-xl hover:shadow-lg hover:shadow-[#8ccf7e]/30 transition-all disabled:opacity-50"
                >
                    {isExporting ? (
                        <>Processing...</>
                    ) : (
                        <>
                            <Download className="w-5 h-5" />
                            Generate Export Script
                        </>
                    )}
                </button>
            )}
        </div>
    )
}
