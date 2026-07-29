import type { NextConfig } from "next";
import withPWAInit from "@ducanh2912/next-pwa";
import os from "os";

const getLocalIPs = () => {
  const interfaces = os.networkInterfaces();
  const ips = ['localhost', '127.0.0.1', 'juiciness-cosmetics-routing.ngrok-free.dev'];
  for (const name of Object.keys(interfaces)) {
    for (const iface of interfaces[name] || []) {
      if (iface.family === 'IPv4' && !iface.internal) {
        ips.push(iface.address);
      }
    }
  }
  return ips;
};

const withPWA = withPWAInit({
  dest: "public",
  disable: process.env.NODE_ENV === "development",
  workboxOptions: {
    runtimeCaching: [
      {
        urlPattern: /^https:\/\/[a-z]\.tile\.openstreetmap\.org\/.*/i,
        handler: "StaleWhileRevalidate",
        options: {
          cacheName: "map-tiles",
          expiration: {
            maxEntries: 250, // Cache recent tiles without blowing up storage
            maxAgeSeconds: 30 * 24 * 60 * 60, // 30 Days
          },
        },
      },
      {
        urlPattern: /^https:\/\/basemaps\.cartocdn\.com\/.*/i, // Common fallback
        handler: "StaleWhileRevalidate",
        options: {
          cacheName: "carto-tiles",
          expiration: {
            maxEntries: 250,
            maxAgeSeconds: 30 * 24 * 60 * 60,
          },
        },
      }
    ],
  },
});

const nextConfig: NextConfig = {
  // @ts-ignore - allowedDevOrigins is suggested by Next.js CLI but may lack TS definitions
  allowedDevOrigins: getLocalIPs(),
  turbopack: {},
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: 'http://127.0.0.1:8000/api/v1/:path*',
      },
    ];
  },
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          { key: 'Cache-Control', value: 'no-store, no-cache, must-revalidate, proxy-revalidate' },
          { key: 'Pragma', value: 'no-cache' },
          { key: 'Expires', value: '0' },
        ],
      },
    ];
  },
};

export default withPWA(nextConfig);
