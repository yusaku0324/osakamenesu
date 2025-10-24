import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'

import { buildApiUrl } from '@/lib/api'

const INTERNAL_API_BASE =
  process.env.OSAKAMENESU_API_INTERNAL_BASE ||
  process.env.API_INTERNAL_BASE ||
  process.env.NEXT_PUBLIC_OSAKAMENESU_API_BASE ||
  process.env.NEXT_PUBLIC_API_BASE ||
  '/api'

function serializeCookieHeader(): string | undefined {
  const store = cookies()
  const entries = store.getAll()
  if (!entries.length) {
    return undefined
  }
  return entries.map((entry) => `${entry.name}=${entry.value}`).join('; ')
}

async function resolveFirstDashboardShopId(): Promise<string | null> {
  const cookieHeader = serializeCookieHeader()
  const url = buildApiUrl(INTERNAL_API_BASE, 'api/dashboard/shops?limit=1')

  try {
    const res = await fetch(url, {
      method: 'GET',
      headers: cookieHeader ? { cookie: cookieHeader } : undefined,
      cache: 'no-store',
      credentials: cookieHeader ? 'omit' : 'include',
    })

    if (!res.ok) {
      return null
    }

    const data = (await res.json().catch(() => undefined)) as
      | { shops?: Array<{ id?: string }> }
      | undefined

    const first = data?.shops?.[0]
    return typeof first?.id === 'string' ? first.id : null
  } catch {
    return null
  }
}

export const dynamic = 'force-dynamic'
export const revalidate = 0

export default async function DashboardIndexPage() {
  const firstShopId = await resolveFirstDashboardShopId()

  if (firstShopId) {
    redirect(`/dashboard/${firstShopId}`)
  }

  redirect('/dashboard/new')
}
