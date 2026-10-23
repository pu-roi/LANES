"use client";

import { parseUtcDate } from "@/lib/utils";

import { useState } from "react";
import { CalendarClock, Car, ChevronLeft, Clock3, EyeOff, FileText, Map as MapIcon, MapPin, Ruler, ShieldCheck, Timer, Users } from "lucide-react";
import { Button, FloodReportDetailsModal, RecordTimeline, Tabs } from "@/shared/ui";
import type { FloodReport } from "@/features/admin/adminApi";
import type { FloodEventDetail, FloodEventZone, HistoricalMapFocusTarget } from "./floodHistoryApi";
import { formatFloodDepth } from "@/lib/floodDepth";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Pagination } from "@/shared/ui";
import { getHistoryCollection, type FloodEventTimelineEntry, type FloodEventLocation } from "./floodHistoryApi";
import type { ReactNode } from "react";
import type { EventNewsSource } from './floodHistoryApi';
import { NewsArticleDialog } from '@/features/news/NewsArticleDialog';
import { publisherLink } from '@/features/news/newsPresentation';

function HistoryCollection<T>({ eventId, datasetId, collection, children }: { eventId: number; datasetId?: string; collection: "reports" | "zones" | "timeline" | "locations" | "news_sources";
  children: (items: T[], total: number, page: number) => ReactNode }) {
  const [page, setPage] = useState(1);
  const query = useQuery({ queryKey: ["flood-event-history", "inspection", eventId, collection, page, datasetId],
    queryFn: ({ signal }) => getHistoryCollection<T>(eventId, collection, page, signal, datasetId), placeholderData: keepPreviousData, staleTime: 30_000, retry: false });
  return <>{query.isError && <div role="alert" className="py-3 text-sm text-red-700">Could not load {collection.replaceAll('_', ' ')}. <Button variant="outline" size="sm" onClick={() => query.refetch()}>Retry {collection.replaceAll('_', ' ')}</Button></div>}
    {!query.data && !query.isError && <p role="status" className="py-3 text-sm text-slate-500">Loading {collection.replaceAll('_', ' ')}…</p>}
    {query.data && <>{children(query.data.items, query.data.total, query.data.page)}<Pagination page={query.data.page} totalPages={query.data.pages} onPageChange={setPage} disabled={query.isFetching} /></>}</>;
}

type DetailTab = "overview" | "official-history" | "reports";

const formatDate = (value: string | null | undefined) => value ? new Intl.DateTimeFormat("en-PH", { timeZone: "Asia/Manila", month: "short", day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit" }).format(parseUtcDate(value) || new Date(value)) : "Not recorded";
const formatDuration = (minutes?: number | null) => minutes == null ? "In progress" : minutes >= 60 ? `${Math.floor(minutes / 60)}h ${minutes % 60}m` : `${minutes}m`;
const timelineLabel = (type: string) => ({ event_verified: "Flood event verified", zone_created: "Official flood zone created", zone_updated: "Official flood zone updated", severity_peak_changed: "Peak severity updated", report_linked: "Supporting report linked", event_ended: "Flood event ended" }[type] ?? type.replaceAll("_", " "));
const reportLocation = (report: FloodReport) => [report.barangay, report.road_name || report.human_readable_location].filter(Boolean).join(" · ") || "Location not recorded";
const displayValue = (value?: string | null) => value?.replaceAll("_", " ") || "Not recorded";
const severityBadgeClass = (severity: string) => ({ low: "border-lime-200 bg-lime-100 text-lime-800", medium: "border-yellow-200 bg-yellow-100 text-yellow-800", high: "border-orange-200 bg-orange-100 text-orange-800", extreme: "border-red-200 bg-red-100 text-red-800" }[severity] ?? "border-slate-200 bg-slate-100 text-slate-700");

interface FloodEventDetailsTabsProps {
  activeTab: DetailTab;
  data: FloodEventDetail;
  onChangeTab: (tab: DetailTab) => void;
  onFocusHistoricalMap: (target: HistoricalMapFocusTarget) => void;
}

export function FloodEventDetailsTabs({ activeTab, data, onChangeTab, onFocusHistoricalMap }: FloodEventDetailsTabsProps) {
  const tabItems = [
    { id: "overview", label: "Overview", icon: FileText },
    { id: "official-history", label: "Official history", icon: ShieldCheck },
    { id: "reports", label: `Reports (${data.supporting_report_count ?? data.reports.length})`, icon: Users },
  ];

  return <div className={activeTab === "reports" ? "space-y-5 lg:flex lg:min-h-0 lg:flex-1 lg:flex-col lg:space-y-0 lg:gap-5" : "space-y-5"}>
    <Tabs tabs={tabItems} activeTab={activeTab} onChange={(tab) => onChangeTab(tab as DetailTab)} variant="pills" fullWidth layoutId="flood-event-detail-tabs" />
    {activeTab === "overview" && <Overview data={data} onFocusHistoricalMap={onFocusHistoricalMap} />}
    {activeTab === "official-history" && <OfficialHistory data={data} onFocusHistoricalMap={onFocusHistoricalMap} />}
    {activeTab === "reports" && <HistoryCollection<FloodReport> eventId={data.id} datasetId={data.historical?.dataset_id} collection="reports">{(reports, total, page) => <SupportingReports key={page} firstPage={page === 1} data={{ ...data, reports, supporting_report_count: total }} onFocusHistoricalMap={onFocusHistoricalMap} />}</HistoryCollection>}
  </div>;
}

function Overview({ data, onFocusHistoricalMap }: Pick<FloodEventDetailsTabsProps, "data" | "onFocusHistoricalMap">) {
  const newsTiming = Boolean(data.duration_basis);
  const lifecycle = [
    { Icon: CalendarClock, iconClassName: "bg-blue-100 text-blue-600", label: newsTiming ? "Source observation" : "First report received", value: newsTiming ? (data.observed_at ? formatDate(data.observed_at) : data.occurrence_date ?? "Not stated in source") : formatDate(data.first_reported_at) },
    { Icon: ShieldCheck, iconClassName: "bg-emerald-100 text-emerald-600", label: newsTiming ? "Administrative record created" : "Officially verified", value: formatDate(data.verified_at) },
    { Icon: Clock3, iconClassName: "bg-slate-200 text-slate-600", label: newsTiming ? data.closure_basis?.startsWith('assumed_') ? "Assumed archive endpoint" : data.closure_basis === 'source_supported' ? "Source-reported clearance" : "Record ended" : data.ended_at ? "Officially ended" : "Current state", value: data.ended_at ? formatDate(data.ended_at) : data.status === "ended" ? "Historical; endpoint unknown" : "Still active" },
    { Icon: Timer, iconClassName: "bg-violet-100 text-violet-600", label: newsTiming ? "Observed duration" : "Official duration", value: newsTiming ? "Not established by source" : formatDuration(data.duration_minutes) },
  ];
  return <>
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{lifecycle.map(({ Icon, iconClassName, label, value }) => <div key={label} className="flex items-start gap-3 rounded-xl border border-slate-200/70 bg-slate-50/80 p-3.5"><div className={`flex size-8 shrink-0 items-center justify-center rounded-lg ${iconClassName}`}><Icon className="size-4" /></div><div><p className="text-[11px] font-bold uppercase tracking-wider text-slate-400">{label}</p><p className="mt-1 text-sm font-bold text-slate-900">{value}</p></div></div>)}</div>
    <section className="grid gap-5 rounded-xl border border-slate-200/70 bg-slate-50/80 p-4 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end"><div><div className="flex flex-wrap items-center gap-2"><h3 className="text-sm font-bold text-slate-900">Official incident summary</h3><span className={`rounded-full border px-2.5 py-1 text-xs font-bold uppercase ${severityBadgeClass(data.peak_severity)}`}>{data.peak_severity}</span></div><p className="mt-2 text-sm text-slate-700">{newsTiming ? "Peak recorded water level:" : "Peak verified water level:"} <span className="font-semibold">{formatFloodDepth(data.peak_depth) || "Not recorded"}</span></p><p className="mt-1 text-sm text-slate-600">{data.zone_count ?? data.zones.length} source zone{(data.zone_count ?? data.zones.length) === 1 ? "" : "s"} · {data.supporting_report_count ?? data.reports.length} linked report{(data.supporting_report_count ?? data.reports.length) === 1 ? "" : "s"} · {data.reporter_count ?? 0} reporter{(data.reporter_count ?? 0) === 1 ? "" : "s"} · {data.media_count ?? 0} evidence file{(data.media_count ?? 0) === 1 ? "" : "s"}</p></div><Button className="w-full gap-2 sm:w-auto" onClick={() => onFocusHistoricalMap({ eventId: data.id, label: `Flood Event #${data.id}` })} size="sm" variant="outline"><MapIcon className="size-4" />View on historical map</Button></section>
    <section><h3 className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-slate-400"><MapPin className="size-3.5 text-slate-500" />Affected places</h3><HistoryCollection<FloodEventLocation> eventId={data.id} datasetId={data.historical?.dataset_id} collection="locations">{locations => <div className="mt-2 flex flex-wrap gap-2">{locations.length ? locations.map((location) => <span key={location.id} className="inline-flex items-center gap-1 rounded-full border border-blue-100 bg-blue-50 px-3 py-1.5 text-xs font-medium text-blue-800"><MapPin className="size-3" />{location.display_name}</span>) : <p className="text-sm text-slate-500">No affected locations recorded.</p>}</div>}</HistoryCollection></section>
    {Boolean(data.news_article_count) && <section aria-label="News article evidence"><h3 className="text-sm font-bold text-slate-900">News sources ({data.news_article_count})</h3><p className="mt-1 text-xs text-slate-500">Captured article evidence linked to this event. Citizen submissions remain in Reports.</p><HistoryCollection<EventNewsSource> eventId={data.id} collection="news_sources">{sources => <div className="divide-y divide-slate-100">{sources.map(source => <NewsSource key={`${source.run_id}-${source.group_id ?? source.claim_index}`} source={source} />)}</div>}</HistoryCollection></section>}
  </>;
}

function NewsSource({ source }: { source: EventNewsSource }) {
  const [open, setOpen] = useState(false);
  const href = source.source_url ? publisherLink(source.source_url) : null;
  const facts = [
    ['Published', source.published_at ? formatDate(source.published_at) : source.published_date ? `${source.published_date} (time not stated)` : 'Not recorded'],
    ['Observation', source.observed_at ? formatDate(source.observed_at) : source.occurrence_date ?? 'Not stated'],
    ['Location', [source.road, source.barangay, source.city].filter(Boolean).join(' · ') || 'Not recorded'],
    ['Reported water level', source.depth_raw ?? 'Not stated'],
    ['Normalized water level', source.depth_normalized ? formatFloodDepth(source.depth_normalized) : 'Not established'],
    ['Passability', displayValue(source.passability)], ['Condition', displayValue(source.condition)],
    ['Extraction', `${displayValue(source.extraction_mode)} · ${source.extraction_status}`],
    ['Geometry', displayValue(source.geometry_basis)],
  ];
  return <article className="min-w-0 space-y-3 py-4"><h4 className="break-words text-sm font-semibold text-slate-900">{source.title ?? 'Captured news article'}</h4><p className="text-xs text-slate-500">{source.publisher ?? 'Publisher not recorded'} · Saved article version #{source.article_version_id}</p><dl className="grid gap-3 sm:grid-cols-2">{facts.map(([label, value]) => <div className="min-w-0" key={label}><dt className="text-xs text-slate-500">{label}</dt><dd className="mt-1 break-words text-sm text-slate-800">{value}</dd></div>)}</dl><blockquote className="whitespace-pre-wrap break-words border-l-2 border-blue-200 pl-3 text-sm leading-6 text-slate-700">{source.excerpt ?? 'Source excerpt not recorded.'}</blockquote><div className="flex flex-wrap items-center gap-3"><Button size="sm" variant="outline" onClick={() => setOpen(true)}>View captured article and extraction</Button>{href && <a className="break-all text-sm text-blue-700 underline" href={href} target="_blank" rel="noopener noreferrer">Publisher article</a>}</div><details className="text-xs text-slate-500"><summary className="min-h-11 cursor-pointer py-3">Evidence details</summary><p className="break-words">Extraction #{source.run_id} · {source.group_id ? `Group ${source.group_id}` : `Claim ${source.claim_index ?? 'unknown'}`} · Completed {formatDate(source.completed_at)}</p>{source.geometry_provenance && <pre className="mt-2 whitespace-pre-wrap break-all">{JSON.stringify(source.geometry_provenance, null, 2)}</pre>}</details>{open && <NewsArticleDialog articleId={source.article_id} initialRunId={source.run_id} onClose={() => setOpen(false)} />}</article>;
}

function OfficialHistory({ data, onFocusHistoricalMap }: Pick<FloodEventDetailsTabsProps, "data" | "onFocusHistoricalMap">) {
  return <div className="grid gap-7 lg:grid-cols-[minmax(0,1fr)_minmax(17rem,0.85fr)]">
    <section><h3 className="text-sm font-bold text-slate-900">Official zone history</h3><p className="mt-1 text-xs text-slate-500">Historical footprints only — never used for active route avoidance.</p>
      <HistoryCollection<FloodEventZone> eventId={data.id} datasetId={data.historical?.dataset_id} collection="zones">{zones => <div className="mt-3 space-y-3">{zones.length ? zones.map(zone => <ZoneHistoryRow key={zone.id} eventId={data.id} onFocusHistoricalMap={onFocusHistoricalMap} zone={zone} />) : <p className="text-sm text-slate-500">No official zones recorded.</p>}</div>}</HistoryCollection>
    </section>
    <section><h3 className="text-sm font-bold text-slate-900">Incident timeline</h3><HistoryCollection<FloodEventTimelineEntry> eventId={data.id} datasetId={data.historical?.dataset_id} collection="timeline">{entries => <RecordTimeline entries={entries.map(entry => ({ id: entry.id, label: timelineLabel(entry.entry_type), description: entry.entry_type === "historical_import" ? "Saved source evidence linked to this record." : entry.entry_type === "historical_demo_deactivated" ? "Zone deactivated." : entry.summary, timestamp: formatDate(entry.occurred_at) }))} emptyMessage="No lifecycle entries recorded." />}</HistoryCollection></section>
  </div>;
}

function ZoneHistoryRow({ eventId, zone, onFocusHistoricalMap }: { eventId: number; zone: FloodEventZone; onFocusHistoricalMap: (target: HistoricalMapFocusTarget) => void }) {
  return <article className="rounded-xl border border-slate-200/70 bg-slate-50/80 p-4"><div className="flex flex-wrap items-start justify-between gap-2"><div><div className="flex flex-wrap items-center gap-2"><p className="font-bold text-slate-900">Official Zone #{zone.id}</p><span className={`rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase ${severityBadgeClass(zone.severity)}`}>{zone.severity}</span></div><p className="mt-1 text-xs text-slate-500">Created {formatDate(zone.created_at)}{zone.updated_at ? ` · Updated ${formatDate(zone.updated_at)}` : ""}</p></div><span className={zone.is_active ? "rounded-full border border-emerald-200 bg-emerald-100 px-2 py-1 text-xs font-semibold text-emerald-800" : "rounded-full border border-slate-200 bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700"}>{zone.is_active ? "Active" : "Ended"}</span></div><div className="mt-3 grid gap-3 sm:grid-cols-2"><ZoneMetric icon={<Ruler className="size-4" />} iconClassName="bg-blue-100 text-blue-600" label="Water level" value={formatFloodDepth(zone.depth) || "Not recorded"} /><ZoneMetric icon={<EyeOff className="size-4" />} iconClassName="bg-amber-100 text-amber-600" label="Submerged hazards" value={displayValue(zone.hidden_hazards)} /><ZoneMetric icon={<Car className="size-4" />} iconClassName="bg-emerald-100 text-emerald-600" label="Passable vehicles" value={displayValue(zone.passable_vehicles)} /></div><Button className="mt-3 gap-1.5" onClick={() => onFocusHistoricalMap({ eventId, geometry: zone.geometry, label: `Official Zone #${zone.id}`, cameraOnly: true })} size="sm" variant="ghost"><MapIcon className="size-3.5" />View zone on map</Button></article>;
}

function SupportingReports({ data, onFocusHistoricalMap, firstPage }: Pick<FloodEventDetailsTabsProps, "data" | "onFocusHistoricalMap"> & { firstPage: boolean }) {
  const [selectedReport, setSelectedReport] = useState<FloodReport | null>(null);
  const reportCount = data.supporting_report_count ?? data.reports.length;

  return <section className="lg:flex lg:min-h-0 lg:flex-1 lg:flex-col">
    <div className="flex flex-wrap items-end justify-between gap-2">
      <div>
        <h3 className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-slate-400"><FileText className="size-3.5 text-slate-500" />Reports linked to this event</h3>
        <p className="mt-1 text-xs text-slate-500">Review the original submission and every merged report as separate historical evidence.</p>
      </div>
      {reportCount > 0 && <span className="text-xs font-semibold text-slate-500">{reportCount} report{reportCount === 1 ? "" : "s"}</span>}
    </div>

    {reportCount === 0 ? <p className="mt-3 rounded-xl border border-slate-200/70 bg-slate-50/40 p-5 text-sm text-slate-500">No citizen reports are linked to this event. News article evidence is available in Overview when recorded.</p> : <div className="mt-3 min-h-[32rem] overflow-hidden rounded-xl border border-slate-200/70 bg-slate-50/40 lg:min-h-0 lg:flex-1 lg:grid lg:grid-cols-[minmax(18rem,0.8fr)_minmax(0,1.2fr)]">
      <div className={selectedReport ? "hidden min-h-0 overflow-y-auto lg:block" : "min-h-0 overflow-y-auto"}>
        <div className="divide-y divide-slate-100 px-4">{data.reports.map((report, index) => <article key={report.id} className={`py-4 ${selectedReport?.id === report.id ? "bg-blue-50/70 -mx-4 px-4" : ""}`}>
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2"><p className="font-bold text-slate-900">Report #{report.id}</p>{firstPage && index === 0 && <span className="rounded-full border border-blue-200 bg-blue-100 px-2 py-0.5 text-[10px] font-bold uppercase text-blue-700">First linked</span>}<span className="rounded-full border border-emerald-200 bg-emerald-100 px-2 py-0.5 text-[10px] font-bold uppercase text-emerald-800">{report.status}</span></div>
              <p className="mt-1 truncate text-sm font-medium text-slate-700">{report.reporter_name || "System ingestion"}</p>
              <p className="mt-1 text-xs text-slate-500">{reportLocation(report)} · {formatDate(report.created_at)}</p>
              <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-xs text-slate-500"><span className="capitalize">Severity: {report.severity}</span><span>{report.media_urls?.length ?? 0} evidence file{(report.media_urls?.length ?? 0) === 1 ? "" : "s"}</span></div>
            </div>
            <Button aria-label={`View report ${report.id} details`} className="shrink-0" onClick={() => setSelectedReport(report)} size="sm" variant={selectedReport?.id === report.id ? "secondary" : "outline"}>View</Button>
          </div>
        </article>)}</div>
      </div>

      <div className={selectedReport ? "min-h-[32rem] bg-white lg:min-h-0" : "hidden min-h-[32rem] border-l border-slate-200 bg-white lg:flex lg:min-h-0 lg:items-center lg:justify-center"}>
        {selectedReport ? <div className="h-full min-h-[32rem] lg:min-h-0">
          <div className="border-b border-slate-100 p-2 lg:hidden"><Button className="gap-1.5" onClick={() => setSelectedReport(null)} size="sm" variant="ghost"><ChevronLeft className="size-4" />Back to reports</Button></div>
          <FloodReportDetailsModal isOpen onClose={() => setSelectedReport(null)} onViewOnMap={(report) => onFocusHistoricalMap({ eventId: data.id, geometry: report.geometry, label: `Flood Report #${report.id}` })} presentation="panel" report={selectedReport} />
        </div> : <p className="max-w-xs text-center text-sm text-slate-500">Select a report to inspect its original survey, reporter, evidence media, and mapped location.</p>}
      </div>
    </div>}
  </section>;
}

function ZoneMetric({ icon, iconClassName, label, value }: { icon: React.ReactNode; iconClassName: string; label: string; value: string }) {
  return <div className="flex items-start gap-3"><div className={`flex size-8 shrink-0 items-center justify-center rounded-lg ${iconClassName}`}>{icon}</div><div><p className="text-[11px] font-bold uppercase tracking-wider text-slate-400">{label}</p><p className="text-sm font-bold capitalize text-slate-900">{value}</p></div></div>;
}
