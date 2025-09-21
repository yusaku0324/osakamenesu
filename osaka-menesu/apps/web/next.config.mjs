/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    // Allow typical dev sources; adjust for production as needed
    remotePatterns: [
      { protocol: 'https', hostname: 'picsum.photos' },
      { protocol: 'http', hostname: 'localhost' },
      { protocol: 'http', hostname: '127.0.0.1' },
    ],
  },
};
export default nextConfig;
