import Image from 'next/image'
import Link from 'next/link'

import { Badge } from '@/components/ui/Badge'
import { Card } from '@/components/ui/Card'

export type TherapistHit = {
  id: string
  staffId: string
  name: string
  alias: string | null
  headline: string | null
  specialties: string[]
  avatarUrl: string | null
  rating: number | null
  reviewCount: number | null
  shopId: string
  shopSlug: string | null
  shopName: string
  shopArea: string
  shopAreaName: string | null
}

const formatter = new Intl.NumberFormat('ja-JP')

function buildShopHref(hit: TherapistHit) {
  const base = hit.shopSlug || hit.shopId
  return `/profiles/${base}`
}

function buildStaffHref(hit: TherapistHit) {
  const base = hit.shopSlug || hit.shopId
  return `/profiles/${base}/staff/${encodeURIComponent(hit.staffId)}`
}

export function TherapistCard({ hit }: { hit: TherapistHit }) {
  const staffHref = buildStaffHref(hit)
  const shopHref = buildShopHref(hit)

  return (
    <Card className="h-full" interactive>
      <Link href={staffHref} className="block focus:outline-none group">
        <div className="relative h-48 overflow-hidden rounded-t-card bg-neutral-surfaceAlt">
          {hit.avatarUrl ? (
            <Image
              src={hit.avatarUrl}
              alt={`${hit.name}の写真`}
              fill
              className="object-cover transition duration-300 group-hover:scale-105"
              sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
            />
          ) : (
            <div className="flex h-full items-center justify-center bg-neutral-surfaceAlt text-neutral-textMuted">
              <span className="text-4xl font-semibold">{hit.name.slice(0, 1)}</span>
            </div>
          )}
        </div>
      </Link>
      <div className="space-y-3 p-4">
        <div className="space-y-1">
          <div className="flex items-start justify-between gap-2">
            <h3 className="text-lg font-semibold text-neutral-text">
              <Link href={staffHref} className="transition hover:text-brand-primary">
                {hit.name}
              </Link>
            </h3>
            {hit.rating ? (
              <span className="flex items-center gap-1 text-sm text-neutral-text">
                <span aria-hidden className="text-amber-400">★</span>
                <span className="font-semibold">{hit.rating.toFixed(1)}</span>
                {typeof hit.reviewCount === 'number' ? (
                  <span className="text-xs text-neutral-textMuted">({formatter.format(hit.reviewCount)}件)</span>
                ) : null}
              </span>
            ) : null}
          </div>
          {hit.alias ? <p className="text-xs text-neutral-textMuted">{hit.alias}</p> : null}
          {hit.headline ? <p className="text-sm text-neutral-textMuted line-clamp-2">{hit.headline}</p> : null}
        </div>

        {hit.specialties.length ? (
          <div className="flex flex-wrap gap-2">
            {hit.specialties.slice(0, 4).map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center rounded-badge border border-neutral-borderLight bg-neutral-surfaceAlt px-2 py-0.5 text-[12px] text-neutral-text"
              >
                {tag}
              </span>
            ))}
          </div>
        ) : null}

        <div className="flex items-center justify-between gap-2 text-sm text-neutral-text">
          <div>
            <Link href={shopHref} className="font-semibold text-brand-primaryDark hover:underline">
              {hit.shopName}
            </Link>
            <div className="text-xs text-neutral-textMuted">
              {hit.shopAreaName || hit.shopArea}
            </div>
          </div>
          <Badge variant="outline">セラピスト</Badge>
        </div>
      </div>
    </Card>
  )
}

export default TherapistCard
