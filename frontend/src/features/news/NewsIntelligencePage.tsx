"use client";

import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { Inbox, Map, Rss } from "lucide-react";
import { Button } from "@/shared/ui";
import { NewsResults } from "./NewsResults";
import { NewsCollectionDrawer } from "./NewsCollectionDrawer";
import { NewsSourcesDrawer } from "./NewsSourcesDrawer";

export default function NewsIntelligencePage() {
  const router = useRouter();
  const [collectionOpen, setCollectionOpen] = useState(false);
  const closeCollection = useCallback(() => setCollectionOpen(false), []);
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const closeSources = useCallback(() => setSourcesOpen(false), []);

  return (
    <div className="mx-auto w-full max-w-[1600px] space-y-6 pb-[calc(var(--bottom-nav-height)+env(safe-area-inset-bottom))] text-gray-900">
      <div className="flex flex-col items-start justify-between gap-4 lg:flex-row lg:items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">Flood Locations from News</h1>
          <p className="mt-1 text-sm text-gray-500">Where flooding was reported, how deep it was, and when. Open Info to inspect the source article.</p>
        </div>
        <div className="flex w-full flex-wrap gap-2 lg:w-auto">
          <Button type="button" variant="outline" className="min-h-11 gap-2" onClick={() => setCollectionOpen(true)}><Inbox className="size-4" aria-hidden="true" />Collection status</Button>
          <Button type="button" variant="outline" className="min-h-11 gap-2" onClick={() => setSourcesOpen(true)}><Rss className="size-4" aria-hidden="true" />Sources &amp; feeds</Button>
          <Button type="button" variant="outline" onClick={() => router.push("/admin/map")} className="min-h-11 gap-2">
            <Map className="h-4 w-4" aria-hidden="true" />Spatial Operations
          </Button>
        </div>
      </div>
      <NewsResults active />
      {collectionOpen && <NewsCollectionDrawer onClose={closeCollection} />}
      {sourcesOpen && <NewsSourcesDrawer onClose={closeSources} />}
    </div>
  );
}
