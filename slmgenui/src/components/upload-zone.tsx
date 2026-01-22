/**
 * Upload Zone Component.
 * 
 * Drag-and-drop file upload with validation feedback.
 * Now also reads file content locally for the chat preview feature!
 * 
 * How it works:
 * 1. User drops a .jsonl file
 * 2. We use FileReader to read the first ~10KB (for preview)
 * 3. We upload the full file to the backend
 * 4. We pass both the session info AND the preview content to the parent
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @contributor Vedant Singh Rajput <teleported0722@gmail.com>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

'use client';

import { useState, useCallback, useRef } from 'react';
import { Upload, FileText } from '@/components/icons';
import type { DatasetStats } from '@/lib/types';
import { uploadDataset, ApiError } from '@/lib/api';

// ============================================================================
// TYPES
// ============================================================================

interface UploadZoneProps {
    /**
     * Called when upload succeeds.
     * Now includes filePreview - the first ~10KB of the file for the chat preview.
     */
    onUpload: (sessionId: string, stats: DatasetStats, filePreview: string) => void;
    onError: (error: string) => void;
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Reads the first N bytes of a file using FileReader.
 * 
 * Why only the first 10KB? We don't need the entire dataset for preview.
 * Reading 100MB into memory would crash the browser tab!
 * 
 * @param file - The File object to read
 * @param maxBytes - Maximum bytes to read (default: 10KB)
 * @returns Promise resolving to the file content as string
 */
function readFilePreview(file: File, maxBytes: number = 10000): Promise<string> {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();

        // Slice the file to only read what we need
        const slice = file.slice(0, maxBytes);

        reader.onload = (event) => {
            if (event.target?.result) {
                resolve(event.target.result as string);
            } else {
                reject(new Error('Failed to read file'));
            }
        };

        reader.onerror = () => reject(new Error('Failed to read file'));

        // Read as text (UTF-8)
        reader.readAsText(slice);
    });
}

// ============================================================================
// COMPONENT
// ============================================================================

export function UploadZone({ onUpload, onError }: UploadZoneProps) {
    const [isDragging, setIsDragging] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [fileName, setFileName] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    /**
     * Handle file selection - this is the main logic.
     * 
     * We do two things in parallel:
     * 1. Read file preview locally (fast)
     * 2. Upload to backend (slower)
     * 
     * This way the user gets instant feedback while upload happens.
     */
    const handleFile = useCallback(async (file: File) => {
        // Step 1: Basic validation - is it a .jsonl file?
        if (!file.name.toLowerCase().endsWith('.jsonl')) {
            onError('Please upload a .jsonl file');
            return;
        }

        setFileName(file.name);
        setIsUploading(true);

        try {
            // Step 2: Read preview content locally (this is instant)
            // We read about 10KB which should cover 5-10 examples
            const filePreview = await readFilePreview(file);

            // Step 3: Upload to backend (this takes time)
            const response = await uploadDataset(file);

            // Step 4: Pass everything to parent
            // The parent (Dashboard) will store this in session state
            onUpload(response.session_id, response.stats, filePreview);

        } catch (error) {
            if (error instanceof ApiError) {
                onError(error.message);
            } else {
                onError('Failed to upload file. Is the backend running?');
            }
            setFileName(null);
        } finally {
            setIsUploading(false);
        }
    }, [onUpload, onError]);

    // ========================================================================
    // DRAG AND DROP HANDLERS
    // These are pretty standard - just updating state on drag events
    // ========================================================================

    const handleDragEnter = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
    }, []);

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    }, [handleFile]);

    // Click to open file browser
    const handleClick = useCallback(() => {
        fileInputRef.current?.click();
    }, []);

    const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (files && files.length > 0) {
            handleFile(files[0]);
        }
    }, [handleFile]);

    // ========================================================================
    // RENDER
    // ========================================================================

    return (
        <div
            onClick={handleClick}
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            className={`
                relative cursor-pointer rounded-2xl border-2 border-dashed p-12
                transition-all duration-300 ease-out
                ${isDragging
                    ? 'border-[#8ccf7e] bg-[#8ccf7e]/10 scale-[1.02]'
                    : 'border-[#2d3437] bg-[#1e2528]/50 hover:border-[#8ccf7e]/50 hover:bg-[#1e2528]/80'
                }
                ${isUploading ? 'pointer-events-none opacity-70' : ''}
            `}
        >
            <input
                ref={fileInputRef}
                type="file"
                accept=".jsonl"
                onChange={handleInputChange}
                className="hidden"
            />

            <div className="flex flex-col items-center gap-4 text-center">
                {isUploading ? (
                    <>
                        {/* Loading spinner - shows while uploading */}
                        <div className="w-16 h-16 border-4 border-[#8ccf7e] border-t-transparent rounded-full animate-spin" />
                        <p className="text-lg text-[#dadada]">Uploading {fileName}...</p>
                    </>
                ) : (
                    <>
                        {/* Upload icon - the gradient circle looks nice */}
                        <div className="w-20 h-20 rounded-full bg-gradient-to-br from-[#8ccf7e] to-[#6cbfbf] flex items-center justify-center shadow-lg shadow-[#8ccf7e]/20">
                            <Upload className="w-10 h-10 text-[#141b1e]" />
                        </div>

                        <div>
                            <p className="text-xl font-semibold text-[#dadada]">
                                Drop your JSONL file here
                            </p>
                            <p className="text-[#8a9899] mt-1">
                                or click to browse
                            </p>
                        </div>

                        {/* Format hint */}
                        <div className="flex items-center gap-2 text-sm text-[#8a9899]">
                            <span className="flex items-center gap-1.5 px-2 py-1 bg-[#1e2528] rounded-md border border-[#2d3437]">
                                <FileText className="w-4 h-4" />
                                <span className="font-mono">.jsonl</span>
                            </span>
                            <span>Minimum 50 examples</span>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}
