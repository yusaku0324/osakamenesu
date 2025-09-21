import './globals.css'
import type { ReactNode } from 'react'
import Script from 'next/script'
import { Noto_Sans_JP } from 'next/font/google'

export const metadata = {
  title: '大阪メンエス.com',
  description: '探しやすい・誤解しない・速い',
}

const brandFont = Noto_Sans_JP({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-sans',
  display: 'swap',
})

export default function RootLayout({ children }: { children: ReactNode }) {
  const gaId = process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID
  return (
    <html lang="ja">
      <head>
        {gaId ? (
          <>
            <Script
              src={`https://www.googletagmanager.com/gtag/js?id=${gaId}`}
              strategy="afterInteractive"
            />
            <Script
              id="ga-init"
              strategy="afterInteractive"
            >{`
              window.dataLayer = window.dataLayer || [];
              function gtag(){dataLayer.push(arguments);}
              gtag('js', new Date());
              gtag('config', '${gaId}', { anonymize_ip: true });
            `}</Script>
          </>
        ) : null}
      </head>
      <body className={`${brandFont.variable} min-h-screen bg-neutral-surfaceAlt text-neutral-text`}>
        <header className="sticky top-0 z-30 border-b border-neutral-borderLight bg-neutral-surface/90 backdrop-blur supports-[backdrop-filter]:bg-neutral-surface/70">
          <div className="max-w-6xl mx-auto h-12 px-4 flex items-center">
            <a href="/" className="font-bold text-lg tracking-tight text-neutral-text">大阪メンエス.com</a>
          </div>
        </header>
        {children}
      </body>
    </html>
  )
}
