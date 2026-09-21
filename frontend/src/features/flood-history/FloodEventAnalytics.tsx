"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Download, FileJson, FileSpreadsheet, RefreshCw } from "lucide-react";
import { Button, Card, CardContent, useToast } from "@/shared/ui";
import {
  downloadFloodEventPlanningData,
  getFloodEventPlanningAnalytics,
  type FloodHistoryFilters,
} from "./floodHistoryApi";
import { FloodEventVisualizations } from "./FloodEventVisualizations";

const initialFilters: FloodHistoryFilters = {
  status: "all", severity: "", dateFrom: "", dateTo: "", barangay: "", road: "", search: "",
};

function FilterControls({ filters, onChange }: { filters: FloodHistoryFilters; onChange: (filters: FloodHistoryFilters) => void }) {
  const set = <K extends keyof FloodHistoryFilters>(key: K, value: FloodHistoryFilters[K]) => onChange({ ...filters, [key]: value });
  return <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7">
    <select aria-label="Analytics event status" value={filters.status} onChange={(event) => set("status", event.target.value as FloodHistoryFilters["status"])} className="h-9 rounded-lg border border-slate-300 bg-white px-3 text-sm"><option value="all">All statuses</option><option value="active">Active</option><option value="ended">Ended</option></select>
    <select aria-label="Analytics peak severity" value={filters.severity} onChange={(event) => set("severity", event.target.value as FloodHistoryFilters["severity"])} className="h-9 rounded-lg border border-slate-300 bg-white px-3 text-sm"><option value="">All severity</option><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option><option value="extreme">Extreme</option></select>
    <input aria-label="Filter analytics by barangay" value={filters.barangay} onChange={(event) => set("barangay", event.target.value)} placeholder="Barangay" className="h-9 rounded-lg border border-slate-300 px-3 text-sm" />
    <input aria-label="Filter analytics by road" value={filters.road} onChange={(event) => set("road", event.target.value)} placeholder="Road / street" className="h-9 rounded-lg border border-slate-300 px-3 text-sm" />
    <input aria-label="Search analytics locations" value={filters.search} onChange={(event) => set("search", event.target.value)} placeholder="Search place" className="h-9 rounded-lg border border-slate-300 px-3 text-sm xl:col-span-1" />
    <label className="flex h-9 items-center gap-2 rounded-lg border border-slate-300 px-3 text-xs text-slate-500">From <input type="date" value={filters.dateFrom} onChange={(event) => set("dateFrom", event.target.value)} className="min-w-0 flex-1 text-sm text-slate-700 outline-none" /></label>
    <label className="flex h-9 items-center gap-2 rounded-lg border border-slate-300 px-3 text-xs text-slate-500">To <input type="date" value={filters.dateTo} onChange={(event) => set("dateTo", event.target.value)} className="min-w-0 flex-1 text-sm text-slate-700 outline-none" /></label>
  </div>;
}

export function FloodEventAnalytics() {
  const [filters, setFilters] = useState(initialFilters);
  const [isExporting, setIsExporting] = useState(false);
  const toast = useToast();
  const analyticsQuery = useQuery({ queryKey: ["flood-event-planning-analytics", filters], queryFn: () => getFloodEventPlanningAnalytics(filters) });
  const exportData = async (exportType: "records" | "analytics", exportFormat: "csv" | "json") => {
    setIsExporting(true);
    try {
      await downloadFloodEventPlanningData(filters, exportType, exportFormat);
      toast.success("Planning export downloaded", "The file contains approved event-level planning data only.");
    } catch (error) {
      toast.error("Export failed", error instanceof Error ? error.message : "Please try again.");
    } finally {
      setIsExporting(false);
    }
  };

  return <section className="space-y-4">
    <Card><CardContent className="space-y-4 p-4 sm:p-5"><div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between"><div><h2 className="font-semibold text-slate-900">City planning analytics</h2><p className="mt-1 text-sm text-slate-500">Every value counts distinct verified Flood Events. Approved reports are shown only as a separate confidence signal.</p></div><div className="flex flex-wrap gap-2"><Button size="sm" variant="outline" onClick={() => void exportData("records", "csv")} disabled={isExporting}><FileSpreadsheet className="mr-1 h-4 w-4" />Records CSV</Button><Button size="sm" variant="outline" onClick={() => void exportData("records", "json")} disabled={isExporting}><FileJson className="mr-1 h-4 w-4" />Records JSON</Button><Button size="sm" variant="outline" onClick={() => void exportData("analytics", "csv")} disabled={isExporting}><Download className="mr-1 h-4 w-4" />Analytics CSV</Button><Button size="sm" variant="outline" onClick={() => void exportData("analytics", "json")} disabled={isExporting}><FileJson className="mr-1 h-4 w-4" />Analytics JSON</Button><Button size="sm" variant="ghost" onClick={() => void analyticsQuery.refetch()} disabled={analyticsQuery.isFetching}><RefreshCw className="mr-1 h-4 w-4" />Refresh</Button></div></div><FilterControls filters={filters} onChange={setFilters} /><Button size="sm" variant="ghost" onClick={() => setFilters(initialFilters)}>Clear filters</Button></CardContent></Card>
    {analyticsQuery.isLoading ? <Card><CardContent className="py-16 text-center text-sm text-slate-500">Calculating distinct-event planning analytics…</CardContent></Card> : analyticsQuery.isError || !analyticsQuery.data ? <Card className="border-red-200 bg-red-50"><CardContent className="py-8 text-sm text-red-800">Planning analytics could not be loaded. Please refresh and try again.</CardContent></Card> : <FloodEventVisualizations analytics={analyticsQuery.data} />}
  </section>;
}
