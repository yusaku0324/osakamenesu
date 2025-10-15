export type StaffIdentifierSource = {
  id?: string | null
  alias?: string | null
  name?: string | null
}

function decode(value: string) {
  try {
    return decodeURIComponent(value)
  } catch {
    return value
  }
}

export function slugifyStaffIdentifier(value?: string | null): string {
  if (value === undefined || value === null) return ''
  const decoded = decode(String(value))
  const normalized = decoded.normalize('NFKC').trim()
  if (!normalized) return ''

  const collapsed = normalized
    .toLowerCase()
    .replace(/[^\p{L}\p{N}]+/gu, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '')

  if (collapsed) return collapsed

  const fallback = normalized.replace(/\s+/g, '-').toLowerCase()
  return fallback || ''
}

export function buildStaffIdentifier(staff: StaffIdentifierSource, fallback?: string): string {
  const candidates = [staff.id, staff.alias, staff.name]
  for (const candidate of candidates) {
    const slug = slugifyStaffIdentifier(candidate)
    if (slug) return slug
  }

  if (fallback) {
    const slug = slugifyStaffIdentifier(fallback)
    if (slug) return slug

    const prefixed = slugifyStaffIdentifier(`staff-${fallback}`)
    if (prefixed) return prefixed
  }

  return 'staff'
}

export function staffMatchesIdentifier(staff: StaffIdentifierSource, target: string): boolean {
  const normalizedTarget = slugifyStaffIdentifier(target)
  if (!normalizedTarget) return false

  const possibilities = new Set<string>()
  for (const candidate of [staff.id, staff.alias, staff.name]) {
    const slug = slugifyStaffIdentifier(candidate)
    if (slug) possibilities.add(slug)
  }

  const generated = buildStaffIdentifier(staff)
  if (generated) possibilities.add(generated)

  return possibilities.has(normalizedTarget)
}
