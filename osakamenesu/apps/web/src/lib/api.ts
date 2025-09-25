const DEFAULT_SITE_ORIGIN = process.env.NEXT_PUBLIC_SITE_URL || 'http://127.0.0.1:3000'

function normalizeBase(base: string): string {
  return base.replace(/\/+$/, '')
}

export function resolveApiBases(): string[] {
  const internal =
    process.env.OSAKAMENESU_API_INTERNAL_BASE ||
    process.env.API_INTERNAL_BASE ||
    ''
  const publicBase =
    process.env.NEXT_PUBLIC_OSAKAMENESU_API_BASE ||
    process.env.NEXT_PUBLIC_API_BASE ||
    '/api'

  const bases: string[] = []
  if (internal) {
    bases.push(internal)
  }
  bases.push(publicBase)
  return bases
}

export function buildApiUrl(base: string, path: string): string {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  if (!base) {
    return `${normalizeBase(DEFAULT_SITE_ORIGIN)}${normalizedPath}`
  }

  if (base.startsWith('http://') || base.startsWith('https://')) {
    return `${normalizeBase(base)}${normalizedPath}`
  }

  const prefix = normalizeBase(base)
  if (!prefix) {
    return normalizedPath
  }

  if (normalizedPath.startsWith(`${prefix}/`) || normalizedPath === prefix) {
    return normalizedPath
  }

  return `${prefix}${normalizedPath}`
}
