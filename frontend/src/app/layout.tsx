import type { Metadata } from "next";
import { Open_Sans, Roboto_Mono } from "next/font/google";
import "./globals.css";
import "maplibre-gl/dist/maplibre-gl.css";
import NavigationWrapper from "@/features/navigation/NavigationWrapper";
import { QueryProvider, AppProviders } from "./providers";
import OfflineBanner from "@/features/offline/OfflineBanner";
import { NotificationBell } from "@/features/notifications/NotificationBell";

const openSans = Open_Sans({
  variable: "--font-open-sans",
  subsets: ["latin"],
});

const robotoMono = Roboto_Mono({
  variable: "--font-roboto-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "LANES Navigation",
  description: "Flood-Adaptive Route Calculation Platform",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "LANES",
  },
};

export const viewport = {
  themeColor: "#ffffff",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${openSans.variable} ${robotoMono.variable} antialiased`}
    >
      <head>
        <meta httpEquiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
        <meta httpEquiv="Pragma" content="no-cache" />
        <meta httpEquiv="Expires" content="0" />
      </head>
      <body suppressHydrationWarning className="min-h-screen flex flex-col font-sans bg-gray-50 text-slate-900">
        <OfflineBanner />
        <QueryProvider>
          <NavigationWrapper>
            <AppProviders>
              {children}
              <NotificationBell />
            </AppProviders>
          </NavigationWrapper>
        </QueryProvider>
      </body>
    </html>
  );
}
