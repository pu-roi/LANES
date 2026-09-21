"use client";

import { BarChart3, History } from "lucide-react";
import { Tabs } from "@/shared/ui";
import { useState } from "react";
import { FloodEventAnalytics } from "@/features/flood-history/FloodEventAnalytics";
import { FloodEventRecords } from "@/features/flood-history/FloodEventRecords";

export default function FloodHistoryPage() {
  const [tab, setTab] = useState<"overview" | "records">("overview");
  return <div className="w-full max-w-[1600px] mx-auto space-y-6 text-gray-900 pb-[calc(var(--bottom-nav-height)+env(safe-area-inset-bottom))]">
    <div><h1 className="text-2xl font-bold tracking-tight text-gray-900">Flood History &amp; Analytics</h1><p className="mt-1 text-sm text-gray-500">Review verified Flood Events separately from active routing zones and supporting reports.</p></div>
    <Tabs tabs={[{ id: "overview", label: "Overview & Analytics", icon: BarChart3 }, { id: "records", label: "Flood Event Records", icon: History }]} activeTab={tab} onChange={setTab} variant="underline" layoutId="flood-history-tabs" className="w-full" />
    {tab === "records" ? <FloodEventRecords /> : <FloodEventAnalytics />}</div>;
}
