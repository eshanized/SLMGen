/**
 * Task and Deployment Selector Component.
 * 
 * Two-step configuration for task type and deployment target.
 * Everblush themed with Lucide icons.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

'use client';

import { useState } from 'react';
import {
    Tag,
    HelpCircle,
    MessageCircle,
    Pencil,
    Database,
    Cloud,
    Server,
    Monitor,
    Smartphone,
    Cpu,
    Globe,
    Check,
    ChevronLeft,
} from '@/components/icons';
import type { TaskType, DeploymentTarget, TaskOption, DeploymentOption } from '@/lib/types';

// Available task Options
const TASK_OPTIONS: (TaskOption & { Icon: React.ComponentType<{ className?: string }> })[] = [
    {
        value: 'classify',
        label: 'Classification',
        description: 'Categorize text into labels',
        Icon: Tag,
    },
    {
        value: 'qa',
        label: 'Question & Answer',
        description: 'Answer questions from context',
        Icon: HelpCircle,
    },
    {
        value: 'conversation',
        label: 'Conversation',
        description: 'Multi-turn chat interactions',
        Icon: MessageCircle,
    },
    {
        value: 'generation',
        label: 'Text Generation',
        description: 'Generate creative content',
        Icon: Pencil,
    },
    {
        value: 'extraction',
        label: 'Data Extraction',
        description: 'Extract structured data',
        Icon: Database,
    },
];

// Available deployment Options
const DEPLOYMENT_OPTIONS: (DeploymentOption & { Icon: React.ComponentType<{ className?: string }> })[] = [
    {
        value: 'cloud',
        label: 'Cloud API',
        description: 'Deploy as an API service',
        Icon: Cloud,
    },
    {
        value: 'server',
        label: 'On-premise Server',
        description: 'Run on your own hardware',
        Icon: Server,
    },
    {
        value: 'desktop',
        label: 'Desktop App',
        description: 'Run locally on desktop',
        Icon: Monitor,
    },
    {
        value: 'mobile',
        label: 'Mobile Device',
        description: 'Deploy to phones/tablets',
        Icon: Smartphone,
    },
    {
        value: 'edge',
        label: 'Edge Device',
        description: 'IoT or embedded systems',
        Icon: Cpu,
    },
    {
        value: 'browser',
        label: 'Web Browser',
        description: 'Run in-browser with WebGPU',
        Icon: Globe,
    },
];

interface TaskSelectorProps {
    onComplete: (task: TaskType, deployment: DeploymentTarget) => void;
}

export function TaskSelector({ onComplete }: TaskSelectorProps) {
    const [step, setStep] = useState<'task' | 'deployment'>('task');
    const [selectedTask, setSelectedTask] = useState<TaskType | null>(null);
    const [selectedDeployment, setSelectedDeployment] = useState<DeploymentTarget | null>(null);

    // Handle task Selection
    const handleTaskSelect = (task: TaskType) => {
        setSelectedTask(task);
        // Auto-advance after short Delay
        setTimeout(() => setStep('deployment'), 200);
    };

    // Handle deployment Selection
    const handleDeploymentSelect = (deployment: DeploymentTarget) => {
        setSelectedDeployment(deployment);
        // Complete after short Delay
        if (selectedTask) {
            setTimeout(() => onComplete(selectedTask, deployment), 200);
        }
    };

    // Option Card component
    const OptionCard = ({
        Icon,
        label,
        description,
        isSelected,
        onClick
    }: {
        Icon: React.ComponentType<{ className?: string }>;
        label: string;
        description: string;
        isSelected: boolean;
        onClick: () => void;
    }) => (
        <button
            onClick={onClick}
            className={`
                p-6 rounded-xl border-2 text-left transition-all duration-200
                hover:scale-[1.02] active:scale-[0.98]
                ${isSelected
                    ? 'border-[#8ccf7e] bg-[#8ccf7e]/10 shadow-lg shadow-[#8ccf7e]/20'
                    : 'border-[#2d3437] bg-[#1e2528]/80 hover:border-[#8ccf7e]/50'
                }
            `}
        >
            <div className={`w-12 h-12 rounded-lg flex items-center justify-center mb-3 ${isSelected ? 'bg-[#8ccf7e]/20' : 'bg-[#141b1e]'
                }`}>
                <Icon className={`w-6 h-6 ${isSelected ? 'text-[#8ccf7e]' : 'text-[#8a9899]'}`} />
            </div>
            <h3 className="font-semibold text-[#dadada] text-lg">{label}</h3>
            <p className="mt-1 text-sm text-[#8a9899]">{description}</p>
        </button>
    );

    return (
        <div className="space-y-8">
            {/* Step Indicator */}
            <div className="flex items-center justify-center gap-4">
                <div className={`flex items-center gap-2 ${step === 'task' ? 'text-[#8ccf7e]' : 'text-[#8a9899]'}`}>
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center font-semibold ${step === 'task'
                        ? 'bg-gradient-to-br from-[#8ccf7e] to-[#6cbfbf] text-[#141b1e]'
                        : selectedTask
                            ? 'bg-[#8ccf7e] text-[#141b1e]'
                            : 'bg-[#1e2528] border border-[#2d3437]'
                        }`}>
                        {selectedTask ? <Check className="w-4 h-4" /> : '1'}
                    </div>
                    <span className="hidden sm:inline font-medium">Task Type</span>
                </div>

                <div className="w-12 h-0.5 bg-[#2d3437]" />

                <div className={`flex items-center gap-2 ${step === 'deployment' ? 'text-[#8ccf7e]' : 'text-[#8a9899]'}`}>
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center font-semibold ${step === 'deployment'
                        ? 'bg-gradient-to-br from-[#8ccf7e] to-[#6cbfbf] text-[#141b1e]'
                        : 'bg-[#1e2528] border border-[#2d3437]'
                        }`}>
                        2
                    </div>
                    <span className="hidden sm:inline font-medium">Deployment</span>
                </div>
            </div>

            {/* Task Selection */}
            {step === 'task' && (
                <div className="space-y-6">
                    <div className="text-center">
                        <h2 className="text-2xl font-bold text-[#dadada]">What will your model do?</h2>
                        <p className="text-[#8a9899] mt-2">Select the primary task for your fine-tuned model</p>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                        {TASK_OPTIONS.map((option) => (
                            <OptionCard
                                key={option.value}
                                Icon={option.Icon}
                                label={option.label}
                                description={option.description}
                                isSelected={selectedTask === option.value}
                                onClick={() => handleTaskSelect(option.value)}
                            />
                        ))}
                    </div>
                </div>
            )}

            {/* Deployment Selection */}
            {step === 'deployment' && (
                <div className="space-y-6">
                    <div className="text-center">
                        <h2 className="text-2xl font-bold text-[#dadada]">Where will it run?</h2>
                        <p className="text-[#8a9899] mt-2">This helps us pick the right model size</p>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                        {DEPLOYMENT_OPTIONS.map((option) => (
                            <OptionCard
                                key={option.value}
                                Icon={option.Icon}
                                label={option.label}
                                description={option.description}
                                isSelected={selectedDeployment === option.value}
                                onClick={() => handleDeploymentSelect(option.value)}
                            />
                        ))}
                    </div>

                    {/* Back Button */}
                    <button
                        onClick={() => setStep('task')}
                        className="mx-auto flex items-center gap-2 text-[#8a9899] hover:text-[#dadada] transition-colors"
                    >
                        <ChevronLeft className="w-4 h-4" />
                        Change task type
                    </button>
                </div>
            )}
        </div>
    );
}
