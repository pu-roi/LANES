"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Download, FileJson, FileSpreadsheet, RefreshCw } from "lucide-react";
import { Button, Card, CardContent, DatePicker, Input, Select, useToast } from "@/shared/ui";
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
    <Select ariaLabel="Analytics event status" options={[{ value: "all", label: "All statuses" }, { value: "active", label: "Active" }, { value: "ended", label: "Ended" }]} value={filters.status} onChange={(event) => set("status", event.target.value as FloodHistoryFilters["status"])} />
    <Select ariaLabel="Analytics peak severity" options={[{ value: "", label: "All severity" }, { value: "low", label: "Low" }, { value: "medium", label: "Medium" }, { value: "high", label: "High" }, { value: "extreme", label: "Extreme" }]} value={filters.severity} onChange={(event) => set("severity", event.target.value as FloodHistoryFilters["severity"])} />
    <Input aria-label="Filter analytics by barangay" value={filters.barangay} onChange={(event) => set("barangay", event.target.value)} placeholder="Barangay" />
    <Input aria-label="Filter analytics by road" value={filters.road} onChange={(event) => set("road", event.target.value)} placeholder="Road / street" />
    <Input aria-label="Search analytics locations" value={filters.search} onChange={(event) => set("search", event.target.value)} placeholder="Search place" />
    <DatePicker emptyDisplay="From date" ariaLabel="Analytics date from" value={filters.dateFrom} onChange={(event) => set("dateFrom", event.target.value)} />
    <DatePicker emptyDisplay="To date" ariaLabel="Analytics date to" value={filters.dateTo} onChange={(event) => set("dateTo", event.target.value)} align="right" />
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
    <Card className="shadow-sm"><CardContent className="space-y-4 p-4"><div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between"><div><h2 className="text-sm font-bold uppercase tracking-wider text-slate-900">City planning analytics</h2><p className="mt-1 text-xs text-slate-500">Every value counts distinct verified Flood Events. Approved reports are a separate confidence signal.</p></div><div className="flex flex-wrap gap-2"><Button size="sm" variant="outline" onClick={() => void exportData("records", "csv")} disabled={isExporting}><FileSpreadsheet className="mr-1 h-4 w-4" />Records CSV</Button><Button size="sm" variant="outline" onClick={() => void exportData("records", "json")} disabled={isExporting}><FileJson className="mr-1 h-4 w-4" />Records JSON</Button><Button size="sm" variant="outline" onClick={() => void exportData("analytics", "csv")} disabled={isExporting}><Download className="mr-1 h-4 w-4" />Analytics CSV</Button><Button size="sm" variant="outline" onClick={() => void exportData("analytics", "json")} disabled={isExporting}><FileJson className="mr-1 h-4 w-4" />Analytics JSON</Button><Button size="sm" variant="ghost" onClick={() => void analyticsQuery.refetch()} disabled={analyticsQuery.isFetching}><RefreshCw className="mr-1 h-4 w-4" />Refresh</Button></div></div><FilterControls filters={filters} onChange={setFilters} /><Button size="sm" variant="ghost" onClick={() => setFilters(initialFilters)}>Clear filters</Button></CardContent></Card>
    {analyticsQuery.isLoading ? <Card><CardContent className="py-16 text-center text-sm text-slate-500">Calculating distinct-event planning analytics…</CardContent></Card> : analyticsQuery.isError || !analyticsQuery.data ? <Card className="border-red-200 bg-red-50"><CardContent className="py-8 text-sm text-red-800">Planning analytics could not be loaded. Please refresh and try again.</CardContent></Card> : <FloodEventVisualizations analytics={analyticsQuery.data} />}
  </section>;
}
