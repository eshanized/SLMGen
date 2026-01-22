/**
 * Root Layout for SLMGEN.
 * 
 * Sets up fonts, auth, and base HTML structure.
 * 
 * @author Eshan Roy <eshanized@proton.me>
 * @license MIT
 * @copyright 2026 Eshan Roy
 */

import type { Metadata, Viewport } from 'next';
import { JetBrains_Mono } from 'next/font/google';
import { SpeedInsights } from '@vercel/speed-insights/next';
import { AuthProvider } from '@/contexts/auth-context';
import './globals.css';

// Primary font for the whole website (JetBrains Mono)
const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-jetbrains-mono',
  display: 'swap',
});

const siteUrl = 'https://slmgen.vercel.app';
const siteName = 'SLMGEN';
const siteDescription = 'Fine-tune Small Language Models in minutes. Upload your dataset, get a ready-to-run Colab notebook. 2x faster with Unsloth, 70% less VRAM, completely free.';

export const metadata: Metadata = {
  // Basic
  title: {
    default: 'SLMGEN - Fine-tune SLMs in Minutes',
    template: '%s | SLMGEN',
  },
  description: siteDescription,
  keywords: [
    'LLM fine-tuning',
    'Small Language Models',
    'machine learning',
    'AI training',
    'Unsloth',
    'LoRA',
    'PEFT',
    'Google Colab',
    'Phi-4',
    'Llama 3.2',
    'Gemma 2',
    'Qwen',
    'Mistral',
    'dataset',
    'JSONL',
  ],
  authors: [{ name: 'Eshan Roy', url: 'https://github.com/eshanized' }],
  creator: 'Eshan Roy',
  publisher: 'SLMGEN',

  // Icons
  icons: {
    icon: [
      { url: '/icon.svg', type: 'image/svg+xml' },
    ],
    apple: '/logo.svg',
  },

  // Open Graph
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: siteUrl,
    siteName: siteName,
    title: 'SLMGEN - Fine-tune SLMs in Minutes',
    description: siteDescription,
    images: [
      {
        url: `${siteUrl}/og-image.png`,
        width: 1200,
        height: 630,
        alt: 'SLMGEN - Small Language Model Generator',
      },
    ],
  },

  // Twitter
  twitter: {
    card: 'summary_large_image',
    title: 'SLMGEN - Fine-tune SLMs in Minutes',
    description: siteDescription,
    creator: '@eshanized',
    images: [`${siteUrl}/og-image.png`],
  },

  // Robots
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },

  // Verification (add your IDs when you have them)
  // verification: {
  //   google: 'your-google-verification-code',
  // },

  // Manifest
  manifest: '/manifest.json',

  // Category
  category: 'technology',
};

export const viewport: Viewport = {
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#8ccf7e' },
    { media: '(prefers-color-scheme: dark)', color: '#141b1e' },
  ],
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <head>
        {/* Structured Data */}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              '@context': 'https://schema.org',
              '@type': 'WebApplication',
              name: 'SLMGEN',
              description: siteDescription,
              url: siteUrl,
              applicationCategory: 'DeveloperApplication',
              operatingSystem: 'Web',
              offers: {
                '@type': 'Offer',
                price: '0',
                priceCurrency: 'USD',
              },
              author: {
                '@type': 'Person',
                name: 'Eshan Roy',
                url: 'https://github.com/eshanized',
              },
            }),
          }}
        />
      </head>
      <body className={`${jetbrainsMono.variable} antialiased`} suppressHydrationWarning>
        <AuthProvider>
          {children}
        </AuthProvider>
        <SpeedInsights />
      </body>
    </html>
  );
}



