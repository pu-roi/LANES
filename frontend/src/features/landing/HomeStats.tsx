"use client";

import { useEffect, useState } from "react";
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

function getOrCreateVisitorId(): string {
  const existingId = localStorage.getItem(VISITOR_ID_STORAGE_KEY);
  if (existingId && UUID_PATTERN.test(existingId)) return existingId;

  const visitorId = crypto.randomUUID();
  localStorage.setItem(VISITOR_ID_STORAGE_KEY, visitorId);
  return visitorId;
}

function errorMessage(error: unknown, fallback: string): string {
  return error instanceof Error && error.message ? error.message : fallback;
}

export function HomeStats() {
  const { error: showError } = useToast();
  const [stats, setStats] = useState<PublicStats>({ daily_verified_reports: 0, total_visitors: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    let trackingStarted = false;

    async function fetchStats() {
      try {
        const data = await apiClient.get<PublicStats>("/public/stats");
        if (!cancelled) setStats(data);
      } catch (err: unknown) {
        if (!cancelled) showError("Stats Error", errorMessage(err, "Failed to fetch public stats"));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    async function trackVisibleVisit() {
      if (trackingStarted) return;
      trackingStarted = true;
      try {
        const data = await apiClient.post<VisitorActivityResponse>("/public/visits", {
          visitor_id: getOrCreateVisitorId(),
        });
        if (!cancelled) setStats(data);
      } catch (err: unknown) {
        if (!cancelled) {
          showError("Visitor Tracking Error", errorMessage(err, "Failed to update visitor statistics"));
          await fetchStats();
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    const onVisibilityChange = () => {
      if (document.visibilityState === "visible") {
        document.removeEventListener("visibilitychange", onVisibilityChange);
        void trackVisibleVisit();
      }
    };

    if (document.visibilityState === "visible") {
      void trackVisibleVisit();
    } else {
      void fetchStats();
      document.addEventListener("visibilitychange", onVisibilityChange);
    }

    return () => {
      cancelled = true;
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  }, [showError]);

  return (
    <div className="p-2 flex items-center justify-center gap-10 h-full">
      {/* Floods Today */}
      <div className="flex flex-col items-center text-center">
        <div className="bg-white/10 p-2.5 rounded-full text-white mb-2">
          <AlertTriangle className="w-5 h-5" />
        </div>
        <span className="text-3xl font-bold text-white">
          {loading ? "..." : stats.daily_verified_reports}
        </span>
        <span className="text-xs font-medium text-white mt-1">Floods Today</span>
      </div>

      <div className="h-16 w-px bg-blue-400/50"></div>

      {/* Site Visitors */}
      <div className="flex flex-col items-center text-center">
        <div className="bg-white/10 p-2.5 rounded-full text-white mb-2">
          <Users className="w-5 h-5" />
        </div>
        <span className="text-3xl font-bold text-white">
          {loading ? "..." : stats.total_visitors.toLocaleString()}
        </span>
        <span className="text-xs font-medium text-white mt-1">Site Visitors</span>
      </div>
    </div>
  );
}
