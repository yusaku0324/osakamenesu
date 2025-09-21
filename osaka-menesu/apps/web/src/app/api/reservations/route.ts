import { NextResponse } from 'next/server'

const PUBLIC_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'
const INTERNAL_BASE = process.env.API_INTERNAL_BASE || 'http://api:8000'

function resolveBases(): string[] {
  // Always prefer internal base when available (SSR environment)
  return [INTERNAL_BASE, PUBLIC_BASE]
}

export async function POST(req: Request) {
  let payload: unknown
  try {
    payload = await req.json()
  } catch {
    return NextResponse.json({ detail: 'invalid JSON body' }, { status: 400 })
  }

  const body = JSON.stringify(payload)
  let lastError: any = null

  for (const base of resolveBases()) {
    try {
      const resp = await fetch(`${base}/api/v1/reservations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body,
        cache: 'no-store',
      })
      const text = await resp.text()
      let json: any = null
      if (text) {
        try {
          json = JSON.parse(text)
        } catch {
          json = { detail: text }
        }
      }
      if (resp.ok) {
        return NextResponse.json(json, { status: resp.status })
      }
      lastError = { status: resp.status, body: json }
    } catch (err) {
      lastError = err
    }
  }

  if (lastError?.status && lastError.body) {
    return NextResponse.json(lastError.body, { status: lastError.status })
  }

  return NextResponse.json({ detail: 'reservation service unavailable' }, { status: 503 })
}
