"use client";

import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import { ArrowLeft, Calendar, CalendarClock, Clock3, MapPin, ShieldCheck, Timer, X } from "lucide-react";
import { Button } from "@/shared/ui";
import { getFloodEventHistoryDetail } from "./floodHistoryApi";
import type { FloodReport } from "@/features/admin/adminApi";
import type { HistoricalMapFocusTarget } from "./floodHistoryApi";
import { FloodEventDetailsTabs } from "./FloodEventDetailsTabs";

const formatDate = (value: string | null | undefined) => value ? new Intl.DateTimeFormat("en-PH", { timeZone: "Asia/Manila", month: "short", day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit" }).format(new Date(value)) : "Not recorded";
const formatDuration = (minutes?: number | null) => minutes == null ? "In progress" : minutes >= 60 ? `${Math.floor(minutes / 60)}h ${minutes % 60}m` : `${minutes}m`;
const timelineLabel = (type: string) => ({ event_verified: "Flood event verified", zone_created: "Official flood zone created", zone_updated: "Official flood zone updated", severity_peak_changed: "Peak severity updated", report_linked: "Supporting report linked", event_ended: "Flood event ended" }[type] ?? type.replaceAll("_", " "));
const reportLocation = (report: FloodReport) => [report.barangay, report.road_name || report.human_readable_location].filter(Boolean).join(" · ") || "Location not recorded";
type DetailTab = "overview" | "official-history" | "reports";

export function FloodEventDetailModal({ eventId, onClose, onFocusHistoricalMap }: { eventId: number | null; onClose: () => void; onFocusHistoricalMap: (target: HistoricalMapFocusTarget) => void }) {
  const [selectedReport, setSelectedReport] = useState<FloodReport | null>(null);
  const [activeTab, setActiveTab] = useState<DetailTab>("overview");
  const { data, isLoading, isError } = useQuery({ queryKey: ["flood-event-history-detail", eventId], queryFn: () => getFloodEventHistoryDetail(eventId!), enabled: eventId !== null });
  const handleClose = () => { setSelectedReport(null); setActiveTab("overview"); onClose(); };
  const focusHistoricalMap = (target: HistoricalMapFocusTarget) => { handleClose(); onFocusHistoricalMap(target); };
  useEffect(() => {
    if (eventId === null) return;
    const closeOnEscape = (event: KeyboardEvent) => { if (event.key === "Escape" && selectedReport === null) { setActiveTab("overview"); onClose(); } };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [eventId, onClose, selectedReport]);
  const summaryCards = data ? [
    { Icon: CalendarClock, label: "First report received", value: formatDate(data.first_reported_at) },
    { Icon: ShieldCheck, label: "Officially verified", value: formatDate(data.verified_at) },
    { Icon: Clock3, label: data.ended_at ? "Officially ended" : "Current state", value: data.ended_at ? formatDate(data.ended_at) : "Still active" },
    { Icon: Timer, label: "Official duration", value: formatDuration(data.duration_minutes) },
  ] : [];
  return <><AnimatePresence>{eventId !== null && <motion.div aria-labelledby="flood-event-details-title" aria-modal="true" className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-3 backdrop-blur-xs sm:p-4" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onMouseDown={handleClose} role="dialog">
    <motion.div className="relative flex max-h-[calc(100dvh-1.5rem)] w-full max-w-4xl flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl sm:max-h-[90vh]" initial={{ opacity: 0, scale: 0.97, y: 12 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.97, y: 12 }} transition={{ duration: 0.18 }} onMouseDown={(event) => event.stopPropagation()}>
      <div className="flex items-start justify-between gap-3 border-b border-slate-100 bg-slate-50/80 px-4 py-4 sm:items-center sm:px-6"><div className="flex min-w-0 items-center gap-3"><div className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-blue-600 text-sm font-bold text-white shadow-sm">#{eventId}</div><div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><h2 id="flood-event-details-title" className="text-base font-bold text-slate-900">Flood Event Details</h2>{data && <span className={`rounded-full border px-2.5 py-1 text-xs font-bold uppercase ${data.status === "active" ? "border-emerald-200 bg-emerald-100 text-emerald-800" : "border-slate-200 bg-slate-100 text-slate-700"}`}>{data.status}</span>}</div><p className="mt-0.5 flex items-center gap-1.5 text-xs text-slate-500"><Calendar className="size-3.5 text-slate-400" />{data ? `Verified ${formatDate(data.verified_at)}` : "Loading verified incident"}</p></div></div><button aria-label="Close flood event details" className="rounded-xl p-2 text-slate-400 transition-colors hover:bg-slate-200/60 hover:text-slate-700" onClick={handleClose} type="button"><X className="size-5" /></button></div>
      <div className="max-h-[75vh] overflow-y-auto p-5 pb-[calc(var(--bottom-nav-height)+env(safe-area-inset-bottom))] sm:p-6 sm:pb-[calc(1.5rem+env(safe-area-inset-bottom))]">
        {isLoading && <p className="py-12 text-center text-sm text-slate-500">Loading protected event evidence…</p>}
        {isError && <p className="rounded-lg bg-red-50 p-4 text-sm text-red-800">Event details could not be loaded. Close this dialog and try again.</p>}
        {data && <FloodEventDetailsTabs activeTab={activeTab} data={data} onChangeTab={setActiveTab} onFocusHistoricalMap={focusHistoricalMap} />}
        <div className="hidden">
        {data && selectedReport ? <section className="space-y-5">
          <Button size="sm" variant="ghost" onClick={() => setSelectedReport(null)}><ArrowLeft className="mr-1 h-4 w-4" />Back to event</Button>
          <div><p className="text-xs font-semibold uppercase tracking-wide text-blue-600">Original supporting evidence</p><h3 className="mt-1 text-lg font-bold text-slate-900">Flood Report #{selectedReport.id}</h3><p className="mt-1 text-sm text-slate-600">{reportLocation(selectedReport)}</p></div>
          <div className="grid gap-3 sm:grid-cols-2"><div className="rounded-xl bg-slate-50 p-4"><p className="text-xs text-slate-500">Reporter</p><p className="mt-1 font-semibold text-slate-900">{selectedReport.reporter_name || "System ingestion"}</p><p className="text-sm text-slate-600">{selectedReport.reporter_username ? `@${selectedReport.reporter_username}` : selectedReport.reporter_role || "Contributor"}</p></div><div className="rounded-xl bg-slate-50 p-4"><p className="text-xs text-slate-500">Moderation outcome</p><p className="mt-1 font-semibold capitalize text-slate-900">{selectedReport.status}</p><p className="text-sm text-slate-600">Submitted {formatDate(selectedReport.created_at)}</p></div></div>
          <div><p className="text-sm font-semibold text-slate-900">Description</p><p className="mt-2 rounded-xl bg-slate-50 p-4 text-sm leading-6 text-slate-700">{selectedReport.raw_text || "No written description."}</p></div>
          <div className="grid gap-3 sm:grid-cols-2"><div className="rounded-xl border border-slate-200 p-4"><p className="text-xs text-slate-500">Flood survey</p><p className="mt-1 text-sm text-slate-800">Depth: {selectedReport.depth || "Not specified"}</p><p className="text-sm text-slate-800">Coverage: {selectedReport.is_bidirectional ? "Both directions" : "One direction or not recorded"}</p><p className="text-sm text-slate-800">Passability: {selectedReport.survey?.passable_vehicles || selectedReport.passable_vehicles || "Not recorded"}</p><p className="text-sm text-slate-800">Hidden hazards: {selectedReport.survey?.hidden_hazards || selectedReport.hidden_hazards || "Not recorded"}</p></div><details className="rounded-xl border border-slate-200 p-4"><summary className="cursor-pointer text-xs text-slate-500">Exact original geometry</summary><pre className="mt-2 max-h-32 overflow-auto whitespace-pre-wrap break-all text-xs text-slate-700">{selectedReport.geometry ? JSON.stringify(selectedReport.geometry) : "No geometry recorded"}</pre></details></div>
          {selectedReport.media_urls && selectedReport.media_urls.length > 0 && <div><p className="text-sm font-semibold text-slate-900">Evidence media</p><div className="mt-2 flex flex-wrap gap-2">{selectedReport.media_urls.map((url, index) => <a key={url} href={url} target="_blank" rel="noreferrer" className="rounded-lg border border-blue-200 bg-blue-50 px-3 py-2 text-sm font-medium text-blue-700 hover:bg-blue-100">Open evidence {index + 1}</a>)}</div></div>}
        </section> : data ? <div className="space-y-6">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{summaryCards.map(({ Icon, label, value }) => <div key={label} className="rounded-xl bg-slate-50 p-4"><Icon className="h-4 w-4 text-blue-600" /><p className="mt-2 text-xs text-slate-500">{label}</p><p className="mt-1 text-sm font-semibold text-slate-900">{value}</p></div>)}</div>
          <section><h3 className="font-semibold text-slate-900">Affected places</h3><div className="mt-2 flex flex-wrap gap-2">{data.locations.map((location) => <span key={location.id} className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-800"><MapPin className="h-3 w-3" />{location.display_name}</span>)}</div></section>
          <section className="grid gap-3 sm:grid-cols-2"><div><h3 className="font-semibold text-slate-900">Incident summary</h3><p className="mt-2 text-sm text-slate-700">Peak severity: <span className="font-semibold capitalize">{data.peak_severity}</span>{data.peak_depth ? ` · ${data.peak_depth}` : ""}</p><p className="mt-1 text-sm text-slate-600">{data.supporting_report_count ?? data.reports.length} linked report{(data.supporting_report_count ?? data.reports.length) === 1 ? "" : "s"} from {data.reporter_count ?? 0} identified reporter{(data.reporter_count ?? 0) === 1 ? "" : "s"} · {data.media_count ?? 0} evidence file{(data.media_count ?? 0) === 1 ? "" : "s"}.</p></div><div><h3 className="font-semibold text-slate-900">Official zone history</h3><p className="mt-2 text-sm text-slate-600">Zone records document the official footprint; they are not live-routing advisories.</p><div className="mt-2 space-y-2">{data.zones.map((zone) => <div key={zone.id} className="flex items-center justify-between gap-3 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-700"><span>Zone #{zone.id} · <span className="capitalize">{zone.severity}</span>{zone.depth ? ` · ${zone.depth}` : ""}<span className="block text-slate-500">Created {formatDate(zone.created_at)}</span></span><span className={zone.is_active ? "font-semibold text-emerald-700" : "text-slate-500"}>{zone.is_active ? "Active" : "Ended"}</span></div>)}</div></div></section>
          <section><h3 className="font-semibold text-slate-900">Incident timeline</h3><ol className="mt-3 space-y-3 border-l border-slate-200 pl-4">{data.timeline.map((entry) => <li key={entry.id}><p className="text-xs font-semibold uppercase tracking-wide text-blue-700">{timelineLabel(entry.entry_type)}</p><p className="mt-1 text-sm text-slate-800">{entry.summary}</p><p className="mt-1 text-xs text-slate-500">{formatDate(entry.occurred_at)}</p></li>)}</ol></section>
          <section><h3 className="font-semibold text-slate-900">Supporting reports</h3><div className="mt-3 divide-y divide-slate-100 rounded-xl border border-slate-200">{data.reports.length === 0 ? <p className="p-4 text-sm text-slate-500">This official event has no public supporting reports.</p> : data.reports.map((report) => <div key={report.id} className="flex items-start justify-between gap-4 p-4"><div><p className="font-medium text-slate-900">Report #{report.id} · {report.reporter_name || "Reporter"}</p><p className="mt-1 text-xs text-slate-500">{reportLocation(report)}</p><p className="mt-1 text-sm text-slate-600">{report.raw_text || "No written description."}</p><p className="mt-1 text-xs text-slate-500">Submitted {formatDate(report.created_at)}</p></div><div className="flex flex-col items-end gap-2"><span className="rounded-full bg-slate-100 px-2 py-1 text-xs capitalize text-slate-600">{report.status}</span><Button size="sm" variant="outline" onClick={() => setSelectedReport(report)}>View</Button></div></div>)}</div></section>
        </div> : null}
        </div>
      </div>
    </motion.div>
  </motion.div>}</AnimatePresence></>;
}
