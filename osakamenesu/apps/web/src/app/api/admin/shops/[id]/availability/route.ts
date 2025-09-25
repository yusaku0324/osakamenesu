import { NextResponse } from 'next/server'

const ADMIN_KEY = process.env.ADMIN_API_KEY
const PUBLIC_BASE = process.env.NEXT_PUBLIC_OSAKAMENESU_API_BASE || process.env.NEXT_PUBLIC_API_BASE || '/api'
const INTERNAL_BASE = process.env.OSAKAMENESU_API_INTERNAL_BASE || process.env.API_INTERNAL_BASE || 'http://osakamenesu-api:8000'

function bases() {
  return [INTERNAL_BASE, PUBLIC_BASE]
}

export async function PUT(request: Request, { params }: { params: { id: string } }) {
  if (!ADMIN_KEY) {
    return NextResponse.json({ detail: 'admin key not configured' }, { status: 500 })
  }
  let body: string
  try {
    body = JSON.stringify(await request.json())
  } catch {
    return NextResponse.json({ detail: 'invalid JSON body' }, { status: 400 })
  }

  const headers = {
    'Content-Type': 'application/json',
    'X-Admin-Key': ADMIN_KEY,
  }

  let lastError: any = null
  for (const base of bases()) {
    try {
      const resp = await fetch(`${base}/api/admin/shops/${params.id}/availability`, {
        method: 'PUT',
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
        return NextResponse.json(json)
      }
      lastError = { status: resp.status, body: json }
    } catch (err) {
      lastError = err
    }
  }

  if (lastError?.status && lastError.body) {
    return NextResponse.json(lastError.body, { status: lastError.status })
  }

  return NextResponse.json({ detail: 'admin availability update failed' }, { status: 503 })
}
