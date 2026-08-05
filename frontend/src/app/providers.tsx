"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { ToastProvider } from "@/shared/ui";
import GlobalMap from "@/features/map/GlobalMap";
import { useSSE } from "@/hooks/useSSE";

function AppHooks() {
  useSSE();
  return null;
}

export default function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // Default settings for LANES
            staleTime: 0, // Data is immediately considered stale so it refetches in the background on mount/navigation
            refetchOnWindowFocus: true, // Auto-refetch when user switches back to the app
            retry: 3, // Retry failed requests 3 times (good for bad network areas)
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <AppHooks />
      <ToastProvider>
        <GlobalMap />
        {children}
      </ToastProvider>
    </QueryClientProvider>
  );
}
