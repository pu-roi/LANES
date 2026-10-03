"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Activity, ExternalLink, Newspaper, RefreshCw, Rss } from "lucide-react";
import { Button, RecordDetailsDialog, Skeleton, Tabs, TabContentPanel } from "@/shared/ui";
import { getNewsFeedCheckpoints, getNewsMonitoring, getNewsSources, type NewsFeedCheckpoint, type NewsMonitoringSummary, type NewsSource } from "./newsApi";
import { newsDate, publisherLink } from "./newsPresentation";
import { NewsTelemetryHistory } from "./NewsTelemetryHistory";

type SourceTab = "publishers" | "feeds" | "pipeline";
const tabs = [{ id: "publishers", label: "Publishers", icon: Newspaper }, { id: "feeds", label: "Feed checks", icon: Rss }, { id: "pipeline", label: "Pipeline", icon: Activity }] satisfies { id: SourceTab; label: string; icon: typeof Rss }[];

export function NewsSourcesDrawer({ onClose }: { onClose: () => void }) {
  const [tab, setTab] = useState<SourceTab>("publishers");
  const sources = useQuery({ queryKey: ["news-sources"], queryFn: ({ signal }) => getNewsSources(signal), staleTime: 30_000, retry: false, refetchOnWindowFocus: false });
  const feeds = useQuery({ queryKey: ["news-feed-checkpoints"], queryFn: ({ signal }) => getNewsFeedCheckpoints(signal), enabled: tab === "feeds", staleTime: 30_000, retry: false, refetchOnWindowFocus: false });
  const monitoring = useQuery({ queryKey: ["news-monitoring"], queryFn: ({ signal }) => getNewsMonitoring(signal), enabled: tab === "pipeline", staleTime: 30_000, retry: false, refetchOnWindowFocus: false });
  const active = tab === "publishers" ? sources : tab === "feeds" ? feeds : monitoring;
  const activeLabel = tab === "publishers" ? "Publishers" : tab === "feeds" ? "Feed checks" : "Pipeline status";
  return <RecordDetailsDialog title="Sources & feeds" subtitle="Publisher configuration and saved RSS collection checks" closeLabel="Close sources and feeds" onClose={onClose} placement="drawer">
    <Tabs<SourceTab> tabs={tabs} activeTab={tab} onChange={setTab} variant="underline" fullWidth layoutId="news-sources-tabs" tabClassName="min-h-11 focus-visible:ring-2 focus-visible:ring-blue-500" />
    <div className="flex flex-wrap items-center justify-between gap-3"><p className="text-xs text-slate-500">Saved status · dates in Philippine time</p><Button size="sm" variant="outline" className="min-h-11 gap-2" disabled={active.isFetching} onClick={() => void active.refetch()}><RefreshCw className="size-3.5" aria-hidden="true" />Refresh saved status</Button></div>
    <p className="text-xs leading-5 text-slate-500">Refresh reads saved information. It does not run collection or check a publisher live.</p>
    {active.isPending && <div role="status" aria-label="Loading source monitoring" className="space-y-3"><Skeleton className="h-24 w-full" /><Skeleton className="h-24 w-full" /></div>}
    {active.isError && <div className="space-y-3"><p role="alert" className="text-sm text-red-800">{activeLabel} could not be loaded. {active.error.message}</p><Button variant="outline" size="sm" className="min-h-11" onClick={() => void active.refetch()}>Retry {activeLabel.toLowerCase()}</Button></div>}
    <TabContentPanel tabKey={tab} direction={tab === "feeds" ? 1 : -1}>
      {tab === "pipeline" && monitoring.data && <PipelineStatus data={monitoring.data} />}
      {tab === "publishers" && sources.data && <section aria-label="Configured publishers" className="space-y-4"><p className="text-xs text-slate-500">{sources.data.length} configured publishers. Enabled status and source verification do not verify any flood.</p>{!sources.data.length && <p className="text-sm text-slate-500">No publishers are configured.</p>}<div className="divide-y divide-slate-100">{sources.data.map((source) => <PublisherRow key={source.id} source={source} />)}</div></section>}
      {tab === "feeds" && feeds.data && <section aria-label="Saved feed checks" className="space-y-4"><p className="text-xs text-slate-500">{feeds.data.length} saved feed checkpoints. A successful feed fetch does not establish that a qualifying flood article was found.</p>{!feeds.data.length && <p className="text-sm text-slate-500">No feed checkpoints recorded. Feed health is not established.</p>}<div className="divide-y divide-slate-100">{feeds.data.map((feed) => <FeedRow key={`${feed.source_id}:${feed.feed_url}`} feed={feed} publisher={sources.data?.find((source) => source.id === feed.source_id)?.publisher ?? feed.source_id} />)}</div></section>}
    </TabContentPanel>
    <details className="border-t border-slate-100 pt-2 text-xs text-slate-500"><summary className="min-h-11 cursor-pointer py-3 font-semibold">Monitoring limitations</summary><p className="leading-6">Pipeline totals describe current saved articles and their newest extraction runs. Retrieval issues show current errors. Discovery and fallback history begins after telemetry is enabled, without historical backfill. Collection-to-alert delay is unavailable until durable publication records exist. Article-level inspection remains in Collection status.</p></details>
  </RecordDetailsDialog>;
}

function PipelineStatus({ data }: { data: NewsMonitoringSummary }) {
  const processingLabels = { not_recorded: "No extraction recorded", pending: "Pending", processing: "Processing", completed: "Completed", retry_wait: "Waiting for retry", failed: "Failed" };
  return <section aria-label="Saved pipeline status" className="space-y-6">
    <div><h3 className="text-base font-bold text-slate-900">Current saved evidence</h3><p className="mt-1 text-xs leading-5 text-slate-500">{data.articles_total} saved articles across all publishers. These are current totals, not discovery-run counts.</p></div>
    <dl className="grid grid-cols-1 gap-3 min-[360px]:grid-cols-3">{([ ["Readable body", data.body_counts.available], ["Missing body", data.body_counts.missing], ["Retrieval error", data.body_counts.error] ] as const).map(([label, count]) => <div key={label}><dt className="text-xs text-slate-500">{label}</dt><dd className="mt-1 text-xl font-bold text-slate-900">{count}</dd></div>)}</dl>
    <div><h3 className="text-sm font-bold text-slate-900">Newest extraction per article</h3><dl className="mt-3 grid gap-x-6 gap-y-3 sm:grid-cols-2">{Object.entries(data.latest_processing_counts).map(([status, count]) => <div key={status} className="flex items-center justify-between gap-3 text-sm"><dt className="text-slate-600">{processingLabels[status as keyof typeof processingLabels]}</dt><dd className="font-semibold text-slate-900">{count}</dd></div>)}</dl><p className="mt-3 text-xs text-slate-500">Completed extraction does not mean an alert is published or a zone is active.</p></div>
    <div><h3 className="text-sm font-bold text-slate-900">Recent retrieval issues</h3><p className="mt-1 text-xs text-slate-500">Up to {data.issue_limit} articles, ordered by last saved sighting.</p>{!data.recent_retrieval_issues.length && <p className="mt-3 text-sm text-slate-500">No saved articles currently have a missing body or retrieval error.</p>}<div className="divide-y divide-slate-100">{data.recent_retrieval_issues.map((issue) => <article key={issue.article_id} className="space-y-1 py-4"><h4 className="break-words text-sm font-semibold text-slate-900">{issue.title}</h4><p className="text-xs text-slate-500">{issue.publisher} · Last seen {newsDate(issue.last_seen_at)}</p><p className="break-words text-sm text-red-800">{issue.article_error ?? "Article body unavailable"}</p></article>)}</div></div>
    <NewsTelemetryHistory kind="discovery" />
    <NewsTelemetryHistory kind="fallback" />
    <p className="border-t border-slate-100 pt-4 text-xs leading-5 text-slate-500">Collection-to-alert delay: unavailable until durable publication records exist.</p>
  </section>;
}

function PublisherRow({ source }: { source: NewsSource }) {
  return <article className="space-y-3 py-5 first:pt-0">
    <div className="flex flex-wrap items-center justify-between gap-2"><h3 className="text-base font-bold text-slate-900">{source.publisher}</h3><span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${source.enabled ? "bg-blue-50 text-blue-700" : "bg-slate-100 text-slate-600"}`}>{source.enabled ? "Enabled" : "Disabled"}</span></div>
    <dl className="grid gap-3 sm:grid-cols-2"><div><dt className="text-xs text-slate-500">Source verification date</dt><dd className="mt-1 text-sm text-slate-800">{source.verified_at ?? "Not recorded"}</dd></div><div><dt className="text-xs text-slate-500">Publisher domains</dt><dd className="mt-1 break-words text-sm text-slate-800">{source.article_domains.join(", ") || "Not configured"}</dd></div></dl>
    <details className="text-xs text-slate-600"><summary className="min-h-11 cursor-pointer py-3 font-semibold">Feed URLs ({source.feed_urls.length})</summary><ul className="space-y-2">{source.feed_urls.map((url) => <li key={url}><FeedLink url={url} /></li>)}</ul>{!source.feed_urls.length && <p>No feed URLs configured.</p>}<p className="mt-3">Source ID: {source.id}</p></details>
  </article>;
}

function FeedRow({ feed, publisher }: { feed: NewsFeedCheckpoint; publisher: string }) {
  return <article className="space-y-3 py-5 first:pt-0">
    <h3 className="text-base font-bold text-slate-900">{publisher}</h3>
    <dl className="grid gap-3 sm:grid-cols-2"><div><dt className="text-xs text-slate-500">Last checked</dt><dd className="mt-1 text-sm text-slate-800">{newsDate(feed.last_checked_at)}</dd></div><div><dt className="text-xs text-slate-500">Last successful fetch</dt><dd className="mt-1 text-sm text-slate-800">{newsDate(feed.last_success_at)}</dd></div></dl>
    {feed.last_error ? <div className="space-y-1"><p className="text-xs font-semibold text-red-800">Last recorded error</p><p className="break-words text-sm leading-6 text-red-800">{feed.last_error}</p></div> : <p className="text-xs text-slate-500">No error recorded in this checkpoint.</p>}
    <details className="text-xs text-slate-600"><summary className="min-h-11 cursor-pointer py-3 font-semibold">Feed details</summary><FeedLink url={feed.feed_url} /><p className="mt-3">Source ID: {feed.source_id}</p></details>
  </article>;
}

function FeedLink({ url }: { url: string }) {
  const href = publisherLink(url);
  return href ? <a href={href} target="_blank" rel="noopener noreferrer" className="inline-flex min-h-11 items-start gap-1.5 break-all py-2 text-blue-700 underline underline-offset-4">{url}<ExternalLink className="mt-1 size-3 shrink-0" aria-hidden="true" /></a> : <span className="break-all">{url}</span>;
}
