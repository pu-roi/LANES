"use client";

import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { Activity, CloudRain, Inbox, Map, Rss } from "lucide-react";
import { Button, Tabs } from "@/shared/ui";
import { NewsResults } from "./NewsResults";
import { NewsCollectionDrawer } from "./NewsCollectionDrawer";
import { NewsSourcesDrawer } from "./NewsSourcesDrawer";
import { useNewsSimulation } from "./useNewsSimulation";
import { NewsAutomationPanel } from "./NewsAutomationPanel";

export default function NewsIntelligencePage() {
  const router = useRouter();
  const simulation = useNewsSimulation();
  const [activeTab, setActiveTab] = useState<"overview" | "areas">("overview");
  const [collectionOpen, setCollectionOpen] = useState(false);
  const closeCollection = useCallback(() => setCollectionOpen(false), []);
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const closeSources = useCallback(() => setSourcesOpen(false), []);

  return (
    <div className="mx-auto w-full max-w-[1600px] space-y-6 pb-[calc(var(--bottom-nav-height)+env(safe-area-inset-bottom))] text-gray-900">
      <div className="flex flex-col items-start justify-between gap-4 lg:flex-row lg:items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">News Intelligence</h1>
          <p className="mt-1 text-sm text-gray-500">Track news collection and reported flood areas.</p>
        </div>
        <div className="flex w-full flex-wrap gap-2 lg:w-auto">
          <Button type="button" variant="outline" className="min-h-11 gap-2" onClick={() => setCollectionOpen(true)}><Inbox className="size-4" aria-hidden="true" />Collection status</Button>
          <Button type="button" variant="outline" className="min-h-11 gap-2" onClick={() => setSourcesOpen(true)}><Rss className="size-4" aria-hidden="true" />Sources &amp; feeds</Button>
          <Button type="button" variant="outline" onClick={() => router.push("/admin/map")} className="min-h-11 gap-2">
            <Map className="h-4 w-4" aria-hidden="true" />Spatial Operations
          </Button>
        </div>
      </div>
      <Tabs<"overview" | "areas"> tabs={[
        { id: "overview", label: "Overview", icon: Activity, panelId: "news-overview" },
        { id: "areas", label: "Flooded Areas", icon: CloudRain, panelId: "news-areas" },
      ]} activeTab={activeTab} onChange={setActiveTab} variant="underline" layoutId="news-intelligence-tabs"
        ariaLabel="News Intelligence views" className="w-full" fullWidth
        tabClassName="min-h-11 px-2 text-xs sm:flex-none sm:px-4 sm:text-sm focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-blue-500 [&>svg]:hidden sm:[&>svg]:block" />
      <div id="news-overview" role="tabpanel" aria-labelledby="news-intelligence-tabs-overview" hidden={activeTab !== "overview"} tabIndex={0}>
        <NewsAutomationPanel />
      </div>
      <div id="news-areas" role="tabpanel" aria-labelledby="news-intelligence-tabs-areas" hidden={activeTab !== "areas"} tabIndex={0}>
        <NewsResults key={simulation.data?.article_title ?? "normal"}
          active={activeTab === "areas"} defaultSearch={simulation.data?.article_title} />
      </div>
      {collectionOpen && <NewsCollectionDrawer onClose={closeCollection} />}
      {sourcesOpen && <NewsSourcesDrawer onClose={closeSources} />}
    </div>
  );
}
