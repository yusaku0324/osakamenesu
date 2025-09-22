import { NextResponse } from 'next/server'

const PUBLIC_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'
const INTERNAL_BASE = process.env.API_INTERNAL_BASE || 'http://api:8000'

function resolveBases(): string[] {
  return [INTERNAL_BASE, PUBLIC_BASE]
}

function buildQuery(params: URLSearchParams): string {
  const qs = params.toString()
  return qs ? `?${qs}` : ''
}

async function relay(
  method: 'GET' | 'POST',
  url: string,
  init?: RequestInit,
): Promise<Response> {
  let lastError: { status?: number; body?: any } | null = null
  for (const base of resolveBases()) {
    try {
      const resp = await fetch(`${base}${url}`, {
        method,
        cache: 'no-store',
        ...init,
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
      lastError = { body: err }
    }
  }

  if (lastError?.status && lastError.body) {
    return NextResponse.json(lastError.body, { status: lastError.status })
  }

  return NextResponse.json({ detail: 'review service unavailable' }, { status: 503 })
}

export async function GET(req: Request, { params }: { params: { id: string } }) {
  const url = new URL(req.url)
  const search = new URLSearchParams(url.search)
  if (!search.get('page')) search.set('page', '1')
  if (!search.get('page_size')) search.set('page_size', '10')
  return relay('GET', `/api/v1/shops/${params.id}/reviews${buildQuery(search)}`)
}

export async function POST(req: Request, { params }: { params: { id: string } }) {
  let payload: unknown
  try {
    payload = await req.json()
  } catch {
    return NextResponse.json({ detail: 'invalid JSON body' }, { status: 400 })
  }
  return relay('POST', `/api/v1/shops/${params.id}/reviews`, {
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

