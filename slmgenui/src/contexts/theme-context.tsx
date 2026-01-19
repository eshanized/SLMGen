/**
 * Theme Context.
 * 
 * Manages dark/light theme state with system preference detection.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

'use client'

import { createContext, useContext, useState, useEffect, useLayoutEffect, ReactNode } from 'react'

type Theme = 'dark' | 'light' | 'system'

interface ThemeContextType {
    theme: Theme
    resolvedTheme: 'dark' | 'light'
    setTheme: (theme: Theme) => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export function ThemeProvider({ children }: { children: ReactNode }) {
    const [theme, setThemeState] = useState<Theme>('dark')
    const [resolvedTheme, setResolvedTheme] = useState<'dark' | 'light'>('dark')

    useLayoutEffect(() => {
        // Load from localStorage
        const stored = localStorage.getItem('slmgen-theme') as Theme | null
        if (stored && stored !== theme) {
            setThemeState(stored)
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [])

    useEffect(() => {
        // Detect system preference
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')

        const updateResolvedTheme = () => {
            if (theme === 'system') {
                setResolvedTheme(mediaQuery.matches ? 'dark' : 'light')
            } else {
                setResolvedTheme(theme)
            }
        }

        updateResolvedTheme()
        mediaQuery.addEventListener('change', updateResolvedTheme)

        return () => mediaQuery.removeEventListener('change', updateResolvedTheme)
    }, [theme])

    useEffect(() => {
        // Apply theme to document
        document.documentElement.classList.remove('dark', 'light')
        document.documentElement.classList.add(resolvedTheme)
    }, [resolvedTheme])

    const setTheme = (newTheme: Theme) => {
        setThemeState(newTheme)
        localStorage.setItem('slmgen-theme', newTheme)
    }

    return (
        <ThemeContext.Provider value={{ theme, resolvedTheme, setTheme }}>
            {children}
        </ThemeContext.Provider>
    )
}

export function useTheme() {
    const context = useContext(ThemeContext)
    if (!context) {
        throw new Error('useTheme must be used within ThemeProvider')
    }
    return context
}
