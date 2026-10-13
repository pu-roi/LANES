"use client";

import { useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Activity, AlertTriangle, ArrowRight, CloudRain, LoaderCircle, RefreshCw } from "lucide-react";
import { Button, Card, CardContent, Skeleton } from "@/shared/ui";
import { getNewsAutomation } from "./newsApi";
import { newsDate } from "./newsPresentation";

const providerLabels: Record<string, string> = { risk: "Rain risk", quiet: "Quiet", uncertain: "Incomplete", unavailable: "Unavailable" };

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
  const weather = data?.weather;
  const count = (value: number | null | undefined) => value == null ? "Not recorded" : value.toLocaleString();
  const attention = data && ["overdue", "partial", "requires_attention", "interrupted"].includes(data.state);

  return <div className="space-y-4">
    <Card className="shadow-sm"><CardContent className="space-y-5 p-4 sm:p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 space-y-2">
          <h2 className="flex items-center gap-2 font-semibold"><Activity className="size-4 shrink-0 text-blue-600" aria-hidden="true" />News automation</h2>
          <p role="status" aria-live="polite" className={`inline-flex items-center gap-2 rounded-full px-2.5 py-1 text-xs font-medium ${query.isError ? "bg-red-50 text-red-800" : attention ? "bg-amber-50 text-amber-800" : data?.running ? "bg-blue-50 text-blue-700" : "bg-slate-100 text-slate-700"}`}>
            {data?.running && <LoaderCircle className="size-3.5 shrink-0 animate-spin motion-reduce:animate-none" aria-hidden="true" />}
            {query.isError ? "Status unavailable" : data?.status_label ?? "Loading status…"}
          </p>
        </div>
        <Button size="sm" variant="outline" aria-label="Refresh automation status" className="min-h-11 shrink-0 gap-1.5" disabled={query.isFetching} onClick={() => void query.refetch()}>
          <RefreshCw className="size-3.5" aria-hidden="true" />Refresh
        </Button>
      </div>
      {query.isError && <Notice tone="error">{query.error.message}{data && " Previously loaded status may be stale."}</Notice>}
      {query.isPending && <div aria-label="Loading automation details" className="grid gap-3 sm:grid-cols-2"><Skeleton className="h-12 w-full" /><Skeleton className="h-12 w-full" /></div>}
      {data && <>
        <dl className="grid grid-cols-2 gap-x-5 gap-y-4 text-sm xl:grid-cols-4">
          <Metric label="Next collection due" value={newsDate(data.next_collection_due_at, data.collection_enabled ? "Not scheduled" : "Collection paused")} />
          <Metric label="Last cycle finished" value={newsDate(data.last_finished_at)} />
          <Metric label="Collection interval" value={`${data.collection_interval_minutes} minutes · automatic`} />
          <Metric label="Enabled publishers" value={count(data.enabled_sources)} />
        </dl>
        <div className="grid gap-3 border-t border-gray-100 pt-4 sm:grid-cols-3" aria-label="News pipeline">
          {[
            { label: "Collection", description: "Gather articles", enabled: data.collection_enabled },
            { label: "Processing", description: "Extract flood claims", enabled: data.processing_enabled },
            { label: "Publication", description: "Publish eligible areas", enabled: data.publication_enabled },
          ].map((stage, index) => <div key={stage.label} className="flex min-w-0 items-center justify-between gap-2">
            <div className="min-w-0"><p className="text-sm font-medium text-gray-900">{stage.label} <span className={`ml-1 text-xs font-normal ${stage.enabled ? "text-emerald-700" : "text-slate-500"}`}>{stage.enabled ? "Enabled" : "Paused"}</span></p>
              <p className="mt-0.5 text-xs text-gray-500">{stage.description}</p></div>
            {index < 2 && <ArrowRight className="hidden size-4 shrink-0 text-gray-300 sm:block" aria-hidden="true" />}
          </div>)}
        </div>
        {data.collection_overdue && <Notice>Collection is overdue. Check the deployed scheduler and worker.</Notice>}
        {data.error_code && <Notice tone="error">The last worker cycle needs attention. Open run details.</Notice>}
        {(data.feed_counts.feed_errors > 0 || data.feed_counts.body_errors > 0 || data.feed_counts.scope_unresolved > 0) &&
          <Notice>Some feeds, article retrieval or locations need checking.</Notice>}
      </>}
    </CardContent></Card>

    {data && <>
      <div className="grid items-start gap-4 lg:grid-cols-2">
        <Card className="shadow-sm"><CardContent className="space-y-4 p-4 sm:p-5">
          <div><h2 className="font-semibold text-gray-900">Recent results</h2><p className="mt-1 text-xs text-gray-500">Latest collection and last completed cycle</p></div>
          <dl className="grid grid-cols-2 gap-x-5 gap-y-5 text-sm">
            <Metric label="Feed entries read" value={count(data.feed_counts.entries_read)} />
            <Metric label="Flood candidates" value={count(data.feed_counts.eligible_candidates)} />
            <Metric label="Articles processed" value={count(cycle?.counts.extraction?.completed)} />
            <Metric label="Flood areas activated" value={count(cycle?.counts.footprints?.total_activated)} />
          </dl>
          {data.feed_counts.eligible_candidates === 0 && <p className="text-xs text-gray-500">No new flood candidates in the latest collection.</p>}
        </CardContent></Card>

        <Card className="shadow-sm"><CardContent className="space-y-4 p-4 sm:p-5">
          <section aria-label="Weather-based scheduling" className="space-y-3 text-sm">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="flex items-center gap-2 font-semibold text-gray-900"><CloudRain className="size-4 text-blue-600" aria-hidden="true" />Weather-based scheduling</h2>
              <span className="text-xs font-medium text-blue-700">{weather ? `${weather.effective_interval_minutes}-minute automatic interval` : "Not recorded"}</span>
            </div>
            {weather ? <>
              <p className="text-sm text-gray-600">{weather.reason}</p>
              {weather.controller_stale && <Notice>Weather check is missing or stale.</Notice>}
              {weather.dispatch_error && <Notice tone="error">Worker dispatch needs attention.</Notice>}
              <div className="divide-y divide-gray-100">{weather.providers.map(provider => <div key={provider.name} className="flex flex-wrap items-start justify-between gap-2 py-2">
                <div className="min-w-0"><a className="font-medium text-gray-900 underline underline-offset-2" href={provider.source_url} target="_blank" rel="noopener noreferrer">{provider.name}</a>
                  <p className="mt-1 text-xs text-gray-500">Checked {newsDate(provider.checked_at)}</p></div>
                <div className="text-right text-xs">
                  <span className={provider.status === "risk" ? "font-medium text-blue-700" : "text-gray-600"}>{providerLabels[provider.status] ?? provider.status}</span>
                  {provider.error_code && <p className="mt-1 text-amber-800">Needs checking</p>}
                </div>
              </div>)}</div>
              <details className="text-xs text-gray-600">
                <summary className="min-h-11 cursor-pointer py-3 font-medium focus-visible:outline-blue-600">Weather details</summary>
                <div className="space-y-4 pt-2">
                  <p>{weather.coverage_label}. Weather guides collection; news evidence determines flood areas.</p>
                  <p>Controller last checked: {newsDate(weather.controller_heartbeat_at)} · Dispatch: {weather.dispatch_state}</p>
                  {weather.dispatch_error && <p role="alert" className="break-words text-red-800">Worker dispatch: {weather.dispatch_error}</p>}
                  {weather.providers.map(provider => <div key={provider.name} className="space-y-1">
                    <p className="font-medium text-gray-900">{provider.name}</p>
                    {provider.risk_locations.length > 0 && <p className="break-words">Risk locations: {provider.risk_locations.join(", ")}</p>}
                    {provider.error_code && <p role="alert" className="break-words text-amber-800">{provider.name}: {provider.error_code}</p>}
                    {provider.bulletins.map(bulletin => <p key={`${bulletin.identity}:${bulletin.issued_at}`} className="break-words">{bulletin.identity} · Issued {newsDate(bulletin.issued_at, "Unknown")} · Valid until {newsDate(bulletin.valid_until, "Unknown")}</p>)}
                  </div>)}
                  <p className="font-medium text-gray-900">Monitored locations and controller diagnostics</p>
                  <p className="break-words">{weather.points.map(point => `${point.locality}${point.role === "upstream" ? " (upstream)" : ""}`).join(", ")}</p>
                  <p>Catalog {weather.catalog_version} · {weather.checks} checks · {weather.provider_failures} provider issues · {weather.worker_starts} accepted worker starts · Last check {weather.last_tick_duration_ms} ms</p>
                  <p>Last worker dispatch: {newsDate(weather.last_dispatch_at)} · Last positive signal: {newsDate(weather.last_positive_at)}</p>
                  <p>Cloud check target: every {data.scheduler_tick_target_minutes} minutes. A due time does not confirm a worker start.</p>
                </div>
              </details>
            </> : <p className="text-gray-500">No saved weather checks. Refresh after the controller runs.</p>}
          </section>
        </CardContent></Card>
      </div>

      <Card className="shadow-sm"><CardContent className="p-4 sm:p-5">
        <details className="text-sm">
          <summary className="min-h-11 cursor-pointer py-3 font-semibold text-gray-700 focus-visible:outline-blue-600">Run details and diagnostics</summary>
          <div className="space-y-5 pt-3">
            <dl className="grid grid-cols-2 gap-4 text-sm lg:grid-cols-4">
              <Metric label="Worker last started" value={newsDate(data.last_started_at)} />
              <Metric label="Last successful cycle" value={newsDate(data.last_successful_at)} />
              <Metric label="Last progress saved" value={newsDate(data.last_progress_at)} />
              <Metric label="Current stage started" value={newsDate(data.stage_started_at)} />
            </dl>
            <div className="space-y-3">
              <p className="text-xs font-medium text-gray-500">Latest saved collection · {newsDate(data.latest_collection_at)}</p>
              <dl className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-3 xl:grid-cols-6">
                <Metric label="Feed entries read" value={count(data.feed_counts.entries_read)} />
                <Metric label="Flood candidates" value={count(data.feed_counts.eligible_candidates)} />
                <Metric label="Articles saved or seen" value={count(data.feed_counts.articles_saved_or_seen)} />
                <Metric label="Feed errors" value={count(data.feed_counts.feed_errors)} />
                <Metric label="Article retrieval errors" value={count(data.feed_counts.body_errors)} />
                <Metric label="Unresolved article scope" value={count(data.feed_counts.scope_unresolved)} />
              </dl>
            </div>
            <div className="space-y-3">
              <p className="text-xs font-medium text-gray-500">Last completed cycle · {newsDate(cycle?.finished_at)}</p>
              <dl className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-3 xl:grid-cols-6">
                <Metric label="Articles processed" value={count(cycle?.counts.extraction?.completed)} />
                <Metric label="Claims evaluated" value={count(cycle?.counts.evaluation?.completed)} />
                <Metric label="Publications created" value={count(cycle?.counts.publication?.published)} />
                <Metric label="Flood areas activated" value={count(cycle?.counts.footprints?.total_activated)} />
                <Metric label="Floods cleared" value={count(cycle?.counts.publication?.cleared)} />
                <Metric label="Needs review" value={count(cycle?.counts.publication?.needs_review)} />
              </dl>
            </div>
            <p className="text-xs text-gray-600">Extraction queue: {count(data.queue_counts.pending)} waiting · {count(data.queue_counts.processing)} processing · {count(data.queue_counts.retry_wait)} awaiting retry · {count(data.queue_counts.failed)} failed.</p>
            {data.audit && <div className="space-y-2" data-testid="news-audit-diagnostics">
              <p className="text-xs font-medium text-gray-500">{data.audit.validation_mode === "source_rules" ? "NLP + source checks" : "Audit diagnostics"} · {data.audit.state}</p>
              {data.audit.validation_mode === "source_rules" ? <p className="text-xs text-gray-600">Checks the original article without AI requests. Flood zones are estimated from mapped roads; uncertain claims need review.</p> : <>
              <dl className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-3 xl:grid-cols-6">
                <Metric label="Audit requests" value={count(data.audit.request_count)} />
                <Metric label="Claims sent for audit" value={count(data.audit.claims_dispatched)} />
                <Metric label="Daily requests used" value={count(data.audit.used)} />
                <Metric label="Daily request limit" value={count(data.audit.limit)} />
                <Metric label="Requests remaining" value={count(data.audit.remaining)} />
                <Metric label="Next quota check" value={newsDate(data.audit.next_check_at)} />
              </dl>
              <p className="text-xs text-gray-500">Quota checked · {newsDate(data.audit.checked_at)} · Provider HTTP status · {data.audit.http_status ?? "Not recorded"}</p>
              {data.audit.model_next_check_at && <p className="text-xs text-gray-600">Model recovery check · {newsDate(data.audit.model_next_check_at)}</p>}
              {data.audit.failure_phase && <p role="alert" className="break-words text-xs text-red-800">Audit stopped during {data.audit.failure_phase}{data.audit.timeout_kind ? ` · ${data.audit.timeout_kind} timeout` : ""}{data.audit.elapsed_ms != null ? ` · ${(data.audit.elapsed_ms / 1000).toFixed(1)} seconds` : ""}.</p>}
              {data.audit.actual_model && <p className="break-words text-xs text-gray-500">Last response model · {data.audit.actual_model}</p>}
              </>}
              {data.audit.boundary_expected != null && <p className="text-xs text-gray-600">Qualified barangay boundaries · {data.audit.boundary_qualified ?? 0} of {data.audit.boundary_expected}. {data.audit.boundary_missing ?? 0} still need reviewed coverage.</p>}
              {data.audit.boundary_error && <p role="alert" className="break-words text-xs text-red-800">Boundary coverage is unavailable · {data.audit.boundary_error}</p>}
              {data.audit.error_code && <p role="alert" className="break-words text-xs text-red-800">Audit diagnostic: {data.audit.error_code}</p>}
            </div>}
            {data.error_code && <p role="alert" className="break-words text-xs text-red-800">Worker diagnostic: {data.error_code}</p>}
            {cycle?.error_code && <p role="alert" className="break-words text-xs text-red-800">Last completed cycle: {cycle.error_code}</p>}
            {Object.entries(data.stages).filter(([, stage]) => stage.errors.length > 0).map(([name, stage]) => <p key={name} role="alert" className="break-words text-xs text-red-800">{name}: {stage.errors.join(", ")}</p>)}
            <p className="text-xs text-gray-500">Status refreshes every 15 seconds while this page is open. Times are in the Philippines. Reading status does not collect news.</p>
          </div>
        </details>
      </CardContent></Card>
    </>}
  </div>;
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div className="min-w-0"><dt className="text-xs text-gray-500">{label}</dt><dd className="mt-1 break-words font-semibold text-gray-900">{value}</dd></div>;
}

function Notice({ children, tone = "warning" }: { children: React.ReactNode; tone?: "warning" | "error" }) {
  return <p role="alert" className={`flex items-start gap-2 text-xs leading-5 ${tone === "error" ? "text-red-800" : "text-amber-800"}`}>
    <AlertTriangle className="mt-0.5 size-3.5 shrink-0" aria-hidden="true" /><span className="min-w-0 break-words">{children}</span>
  </p>;
}
