"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { ToastProvider } from "@/shared/ui";
import GlobalMap from "@/features/map/GlobalMap";
import { useSSE } from "@/hooks/useSSE";
import { useLiveSync } from "@/hooks/useLiveSync";

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
      {children}
    </QueryClientProvider>
  );
}

export function AppProviders({ children }: { children: React.ReactNode }) {
  return (
    <>
      <AppHooks />
      <ToastProvider>
        <GlobalMap />
        {children}
      </ToastProvider>
    </>
  );
}
