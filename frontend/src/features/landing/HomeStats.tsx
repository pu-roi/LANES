"use client";

import { useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Users } from "lucide-react";
import { apiClient } from "@/lib/apiClient";
import { useToast } from "@/shared/ui";

interface PublicStats {
  daily_verified_reports: number;
  total_visitors: number;
}

interface VisitorActivityResponse extends PublicStats {
  recorded: boolean;
}

const VISITOR_ID_STORAGE_KEY = "lanes_visitor_id";
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function generateFallbackUUID(): string {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

function getOrCreateVisitorId(): string {
  const existingId = localStorage.getItem(VISITOR_ID_STORAGE_KEY);
  if (existingId && UUID_PATTERN.test(existingId)) return existingId;

  const visitorId =
    typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
      ? crypto.randomUUID()
      : generateFallbackUUID();
  localStorage.setItem(VISITOR_ID_STORAGE_KEY, visitorId);
  return visitorId;
}

function errorMessage(error: unknown, fallback: string): string {
  return error instanceof Error && error.message ? error.message : fallback;
}

export function HomeStats() {
  const { error: showError } = useToast();
  const queryClient = useQueryClient();
  const { data: stats, isPending: loading, error } = useQuery({
    queryKey: ["publicStats"],
    queryFn: () => apiClient.get<PublicStats>("/public/stats", { cache: "no-store" }),
    refetchInterval: 60_000,
  });

  useEffect(() => {
    if (error) showError("Stats Error", errorMessage(error, "Failed to fetch public stats"));
  }, [error, showError]);

  useEffect(() => {
    let cancelled = false;
    let trackingStarted = false;

    async function trackVisibleVisit() {
      if (trackingStarted) return;
      trackingStarted = true;
      try {
        await apiClient.post<VisitorActivityResponse>("/public/visits", {
          visitor_id: getOrCreateVisitorId(),
        });
        // Refetch current counts rather than overwriting a newer live snapshot
        // with a visitor request that started before a moderation action.
        if (!cancelled) void queryClient.invalidateQueries({ queryKey: ["publicStats"] });
      } catch (err: unknown) {
        if (!cancelled) {
          console.warn("Visitor telemetry could not be recorded:", err);
          showError("Visitor Count Unavailable", "Your visit could not be recorded. Flood statistics are still checked separately.");
          void queryClient.invalidateQueries({ queryKey: ["publicStats"] });
        }
      }
    }

    const onVisibilityChange = () => {
      if (document.visibilityState === "visible") {
        void trackVisibleVisit();
        void queryClient.invalidateQueries({ queryKey: ["publicStats"] });
      }
    };

    if (document.visibilityState === "visible") {
      void trackVisibleVisit();
    }
    document.addEventListener("visibilitychange", onVisibilityChange);

    return () => {
      cancelled = true;
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  }, [queryClient, showError]);

  return (
    <div className="p-2 flex items-center justify-center gap-10 h-full">
      {/* Current zones use the same eligibility rules as the public map. */}
      <div className="flex flex-col items-center text-center">
        <div className="bg-white/10 p-2.5 rounded-full text-white mb-2">
          <AlertTriangle className="w-5 h-5" />
        </div>
        <span className="text-3xl font-bold text-white">
          {loading ? "..." : stats?.daily_verified_reports ?? "—"}
        </span>
        <span className="text-xs font-medium text-white mt-1" title="Active map zones created today, counted once per zone using the UTC date.">Floods Today (UTC)</span>
      </div>

      <div className="h-16 w-px bg-blue-400/50"></div>

      {/* Site Visitors */}
      <div className="flex flex-col items-center text-center">
        <div className="bg-white/10 p-2.5 rounded-full text-white mb-2">
          <Users className="w-5 h-5" />
        </div>
        <span className="text-3xl font-bold text-white">
          {loading ? "..." : stats?.total_visitors.toLocaleString() ?? "—"}
        </span>
        <span className="text-xs font-medium text-white mt-1">Site Visitors</span>
      </div>
    </div>
  );
}
