import { NextRequest, NextResponse } from 'next/server'

const REALM = 'Admin'
const FALLBACK_USER = 'yusaku0324'
const FALLBACK_PASS = 'sakanon0402'

function unauthorized(message: string) {
  return new NextResponse(message, {
    status: 401,
    headers: {
      'WWW-Authenticate': `Basic realm="${REALM}", charset="UTF-8"`,
    },
  })
}

export function middleware(request: NextRequest) {
  const user = process.env.ADMIN_BASIC_USER || FALLBACK_USER
  const pass = process.env.ADMIN_BASIC_PASS || FALLBACK_PASS

  const authHeader = request.headers.get('authorization')
  if (!authHeader || !authHeader.startsWith('Basic ')) {
    return unauthorized('Authentication required')
  }

  try {
    const decoded = atob(authHeader.slice('Basic '.length))
    const separator = decoded.indexOf(':')
    const providedUser = separator >= 0 ? decoded.slice(0, separator) : ''
    const providedPass = separator >= 0 ? decoded.slice(separator + 1) : ''

    if (providedUser !== user || providedPass !== pass) {
      return unauthorized('Invalid credentials')
    }
  } catch (error) {
    return unauthorized('Invalid credentials')
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/admin/:path*', '/api/admin/:path*'],
}
