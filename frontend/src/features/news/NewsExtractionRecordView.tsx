"use client";

import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, FileText, MapPin, Settings2 } from "lucide-react";
import { Button, Skeleton, Tabs, TabContentPanel } from "@/shared/ui";
import { getNewsArticle, type NewsArticleDetail, type NewsRun } from "./newsApi";
import { newsDate, processingLabels } from "./newsPresentation";
import { NewsSourceArticle } from "./NewsSourceArticle";

type RecordTab = "mentions" | "article" | "technical";
const tabs = [{ id: "mentions", label: "Mentions", icon: MapPin }, { id: "article", label: "Article", icon: FileText }, { id: "technical", label: "Technical", icon: Settings2 }] satisfies { id: RecordTab; label: string; icon: typeof MapPin }[];

/** Inspect a saved extraction in the existing dialog, without growing the sidebar. */
export function NewsExtractionRecordView({ articleId, runId, currentRunId, onBack }: { articleId: number; runId: number; currentRunId: number; onBack: () => void }) {
  const heading = useRef<HTMLHeadingElement>(null);
  const [tab, setTab] = useState<RecordTab>("mentions");
  const [direction, setDirection] = useState(1);
  const query = useQuery({ queryKey: ["news-article", articleId], queryFn: ({ signal }) => getNewsArticle(articleId, signal), retry: false, refetchOnWindowFocus: false });
  useEffect(() => { heading.current?.focus({ preventScroll: true }); }, []);
  const run = query.data?.runs.find((item) => item.id === runId);
  const version = query.data?.versions.find((item) => item.id === run?.article_version_id);
  return <section aria-label="Extraction record inspection" className="flex min-h-0 flex-1 flex-col gap-4">
    <div className="shrink-0 space-y-3">
      <Button variant="ghost" size="sm" className="min-h-11 gap-2 px-0 text-blue-700" onClick={onBack}><ArrowLeft className="size-4" aria-hidden="true" />Back to source article</Button>
      <div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Saved processing record</p><h3 ref={heading} tabIndex={-1} className="mt-1 text-xl font-bold text-slate-900 focus:outline-none">Extraction record #{runId}</h3>{run && <p className="mt-1 text-xs text-slate-500">{newsDate(run.completed_at ?? run.started_at ?? run.created_at)} · Philippine time{run.id === currentRunId ? " · Used for this flood card" : " · Earlier record"}</p>}</div>{run && <span className={`rounded-full px-3 py-1.5 text-xs font-semibold ${run.status === "failed" ? "bg-red-50 text-red-800" : run.status === "completed" ? "bg-blue-50 text-blue-700" : "bg-amber-50 text-amber-800"}`}>{processingLabels[run.status]}</span>}</div>
      {run && <Tabs<RecordTab> tabs={tabs} activeTab={tab} onChange={(next) => { setDirection(tabs.findIndex((item) => item.id === next) > tabs.findIndex((item) => item.id === tab) ? 1 : -1); setTab(next); }} variant="underline" fullWidth layoutId="news-record-inspection-tabs" tabClassName="min-h-11 min-w-0 px-2 text-xs focus-visible:ring-2 focus-visible:ring-blue-500" />}
    </div>
    <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain pr-1" tabIndex={0} aria-label="Extraction record content">
      {query.isPending && <div role="status" aria-label="Loading extraction record"><Skeleton className="h-36 w-full" /></div>}
      {query.isError && <div className="space-y-3"><p role="alert" className="text-sm text-red-800">Extraction record could not be loaded. {query.error.message}</p><Button variant="outline" size="sm" onClick={() => void query.refetch()}>Retry extraction record</Button></div>}
      {query.data && !run && <p role="alert" className="text-sm text-amber-800">This record is not available in the loaded processing history.</p>}
      {run && query.data && <TabContentPanel tabKey={tab} direction={direction}>
        {tab === "mentions" ? <RecordMentions run={run} data={query.data} /> : tab === "article" ? version ? <NewsSourceArticle source={version.input_snapshot} publisher={query.data.publisher} savedAt={query.data.article.first_seen_at} articleId={articleId} presentation="reader" /> : <p role="alert" className="text-sm text-amber-800">The captured article is unavailable for this record.</p> : <RecordTechnicalDetails run={run} fingerprint={version?.input_fingerprint} capturedAt={version?.created_at} />}
      </TabContentPanel>}
    </div>
  </section>;
}

function RecordMentions({ run, data }: { run: NewsRun; data: NewsArticleDetail }) {
  const summaries = data.flood_summaries[run.id] ?? [];
  return <div className="space-y-5">
    <div><h4 className="text-sm font-bold text-slate-900">Extracted mentions {run.result ? `(${run.result.claims.length})` : ""}</h4><p className="mt-1 text-xs leading-5 text-slate-500">Saved extraction output. Locations and measurements still need evidence checks before operational use.</p></div>
    {run.error_code && <p role="alert" className="break-words text-sm text-red-800">Processing failed: {run.error_code}</p>}
    {run.result?.is_metadata_only && <p className="text-sm text-amber-800">Only article metadata was processed.</p>}
    {run.result?.errors.length ? <p role="alert" className="text-sm text-red-800">Processing issues: {run.result.errors.join("; ")}</p> : null}
    {!run.result ? <p className="text-sm text-slate-500">No extraction output recorded.</p> : !run.result.claims.length ? <p className="text-sm text-slate-500">No flood locations extracted.</p> : !summaries.length ? <p className="text-sm text-amber-800">Location summaries are unavailable for this saved output.</p> : <ul className="grid gap-x-8 gap-y-6 lg:grid-cols-2">{summaries.map((summary, index) => <li key={index} className="min-w-0 space-y-3 border-t border-slate-200 pt-4"><div><h4 className="break-words text-base font-bold text-slate-900">{summary.location}</h4>{summary.area && <p className="mt-1 break-words text-sm text-slate-500">{summary.area}</p>}{summary.location_qualifier && <p className="mt-1 break-words text-sm text-slate-600">{summary.location_qualifier}</p>}</div><dl className="grid gap-3 sm:grid-cols-2"><RecordFact label="Water level" value={summary.water_level} /><RecordFact label={summary.flood_time_label} value={newsDate(summary.flood_time, "Not stated in article")} /><RecordFact label="Condition" value={summary.condition} /><RecordFact label="Map placement" value={summary.map_status} /></dl>{summary.reading_reason && <p className="text-sm text-amber-800">Needs checking: {summary.reading_reason}</p>}<details className="text-sm text-slate-600"><summary className="min-h-11 cursor-pointer py-3 font-semibold">Supporting sentence</summary><blockquote className="mt-2 whitespace-pre-wrap break-words border-l-2 border-blue-200 pl-3 leading-6">{run.result?.claims[index]?.evidence_sentence}</blockquote></details></li>)}</ul>}
  </div>;
}

function RecordFact({ label, value }: { label: string; value: string }) {
  return <div className="min-w-0"><dt className="text-xs text-slate-500">{label}</dt><dd className="mt-1 break-words text-sm font-medium text-slate-800">{value}</dd></div>;
}

function RecordTechnicalDetails({ run, fingerprint, capturedAt }: { run: NewsRun; fingerprint?: string; capturedAt?: string }) {
  return <dl className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3"><RecordFact label="Extraction record" value={`#${run.id}`} /><RecordFact label="Captured input" value={`#${run.article_version_id}`} /><RecordFact label="Pipeline version" value={run.pipeline_version} /><RecordFact label="Attempts" value={String(run.attempt_count)} /><RecordFact label="Input captured" value={newsDate(capturedAt)} /><RecordFact label="Processing started" value={newsDate(run.started_at)} /><RecordFact label="Processing completed" value={newsDate(run.completed_at)} />{run.next_attempt_at && <RecordFact label="Next attempt" value={newsDate(run.next_attempt_at)} />}{fingerprint && <div className="sm:col-span-2 lg:col-span-3"><dt className="text-xs text-slate-500">Input fingerprint</dt><dd className="mt-1 break-all font-mono text-xs text-slate-700">{fingerprint}</dd></div>}</dl>;
}
