/**
 * Training Configuration Component.
 * 
 * Allows selection of training presets and custom hyperparameters.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

'use client'

import { useState } from 'react'
import {
    Settings,
    Zap,
    Target,
    Award,
    SlidersHorizontal,
    ChevronRight,
    Info
} from '@/components/icons'
import { Tooltip } from '@/components/ui/tooltip'

interface TrainingConfig {
    preset: string
    lora_rank: number
    lora_alpha: number
    learning_rate: number
    num_epochs: number
    batch_size: number
    max_seq_length: number
    warmup_ratio: number
}

interface TrainingConfigProps {
    value: TrainingConfig
    onChange: (config: TrainingConfig) => void
    totalTokens?: number
}

const PRESETS = [
    {
        id: 'fast',
        name: 'Fast',
        icon: Zap,
        color: 'text-[#e5c76b]',
        description: '~15 min training',
        config: { lora_rank: 8, learning_rate: 5e-4, num_epochs: 1, batch_size: 8 }
    },
    {
        id: 'balanced',
        name: 'Balanced',
        icon: Target,
        color: 'text-[#8ccf7e]',
        description: '~45 min, best for most',
        config: { lora_rank: 16, learning_rate: 2e-4, num_epochs: 3, batch_size: 4 }
    },
    {
        id: 'quality',
        name: 'Quality',
        icon: Award,
        color: 'text-[#c47fd5]',
        description: '~2 hours, maximum quality',
        config: { lora_rank: 32, learning_rate: 1e-4, num_epochs: 5, batch_size: 2 }
    },
    {
        id: 'custom',
        name: 'Custom',
        icon: SlidersHorizontal,
        color: 'text-[#67b0e8]',
        description: 'Configure manually',
        config: null
    }
]

export function TrainingConfigSelector({ value, onChange, totalTokens }: TrainingConfigProps) {
    const [showAdvanced, setShowAdvanced] = useState(value.preset === 'custom')

    const handlePresetChange = (presetId: string) => {
        const preset = PRESETS.find(p => p.id === presetId)
        if (!preset) return

        if (preset.config) {
            onChange({
                ...value,
                preset: presetId,
                ...preset.config,
                lora_alpha: preset.config.lora_rank * 2,
            })
            setShowAdvanced(false)
        } else {
            onChange({ ...value, preset: presetId })
            setShowAdvanced(true)
        }
    }

    const handleParamChange = (key: keyof TrainingConfig, val: number) => {
        onChange({
            ...value,
            preset: 'custom',
            [key]: val
        })
    }

    // Estimate training time
    const estimatedMinutes = totalTokens
        ? Math.round((totalTokens / 1000000) * value.num_epochs * 15 * (32 / value.lora_rank))
        : null

    return (
        <div className="space-y-4">
            {/* Header */}
            <div className="flex items-center gap-2 text-[#dadada]">
                <Settings className="w-5 h-5 text-[#8ccf7e]" />
                <span className="font-medium">Training Configuration</span>
            </div>

            {/* Preset Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {PRESETS.map((preset) => {
                    const Icon = preset.icon
                    const isSelected = value.preset === preset.id

                    return (
                        <button
                            key={preset.id}
                            onClick={() => handlePresetChange(preset.id)}
                            className={`p-4 rounded-xl border text-left transition-all ${isSelected
                                ? 'bg-[#8ccf7e]/10 border-[#8ccf7e]'
                                : 'bg-[#1e2528] border-[#2d3437] hover:border-[#8ccf7e]/50'
                                }`}
                        >
                            <Icon className={`w-5 h-5 mb-2 ${preset.color}`} />
                            <h4 className="font-medium text-[#dadada]">{preset.name}</h4>
                            <p className="text-xs text-[#8a9899] mt-1">{preset.description}</p>
                        </button>
                    )
                })}
            </div>

            {/* Time Estimate */}
            {estimatedMinutes && (
                <div className="flex items-center gap-2 p-3 bg-[#1e2528] border border-[#2d3437] rounded-lg">
                    <Info className="w-4 h-4 text-[#67b0e8]" />
                    <span className="text-sm text-[#8a9899]">
                        Estimated training time: <strong className="text-[#dadada]">
                            {estimatedMinutes < 60
                                ? `~${estimatedMinutes} min`
                                : `~${Math.round(estimatedMinutes / 60 * 10) / 10} hours`
                            }
                        </strong> on Colab T4
                    </span>
                </div>
            )}

            {/* Advanced Options */}
            <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="flex items-center gap-2 text-sm text-[#8a9899] hover:text-[#dadada] transition-colors"
            >
                <ChevronRight className={`w-4 h-4 transition-transform ${showAdvanced ? 'rotate-90' : ''}`} />
                Advanced Options
            </button>

            {showAdvanced && (
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 p-4 bg-[#1e2528] border border-[#2d3437] rounded-xl animate-in slide-in-from-top-2">
                    <div>
                        <Tooltip content="Higher rank = more parameters. Improves capacity but needs more VRAM.">
                            <label className="flex items-center gap-1 text-xs text-[#8a9899] mb-1 cursor-help w-max">
                                LoRA Rank <Info className="w-3 h-3" />
                            </label>
                        </Tooltip>
                        <select
                            value={value.lora_rank}
                            onChange={(e) => handleParamChange('lora_rank', Number(e.target.value))}
                            className="w-full px-3 py-2 bg-[#141b1e] border border-[#2d3437] rounded-lg text-[#dadada] focus:outline-none focus:border-[#8ccf7e]"
                        >
                            {[4, 8, 16, 32, 64].map(v => (
                                <option key={v} value={v}>{v}</option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <Tooltip content="Controls adaptation speed. Too high = unstable; too low = slow.">
                            <label className="flex items-center gap-1 text-xs text-[#8a9899] mb-1 cursor-help w-max">
                                Learning Rate <Info className="w-3 h-3" />
                            </label>
                        </Tooltip>
                        <select
                            value={value.learning_rate}
                            onChange={(e) => handleParamChange('learning_rate', Number(e.target.value))}
                            className="w-full px-3 py-2 bg-[#141b1e] border border-[#2d3437] rounded-lg text-[#dadada] focus:outline-none focus:border-[#8ccf7e]"
                        >
                            {[1e-5, 5e-5, 1e-4, 2e-4, 5e-4, 1e-3].map(v => (
                                <option key={v} value={v}>{v.toExponential(0)}</option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <Tooltip content="Passes through the full dataset. More = better fit but risk of overfitting.">
                            <label className="flex items-center gap-1 text-xs text-[#8a9899] mb-1 cursor-help w-max">
                                Epochs <Info className="w-3 h-3" />
                            </label>
                        </Tooltip>
                        <select
                            value={value.num_epochs}
                            onChange={(e) => handleParamChange('num_epochs', Number(e.target.value))}
                            className="w-full px-3 py-2 bg-[#141b1e] border border-[#2d3437] rounded-lg text-[#dadada] focus:outline-none focus:border-[#8ccf7e]"
                        >
                            {[1, 2, 3, 5, 10].map(v => (
                                <option key={v} value={v}>{v}</option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <Tooltip content="Examples per step. Higher = faster but more VRAM.">
                            <label className="flex items-center gap-1 text-xs text-[#8a9899] mb-1 cursor-help w-max">
                                Batch Size <Info className="w-3 h-3" />
                            </label>
                        </Tooltip>
                        <select
                            value={value.batch_size}
                            onChange={(e) => handleParamChange('batch_size', Number(e.target.value))}
                            className="w-full px-3 py-2 bg-[#141b1e] border border-[#2d3437] rounded-lg text-[#dadada] focus:outline-none focus:border-[#8ccf7e]"
                        >
                            {[1, 2, 4, 8, 16].map(v => (
                                <option key={v} value={v}>{v}</option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <Tooltip content="Max tokens per example. Long sequences use significantly more VRAM.">
                            <label className="flex items-center gap-1 text-xs text-[#8a9899] mb-1 cursor-help w-max">
                                Max Seq Length <Info className="w-3 h-3" />
                            </label>
                        </Tooltip>
                        <select
                            value={value.max_seq_length}
                            onChange={(e) => handleParamChange('max_seq_length', Number(e.target.value))}
                            className="w-full px-3 py-2 bg-[#141b1e] border border-[#2d3437] rounded-lg text-[#dadada] focus:outline-none focus:border-[#8ccf7e]"
                        >
                            {[512, 1024, 2048, 4096, 8192].map(v => (
                                <option key={v} value={v}>{v}</option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <Tooltip content="% of steps to ramp up LR. Stabilizes early training.">
                            <label className="flex items-center gap-1 text-xs text-[#8a9899] mb-1 cursor-help w-max">
                                Warmup Ratio <Info className="w-3 h-3" />
                            </label>
                        </Tooltip>
                        <select
                            value={value.warmup_ratio}
                            onChange={(e) => handleParamChange('warmup_ratio', Number(e.target.value))}
                            className="w-full px-3 py-2 bg-[#141b1e] border border-[#2d3437] rounded-lg text-[#dadada] focus:outline-none focus:border-[#8ccf7e]"
                        >
                            {[0, 0.03, 0.05, 0.1].map(v => (
                                <option key={v} value={v}>{v}</option>
                            ))}
                        </select>
                    </div>
                </div>
            )}
        </div>
    )
}

// Default config export
export const DEFAULT_TRAINING_CONFIG: TrainingConfig = {
    preset: 'balanced',
    lora_rank: 16,
    lora_alpha: 32,
    learning_rate: 2e-4,
    num_epochs: 3,
    batch_size: 4,
    max_seq_length: 2048,
    warmup_ratio: 0.03
}
