/**
 * Custom Model Input Component.
 * 
 * Allows users to input ANY Hugging Face model ID and validate it
 * against our backend (which checks Unsloth compatibility).
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @license MIT
 */

'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Loader2, Check, AlertTriangle, X, Box, Info } from 'lucide-react';
import { validateModel } from '@/lib/api';
import type { ValidateModelResponse } from '@/lib/types';
import { toast } from 'sonner';

interface CustomModelInputProps {
    onSelect: (modelId: string) => void;
    disabled?: boolean;
}

export function CustomModelInput({ onSelect, disabled }: CustomModelInputProps) {
    const [modelId, setModelId] = useState('');
    const [isValidating, setIsValidating] = useState(false);
    const [result, setResult] = useState<ValidateModelResponse | null>(null);
    const [error, setError] = useState<string | null>(null);

    const handleValidate = async () => {
        if (!modelId.trim()) return;

        setIsValidating(true);
        setError(null);
        setResult(null);

        try {
            const data = await validateModel(modelId.trim());
            setResult(data);
            if (data.is_compatible) {
                toast.success('Model is compatible!');
            } else {
                toast.warning('Model may not be supported');
            }
        } catch (err: any) {
            console.error(err);
            setError(err.message || 'Failed to validate model. Check the ID and try again.');
        } finally {
            setIsValidating(false);
        }
    };

    return (
        <div className="bg-[#1e2528]/50 border border-[#2d3437] rounded-xl p-6 mt-8">
            <h3 className="text-lg font-semibold text-[#dadada] mb-4 flex items-center gap-2">
                <Box className="w-5 h-5 text-[#6cbfbf]" />
                Use a Custom Model
            </h3>

            <div className="flex flex-col sm:flex-row gap-3">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8a9899]" />
                    <input
                        type="text"
                        value={modelId}
                        onChange={(e) => setModelId(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleValidate()}
                        placeholder="e.g. microsoft/Phi-4-mini-instruct"
                        className="w-full bg-[#141b1e] border border-[#2d3437] rounded-lg pl-10 pr-4 py-3 text-[#dadada] placeholder:text-[#8a9899]/50 focus:outline-none focus:ring-2 focus:ring-[#6cbfbf]/50 focus:border-[#6cbfbf] transition-all"
                        disabled={isValidating || disabled}
                    />
                </div>
                <button
                    onClick={handleValidate}
                    disabled={!modelId.trim() || isValidating || disabled}
                    className="px-6 py-3 bg-[#2d3437] text-[#dadada] font-medium rounded-lg hover:bg-[#3d4548] disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2 min-w-[120px]"
                >
                    {isValidating ? (
                        <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            Checking...
                        </>
                    ) : (
                        'Validate'
                    )}
                </button>
            </div>

            {/* Validation Error */}
            <AnimatePresence>
                {error && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="mt-4 text-[#e69875] flex items-start gap-2 text-sm bg-[#e69875]/10 p-3 rounded-lg"
                    >
                        <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                        {error}
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Validation Result */}
            <AnimatePresence>
                {result && (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 10 }}
                        className="mt-6 border-t border-[#2d3437] pt-6"
                    >
                        <div className="flex items-start justify-between gap-4">
                            <div>
                                <h4 className="text-lg font-medium text-[#dadada] flex items-center gap-2">
                                    {result.name}
                                    {result.is_gated && (
                                        <span className="px-2 py-0.5 text-xs bg-[#e69875]/20 text-[#e69875] rounded-full border border-[#e69875]/30">
                                            Gated
                                        </span>
                                    )}
                                </h4>
                                <p className="text-[#8a9899] text-sm mt-1">{result.model_id}</p>

                                <div className="flex flex-wrap gap-4 mt-4 text-sm">
                                    <div className="flex items-center gap-2 text-[#8a9899]">
                                        <div className="w-2 h-2 rounded-full bg-[#6cbfbf]" />
                                        Context: <span className="text-[#dadada]">{result.context_window?.toLocaleString() || '?'} tok</span>
                                    </div>
                                    <div className="flex items-center gap-2 text-[#8a9899]">
                                        <div className="w-2 h-2 rounded-full bg-[#8ccf7e]" />
                                        Architecture: <span className="text-[#dadada]">{result.architecture}</span>
                                    </div>
                                    <div className="flex items-center gap-2 text-[#8a9899]">
                                        <div className="w-2 h-2 rounded-full bg-[#e69875]" />
                                        Likes: <span className="text-[#dadada]">{result.likes?.toLocaleString() || 0}</span>
                                    </div>
                                </div>

                                <div className={`mt-4 p-3 rounded-lg text-sm flex items-start gap-2 ${result.is_compatible
                                        ? 'bg-[#8ccf7e]/10 text-[#8ccf7e]'
                                        : 'bg-[#e69875]/10 text-[#e69875]'
                                    }`}>
                                    {result.is_compatible ? <Check className="w-4 h-4 mt-0.5" /> : <Info className="w-4 h-4 mt-0.5" />}
                                    {result.compatibility_reason}
                                </div>
                            </div>
                        </div>

                        {result.is_compatible && (
                            <button
                                onClick={() => onSelect(result.model_id)}
                                disabled={disabled}
                                className="mt-6 w-full py-3 bg-[#8ccf7e] text-[#141b1e] font-semibold rounded-lg hover:bg-[#7bc46e] transition-colors flex items-center justify-center gap-2"
                            >
                                Use This Model
                            </button>
                        )}
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
