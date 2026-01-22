/**
 * Data Preview Component - Live Dataset Chat Preview
 * 
 * This component takes uploaded JSONL data and renders it as a beautiful
 * chat interface. Think of it like iMessage or WhatsApp, but for your
 * training data. Users can instantly see if their data is formatted correctly.
 * 
 * How it works:
 * 1. We receive a raw JSONL string (each line is a JSON object)
 * 2. We parse each line and extract the "messages" array
 * 3. We render each message as a chat bubble (User on right, Assistant on left)
 * 4. We validate the structure and show green checkmarks or red X's
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @contributor Vedant Singh Rajput <teleported0722@gmail.com>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

'use client';

import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    MessageCircle,
    User,
    Bot,
    AlertCircle,
    Check,
    ChevronDown,
    ChevronUp,
    Sparkles
} from '@/components/icons';

// ============================================================================
// TYPES - What our data looks like
// ============================================================================

/**
 * A single message in a conversation.
 * This matches the standard OpenAI/Unsloth format that most people use.
 */
interface ChatMessage {
    role: 'system' | 'user' | 'assistant';
    content: string;
}

/**
 * A complete conversation example from the JSONL file.
 * Each line in the file becomes one of these.
 */
interface ConversationExample {
    messages: ChatMessage[];
    isValid: boolean;
    validationError?: string;
}

/**
 * Props for the DataPreview component.
 * We need the raw file content as a string.
 */
interface DataPreviewProps {
    /** The raw JSONL content from the uploaded file */
    fileContent: string;
    /** Maximum number of examples to show (default: 3) */
    maxExamples?: number;
}

// ============================================================================
// PARSING LOGIC - The brain of the component
// ============================================================================

/**
 * Parses a JSONL string into an array of conversation examples.
 * 
 * Why JSONL? It's a format where each line is a valid JSON object.
 * This makes it easy to stream large files and process them line by line.
 * 
 * Example input:
 * {"messages": [{"role": "user", "content": "Hi!"}, {"role": "assistant", "content": "Hello!"}]}
 * {"messages": [{"role": "user", "content": "Bye"}, {"role": "assistant", "content": "Goodbye!"}]}
 * 
 * @param content - The raw JSONL string from the file
 * @param maxLines - How many lines to parse (we don't need all 10,000!)
 * @returns Array of parsed and validated conversation examples
 */
function parseJsonl(content: string, maxLines: number = 5): ConversationExample[] {
    // Split by newlines and filter out empty lines
    // (Some people have trailing newlines, we don't want to fail on those)
    const lines = content.split('\n').filter(line => line.trim().length > 0);

    // Only parse the first N lines - no need to process entire dataset
    const linesToParse = lines.slice(0, maxLines);

    return linesToParse.map((line, index) => {
        try {
            // Try to parse this line as JSON
            const parsed = JSON.parse(line);

            // Check if it has the "messages" array we expect
            if (!parsed.messages || !Array.isArray(parsed.messages)) {
                return {
                    messages: [],
                    isValid: false,
                    validationError: `Line ${index + 1}: Missing "messages" array`
                };
            }

            // Validate each message has role and content
            for (let i = 0; i < parsed.messages.length; i++) {
                const msg = parsed.messages[i];
                if (!msg.role || !msg.content) {
                    return {
                        messages: parsed.messages,
                        isValid: false,
                        validationError: `Line ${index + 1}, Message ${i + 1}: Missing "role" or "content"`
                    };
                }
                // Check role is one of the valid options
                if (!['system', 'user', 'assistant'].includes(msg.role)) {
                    return {
                        messages: parsed.messages,
                        isValid: false,
                        validationError: `Line ${index + 1}: Invalid role "${msg.role}"`
                    };
                }
            }

            // All good! This example is valid
            return {
                messages: parsed.messages,
                isValid: true
            };
        } catch {
            // JSON.parse failed - this line is broken
            return {
                messages: [],
                isValid: false,
                validationError: `Line ${index + 1}: Invalid JSON syntax`
            };
        }
    });
}

// ============================================================================
// SUB-COMPONENTS - The building blocks
// ============================================================================

/**
 * A single chat message bubble.
 * User messages go on the right (green), Assistant on left (gray).
 * System prompts get a special yellow treatment.
 */
function MessageBubble({ message, index }: { message: ChatMessage; index: number }) {
    const isUser = message.role === 'user';
    const isSystem = message.role === 'system';
    const isAssistant = message.role === 'assistant';

    // Truncate very long messages to keep the UI clean
    const displayContent = message.content.length > 200
        ? message.content.slice(0, 200) + '...'
        : message.content;

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className={`flex gap-2 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
        >
            {/* Avatar - shows who's talking */}
            <div className={`
                w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0
                ${isSystem
                    ? 'bg-[#e5c76b]/20 text-[#e5c76b]'
                    : isUser
                        ? 'bg-[#8ccf7e]/20 text-[#8ccf7e]'
                        : 'bg-[#67b0e8]/20 text-[#67b0e8]'
                }
            `}>
                {isSystem && <Sparkles className="w-4 h-4" />}
                {isUser && <User className="w-4 h-4" />}
                {isAssistant && <Bot className="w-4 h-4" />}
            </div>

            {/* The actual message bubble */}
            <div className={`
                max-w-[80%] px-4 py-2 rounded-2xl text-sm
                ${isSystem
                    ? 'bg-[#e5c76b]/10 text-[#e5c76b] border border-[#e5c76b]/30'
                    : isUser
                        ? 'bg-[#8ccf7e] text-[#141b1e]'
                        : 'bg-[#1e2528] text-[#dadada] border border-[#2d3437]'
                }
            `}>
                {/* Role label for system prompts */}
                {isSystem && (
                    <span className="text-xs font-medium block mb-1 opacity-70">
                        System Prompt
                    </span>
                )}
                <p className="whitespace-pre-wrap break-words">{displayContent}</p>
            </div>
        </motion.div>
    );
}

/**
 * A single conversation example card.
 * Shows all messages in that example, with expand/collapse for long ones.
 */
function ConversationCard({
    example,
    index
}: {
    example: ConversationExample;
    index: number;
}) {
    const [isExpanded, setIsExpanded] = useState(index === 0); // First one starts open

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.15 }}
            className="bg-[#1e2528]/80 border border-[#2d3437] rounded-xl overflow-hidden"
        >
            {/* Header with example number and validation status */}
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-[#141b1e]/50 transition-colors"
            >
                <div className="flex items-center gap-3">
                    <span className="text-sm font-medium text-[#dadada]">
                        Example {index + 1}
                    </span>

                    {/* Validation badge */}
                    {example.isValid ? (
                        <span className="flex items-center gap-1 text-xs text-[#8ccf7e] bg-[#8ccf7e]/10 px-2 py-0.5 rounded-full">
                            <Check className="w-3 h-3" />
                            Valid
                        </span>
                    ) : (
                        <span className="flex items-center gap-1 text-xs text-[#e67e80] bg-[#e67e80]/10 px-2 py-0.5 rounded-full">
                            <AlertCircle className="w-3 h-3" />
                            Error
                        </span>
                    )}

                    {/* Message count */}
                    <span className="text-xs text-[#8a9899]">
                        {example.messages.length} messages
                    </span>
                </div>

                {isExpanded ? (
                    <ChevronUp className="w-4 h-4 text-[#8a9899]" />
                ) : (
                    <ChevronDown className="w-4 h-4 text-[#8a9899]" />
                )}
            </button>

            {/* Expandable content */}
            <AnimatePresence>
                {isExpanded && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="overflow-hidden"
                    >
                        <div className="px-4 pb-4 space-y-3">
                            {/* Error message if validation failed */}
                            {example.validationError && (
                                <div className="p-3 bg-[#e67e80]/10 border border-[#e67e80]/30 rounded-lg text-sm text-[#e67e80]">
                                    {example.validationError}
                                </div>
                            )}

                            {/* Chat messages */}
                            {example.messages.map((message, msgIndex) => (
                                <MessageBubble
                                    key={msgIndex}
                                    message={message}
                                    index={msgIndex}
                                />
                            ))}

                            {/* Empty state */}
                            {example.messages.length === 0 && !example.validationError && (
                                <p className="text-sm text-[#8a9899] text-center py-4">
                                    No messages in this example
                                </p>
                            )}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
}

// ============================================================================
// MAIN COMPONENT - Putting it all together
// ============================================================================

/**
 * DataPreview - The main component that renders the chat preview.
 * 
 * This is what users see after uploading their JSONL file. It gives them
 * instant feedback on whether their data is correctly formatted for training.
 */
export function DataPreview({ fileContent, maxExamples = 3 }: DataPreviewProps) {
    // Parse the file content and memoize to avoid re-parsing on every render
    const examples = useMemo(
        () => parseJsonl(fileContent, maxExamples),
        [fileContent, maxExamples]
    );

    // Count valid vs invalid examples for the summary
    const validCount = examples.filter(e => e.isValid).length;
    const totalCount = examples.length;
    const allValid = validCount === totalCount;

    // Don't render anything if there's no content
    if (!fileContent || fileContent.trim().length === 0) {
        return null;
    }

    return (
        <div className="space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <MessageCircle className="w-5 h-5 text-[#8ccf7e]" />
                    <h3 className="font-medium text-[#dadada]">Data Preview</h3>
                </div>

                {/* Summary badge */}
                <span className={`
                    text-xs px-2 py-1 rounded-full
                    ${allValid
                        ? 'bg-[#8ccf7e]/10 text-[#8ccf7e]'
                        : 'bg-[#e5c76b]/10 text-[#e5c76b]'
                    }
                `}>
                    {validCount}/{totalCount} valid
                </span>
            </div>

            {/* Conversation cards */}
            <div className="space-y-3">
                {examples.map((example, index) => (
                    <ConversationCard
                        key={index}
                        example={example}
                        index={index}
                    />
                ))}
            </div>

            {/* Footer hint */}
            <p className="text-xs text-[#8a9899] text-center">
                Showing first {examples.length} examples from your dataset
            </p>
        </div>
    );
}
