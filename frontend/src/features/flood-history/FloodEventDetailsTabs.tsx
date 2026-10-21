"use client";

import { parseUtcDate } from "@/lib/utils";

import { useState } from "react";
import { CalendarClock, Car, ChevronLeft, Clock3, EyeOff, FileText, Map as MapIcon, MapPin, Ruler, ShieldCheck, Timer, Users } from "lucide-react";
import { Button, FloodReportDetailsModal, RecordTimeline, Tabs } from "@/shared/ui";
import type { FloodReport } from "@/features/admin/adminApi";
import type { FloodEventDetail, FloodEventZone, HistoricalMapFocusTarget } from "./floodHistoryApi";
import { formatFloodDepth } from "@/lib/floodDepth";
import { useQuery } from "@tanstack/react-query";
import { Pagination } from "@/shared/ui";
import { getHistoryCollection, type FloodEventTimelineEntry, type FloodEventLocation } from "./floodHistoryApi";
import type { ReactNode } from "react";

function HistoryCollection<T>({ eventId, collection, children }: { eventId: number; collection: "reports" | "zones" | "timeline" | "locations";
  children: (items: T[], total: number, page: number) => ReactNode }) {
  const [page, setPage] = useState(1);
  const query = useQuery({ queryKey: ["flood-event-history", "inspection", eventId, collection, page],
    queryFn: ({ signal }) => getHistoryCollection<T>(eventId, collection, page, signal), staleTime: 30_000, retry: false });
  if (query.isError) return <div role="alert" className="py-3 text-sm text-red-700">Could not load {collection}. <Button variant="outline" size="sm" onClick={() => query.refetch()}>Retry {collection}</Button></div>;
  if (!query.data) return <p role="status" className="py-3 text-sm text-slate-500">Loading {collection}…</p>;
  return <>{children(query.data.items, query.data.total, query.data.page)}<Pagination page={query.data.page} totalPages={query.data.pages} onPageChange={setPage} disabled={query.isFetching} /></>;
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
    {activeTab === "reports" && <HistoryCollection<FloodReport> eventId={data.id} collection="reports">{(reports, total, page) => <SupportingReports key={page} firstPage={page === 1} data={{ ...data, reports, supporting_report_count: total }} onFocusHistoricalMap={onFocusHistoricalMap} />}</HistoryCollection>}
  </div>;
}

function Overview({ data, onFocusHistoricalMap }: Pick<FloodEventDetailsTabsProps, "data" | "onFocusHistoricalMap">) {
  const lifecycle = [
    { Icon: CalendarClock, iconClassName: "bg-blue-100 text-blue-600", label: "First report received", value: formatDate(data.first_reported_at) },
    { Icon: ShieldCheck, iconClassName: "bg-emerald-100 text-emerald-600", label: "Officially verified", value: formatDate(data.verified_at) },
    { Icon: Clock3, iconClassName: "bg-slate-200 text-slate-600", label: data.ended_at ? "Officially ended" : "Current state", value: data.ended_at ? formatDate(data.ended_at) : "Still active" },
    { Icon: Timer, iconClassName: "bg-violet-100 text-violet-600", label: "Official duration", value: formatDuration(data.duration_minutes) },
  ];
  return <>
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{lifecycle.map(({ Icon, iconClassName, label, value }) => <div key={label} className="flex items-start gap-3 rounded-xl border border-slate-200/70 bg-slate-50/80 p-3.5"><div className={`flex size-8 shrink-0 items-center justify-center rounded-lg ${iconClassName}`}><Icon className="size-4" /></div><div><p className="text-[11px] font-bold uppercase tracking-wider text-slate-400">{label}</p><p className="mt-1 text-sm font-bold text-slate-900">{value}</p></div></div>)}</div>
    <section className="grid gap-5 rounded-xl border border-slate-200/70 bg-slate-50/80 p-4 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end"><div><div className="flex flex-wrap items-center gap-2"><h3 className="text-sm font-bold text-slate-900">Official incident summary</h3><span className={`rounded-full border px-2.5 py-1 text-xs font-bold uppercase ${severityBadgeClass(data.peak_severity)}`}>{data.peak_severity}</span></div><p className="mt-2 text-sm text-slate-700">Peak verified water level: <span className="font-semibold">{formatFloodDepth(data.peak_depth) || "Not recorded"}</span></p><p className="mt-1 text-sm text-slate-600">{data.zone_count ?? data.zones.length} source zone{(data.zone_count ?? data.zones.length) === 1 ? "" : "s"} · {data.supporting_report_count ?? data.reports.length} linked report{(data.supporting_report_count ?? data.reports.length) === 1 ? "" : "s"} · {data.reporter_count ?? 0} reporter{(data.reporter_count ?? 0) === 1 ? "" : "s"} · {data.media_count ?? 0} evidence file{(data.media_count ?? 0) === 1 ? "" : "s"}</p></div><Button className="w-full gap-2 sm:w-auto" onClick={() => onFocusHistoricalMap({ eventId: data.id, label: `Flood Event #${data.id}` })} size="sm" variant="outline"><MapIcon className="size-4" />View on historical map</Button></section>
    <section><h3 className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-slate-400"><MapPin className="size-3.5 text-slate-500" />Affected places</h3><HistoryCollection<FloodEventLocation> eventId={data.id} collection="locations">{locations => <div className="mt-2 flex flex-wrap gap-2">{locations.length ? locations.map((location) => <span key={location.id} className="inline-flex items-center gap-1 rounded-full border border-blue-100 bg-blue-50 px-3 py-1.5 text-xs font-medium text-blue-800"><MapPin className="size-3" />{location.display_name}</span>) : <p className="text-sm text-slate-500">No affected locations recorded.</p>}</div>}</HistoryCollection></section>
  </>;
}

function OfficialHistory({ data, onFocusHistoricalMap }: Pick<FloodEventDetailsTabsProps, "data" | "onFocusHistoricalMap">) {
  return <div className="grid gap-7 lg:grid-cols-[minmax(0,1fr)_minmax(17rem,0.85fr)]">
    <section><h3 className="text-sm font-bold text-slate-900">Official zone history</h3><p className="mt-1 text-xs text-slate-500">Historical footprints only — never used for active route avoidance.</p>
      <HistoryCollection<FloodEventZone> eventId={data.id} collection="zones">{zones => <div className="mt-3 space-y-3">{zones.length ? zones.map(zone => <ZoneHistoryRow key={zone.id} eventId={data.id} onFocusHistoricalMap={onFocusHistoricalMap} zone={zone} />) : <p className="text-sm text-slate-500">No official zones recorded.</p>}</div>}</HistoryCollection>
    </section>
    <section><h3 className="text-sm font-bold text-slate-900">Incident timeline</h3><HistoryCollection<FloodEventTimelineEntry> eventId={data.id} collection="timeline">{entries => <RecordTimeline entries={entries.map(entry => ({ id: entry.id, label: timelineLabel(entry.entry_type), description: entry.summary, timestamp: formatDate(entry.occurred_at) }))} emptyMessage="No lifecycle entries recorded." />}</HistoryCollection></section>
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

    {reportCount === 0 ? <p className="mt-3 rounded-xl border border-slate-200/70 bg-slate-50/40 p-5 text-sm text-slate-500">No reports are linked to this event. Historical event records should retain their originating report when one was used to create the incident.</p> : <div className="mt-3 min-h-[32rem] overflow-hidden rounded-xl border border-slate-200/70 bg-slate-50/40 lg:min-h-0 lg:flex-1 lg:grid lg:grid-cols-[minmax(18rem,0.8fr)_minmax(0,1.2fr)]">
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
