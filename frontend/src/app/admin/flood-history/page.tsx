"use client";

import { BarChart3, History } from "lucide-react";
import { Tabs } from "@/shared/ui";
import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import dynamic from "next/dynamic";
import { FloodEventAnalytics } from "@/features/flood-history/FloodEventAnalytics";

const FloodEventRecords = dynamic(() => import("@/features/flood-history/FloodEventRecords").then(module => module.FloodEventRecords), { ssr: false });

export default function FloodHistoryPage() { return <Suspense><FloodHistoryContent /></Suspense>; }

function FloodHistoryContent() {
  const params = useSearchParams();
  const router = useRouter();
  const [tab, setTab] = useState<"overview" | "records">(params.get("event_id") ? "records" : "overview");
  const [recordsOpened, setRecordsOpened] = useState(!!params.get("event_id"));
  useEffect(() => {
    if (!params.has("dataset_id")) return;
    const next = new URLSearchParams(params.toString());
    next.delete("dataset_id");
    router.replace(`/admin/flood-history${next.size ? `?${next}` : ""}`, { scroll: false });
  }, [params, router]);
  return <div className="w-full max-w-[1600px] mx-auto space-y-6 text-gray-900 pb-[calc(var(--bottom-nav-height)+env(safe-area-inset-bottom))]">
    <div><h1 className="text-2xl font-bold tracking-tight text-gray-900">Flood History &amp; Analytics</h1><p className="mt-1 text-sm text-gray-500">Review verified Flood Events separately from active routing zones and supporting reports.</p></div>
    <Tabs
      tabs={[
        { id: "overview", label: "Analytics", icon: BarChart3 },
        { id: "records", label: "Flood Events", icon: History },
      ]}
      activeTab={tab}
      onChange={(next) => { setTab(next); if (next === "records") setRecordsOpened(true); }}
      variant="underline"
      layoutId="flood-history-tabs"
      className="w-full"
    />
    <div className={tab === "overview" ? "block" : "hidden"}><FloodEventAnalytics active={tab === "overview"} /></div>
    {recordsOpened && <div className={tab === "records" ? "block" : "hidden"}><FloodEventRecords initialEventId={Number(params.get("event_id")) || null} active={tab === "records"} /></div>}</div>;
}
