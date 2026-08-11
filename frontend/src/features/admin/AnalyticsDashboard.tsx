"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/apiClient";
import { Loader2, TrendingUp, MapPin, AlertCircle, Download } from "lucide-react";
import { Button } from "@/shared/ui/Button";

interface StatItem {
  barangay?: string;
  location?: string;
  count: number;
}

interface AnalyticsStats {
  top_barangays: StatItem[];
  top_locations: StatItem[];
}

export default function AnalyticsDashboard() {
  const { data, isLoading } = useQuery({
    queryKey: ["analyticsStats"],
    queryFn: () => apiClient.get<AnalyticsStats>("/analytics/stats"),
  });

  const handleExport = () => {
    if (!data) return;
    
    let csv = "Type,Name,Alert Count\n";
    data.top_barangays.forEach(b => {
      csv += `Barangay,${b.barangay || "Unknown"},${b.count}\n`;
    });
    data.top_locations.forEach(l => {
      csv += `Location,${l.location || "Unknown"},${l.count}\n`;
    });
    
    const blob = new Blob([csv], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.setAttribute("hidden", "");
    a.setAttribute("href", url);
    a.setAttribute("download", "lanes_analytics_export.csv");
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1600px] mx-auto space-y-8">
      <div className="fixed top-6 right-6 z-[60]">
        <Button 
          onClick={handleExport} 
          disabled={isLoading || !data}
          className="flex items-center gap-2 shadow-lg hover:shadow-xl transition-shadow"
        >
          <Download className="w-4 h-4" />
          Export to CSV
        </Button>
      </div>

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <TrendingUp className="w-6 h-6 text-blue-600" />
            Spatial Analytics
          </h1>
          <p className="text-slate-500 mt-1">
            Data insights on flood hotspots for DRRMO reporting.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Barangays Table */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
            <MapPin className="w-5 h-5 text-orange-500" />
            Top Flooded Barangays
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-500">
                <tr>
                  <th className="px-4 py-3 font-medium rounded-l-lg">Rank</th>
                  <th className="px-4 py-3 font-medium">Barangay</th>
                  <th className="px-4 py-3 font-medium text-right rounded-r-lg">Incidents</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data?.top_barangays.map((item, idx) => (
                  <tr key={idx} className="hover:bg-slate-50 transition-colors">
                    <td className="px-4 py-3 font-semibold text-slate-400">#{idx + 1}</td>
                    <td className="px-4 py-3 font-medium text-slate-700">{item.barangay || "Unknown"}</td>
                    <td className="px-4 py-3 text-right">
                      <span className="bg-red-100 text-red-700 px-2.5 py-1 rounded-full text-xs font-bold">
                        {item.count}
                      </span>
                    </td>
                  </tr>
                ))}
                {data?.top_barangays.length === 0 && (
                  <tr>
                    <td colSpan={3} className="px-4 py-8 text-center text-slate-400 italic">
                      No data available
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Locations Table */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-orange-500" />
            Frequent Flood Locations (Streets)
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-500">
                <tr>
                  <th className="px-4 py-3 font-medium rounded-l-lg">Rank</th>
                  <th className="px-4 py-3 font-medium">Location</th>
                  <th className="px-4 py-3 font-medium text-right rounded-r-lg">Incidents</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data?.top_locations.map((item, idx) => (
                  <tr key={idx} className="hover:bg-slate-50 transition-colors">
                    <td className="px-4 py-3 font-semibold text-slate-400">#{idx + 1}</td>
                    <td className="px-4 py-3 font-medium text-slate-700 line-clamp-1" title={item.location}>
                      {item.location || "Unknown"}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span className="bg-orange-100 text-orange-700 px-2.5 py-1 rounded-full text-xs font-bold">
                        {item.count}
                      </span>
                    </td>
                  </tr>
                ))}
                {data?.top_locations.length === 0 && (
                  <tr>
                    <td colSpan={3} className="px-4 py-8 text-center text-slate-400 italic">
                      No data available
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
