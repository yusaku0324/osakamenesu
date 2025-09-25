/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    // Allow typical dev sources; adjust for production as needed
    remotePatterns: [
      { protocol: 'https', hostname: 'picsum.photos' },
      { protocol: 'https', hostname: 'images.unsplash.com' },
      { protocol: 'https', hostname: 'i.pravatar.cc' },
      { protocol: 'http', hostname: 'localhost' },
      { protocol: 'http', hostname: '127.0.0.1' },
    ],
  },
  async rewrites() {
    return {
      beforeFiles: [],
      afterFiles: [],
      // Fall back to the API container only when Next.js has no matching route on disk
      fallback: [
        { source: '/api/:path*', destination: 'http://osakamenesu-api:8000/api/:path*' },
      ],
    }
  },
}

module.exports = nextConfig
