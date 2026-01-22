/**
 * Confetti Component - Success Celebration Animation
 * 
 * Who doesn't love confetti? This component triggers a beautiful explosion
 * of colorful particles when the notebook generation is complete. It's those
 * little touches that make users feel like they've accomplished something!
 * 
 * How it works:
 * 1. On mount, we generate a bunch of confetti particles with random properties
 * 2. Each particle has a random color, size, position, and animation delay
 * 3. We use CSS keyframes for the falling/spinning animation
 * 4. After the animation completes, the component auto-cleans up
 * 
 * Technical notes:
 * - We use pure CSS animations for performance (no JS animation loops)
 * - Particles are absolutely positioned within a fixed container
 * - The container is pointer-events: none so it doesn't block clicks
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @contributor Vedant Singh Rajput <teleported0722@gmail.com>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

'use client';

import { useEffect, useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

// ============================================================================
// CONFIGURATION
// ============================================================================

/**
 * Confetti colors - using the Everblush palette for consistency.
 * These are the accent colors that look great against the dark background.
 */
const CONFETTI_COLORS = [
    '#8ccf7e', // Green (primary)
    '#6cbfbf', // Teal
    '#e5c76b', // Yellow
    '#67b0e8', // Blue
    '#e69875', // Orange
    '#c47fd5', // Purple
    '#e67e80', // Red/Pink
];

/**
 * How many confetti pieces to spawn.
 * More = more festive, but also more DOM elements.
 */
const PARTICLE_COUNT = 50;

/**
 * How long the confetti animation lasts (in milliseconds).
 * After this, particles are removed from DOM.
 */
const ANIMATION_DURATION_MS = 3000;

// ============================================================================
// TYPES
// ============================================================================

/**
 * A single confetti particle with its random properties.
 */
interface ConfettiParticle {
    id: number;
    color: string;
    size: number;       // Width in pixels
    x: number;          // Starting X position (0-100%)
    delay: number;      // Animation delay in ms
    duration: number;   // Animation duration in ms
    rotation: number;   // Initial rotation angle
}

// ============================================================================
// PARTICLE GENERATOR
// ============================================================================

/**
 * Generates an array of random confetti particles.
 * 
 * Each particle gets:
 * - A random color from our palette
 * - A random size (small variations look more natural)
 * - A random starting X position (spread across the screen)
 * - A random animation delay (so they don't all fall at once)
 * - A random duration (different fall speeds)
 * - A random initial rotation
 * 
 * @param count - How many particles to generate
 * @returns Array of particles
 */
function generateParticles(count: number): ConfettiParticle[] {
    return Array.from({ length: count }, (_, i) => ({
        id: i,
        color: CONFETTI_COLORS[Math.floor(Math.random() * CONFETTI_COLORS.length)],
        size: Math.random() * 8 + 4, // 4-12px
        x: Math.random() * 100, // 0-100%
        delay: Math.random() * 500, // 0-500ms delay
        duration: Math.random() * 1000 + 2000, // 2-3 seconds
        rotation: Math.random() * 360, // 0-360 degrees
    }));
}

// ============================================================================
// PROPS
// ============================================================================

interface ConfettiProps {
    /** If true, confetti will be shown */
    active?: boolean;
    /** Called when animation completes */
    onComplete?: () => void;
}

// ============================================================================
// COMPONENT
// ============================================================================

export function Confetti({ active = true, onComplete }: ConfettiProps) {
    // Track if we should show confetti
    const [isVisible, setIsVisible] = useState(active);

    // Generate particles once on mount (memoized so they don't regenerate)
    const particles = useMemo(() => generateParticles(PARTICLE_COUNT), []);

    // Auto-hide after animation completes
    useEffect(() => {
        if (active) {
            // Defer update to avoid sync render warning
            setTimeout(() => {
                setIsVisible(true);
            }, 0);

            const timer = setTimeout(() => {
                setIsVisible(false);
                onComplete?.();
            }, ANIMATION_DURATION_MS);
            return () => clearTimeout(timer);
        } else {
            setTimeout(() => {
                setIsVisible(false);
            }, 0);
        }
    }, [active, onComplete]);

    // Don't render anything if not visible
    if (!isVisible) return null;

    return (
        <AnimatePresence>
            {isVisible && (
                <motion.div
                    initial={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.5 }}
                    className="fixed inset-0 pointer-events-none overflow-hidden z-50"
                    aria-hidden="true"
                >
                    {particles.map((particle) => (
                        <motion.div
                            key={particle.id}
                            initial={{
                                x: `${particle.x}vw`,
                                y: -20,
                                rotate: particle.rotation,
                                opacity: 1,
                            }}
                            animate={{
                                y: '110vh',
                                rotate: particle.rotation + 720, // Spin twice
                                opacity: [1, 1, 0],
                            }}
                            transition={{
                                duration: particle.duration / 1000,
                                delay: particle.delay / 1000,
                                ease: 'easeIn',
                            }}
                            style={{
                                position: 'absolute',
                                width: particle.size,
                                height: particle.size * 1.5, // Slightly rectangular
                                backgroundColor: particle.color,
                                borderRadius: '2px',
                            }}
                        />
                    ))}
                </motion.div>
            )}
        </AnimatePresence>
    );
}

// ============================================================================
// BONUS: Hook for programmatic confetti
// ============================================================================

/**
 * Use this hook if you want to trigger confetti programmatically.
 * 
 * Example usage:
 * ```
 * const { showConfetti, ConfettiComponent } = useConfetti();
 * 
 * // In your handler:
 * showConfetti();
 * 
 * // In your JSX:
 * <ConfettiComponent />
 * ```
 */
export function useConfetti() {
    const [isActive, setIsActive] = useState(false);

    const showConfetti = () => setIsActive(true);
    const hideConfetti = () => setIsActive(false);

    const ConfettiComponent = () => (
        <Confetti active={isActive} onComplete={hideConfetti} />
    );

    return { showConfetti, hideConfetti, ConfettiComponent, isActive };
}
