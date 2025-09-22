import { NextResponse } from 'next/server'

const ADMIN_KEY = process.env.ADMIN_API_KEY
const PUBLIC_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'
const INTERNAL_BASE = process.env.API_INTERNAL_BASE || 'http://api:8000'

function bases() {
  return [INTERNAL_BASE, PUBLIC_BASE]
}

type Method = 'GET' | 'POST'

async function proxy(method: Method, request: Request, params: { id: string }) {
  if (!ADMIN_KEY) {
    return NextResponse.json({ detail: 'admin key not configured' }, { status: 500 })
  }

  const headers: Record<string, string> = { 'X-Admin-Key': ADMIN_KEY }
  let body: string | undefined
  let query = ''

  if (method === 'GET') {
    const url = new URL(request.url)
    query = url.search
  } else {
    try {
      body = JSON.stringify(await request.json())
    } catch {
      return NextResponse.json({ detail: 'invalid JSON body' }, { status: 400 })
    }
    headers['Content-Type'] = 'application/json'
  }

  const path = `/api/admin/profiles/${params.id}/reviews${query}`
  let lastError: any = null
  for (const base of bases()) {
    try {
      const resp = await fetch(`${base}${path}`, {
        method,
        headers,
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
  return NextResponse.json({ detail: 'admin reviews unavailable' }, { status: 503 })
}

export async function GET(request: Request, context: { params: { id: string } }) {
  return proxy('GET', request, context.params)
}

export async function POST(request: Request, context: { params: { id: string } }) {
  return proxy('POST', request, context.params)
}

