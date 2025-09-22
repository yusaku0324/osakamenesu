"use client"

import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { usePathname } from 'next/navigation'

const COOKIE_NAME = 'age_verified'
const COOKIE_VALUE = '1'
const ONE_YEAR_IN_DAYS = 365

function readCookie(name: string): string | null {
  if (typeof document === 'undefined') return null
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`))
  return match ? decodeURIComponent(match[1]) : null
}

function setCookie(name: string, value: string, days: number) {
  if (typeof document === 'undefined') return
  const expires = new Date(Date.now() + days * 86400 * 1000).toUTCString()
  document.cookie = `${name}=${encodeURIComponent(value)}; path=/; expires=${expires}; SameSite=Lax`
}

type AgeGateProps = {
  initialVerified: boolean
}

export default function AgeGate({ initialVerified }: AgeGateProps) {
  const pathname = usePathname()
  const [mounted, setMounted] = useState(false)
  const [verified, setVerified] = useState(initialVerified)

  const bypass = Boolean(pathname && (pathname.startsWith('/admin') || pathname.startsWith('/api')))

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (initialVerified) {
      setVerified(true)
      return
    }
    const cookieValue = readCookie(COOKIE_NAME)
    setVerified(cookieValue === COOKIE_VALUE)
  }, [initialVerified])

  useEffect(() => {
    if (!mounted || verified || bypass) return undefined
    const originalOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = originalOverflow
    }
  }, [mounted, verified, bypass])

  if (!mounted || verified || bypass) {
    return null
  }

  const handleConfirm = () => {
    setCookie(COOKIE_NAME, COOKIE_VALUE, ONE_YEAR_IN_DAYS)
    setVerified(true)
    document.body.style.overflow = ''
  }

  const handleExit = () => {
    window.location.href = 'https://www.google.com'
  }

  return createPortal(
    <div className="fixed inset-0 z-[999] flex items-center justify-center bg-black/70 backdrop-blur-sm">
      <div className="mx-4 max-w-lg rounded-section border border-neutral-borderLight bg-neutral-surface p-6 text-center shadow-lg">
        <h2 className="text-xl font-semibold text-neutral-text">18歳以上の確認</h2>
        <p className="mt-3 text-sm leading-relaxed text-neutral-textMuted">
          このサイトには成人向けの情報が含まれます。18歳未満の方の閲覧は固くお断りします。
          「同意して入場」を押すことで、利用規約に同意し18歳以上であることを確認します。
        </p>
        <div className="mt-6 flex flex-col gap-3 sm:flex-row">
          <button
            type="button"
            onClick={handleConfirm}
            className="flex-1 rounded-lg bg-brand-primary px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-brand-primaryDark"
          >
            同意して入場
          </button>
          <button
            type="button"
            onClick={handleExit}
            className="flex-1 rounded-lg border border-neutral-borderLight px-4 py-2 text-sm font-semibold text-neutral-text transition hover:bg-neutral-surfaceAlt"
          >
            退出する
          </button>
        </div>
        <p className="mt-4 text-xs text-neutral-textMuted">
          ブラウザに確認情報を保存し、次回以降は表示されません。
        </p>
      </div>
    </div>,
    document.body,
  )
}
