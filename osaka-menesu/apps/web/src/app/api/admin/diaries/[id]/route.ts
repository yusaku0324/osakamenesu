import { NextResponse } from 'next/server'

const ADMIN_KEY = process.env.ADMIN_API_KEY
const PUBLIC_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'
const INTERNAL_BASE = process.env.API_INTERNAL_BASE || 'http://api:8000'

function bases() {
  return [INTERNAL_BASE, PUBLIC_BASE]
}

type Method = 'PATCH' | 'DELETE'

async function proxy(method: Method, request: Request, params: { id: string }) {
  if (!ADMIN_KEY) {
    return NextResponse.json({ detail: 'admin key not configured' }, { status: 500 })
  }

  const headers: Record<string, string> = { 'X-Admin-Key': ADMIN_KEY }
  let body: string | undefined

  if (method === 'PATCH') {
    try {
      body = JSON.stringify(await request.json())
    } catch {
      return NextResponse.json({ detail: 'invalid JSON body' }, { status: 400 })
    }
    headers['Content-Type'] = 'application/json'
  }

  const path = `/api/admin/diaries/${params.id}`
  let lastError: any = null
  for (const base of bases()) {
    try {
      const resp = await fetch(`${base}${path}`, {
        method,
        headers,
        body,
        cache: 'no-store',
      })
      if (resp.ok) {
        if (method === 'DELETE') {
          return NextResponse.json({}, { status: 204 })
        }
        const json = await resp.json()
        return NextResponse.json(json, { status: resp.status })
      }
      const text = await resp.text()
      let json: any = null
      if (text) {
        try {
          json = JSON.parse(text)
        } catch {
          json = { detail: text }
        }
      }
      lastError = { status: resp.status, body: json }
    } catch (err) {
      lastError = err
    }
  }

  if (lastError?.status && lastError.body) {
    return NextResponse.json(lastError.body, { status: lastError.status })
  }
  return NextResponse.json({ detail: 'admin diary unavailable' }, { status: 503 })
}

export async function PATCH(request: Request, context: { params: { id: string } }) {
  return proxy('PATCH', request, context.params)
}

export async function DELETE(request: Request, context: { params: { id: string } }) {
  return proxy('DELETE', request, context.params)
}

