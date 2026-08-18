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
  fallbacks: {
    document: "/~offline",
  },
  workboxOptions: {
    runtimeCaching: [
      {
        urlPattern: /^https:\/\/[a-z]\.tile\.openstreetmap\.org\/.*/i,
        handler: "StaleWhileRevalidate",
        options: {
          cacheName: "osm-map-tiles",
          expiration: {
            maxEntries: 1500, // Generous tile cache for offline exploration
            maxAgeSeconds: 30 * 24 * 60 * 60, // 30 Days
          },
        },
      },
      {
        urlPattern: /^https:\/\/api\.maptiler\.com\/tiles\/.*/i,
        handler: "StaleWhileRevalidate",
        options: {
          cacheName: "maptiler-tiles",
          expiration: {
            maxEntries: 1500,
            maxAgeSeconds: 30 * 24 * 60 * 60,
          },
        },
      },
      {
        urlPattern: /^https:\/\/basemaps\.cartocdn\.com\/.*/i,
        handler: "StaleWhileRevalidate",
        options: {
          cacheName: "carto-tiles",
          expiration: {
            maxEntries: 500,
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
        destination: `${process.env.BACKEND_URL || 'http://127.0.0.1:8000'}/api/v1/:path*`,
      },
    ];
  },
};

export default withPWA(nextConfig);
