"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { FileText, History, MapPin } from "lucide-react";
import { Button, FloodLocationSummary, RecordDetailsDialog, RecordDetailsPanels, Skeleton, Tabs, TabContentPanel } from "@/shared/ui";
import { getNewsResult } from "./newsApi";
import { floodSummaryData } from "./newsPresentation";
import { NewsSourceArticle } from "./NewsSourceArticle";
import { NewsProcessingDetails } from "./NewsProcessingDetails";
import { NewsExtractionRecordView } from "./NewsExtractionRecordView";

type DetailTab = "flood" | "source";
const tabs = [{ id: "flood", label: "Flood Details", icon: MapPin }, { id: "source", label: "Source Article", icon: FileText }] satisfies { id: DetailTab; label: string; icon: typeof MapPin }[];
type SourcePane = "article" | "history";
const sourcePanes = [{ id: "article", label: "Article", icon: FileText }, { id: "history", label: "Processing history", icon: History }] satisfies { id: SourcePane; label: string; icon: typeof MapPin }[];

export function NewsResultDialog({ runId, claimIndex, onClose }: { runId: number; claimIndex: number; onClose: () => void }) {
  const router = useRouter();
  const [tab, setTab] = useState<DetailTab>("flood");
  const [direction, setDirection] = useState(1);
  const [mobileHistory, setMobileHistory] = useState(false);
  const [inspectedRunId, setInspectedRunId] = useState<number | null>(null);
  const recordOpener = useRef<HTMLButtonElement | null>(null);
  const query = useQuery({ queryKey: ["news-result", runId, claimIndex], queryFn: ({ signal }) => getNewsResult(runId, claimIndex, signal), retry: false, refetchOnWindowFocus: false });
  const data = query.data;
  const changeTab = (next: DetailTab) => { setDirection(next === "source" ? 1 : -1); setTab(next); setMobileHistory(false); setInspectedRunId(null); };
  const inspectRun = (id: number, opener: HTMLButtonElement) => { recordOpener.current = opener; setInspectedRunId(id); };
  const backToArticle = () => { setInspectedRunId(null); requestAnimationFrame(() => recordOpener.current?.focus({ preventScroll: true })); };
  return <RecordDetailsDialog title="News Flood Details" subtitle={data?.item.publisher} closeLabel="Close flood details" onClose={onClose} size={tab === "source" ? "wide" : "default"} bodyLayout={tab === "source" ? "panels" : "flow"}>
    {query.isPending && <div aria-label="Loading flood details" role="status" className="space-y-4"><Skeleton className="h-7 w-3/4" /><Skeleton className="h-36 w-full" /></div>}
    {query.isError && <div className="space-y-3"><p role="alert" className="text-sm text-red-800">Flood details could not be loaded. {query.error.message}</p><Button variant="outline" size="sm" onClick={() => void query.refetch()}>Retry flood details</Button></div>}
    {data && <div className="flex min-h-0 flex-1 flex-col gap-5">
      <div className="shrink-0"><Tabs<DetailTab> tabs={tabs} activeTab={tab} onChange={changeTab} variant="underline" layoutId="news-flood-detail-tabs" tabClassName="min-h-11 min-w-0 focus-visible:ring-2 focus-visible:ring-blue-500" /></div>
      <div className={inspectedRunId !== null ? "hidden" : "flex min-h-0 flex-1 flex-col gap-4"}>
      {tab === "source" && <div className="shrink-0 lg:hidden"><Tabs<SourcePane> tabs={sourcePanes} activeTab={mobileHistory ? "history" : "article"} onChange={(next) => setMobileHistory(next === "history")} variant="underline" fullWidth tabClassName="min-h-11 px-2 text-xs focus-visible:ring-2 focus-visible:ring-blue-500" layoutId="news-source-panes" /></div>}
      <RecordDetailsPanels mainLabel="News evidence" asideLabel="Article processing records" showAsideOnMobile={tab === "source" && mobileHistory} main={<TabContentPanel tabKey={tab} direction={direction}>
        {tab === "flood" ? <section aria-label="Flood details" className="space-y-4">
          <FloodLocationSummary showPublication={false} data={floodSummaryData(data.item.summary, data.captured_input.published_at)} locationDetails={
            <section aria-label="Reported location" className="space-y-3">
              <h4 className="text-sm font-semibold text-slate-900">Reported location</h4>
              <dl className="grid gap-x-6 gap-y-3 sm:grid-cols-2">
                <div className="min-w-0"><dt className="text-xs text-slate-500">Street / road</dt><dd className="mt-1 break-words text-sm font-medium text-slate-900">{data.claim.canonical_road || "Not specified for this mention"}</dd></div>
                <div className="min-w-0"><dt className="text-xs text-slate-500">Road passability</dt><dd className="mt-1 break-words text-sm font-medium text-slate-900">{data.item.summary.passability || "Not stated in article"}</dd></div>
                {data.claim.canonical_barangay && <div className="min-w-0"><dt className="text-xs text-slate-500">Barangay</dt><dd className="mt-1 break-words text-sm font-medium text-slate-900">{data.claim.canonical_barangay}</dd></div>}
                {data.claim.road_segment_raw && <div className="min-w-0 sm:col-span-2"><dt className="text-xs text-slate-500">Reported section / intersection</dt><dd className="mt-1 break-words text-sm text-slate-900">{data.claim.road_segment_raw}</dd></div>}
                {data.claim.local_area_raw && <div className="min-w-0 sm:col-span-2"><dt className="text-xs text-slate-500">Local area / landmark</dt><dd className="mt-1 break-words text-sm text-slate-900">{data.claim.local_area_raw}</dd></div>}
              </dl>
            </section>
          } />
          {data.item.summary.reading_reason && <p className="text-sm text-amber-800">Needs checking: {data.item.summary.reading_reason}</p>}
          <div className="space-y-2"><h4 className="text-sm font-semibold">What the article says</h4><blockquote className="whitespace-pre-wrap break-words border-l-2 border-blue-200 pl-3 text-sm leading-6 text-slate-600">{data.claim.evidence_sentence}</blockquote>{data.claim.event_time_raw && <p className="text-xs text-slate-500">Time wording: {data.claim.event_time_raw}</p>}</div>
          <p className="text-xs text-slate-500">Times shown in Philippine time. This is the flood described by the article, not confirmation of flooding now.</p>
          <Button variant="outline" className="min-h-11 w-full gap-2 sm:w-auto"
            onClick={() => router.push(`/admin/map?review_news=${runId}:${claimIndex}`)}>
            <MapPin className="size-4" aria-hidden="true" />Inspect placement on map
          </Button>
        </section> : <NewsSourceArticle articleId={data.item.article_id} source={data.captured_input} publisher={data.item.publisher} savedAt={data.item.saved_at} presentation="reader" />}
      </TabContentPanel>} aside={tab === "source" ? <NewsProcessingDetails articleId={data.item.article_id} currentRunId={runId} presentation="panel" onInspectRun={inspectRun} /> : undefined} />
      </div>
      {tab === "source" && inspectedRunId !== null && <NewsExtractionRecordView key={inspectedRunId} articleId={data.item.article_id} runId={inspectedRunId} currentRunId={runId} onBack={backToArticle} />}
    </div>}
  </RecordDetailsDialog>;
}
