"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Calendar, Clock, ExternalLink, FileText, History, ListChecks } from "lucide-react";
import { Button, FloodDetailMetric, FloodLocationSummary, RecordDetailsDialog, Skeleton, Tabs, TabContentPanel } from "@/shared/ui";
import { getNewsArticle, type NewsArticleDetail, type NewsFloodSummary, type NewsRun } from "./newsApi";
import { floodSummaryData, newsDate, processingLabels, publisherLink } from "./newsPresentation";

type DetailTab = "source" | "facts" | "history";
const tabs = [{ id: "source", label: "Article", icon: FileText }, { id: "facts", label: "Flood locations", icon: ListChecks }, { id: "history", label: "History", icon: History }] satisfies { id: DetailTab; label: string; icon: typeof FileText }[];

export function NewsArticleDialog({ articleId, onClose }: { articleId: number; onClose: () => void }) {
  const [tab, setTab] = useState<DetailTab>("source");
  const [direction, setDirection] = useState(1);
  const [runId, setRunId] = useState<number | null>(null);
  const query = useQuery({ queryKey: ["news-article", articleId], queryFn: ({ signal }) => getNewsArticle(articleId, signal), retry: false, refetchOnWindowFocus: false });
  const data = query.data;
  const run = data?.runs.find((item) => item.id === (runId ?? data.runs[0]?.id));
  const version = data?.versions.find((item) => item.id === run?.article_version_id);
  const changeTab = (next: DetailTab) => { setDirection(tabs.findIndex((item) => item.id === next) > tabs.findIndex((item) => item.id === tab) ? 1 : -1); setTab(next); };
  return <RecordDetailsDialog title="News Article" subtitle={data?.publisher} closeLabel="Close article details" onClose={onClose}>
    {query.isPending && <div aria-label="Loading article details" role="status" className="space-y-4"><Skeleton className="h-7 w-3/4" /><Skeleton className="h-10 w-full" /><Skeleton className="h-36 w-full" /></div>}
    {query.isError && <div className="space-y-3"><p role="alert" className="text-sm text-red-800">Article details could not be loaded. {query.error.message}</p><Button variant="outline" size="sm" onClick={() => void query.refetch()}>Retry details</Button></div>}
    {data && <>
      <h3 className="break-words text-lg font-bold leading-snug">{version?.input_snapshot.title ?? data.article.title}</h3>
      <p className="text-xs text-slate-500">One news article can mention several flood locations.</p>
      {data.article.article_error && <p role="alert" className="break-words text-sm text-red-800">Latest article retrieval failed: {data.article.article_error}</p>}
      <Tabs<DetailTab> tabs={tabs} activeTab={tab} onChange={changeTab} variant="pills" fullWidth layoutId="news-article-detail-tabs" tabClassName="min-h-11" />
      <TabContentPanel tabKey={`${tab}-${run?.id ?? "current"}`} direction={direction}>
        {tab === "source" && <Source data={data} version={version} />}
        {tab === "facts" && <Facts run={run} summaries={run ? data.flood_summaries?.[run.id] : undefined} publishedAt={version?.input_snapshot.published_at} />}
        {tab === "history" && <HistoryList data={data} onSelect={(item) => { setRunId(item.id); changeTab("facts"); }} />}
      </TabContentPanel>
      {data.runs.length > 0 && <details className="text-xs text-slate-500"><summary className="cursor-pointer font-semibold">Article version & processing details</summary><div className="mt-3 space-y-3">
        <p>{run ? `Viewing extraction #${run.id} from saved article version #${run.article_version_id}` : "Viewing the current saved article"}</p>
        <div className="flex flex-wrap gap-2"><Button variant="outline" size="sm" onClick={() => setRunId(run ? 0 : data.runs[0].id)}>{run ? "View current article" : "View latest extraction"}</Button><Button variant="ghost" size="sm" onClick={() => changeTab("history")}>Older extractions</Button></div>
        {version && <p className="break-all">Input fingerprint: {version.input_fingerprint}</p>}
      </div></details>}
    </>}
  </RecordDetailsDialog>;
}

function Source({ data, version }: { data: NewsArticleDetail; version?: NewsArticleDetail["versions"][number] }) {
  const source = version?.input_snapshot ?? data.article;
  const href = publisherLink(source.canonical_url);
  return <section aria-label="Article source" className="space-y-4">
    <div className="grid gap-3 sm:grid-cols-2"><FloodDetailMetric icon={<Calendar className="size-4" />} iconClassName="bg-blue-100 text-blue-600" label="Article published" value={newsDate(source.published_at, "Not stated")} /><FloodDetailMetric icon={<Clock className="size-4" />} iconClassName="bg-violet-100 text-violet-600" label="Saved in LANES" value={newsDate(version?.created_at ?? data.article.first_seen_at)} /></div>
    {href && <a href={href} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 text-sm font-semibold text-blue-700 underline underline-offset-4">Read on {data.publisher}<ExternalLink className="size-3.5" aria-hidden="true" /></a>}
    {source.excerpt && <p className="break-words text-sm leading-6 text-slate-600">{source.excerpt}</p>}
    {source.article_text ? <details className="text-sm text-slate-600"><summary className="cursor-pointer font-semibold">Full article text</summary><p className="mt-3 whitespace-pre-wrap break-words leading-7">{source.article_text}</p></details> : <p className="text-sm text-amber-800">Article text unavailable. Only publisher metadata is saved.</p>}
    <details className="text-xs text-slate-500"><summary className="cursor-pointer font-semibold">Collection details</summary><div className="mt-3 space-y-2 break-all"><p>First collected: {newsDate(data.article.first_seen_at)}</p><p>Last seen: {newsDate(data.article.last_seen_at)}</p><p>Latest retrieval attempt: {newsDate(data.article.fetched_at)}</p>{data.article.feed_entries.length ? data.article.feed_entries.map((entry, index) => <p key={index}>Feed: {entry.feed_url}<br />GUID: {entry.feed_guid}</p>) : <p>No feed provenance recorded for this article.</p>}<p>Retrieval attempt history is unavailable.</p></div></details>
  </section>;
}

function Facts({ run, summaries, publishedAt }: { run?: NewsRun; summaries?: NewsFloodSummary[]; publishedAt?: string | null }) {
  if (!run) return <p className="text-sm text-slate-500">No saved extraction selected. Choose an extraction under History.</p>;
  if (run.status !== "completed" || !run.result) return <div className="space-y-2"><p className="text-sm font-semibold">{processingLabels[run.status]}</p><p className="text-sm text-slate-500">Flood locations are unavailable for this extraction.</p>{run.error_code && <p role="alert" className="break-words text-sm text-red-800">Processing error: {run.error_code}</p>}</div>;
  return <section aria-label="Flood locations in article" className="space-y-4">
    {run.result.is_metadata_only && <p className="text-sm text-amber-800">Only article metadata was available for this extraction.</p>}
    {run.result.errors.length > 0 && <p role="alert" className="break-words text-sm text-red-800">Processing issues: {run.result.errors.join("; ")}</p>}
    <p className="text-sm font-semibold">{run.result.claims.length} possible flood location{run.result.claims.length === 1 ? "" : "s"} mentioned</p>
    {run.result.claims.length === 0 ? <p className="text-sm text-slate-500">No flood locations found in this saved article.</p> : summaries ? <div className="divide-y divide-slate-100">{summaries.map((summary, index) => <article key={index} className="space-y-3 py-5 first:pt-0"><FloodLocationSummary compact data={floodSummaryData(summary, publishedAt)} /><details className="text-sm text-slate-600"><summary className="cursor-pointer font-semibold">What the article says</summary><blockquote className="mt-3 whitespace-pre-wrap break-words border-l-2 border-blue-200 pl-3 leading-6">{run.result!.claims[index].evidence_sentence}</blockquote></details></article>)}</div> : <p role="alert" className="text-sm text-amber-800">Location summaries are unavailable. Update the backend and retry.</p>}
  </section>;
}

function HistoryList({ data, onSelect }: { data: NewsArticleDetail; onSelect: (run: NewsRun) => void }) {
  return <section aria-label="Recorded processing history" className="space-y-3"><p className="text-xs text-slate-500">{data.runs.length} of {data.history_total} saved extractions. Staff decisions and retrieval attempts are not included.</p>{data.runs.length === 0 ? <p className="text-sm text-slate-500">No processing history is recorded.</p> : <ol className="divide-y divide-slate-100">{data.runs.map((run) => <li key={run.id} className="space-y-2 py-4 first:pt-0"><div className="flex flex-wrap items-center justify-between gap-2"><div><p className="text-sm font-semibold">{processingLabels[run.status]}</p><p className="mt-1 text-xs text-slate-500">{newsDate(run.completed_at ?? run.started_at ?? run.created_at)}</p></div><Button size="sm" variant="outline" onClick={() => onSelect(run)}>View extraction #{run.id}</Button></div>{run.error_code && <p role="alert" className="break-words text-xs text-red-800">Processing error: {run.error_code}</p>}<details className="text-xs text-slate-500"><summary className="cursor-pointer">Processing details</summary><p className="mt-2 break-all">Run #{run.id} · Input #{run.article_version_id} · Attempts: {run.attempt_count}<br />{run.pipeline_version}<br />Started: {newsDate(run.started_at)}<br />Completed: {newsDate(run.completed_at)}{run.next_attempt_at && <><br />Next retry: {newsDate(run.next_attempt_at)}</>}</p></details></li>)}</ol>}</section>;
}
