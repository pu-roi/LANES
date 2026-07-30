"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, Users } from "lucide-react";
import { apiClient } from "@/lib/apiClient";
import { useToast } from "@/shared/ui";

interface PublicStats {
  daily_verified_reports: number;
  total_visitors: number;
}

export function HomeStats() {
  const toast = useToast();
  const [stats, setStats] = useState<PublicStats>({ daily_verified_reports: 0, total_visitors: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchStats() {
      try {
        const hasVisited = localStorage.getItem("lanes_has_visited");
        const shouldIncrement = !hasVisited;
        
        if (shouldIncrement) {
          localStorage.setItem("lanes_has_visited", "true");
        }

        const data = await apiClient.get<PublicStats>(`/public/stats?increment=${shouldIncrement}`);
        setStats(data);
      } catch (err: any) {
        toast.error("Stats Error", err.message || "Failed to fetch public stats");
      } finally {
        setLoading(false);
      }
    }
    fetchStats();
  }, []);

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
