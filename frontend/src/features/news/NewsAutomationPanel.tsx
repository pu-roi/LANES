"use client";

import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Clock,
  CloudRain,
  ExternalLink,
  FileText,
  Info,
  Loader2,
  MapPin,
  RefreshCw,
  ShieldCheck,
  Timer,
} from "lucide-react";
import { Button, Card, CardContent, Skeleton } from "@/shared/ui";
import { getNewsAutomation } from "./newsApi";
import { newsDate } from "./newsPresentation";

const providerLabels: Record<string, string> = {
  risk: "Rain risk detected",
  quiet: "Quiet / Clear",
  uncertain: "Incomplete",
  unavailable: "Unavailable",
};

function formatErrorCode(code: string | null | undefined): string | null {
  if (!code) return null;
  if (code === "weather_snapshot_stale") return "Snapshot stale (re-checking)";
  if (code === "rate_limited") return "Provider rate limited";
  if (code === "connection_error") return "Connection timeout";
  return code.replaceAll("_", " ");
}

export function NewsAutomationPanel() {
  const client = useQueryClient();
  const [locationsOpen, setLocationsOpen] = useState(false);
  const [diagnosticsOpen, setDiagnosticsOpen] = useState(false);

  const query = useQuery({
    queryKey: ["news-automation"],
    queryFn: ({ signal }) => getNewsAutomation(signal),
    refetchInterval: 15_000,
    staleTime: 10_000,
    retry: false,
  });

  const finished = query.data?.last_finished_at;
  useEffect(() => {
    if (!finished) return;
    for (const key of [
      "news-results",
      "news-collection",
      "news-feed-checkpoints",
      "news-monitoring",
      "news-telemetry",
    ]) {
      void client.invalidateQueries({ queryKey: [key] });
    }
  }, [client, finished]);

  const data = query.data;
  const cycle = data?.last_cycle;
  const weather = data?.weather;
  const count = (value: number | null | undefined) =>
    value == null ? "Not recorded" : value.toLocaleString();
  const attention =
    data && ["overdue", "partial", "requires_attention", "interrupted"].includes(data.state);

  return (
    <div className="space-y-6">
      {/* 1. NEWS AUTOMATION HERO CARD */}
      <Card className="border border-gray-200/80 shadow-sm">
        <CardContent className="space-y-6 p-5 sm:p-6">
          {/* Header Bar */}
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="space-y-1.5">
              <div className="flex items-center gap-2.5">
                <div className="flex size-8 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
                  <Activity className="size-4 shrink-0" aria-hidden="true" />
                </div>
                <div>
                  <h2 className="text-base font-bold tracking-tight text-gray-900 sm:text-lg">
                    News Automation Engine
                  </h2>
                  <p className="text-xs text-gray-500">
                    Automated news discovery, Taglish NLP extraction, and spatial flood corridor activation
                  </p>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div
                role="status"
                aria-live="polite"
                className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold ${
                  query.isError
                    ? "border border-red-200 bg-red-50 text-red-700"
                    : attention
                    ? "border border-amber-200 bg-amber-50 text-amber-800"
                    : data?.running
                    ? "border border-blue-200 bg-blue-50 text-blue-700"
                    : "border border-emerald-200 bg-emerald-50 text-emerald-700"
                }`}
              >
                {data?.running ? (
                  <Loader2 className="size-3.5 shrink-0 animate-spin text-blue-600 motion-reduce:animate-none" aria-hidden="true" />
                ) : (
                  <span className={`size-2 rounded-full ${attention ? "bg-amber-500" : "bg-emerald-500"}`} />
                )}
                {query.isError ? "Status unavailable" : data?.status_label ?? "Loading status…"}
              </div>

              <Button
                size="sm"
                variant="outline"
                aria-label="Refresh automation status"
                className="min-h-11 shrink-0 gap-2 border-gray-200 text-xs font-semibold"
                disabled={query.isFetching}
                onClick={() => void query.refetch()}
              >
                <RefreshCw
                  className={`size-3.5 ${query.isFetching ? "animate-spin" : ""}`}
                  aria-hidden="true"
                />
                Refresh
              </Button>
            </div>
          </div>

          {query.isError && (
            <Notice tone="error">
              {query.error.message}
              {data && " Previously loaded status may be stale."}
            </Notice>
          )}

          {query.isPending && (
            <div aria-label="Loading automation details" className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <Skeleton className="h-16 w-full rounded-xl" />
              <Skeleton className="h-16 w-full rounded-xl" />
              <Skeleton className="h-16 w-full rounded-xl" />
              <Skeleton className="h-16 w-full rounded-xl" />
            </div>
          )}

          {data && (
            <>
              {/* Stat Tiles Strip */}
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <StatTile
                  icon={Clock}
                  label="Next Collection Due"
                  value={newsDate(
                    data.next_collection_due_at,
                    data.collection_enabled ? "Not scheduled" : "Collection paused"
                  )}
                  tone={data.collection_overdue ? "warning" : "default"}
                />
                <StatTile
                  icon={CheckCircle2}
                  label="Last Cycle Finished"
                  value={newsDate(data.last_finished_at)}
                />
                <StatTile
                  icon={Timer}
                  label="Collection Cadence"
                  value={`${data.collection_interval_minutes}m · Automatic`}
                />
                <StatTile
                  icon={FileText}
                  label="Active Publishers"
                  value={`${count(data.enabled_sources)} sources`}
                />
              </div>

              {/* 3-Step Pipeline Stepper */}
              <div className="rounded-xl border border-gray-100 bg-slate-50/70 p-4">
                <div className="mb-3 flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-gray-500">
                    Execution Pipeline
                  </span>
                  <span className="text-[11px] text-gray-400">
                    Automatic multi-stage processing
                  </span>
                </div>

                <div className="grid gap-3 sm:grid-cols-3">
                  {[
                    {
                      step: "01",
                      label: "Collection",
                      description: "Ingest RSS & public news",
                      enabled: data.collection_enabled,
                    },
                    {
                      step: "02",
                      label: "Processing",
                      description: "Taglish NLP flood claims",
                      enabled: data.processing_enabled,
                    },
                    {
                      step: "03",
                      label: "Publication",
                      description: "Spatial zones & avoidance",
                      enabled: data.publication_enabled,
                    },
                  ].map((stage) => (
                    <div
                      key={stage.label}
                      aria-label={`${stage.label} ${stage.enabled ? "Enabled" : "Paused"}`}
                      className="relative flex items-center justify-between rounded-lg border border-gray-200/70 bg-white p-3 shadow-xs"
                    >
                      <div className="min-w-0 space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-[11px] font-bold text-gray-400">
                            {stage.step}
                          </span>
                          <span className="text-sm font-semibold text-gray-900">
                            {stage.label}
                          </span>
                        </div>
                        <p className="text-xs text-gray-500 truncate">
                          {stage.description}
                        </p>
                      </div>

                      <div className="shrink-0 pl-2">
                        <span
                          className={`inline-flex items-center rounded-md px-2 py-0.5 text-[11px] font-semibold ${
                            stage.enabled
                              ? "bg-emerald-50 text-emerald-700 border border-emerald-200/70"
                              : "bg-slate-100 text-slate-500 border border-slate-200"
                          }`}
                        >
                          {stage.enabled ? "Active" : "Paused"}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Warnings / Notices */}
              {data.collection_overdue && (
                <Notice>Collection is overdue. Check the deployed scheduler and worker status.</Notice>
              )}
              {data.error_code && (
                <Notice tone="error">
                  The last worker cycle reported an issue ({formatErrorCode(data.error_code)}). Check run diagnostics.
                </Notice>
              )}
              {(data.feed_counts.feed_errors > 0 ||
                data.feed_counts.body_errors > 0 ||
                data.feed_counts.scope_unresolved > 0) && (
                <Notice>
                  Feed health alert: {data.feed_counts.feed_errors} feed errors,{" "}
                  {data.feed_counts.body_errors} article retrieval errors, and{" "}
                  {data.feed_counts.scope_unresolved} unresolved scopes require review.
                </Notice>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {data && (
        <>
          {/* 2. RECENT RESULTS & WEATHER-BASED SCHEDULING (BALANCED 2-COLUMN GRID) */}
          <div className="grid items-stretch gap-6 lg:grid-cols-2">
            {/* 2A. RECENT COLLECTION & INGESTION TELEMETRY (BALANCED HEIGHT) */}
            <Card className="flex h-full flex-col justify-between border border-gray-200/80 shadow-sm">
              <CardContent className="flex flex-1 flex-col justify-between space-y-5 p-5 sm:p-6">
                <div className="space-y-4">
                  {/* Card Header */}
                  <div className="flex items-center justify-between border-b border-gray-100 pb-3">
                    <div className="flex items-center gap-2.5">
                      <div className="flex size-8 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
                        <FileText className="size-4 shrink-0" aria-hidden="true" />
                      </div>
                      <div>
                        <h3 className="text-base font-bold text-gray-900">Recent Collection Results</h3>
                        <p className="text-xs text-gray-500">
                          Latest collection cycle and ingestion pipeline throughput
                        </p>
                      </div>
                    </div>
                    <span className="inline-flex items-center rounded-full border border-gray-200 bg-slate-50 px-2.5 py-1 text-xs font-bold text-gray-700">
                      {newsDate(data.latest_collection_at)}
                    </span>
                  </div>

                  {/* Primary 2x2 Stat Grid */}
                  <div className="grid grid-cols-2 gap-3 sm:gap-4">
                    <div className="rounded-xl border border-gray-100 bg-slate-50/70 p-3.5">
                      <span className="text-[11px] font-semibold uppercase tracking-wider text-gray-400">
                        Feed Entries Read
                      </span>
                      <p className="mt-1 text-2xl font-black text-gray-900">
                        {count(data.feed_counts.entries_read)}
                      </p>
                      <p className="mt-0.5 text-[11px] text-gray-500">Raw publisher articles found</p>
                    </div>

                    <div className="rounded-xl border border-blue-100 bg-blue-50/40 p-3.5">
                      <span className="text-[11px] font-semibold uppercase tracking-wider text-blue-600">
                        Flood Candidates
                      </span>
                      <p className="mt-1 text-2xl font-black text-blue-700">
                        {count(data.feed_counts.eligible_candidates)}
                      </p>
                      <p className="mt-0.5 text-[11px] text-blue-600/80">Filtered keyword matches</p>
                    </div>

                    <div className="rounded-xl border border-gray-100 bg-slate-50/70 p-3.5">
                      <span className="text-[11px] font-semibold uppercase tracking-wider text-gray-400">
                        Articles Processed
                      </span>
                      <p className="mt-1 text-2xl font-black text-gray-900">
                        {count(cycle?.counts.extraction?.completed)}
                      </p>
                      <p className="mt-0.5 text-[11px] text-gray-500">Passed to Taglish NLP parser</p>
                    </div>

                    <div className="rounded-xl border border-emerald-100 bg-emerald-50/40 p-3.5">
                      <span className="text-[11px] font-semibold uppercase tracking-wider text-emerald-600">
                        Flood Areas Activated
                      </span>
                      <p className="mt-1 text-2xl font-black text-emerald-700">
                        {count(cycle?.counts.footprints?.total_activated)}
                      </p>
                      <p className="mt-0.5 text-[11px] text-emerald-600/80">Active detour polygons</p>
                    </div>
                  </div>

                  {/* Extraction Queue State (Parallel to Provider Cards) */}
                  <div className="rounded-xl border border-gray-100 bg-slate-50/70 p-3.5 space-y-2.5">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-bold uppercase tracking-wider text-gray-400">
                        Extraction Queue State
                      </span>
                      <span className="text-[11px] text-gray-400">Worker scheduling buffer</span>
                    </div>

                    <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                      <div className="rounded-lg bg-white p-2 border border-gray-200/70 text-center">
                        <span className="text-[10px] font-bold uppercase text-gray-400 block">Waiting</span>
                        <strong className="text-sm font-black text-gray-900 mt-0.5 block">{count(data.queue_counts.pending)}</strong>
                      </div>
                      <div className="rounded-lg bg-white p-2 border border-gray-200/70 text-center">
                        <span className="text-[10px] font-bold uppercase text-blue-600 block">Processing</span>
                        <strong className="text-sm font-black text-blue-700 mt-0.5 block">{count(data.queue_counts.processing)}</strong>
                      </div>
                      <div className="rounded-lg bg-white p-2 border border-gray-200/70 text-center">
                        <span className="text-[10px] font-bold uppercase text-amber-600 block">Retry Wait</span>
                        <strong className="text-sm font-black text-amber-700 mt-0.5 block">{count(data.queue_counts.retry_wait)}</strong>
                      </div>
                      <div className="rounded-lg bg-white p-2 border border-gray-200/70 text-center">
                        <span className="text-[10px] font-bold uppercase text-red-600 block">Failed</span>
                        <strong className="text-sm font-black text-red-700 mt-0.5 block">{count(data.queue_counts.failed)}</strong>
                      </div>
                    </div>
                  </div>

                  {/* Ingestion & Feed Telemetry (Parallel to Controller Telemetry) */}
                  <div className="rounded-xl border border-gray-100 bg-slate-50/70 p-3.5 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-bold uppercase tracking-wider text-gray-400">
                        Feed Retrieval &amp; Article Scope
                      </span>
                      <span className="text-[11px] text-gray-500 font-medium">
                        {count(data.feed_counts.articles_saved_or_seen)} saved or seen
                      </span>
                    </div>

                    <div className="grid grid-cols-3 gap-2">
                      <div className="rounded-lg bg-white p-2.5 border border-gray-200/70 text-center">
                        <span className="text-[10px] uppercase font-bold text-gray-400 block">Feed Errors</span>
                        <span className={`text-sm font-extrabold mt-0.5 block ${data.feed_counts.feed_errors > 0 ? "text-amber-700" : "text-gray-900"}`}>
                          {count(data.feed_counts.feed_errors)}
                        </span>
                      </div>
                      <div className="rounded-lg bg-white p-2.5 border border-gray-200/70 text-center">
                        <span className="text-[10px] uppercase font-bold text-gray-400 block">Body Errors</span>
                        <span className={`text-sm font-extrabold mt-0.5 block ${data.feed_counts.body_errors > 0 ? "text-amber-700" : "text-gray-900"}`}>
                          {count(data.feed_counts.body_errors)}
                        </span>
                      </div>
                      <div className="rounded-lg bg-white p-2.5 border border-gray-200/70 text-center">
                        <span className="text-[10px] uppercase font-bold text-gray-400 block">Unresolved</span>
                        <span className={`text-sm font-extrabold mt-0.5 block ${data.feed_counts.scope_unresolved > 0 ? "text-amber-700" : "text-gray-900"}`}>
                          {count(data.feed_counts.scope_unresolved)}
                        </span>
                      </div>
                    </div>

                    <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] text-gray-400 border-t border-gray-200/60 pt-2">
                      <span>Evaluated claims: <strong className="text-gray-700">{count(cycle?.counts.evaluation?.completed)}</strong></span>
                      <span>Published: <strong className="text-emerald-700">{count(cycle?.counts.publication?.published)}</strong></span>
                    </div>
                  </div>
                </div>

                {/* Bottom Status Note */}
                <div className="pt-2">
                  {data.feed_counts.eligible_candidates === 0 ? (
                    <div className="flex items-center gap-2 rounded-lg bg-slate-50 px-3 py-2 text-xs text-gray-500 border border-slate-100">
                      <Info className="size-3.5 text-gray-400 shrink-0" aria-hidden="true" />
                      <span>No new flood candidates identified in the latest collection cycle.</span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 rounded-lg bg-blue-50 px-3 py-2 text-xs text-blue-700 border border-blue-100">
                      <CheckCircle2 className="size-3.5 text-blue-600 shrink-0" aria-hidden="true" />
                      <span>{count(data.feed_counts.eligible_candidates)} flood candidates captured for evaluation.</span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* 2B. WEATHER-BASED SCHEDULING (BALANCED HEIGHT) */}
            <Card role="region" aria-label="Weather-based scheduling" className="flex h-full flex-col justify-between border border-gray-200/80 shadow-sm">
              <CardContent className="flex flex-1 flex-col justify-between space-y-5 p-5 sm:p-6">
                <div className="space-y-4">
                  {/* Header */}
                  <div className="flex flex-wrap items-center justify-between gap-3 border-b border-gray-100 pb-3">
                    <div className="flex items-center gap-2.5">
                      <div className="flex size-8 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
                        <CloudRain className="size-4 shrink-0" aria-hidden="true" />
                      </div>
                      <div>
                        <h3 className="text-base font-bold text-gray-900">Weather-Based Scheduling</h3>
                        <p className="text-xs text-gray-500">Real-time precipitation telemetry &amp; cadence control</p>
                      </div>
                    </div>

                    <span className="inline-flex items-center rounded-full border border-blue-200 bg-blue-50 px-2.5 py-1 text-xs font-bold text-blue-700">
                      {weather ? `${weather.effective_interval_minutes}-minute automatic interval` : "Not recorded"}
                    </span>
                  </div>

                  {weather ? (
                    <>
                      {/* Reason & Alert Banners */}
                      <div className="space-y-2">
                        <div className="flex items-start gap-2.5 rounded-xl border border-slate-200/80 bg-slate-50/80 p-3.5 text-xs">
                          <Info className="mt-0.5 size-4 shrink-0 text-blue-600" aria-hidden="true" />
                          <div className="min-w-0 space-y-0.5">
                            <p className="font-semibold text-gray-900">{weather.reason}</p>
                            <p className="text-gray-500">{weather.coverage_label || "Weather guides collection cadence; news evidence determines flood areas."}</p>
                          </div>
                        </div>

                        {weather.controller_stale && (
                          <Notice>Weather controller heartbeat is missing or stale. Re-evaluating.</Notice>
                        )}
                        {weather.dispatch_error && (
                          <Notice tone="error">Worker dispatch needs attention: {weather.dispatch_error}</Notice>
                        )}
                      </div>

                      {/* Clean, Symmetrical Provider Mini-Cards (Open-Meteo & PAGASA) */}
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-[11px] font-bold uppercase tracking-wider text-gray-400">
                            Weather Telemetry Providers
                          </span>
                          <span className="text-[11px] text-gray-400">{weather.providers.length} sources checked</span>
                        </div>

                        <div className="grid gap-2.5 sm:grid-cols-2">
                          {weather.providers.map((provider) => {
                            const isRisk = provider.status === "risk";
                            const isQuiet = provider.status === "quiet";
                            const formattedErr = formatErrorCode(provider.error_code);
                            const riskCount = provider.risk_locations.length;

                            return (
                              <div
                                key={provider.name}
                                className={`flex flex-col justify-between rounded-xl border p-3.5 transition-colors ${
                                  isRisk
                                    ? "border-blue-200 bg-blue-50/40"
                                    : "border-gray-200/80 bg-white"
                                }`}
                              >
                                <div>
                                  <div className="flex items-start justify-between gap-2">
                                    <a
                                      href={provider.source_url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="group inline-flex items-center gap-1.5 text-xs font-bold text-gray-900 hover:text-blue-600 transition-colors"
                                    >
                                      <span>{provider.name}</span>
                                      <ExternalLink className="size-3 text-gray-400 group-hover:text-blue-600 transition-colors" />
                                    </a>

                                    <span
                                      className={`inline-flex items-center rounded-md px-2 py-0.5 text-[11px] font-semibold ${
                                        isRisk
                                          ? "bg-blue-100 text-blue-800"
                                          : isQuiet
                                          ? "bg-emerald-50 text-emerald-700"
                                          : "bg-amber-50 text-amber-800"
                                      }`}
                                    >
                                      {providerLabels[provider.status] ?? provider.status}
                                    </span>
                                  </div>

                                  <p className="mt-1 text-[11px] text-gray-400">
                                    Checked {newsDate(provider.checked_at)}
                                  </p>

                                  {formattedErr && (
                                    <p className="mt-2 inline-flex items-center gap-1 text-[11px] font-medium text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200/70">
                                      <AlertTriangle className="size-3 shrink-0" />
                                      <span>{formattedErr}</span>
                                    </p>
                                  )}
                                </div>

                                {/* Symmetrical Risk Status Bar (Eliminates the giant 18-city text dump) */}
                                <div className="mt-3 border-t border-gray-100 pt-2">
                                  {riskCount > 0 ? (
                                    <div className="flex items-center justify-between text-[11px] text-blue-700">
                                      <span className="font-semibold">Rain risk detected</span>
                                      <span className="rounded-md bg-blue-100 px-1.5 py-0.5 font-bold">
                                        {riskCount} localities
                                      </span>
                                    </div>
                                  ) : (
                                    <div className="flex items-center justify-between text-[11px] text-emerald-700">
                                      <span className="font-semibold">No active rain risk</span>
                                      <span className="rounded-md bg-emerald-50 px-1.5 py-0.5 font-bold border border-emerald-200/60">
                                        0 localities
                                      </span>
                                    </div>
                                  )}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>

                      {/* Monitored Locations Section (Clean & Collapsible) */}
                      <div className="rounded-xl border border-gray-100 bg-slate-50/60 p-3.5 space-y-2.5">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <MapPin className="size-3.5 text-blue-600" aria-hidden="true" />
                            <span className="text-xs font-bold text-gray-900">
                              Monitored River Basins &amp; LGUs
                            </span>
                          </div>
                          <span className="rounded-md bg-white px-2 py-0.5 text-[11px] font-semibold text-gray-600 border border-gray-200/70">
                            {weather.points.length} Localities
                          </span>
                        </div>

                        <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-gray-500">
                          <span>
                            17 Metro Manila LGUs + 3 Upstream Basins (Rodriguez, San Mateo, Antipolo)
                          </span>
                          <button
                            type="button"
                            onClick={() => setLocationsOpen(!locationsOpen)}
                            aria-expanded={locationsOpen}
                            className="inline-flex min-h-11 items-center gap-1 font-semibold text-blue-600 hover:text-blue-700 transition-colors focus-visible:outline-blue-600 cursor-pointer"
                          >
                            <span>{locationsOpen ? "Hide list" : "View all locations"}</span>
                            {locationsOpen ? <ChevronUp className="size-3.5" /> : <ChevronDown className="size-3.5" />}
                          </button>
                        </div>

                        {/* Expandable Locality Tag Cloud */}
                        {locationsOpen && (
                          <div className="pt-2 border-t border-gray-200/60">
                            <div className="flex flex-wrap gap-1.5 max-h-48 overflow-y-auto pr-1">
                              {weather.points.map((point) => {
                                const isUpstream = point.role === "upstream";
                                const hasRisk = weather.providers.some((p) =>
                                  p.risk_locations.includes(point.locality)
                                );

                                return (
                                  <span
                                    key={point.locality}
                                    className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-[11px] font-medium border ${
                                      hasRisk
                                        ? "bg-blue-50 text-blue-700 border-blue-200 font-bold"
                                        : isUpstream
                                        ? "bg-amber-50/70 text-amber-800 border-amber-200/70"
                                        : "bg-white text-gray-700 border-gray-200/80"
                                    }`}
                                  >
                                    {point.locality}
                                    {isUpstream && (
                                      <span className="text-[9px] text-amber-600 font-bold uppercase tracking-wider">
                                        (Upstream)
                                      </span>
                                    )}
                                  </span>
                                );
                              })}
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Controller Telemetry Strip */}
                      <div className="rounded-xl border border-gray-100 bg-slate-50/60 p-3.5 space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-[11px] font-bold uppercase tracking-wider text-gray-400">
                            Controller Telemetry
                          </span>
                          <span className="text-[11px] text-gray-500 font-medium">
                            Catalog {weather.catalog_version}
                          </span>
                        </div>

                        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                          <div className="rounded-lg bg-white p-2.5 border border-gray-200/70 text-center">
                            <span className="text-[10px] uppercase font-bold text-gray-400 block">Total Checks</span>
                            <span className="text-sm font-extrabold text-gray-900 mt-0.5 block">
                              {weather.checks.toLocaleString()}
                            </span>
                          </div>

                          <div className="rounded-lg bg-white p-2.5 border border-gray-200/70 text-center">
                            <span className="text-[10px] uppercase font-bold text-gray-400 block">Worker Starts</span>
                            <span className="text-sm font-extrabold text-gray-900 mt-0.5 block">
                              {weather.worker_starts.toLocaleString()}
                            </span>
                          </div>

                          <div className="rounded-lg bg-white p-2.5 border border-gray-200/70 text-center">
                            <span className="text-[10px] uppercase font-bold text-gray-400 block">Provider Retries</span>
                            <span className="text-sm font-extrabold text-gray-900 mt-0.5 block">
                              {weather.provider_failures.toLocaleString()}
                            </span>
                          </div>

                          <div className="rounded-lg bg-white p-2.5 border border-gray-200/70 text-center">
                            <span className="text-[10px] uppercase font-bold text-gray-400 block">Latency</span>
                            <span className="text-sm font-extrabold text-gray-900 mt-0.5 block">
                              {weather.last_tick_duration_ms} ms
                            </span>
                          </div>
                        </div>

                        <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] text-gray-400 border-t border-gray-200/60 pt-2">
                          <span>Dispatch state: <strong className="text-gray-700 capitalize">{weather.dispatch_state}</strong></span>
                          <span>Heartbeat: {newsDate(weather.controller_heartbeat_at)}</span>
                        </div>
                      </div>
                    </>
                  ) : (
                    <p className="text-sm text-gray-500">No saved weather checks. Refresh after the controller runs.</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 3. RUN DETAILS AND DIAGNOSTICS (COLLAPSIBLE ACCORDION) */}
          <Card className="border border-gray-200/80 shadow-sm">
            <CardContent className="p-5 sm:p-6">
              <button
                type="button"
                onClick={() => setDiagnosticsOpen(!diagnosticsOpen)}
                aria-expanded={diagnosticsOpen}
                className="flex w-full min-h-11 items-center justify-between gap-3 text-left focus-visible:outline-blue-600 cursor-pointer"
              >
                <div className="flex items-center gap-2.5">
                  <div className="flex size-8 items-center justify-center rounded-lg bg-slate-100 text-slate-700">
                    <ShieldCheck className="size-4 shrink-0" aria-hidden="true" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-gray-900">Run Details &amp; Diagnostics</h3>
                    <p className="text-xs text-gray-500">
                      Telemetry, ingestion metrics, queue breakdown, and verification audit logs
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2 text-xs font-semibold text-gray-500">
                  <span>{diagnosticsOpen ? "Collapse" : "Expand"}</span>
                  {diagnosticsOpen ? <ChevronUp className="size-4" /> : <ChevronDown className="size-4" />}
                </div>
              </button>

              {diagnosticsOpen && (
                <div className="mt-5 space-y-6 border-t border-gray-100 pt-5 text-sm">
                  {/* Worker Lifecycle Timestamps */}
                  <div className="space-y-3">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-gray-400">
                      Worker Lifecycle Timestamps
                    </h4>
                    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                      <StatTile label="Worker Last Started" value={newsDate(data.last_started_at)} />
                      <StatTile label="Last Successful Cycle" value={newsDate(data.last_successful_at)} />
                      <StatTile label="Last Progress Saved" value={newsDate(data.last_progress_at)} />
                      <StatTile label="Current Stage Started" value={newsDate(data.stage_started_at)} />
                    </div>
                  </div>

                  {/* Complete Cycle Processing Statistics */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-gray-400">
                        Cycle Processing Summary
                      </h4>
                      <span className="text-xs text-gray-400">{newsDate(cycle?.finished_at)}</span>
                    </div>

                    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-6">
                      <StatTile label="Articles Processed" value={count(cycle?.counts.extraction?.completed)} />
                      <StatTile label="Claims Evaluated" value={count(cycle?.counts.evaluation?.completed)} />
                      <StatTile label="Publications Created" value={count(cycle?.counts.publication?.published)} />
                      <StatTile label="Areas Activated" value={count(cycle?.counts.footprints?.total_activated)} />
                      <StatTile label="Floods Cleared" value={count(cycle?.counts.publication?.cleared)} />
                      <StatTile label="Needs Review" value={count(cycle?.counts.publication?.needs_review)} />
                    </div>
                  </div>

                  {/* Verification & Audit Diagnostics */}
                  {data.audit && (
                    <div className="space-y-3 rounded-xl border border-gray-100 bg-slate-50/70 p-4" data-testid="news-audit-diagnostics">
                      <div className="flex items-center justify-between">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-gray-500">
                          {data.audit.validation_mode === "source_rules"
                            ? "NLP + Source Consistency Checks"
                            : "Audit Diagnostics"}{" "}
                          · <span className="text-gray-900 capitalize">{data.audit.state}</span>
                        </h4>
                        <span className="text-xs text-gray-400">Zero external LLM API dependency</span>
                      </div>

                      {data.audit.validation_mode === "source_rules" ? (
                        <p className="text-xs text-gray-600 leading-relaxed">
                          Validation uses deterministic local Taglish NLP and cross-source consistency checks.
                          Avoidance polygons are bounded to verified OSM road sections and UP NOAH susceptibility layers;
                          ambiguous claims remain flagged for staff review.
                        </p>
                      ) : (
                        <>
                          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-6">
                            <StatTile label="Audit Requests" value={count(data.audit.request_count)} />
                            <StatTile label="Claims Dispatched" value={count(data.audit.claims_dispatched)} />
                            <StatTile label="Daily Requests Used" value={count(data.audit.used)} />
                            <StatTile label="Daily Limit" value={count(data.audit.limit)} />
                            <StatTile label="Remaining" value={count(data.audit.remaining)} />
                            <StatTile label="Next Quota Check" value={newsDate(data.audit.next_check_at)} />
                          </div>
                          <p className="text-xs text-gray-400">
                            Quota checked {newsDate(data.audit.checked_at)} · HTTP {data.audit.http_status ?? "Not recorded"}
                          </p>
                        </>
                      )}

                      {data.audit.boundary_expected != null && (
                        <p className="text-xs text-gray-600">
                          Qualified barangay boundaries: <strong>{data.audit.boundary_qualified ?? 0}</strong> of{" "}
                          <strong>{data.audit.boundary_expected}</strong>. (
                          {data.audit.boundary_missing ?? 0} require reviewed boundary coverage).
                        </p>
                      )}
                      {data.audit.boundary_error && (
                        <Notice tone="error">Boundary coverage unavailable: {data.audit.boundary_error}</Notice>
                      )}
                      {data.audit.error_code && (
                        <Notice tone="error">Audit diagnostic: {data.audit.error_code}</Notice>
                      )}
                    </div>
                  )}

                  {/* Stage-Specific Errors */}
                  {data.error_code && <Notice tone="error">Worker diagnostic: {data.error_code}</Notice>}
                  {cycle?.error_code && <Notice tone="error">Last cycle error: {cycle.error_code}</Notice>}
                  {Object.entries(data.stages)
                    .filter(([, stage]) => stage.errors.length > 0)
                    .map(([name, stage]) => (
                      <Notice key={name} tone="error">
                        {name}: {stage.errors.join(", ")}
                      </Notice>
                    ))}

                  <div className="flex flex-wrap items-center justify-between gap-2 border-t border-gray-100 pt-3 text-xs text-gray-400">
                    <span>Telemetry refreshes every 15s while panel is active. Manila Timezone (PHT).</span>
                    <span>Read-only monitoring mode.</span>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

function StatTile({
  label,
  value,
  icon: Icon,
  tone = "default",
}: {
  label: string;
  value: string;
  icon?: React.ComponentType<{ className?: string }>;
  tone?: "default" | "warning" | "error";
}) {
  return (
    <div
      className={`rounded-xl border p-3.5 transition-colors ${
        tone === "warning"
          ? "border-amber-200/80 bg-amber-50/50"
          : tone === "error"
          ? "border-rose-200/80 bg-rose-50/50"
          : "border-gray-100 bg-slate-50/70"
      }`}
    >
      <div className="flex items-center justify-between gap-1">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-gray-400 truncate">
          {label}
        </span>
        {Icon && <Icon className="size-3.5 text-gray-400 shrink-0" />}
      </div>
      <p
        className={`mt-1 font-bold break-words text-sm sm:text-base ${
          tone === "warning"
            ? "text-amber-800"
            : tone === "error"
            ? "text-rose-800"
            : "text-gray-900"
        }`}
      >
        {value}
      </p>
    </div>
  );
}

function Notice({
  children,
  tone = "warning",
}: {
  children: React.ReactNode;
  tone?: "warning" | "error";
}) {
  return (
    <div
      role="alert"
      className={`flex items-start gap-2.5 rounded-xl border p-3 text-xs leading-relaxed ${
        tone === "error"
          ? "border-red-200 bg-red-50 text-red-800"
          : "border-amber-200 bg-amber-50 text-amber-800"
      }`}
    >
      <AlertTriangle className="mt-0.5 size-3.5 shrink-0" aria-hidden="true" />
      <span className="min-w-0 break-words font-medium">{children}</span>
    </div>
  );
}
