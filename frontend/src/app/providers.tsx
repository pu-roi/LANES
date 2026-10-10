"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import dynamic from "next/dynamic";
import { usePathname } from "next/navigation";
import { ToastProvider, SmoothScroll } from "@/shared/ui";
import { useSSE } from "@/hooks/useSSE";
import { useLiveSync } from "@/hooks/useLiveSync";
import { LocalReconstructionNotice } from "@/features/news/LocalReconstructionNotice";

const GlobalMap = dynamic(() => import("@/features/map/GlobalMap"), { ssr: false });

function AppHooks() {
  useSSE();
  useLiveSync();
  return null;
}

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 0,
            refetchOnWindowFocus: true,
            retry: 3,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <LocalReconstructionNotice />
      {children}
    </QueryClientProvider>
  );
}

export function AppProviders({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isMapRoute = pathname === "/map" || pathname === "/analytics" || pathname === "/admin/analytics";
  const [hasOpenedMap, setHasOpenedMap] = useState(false);
  // Once opened, retain route/report state and map navigation listeners across
  // commuter pages. A first visit to Home or Feed need not initialize WebGL.
  if (isMapRoute && !hasOpenedMap) setHasOpenedMap(true);

  return (
    <>
      <ToastProvider>
        <AppHooks />
        <SmoothScroll>
          {(isMapRoute || hasOpenedMap) && <GlobalMap />}
          {children}
        </SmoothScroll>
      </ToastProvider>
    </>
  );
}
