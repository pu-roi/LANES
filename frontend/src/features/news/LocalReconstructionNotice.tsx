"use client";

import { useQuery } from "@tanstack/react-query";
import { getLocalNewsSimulation } from "@/lib/localNewsSimulation";

/** Labels the local historical session without changing either map renderer. */
export function LocalReconstructionNotice() {
  const mode = useQuery({ queryKey: ["local-news-simulation-mode"], queryFn: getLocalNewsSimulation,
    staleTime: Infinity, retry: false });
  if (!mode.isError && mode.data !== "persisted") return null;
  return (
    <div className="pointer-events-none fixed bottom-[calc(var(--bottom-nav-height,0px)+env(safe-area-inset-bottom)+12px)] left-1/2 z-[1100] max-w-[calc(100vw-24px)] -translate-x-1/2 rounded-lg bg-slate-900 px-3 py-2 text-center text-xs font-medium text-white shadow-lg md:text-sm"
      role={mode.isError ? "alert" : "status"}>
      {mode.isError ? mode.error.message : "Historical flood reconstruction"}
    </div>
  );
}
