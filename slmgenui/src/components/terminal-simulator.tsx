/**
 * Terminal Simulator Component - Training Terminal Animation
 * 
 * This component creates that cool "hacker movie" effect where commands
 * appear to be typed in real-time. It's shown during the notebook generation
 * phase to make the wait feel productive and exciting.
 * 
 * How it works:
 * 1. We have an array of commands to "type"
 * 2. Using setInterval, we add one character at a time
 * 3. After each command finishes, there's a pause before the next
 * 4. The terminal has a blinking cursor for that authentic feel
 * 
 * The styling uses a dark background with green text (classic terminal look)
 * with some modern touches like rounded corners and subtle shadows.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @contributor Vedant Singh Rajput <teleported0722@gmail.com>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

'use client';

import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { Terminal } from '@/components/icons';

// ============================================================================
// TYPES & CONFIGURATION
// ============================================================================

/**
 * A single command to be "typed" in the terminal.
 * The delay is how long to wait AFTER this command finishes before the next.
 */
interface TerminalCommand {
    text: string;
    delay: number; // milliseconds after command completes
    isOutput?: boolean; // if true, this appears instantly (like command output)
}

/**
 * The commands we'll simulate typing.
 * These represent typical Unsloth/LoRA fine-tuning setup steps.
 */
const COMMANDS: TerminalCommand[] = [
    { text: '$ pip install unsloth', delay: 500 },
    { text: '✓ Successfully installed unsloth-2026.1', delay: 300, isOutput: true },
    { text: '$ python -c "import unsloth; print(unsloth.__version__)"', delay: 400 },
    { text: '2026.1.0', delay: 200, isOutput: true },
    { text: '$ loading base model...', delay: 600 },
    { text: '✓ Model loaded: unsloth/Llama-3.2-1B-bnb-4bit', delay: 300, isOutput: true },
    { text: '$ preparing LoRA adapters...', delay: 500 },
    { text: '✓ LoRA rank: 16, alpha: 32', delay: 200, isOutput: true },
    { text: '$ optimizing with Unsloth...', delay: 400 },
    { text: '✓ 2x faster training enabled!', delay: 300, isOutput: true },
    { text: '$ generating notebook...', delay: 600 },
];

/**
 * Props for the terminal simulator.
 */
interface TerminalSimulatorProps {
    /** Called when all commands have finished typing */
    onComplete?: () => void;
    /** Optional custom commands to display */
    commands?: TerminalCommand[];
}

// ============================================================================
// TYPING SPEED CONFIGURATION
// ============================================================================

// Characters per second for typing effect
// Lower = slower and more dramatic
const CHARS_PER_SECOND = 30;
const TYPING_INTERVAL_MS = 1000 / CHARS_PER_SECOND;

// ============================================================================
// COMPONENT
// ============================================================================

export function TerminalSimulator({
    onComplete,
    commands = COMMANDS
}: TerminalSimulatorProps) {
    // The lines that have been fully typed (or are outputs)
    const [completedLines, setCompletedLines] = useState<string[]>([]);

    // The line currently being typed
    const [currentLine, setCurrentLine] = useState('');

    // Which command index we're currently on
    const [commandIndex, setCommandIndex] = useState(0);

    // Which character of the current command we're at
    const [charIndex, setCharIndex] = useState(0);

    // Is the animation complete?
    const [isComplete, setIsComplete] = useState(false);

    // Ref for the terminal container (for auto-scroll)
    const terminalRef = useRef<HTMLDivElement>(null);

    /**
     * Main typing effect.
     * 
     * This is where the magic happens! We use setInterval to add one
     * character at a time, creating that typewriter effect.
     */
    useEffect(() => {
        // Don't run if we've finished all commands
        if (commandIndex >= commands.length) {
            if (!isComplete) {
                // Defer state update to avoid sync render warning
                setTimeout(() => {
                    setIsComplete(true);
                    onComplete?.();
                }, 0);
            }
            return;
        }

        const currentCommand = commands[commandIndex];

        // If this is an output line (not typed), show it instantly
        if (currentCommand.isOutput) {
            setTimeout(() => {
                setCompletedLines(prev => [...prev, currentCommand.text]);
                setCurrentLine('');
                setCharIndex(0);
                setCommandIndex(prev => prev + 1);
            }, 0);
            return;
        }

        // Normal typing behavior
        if (charIndex < currentCommand.text.length) {
            // Still typing - add next character
            const timer = setTimeout(() => {
                setCurrentLine(currentCommand.text.slice(0, charIndex + 1));
                setCharIndex(prev => prev + 1);
            }, TYPING_INTERVAL_MS);

            return () => clearTimeout(timer);
        } else {
            // Finished typing this command
            setTimeout(() => {
                setCompletedLines(prev => [...prev, currentCommand.text]);
                setCurrentLine('');
                setCharIndex(0);

                // Add small delay before next command
                setTimeout(() => {
                    setCommandIndex(prev => prev + 1);
                }, currentCommand.delay);
            }, 0);
            return;
        }
    }, [commandIndex, charIndex, commands, isComplete, onComplete]);

    // Auto-scroll to bottom as new lines appear
    useEffect(() => {
        if (terminalRef.current) {
            terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
        }
    }, [completedLines, currentLine]);

    // ========================================================================
    // RENDER
    // ========================================================================

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full max-w-2xl mx-auto"
        >
            {/* Terminal window frame */}
            <div className="rounded-xl overflow-hidden border border-[#2d3437] shadow-xl shadow-black/30">

                {/* Title bar - like a macOS window */}
                <div className="bg-[#1e2528] px-4 py-2 flex items-center gap-2 border-b border-[#2d3437]">
                    {/* Traffic light buttons */}
                    <div className="flex gap-1.5">
                        <div className="w-3 h-3 rounded-full bg-[#e67e80]" />
                        <div className="w-3 h-3 rounded-full bg-[#e5c76b]" />
                        <div className="w-3 h-3 rounded-full bg-[#8ccf7e]" />
                    </div>

                    {/* Title */}
                    <div className="flex-1 text-center">
                        <span className="text-xs text-[#8a9899] flex items-center justify-center gap-1.5">
                            <Terminal className="w-3 h-3" />
                            slmgen — training
                        </span>
                    </div>

                    {/* Spacer for symmetry */}
                    <div className="w-12" />
                </div>

                {/* Terminal content */}
                <div
                    ref={terminalRef}
                    className="bg-[#0d1117] p-4 h-64 overflow-y-auto font-mono text-sm"
                >
                    {/* Completed lines */}
                    {completedLines.map((line, index) => (
                        <div
                            key={index}
                            className={`mb-1 ${line.startsWith('✓')
                                ? 'text-[#8ccf7e]'
                                : line.startsWith('$')
                                    ? 'text-[#67b0e8]'
                                    : 'text-[#8a9899]'
                                }`}
                        >
                            {line}
                        </div>
                    ))}

                    {/* Currently typing line with cursor */}
                    {currentLine && (
                        <div className="text-[#67b0e8] flex">
                            <span>{currentLine}</span>
                            <span className="animate-pulse ml-0.5">▋</span>
                        </div>
                    )}

                    {/* Waiting cursor when between commands */}
                    {!currentLine && !isComplete && (
                        <div className="text-[#67b0e8]">
                            <span className="animate-pulse">▋</span>
                        </div>
                    )}

                    {/* Complete message */}
                    {isComplete && (
                        <div className="text-[#8ccf7e] mt-2">
                            ✓ Notebook ready for download!
                        </div>
                    )}
                </div>
            </div>
        </motion.div>
    );
}
