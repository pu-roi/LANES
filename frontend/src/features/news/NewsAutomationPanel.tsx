"use client";

import { useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Activity, LoaderCircle, RefreshCw } from "lucide-react";
import { Button, Card, CardContent } from "@/shared/ui";
import { getNewsAutomation } from "./newsApi";
import { newsDate } from "./newsPresentation";

export function NewsAutomationPanel() {
  const client = useQueryClient();
  const query = useQuery({ queryKey: ["news-automation"], queryFn: ({ signal }) => getNewsAutomation(signal),
    refetchInterval: 15_000, staleTime: 10_000, retry: false });
  const finished = query.data?.last_finished_at;
  useEffect(() => {
    if (!finished) return;
    for (const key of ["news-results", "news-collection", "news-feed-checkpoints", "news-monitoring", "news-telemetry"]) {
      void client.invalidateQueries({ queryKey: [key] });
    }
  }, [client, finished]);
  const data = query.data;
  const cycle = data?.last_cycle;
  const count = (value: number | undefined) => value === undefined ? "Not recorded" : value.toLocaleString();
  return <Card><CardContent className="space-y-4 p-4 sm:p-5">
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div className="min-w-0"><h2 className="flex items-center gap-2 font-bold"><Activity className="size-4 shrink-0" aria-hidden="true" />News automation</h2>
        <p role="status" aria-live="polite" className="mt-1 flex items-center gap-2 text-sm text-slate-700">
          {data?.running && <LoaderCircle className="size-4 shrink-0 animate-spin motion-reduce:animate-none" aria-hidden="true" />}
          {query.isError ? "Status could not be refreshed" : data?.status_label ?? "Loading saved worker status…"}
        </p>
      </div>
      <Button size="sm" variant="outline" className="min-h-11 gap-2" disabled={query.isFetching} onClick={() => void query.refetch()}><RefreshCw className="size-3.5" aria-hidden="true" />Refresh automation status</Button>
    </div>
    {query.isError && <p role="alert" className="break-words text-sm text-red-800">{query.error.message} {data && "Previously loaded details below may be stale."}</p>}
    {data && <>
      <div className="flex flex-wrap gap-x-5 gap-y-2 text-sm text-slate-600">
        <span>Collection: <strong>{data.collection_enabled ? "Enabled" : "Paused"}</strong></span>
        <span>Processing: <strong>{data.processing_enabled ? "Enabled" : "Paused"}</strong></span>
        <span>Publication: <strong>{data.publication_enabled ? "Enabled" : "Paused"}</strong></span>
        <span>{data.enabled_sources} enabled publishers · {data.collection_interval_minutes}-minute collection interval</span>
      </div>
      <dl className="grid gap-x-6 gap-y-3 text-sm sm:grid-cols-2 xl:grid-cols-4">
        <Metric label="Worker last started" value={newsDate(data.last_started_at, "Not recorded")} />
        <Metric label="Last cycle finished" value={newsDate(data.last_finished_at, "Not recorded")} />
        <Metric label="Last successful cycle" value={newsDate(data.last_successful_at, "Not recorded")} />
        <Metric label="Next collection due" value={newsDate(data.next_collection_due_at, data.collection_enabled ? "Not scheduled" : "Collection paused")} />
      </dl>
      {data.running && <p className="text-xs text-slate-500">Current stage started {newsDate(data.stage_started_at, "at an unrecorded time")}. Stage changes are saved by the worker.</p>}
      {data.collection_overdue && <p role="alert" className="text-sm text-amber-800">Collection is overdue beyond the worker tick target. Check the deployed scheduler and worker; an enabled setting does not start the worker.</p>}
      {data.error_code && <p role="alert" className="break-words text-sm text-red-800">Worker diagnostic: {data.error_code}</p>}
      {(data.feed_counts.feed_errors > 0 || data.feed_counts.body_errors > 0 || data.feed_counts.scope_unresolved > 0) && <p role="alert" className="text-sm text-amber-800">The latest collection has feed, article retrieval or location-scope issues. Successful feed checks do not mean every article was processed.</p>}
      <div className="space-y-2 border-t border-slate-100 pt-3">
        <p className="text-xs text-slate-500">Latest collection and last completed cycle</p>
        <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
          <Metric label="Feed entries read" value={count(data.feed_counts.entries_read)} />
          <Metric label="Flood candidates" value={count(data.feed_counts.eligible_candidates)} />
          <Metric label="Articles processed" value={count(cycle?.counts.extraction?.completed)} />
          <Metric label="Flood areas activated" value={count(cycle?.counts.footprints?.total_activated)} />
        </dl>
        {data.feed_counts.eligible_candidates === 0 && <p className="text-xs text-slate-600">The last recorded collection returned no new flood candidates. General weather and commuter updates do not create flood-location cards.</p>}
      </div>
      <details className="space-y-3 text-sm">
        <summary className="min-h-11 cursor-pointer py-3 font-semibold text-slate-700">Cycle details and retrieval diagnostics</summary>
      <div className="space-y-2 border-t border-slate-100 pt-3">
        <p className="text-xs font-semibold text-slate-500">Latest saved collection · {newsDate(data.latest_collection_at, "Not recorded")}</p>
        <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-3 xl:grid-cols-6">
          <Metric label="Feed entries read" value={count(data.feed_counts.entries_read)} />
          <Metric label="Flood candidates" value={count(data.feed_counts.eligible_candidates)} />
          <Metric label="Articles saved or seen" value={count(data.feed_counts.articles_saved_or_seen)} />
          <Metric label="Feed errors" value={count(data.feed_counts.feed_errors)} />
          <Metric label="Article retrieval errors" value={count(data.feed_counts.body_errors)} />
          <Metric label="Unresolved article scope" value={count(data.feed_counts.scope_unresolved)} />
        </dl>
      </div>
      <div className="space-y-2 border-t border-slate-100 pt-3">
        <p className="text-xs font-semibold text-slate-500">Last completed cycle · {newsDate(cycle?.finished_at, "Not recorded")}</p>
        <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-3 xl:grid-cols-6">
          <Metric label="Articles processed" value={count(cycle?.counts.extraction?.completed)} />
          <Metric label="Claims evaluated" value={count(cycle?.counts.evaluation?.completed)} />
          <Metric label="Publications created" value={count(cycle?.counts.publication?.published)} />
          <Metric label="Flood areas activated" value={count(cycle?.counts.footprints?.total_activated)} />
          <Metric label="Floods cleared" value={count(cycle?.counts.publication?.cleared)} />
          <Metric label="Needs review" value={count(cycle?.counts.publication?.needs_review)} />
        </dl>
        {cycle?.error_code && <p role="alert" className="break-words text-sm text-red-800">Last completed cycle: {cycle.error_code}</p>}
        <p className="text-xs text-slate-600">Extraction queue: {count(data.queue_counts.pending)} waiting · {count(data.queue_counts.processing)} processing · {count(data.queue_counts.retry_wait)} awaiting retry · {count(data.queue_counts.failed)} failed.</p>
        {Object.entries(data.stages).filter(([, stage]) => stage.errors.length > 0).map(([name, stage]) => <p key={name} role="alert" className="break-words text-xs text-red-800">{name}: {stage.errors.join(", ")}</p>)}
      </div>
      </details>
      {data.weather && <section aria-label="Weather-based scheduling" className="space-y-3 border-t border-slate-100 pt-3 text-sm">
        <div className="flex flex-wrap justify-between gap-2">
          <h3 className="font-semibold text-slate-800">Weather-based scheduling</h3>
          <span>{data.weather.effective_interval_minutes}-minute automatic interval</span>
        </div>
        <p>{data.weather.reason}</p>
        <p className="text-xs text-slate-500">{data.weather.coverage_label}. Rain estimates and advisories guide collection; flood areas require news evidence.</p>
        <p className="text-xs text-slate-600">Controller last checked: {newsDate(data.weather.controller_heartbeat_at, "Not recorded")} · Dispatch: {data.weather.dispatch_state}</p>
        {data.weather.controller_stale && <p role="alert" className="text-amber-800">Weather controller is missing or stale. The 30-minute fallback applies unless a current risk signal takes priority. A due time does not guarantee the cloud worker has started.</p>}
        {data.weather.dispatch_error && <p role="alert" className="break-words text-red-800">Worker dispatch needs attention: {data.weather.dispatch_error}</p>}
        <div className="grid gap-3 sm:grid-cols-2">{data.weather.providers.map(provider => <div key={provider.name} className="min-w-0 space-y-1">
          <p className="font-medium"><a className="underline underline-offset-2" href={provider.source_url} target="_blank" rel="noopener noreferrer">{provider.name}</a> · {provider.status}</p>
          <p className="text-xs text-slate-600">Checked: {newsDate(provider.checked_at, "Not recorded")}</p>
          {provider.risk_locations.length > 0 && <p className="break-words text-xs text-slate-700">Risk locations: {provider.risk_locations.join(", ")}</p>}
          {provider.error_code && <p role="alert" className="break-words text-xs text-amber-800">{provider.name}: {provider.error_code}</p>}
          {provider.bulletins.map(bulletin => <p key={`${bulletin.identity}:${bulletin.issued_at}`} className="break-words text-xs text-slate-600">{bulletin.identity} · Issued {newsDate(bulletin.issued_at, "Unknown")} · Valid until {newsDate(bulletin.valid_until, "Unknown")}</p>)}
        </div>)}</div>
        <details className="text-xs text-slate-600"><summary className="min-h-11 cursor-pointer py-3 font-medium">Monitored locations and controller diagnostics</summary>
          <p className="break-words">{data.weather.points.map(point => `${point.locality}${point.role === "upstream" ? " (upstream)" : ""}`).join(", ")}</p>
          <p className="mt-2">Catalog {data.weather.catalog_version} · {data.weather.checks} checks · {data.weather.provider_failures} provider issues · {data.weather.worker_starts} accepted worker starts · Last check {data.weather.last_tick_duration_ms} ms</p>
        </details>
      </section>}
      <p className="text-xs leading-5 text-slate-500">Status refreshes every 15 seconds while this page is open. Dates are in Philippine time. The backend automatically selects the collection interval. The cloud checks what is due every {data.scheduler_tick_target_minutes} minutes when the matching scheduler is deployed. Reading status does not trigger collection.</p>
    </>}
  </CardContent></Card>;
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div className="min-w-0"><dt className="text-xs text-slate-500">{label}</dt><dd className="mt-1 break-words font-semibold text-slate-800">{value}</dd></div>;
}
