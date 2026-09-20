"use client";

import { useQuery } from "@tanstack/react-query";
import { BarChart3, Clock, History, MapPin, RefreshCw, type LucideIcon } from "lucide-react";
import { apiClient } from "@/lib/apiClient";
import { Button, Card, CardContent, Tabs } from "@/shared/ui";
import { useState } from "react";
import { FloodEventRecords } from "@/features/flood-history/FloodEventRecords";

type FloodEvent = { id: number; status: "active" | "ended"; verified_at: string; ended_at?: string | null; peak_severity: string; peak_depth?: string | null };

export default function FloodHistoryPage() {
  const [tab, setTab] = useState<"overview" | "records">("overview");
  const { data: events = [], isLoading, isError, refetch } = useQuery({ queryKey: ["flood-events"], queryFn: () => apiClient.get<FloodEvent[]>("/admin/flood-events") });
  const ended = events.filter((event) => event.status === "ended").length;
  const active = events.length - ended;
  const overviewMetrics: Array<{ label: string; value: number; Icon: LucideIcon }> = [
    { label: "Verified events", value: events.length, Icon: History },
    { label: "Ended events", value: ended, Icon: Clock },
    { label: "Active events", value: active, Icon: MapPin },
    { label: "Peak extreme", value: events.filter((event) => event.peak_severity === "extreme").length, Icon: BarChart3 },
  ];
  return <div className="w-full max-w-[1600px] mx-auto space-y-6 text-gray-900 pb-[calc(var(--bottom-nav-height)+env(safe-area-inset-bottom))]">
    <div className="flex flex-col items-start justify-between gap-4 md:flex-row md:items-center"><div><h1 className="text-2xl font-bold tracking-tight text-gray-900">Flood History &amp; Analytics</h1><p className="mt-1 text-sm text-gray-500">Review verified Flood Events separately from active routing zones and supporting reports.</p></div><Button variant="outline" onClick={() => void refetch()} disabled={isLoading} className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"><RefreshCw className="h-4 w-4" />Refresh</Button></div>
    <Tabs tabs={[{ id: "overview", label: "Overview & Analytics", icon: BarChart3 }, { id: "records", label: "Flood Event Records", icon: History }]} activeTab={tab} onChange={setTab} variant="underline" layoutId="flood-history-tabs" className="w-full" />
    {tab === "records" ? <FloodEventRecords /> : isLoading ? <Card><CardContent className="py-16 text-center text-sm text-slate-500">Loading verified Flood Events…</CardContent></Card> : isError ? <Card className="border-red-200 bg-red-50"><CardContent className="py-8 text-sm text-red-800">Flood History could not be loaded. Please refresh and try again.</CardContent></Card> : <><div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{overviewMetrics.map(({ label, value, Icon }) => <Card key={label}><CardContent className="flex items-center justify-between p-5"><div><p className="text-sm text-slate-500">{label}</p><p className="mt-1 text-3xl font-bold text-slate-900">{value}</p></div><Icon className="h-6 w-6 text-blue-600" /></CardContent></Card>)}</div><Card><CardContent className="py-12 text-center text-sm text-slate-500">Event-based charts and recurrence analysis will appear here as the historical dataset grows.</CardContent></Card></>}</div>;
}
