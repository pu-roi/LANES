"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, CalendarClock, FileText, MapPin, Users } from "lucide-react";
import { Modal, Button } from "@/shared/ui";
import { getFloodEventHistoryDetail } from "./floodHistoryApi";
import type { FloodReport } from "@/features/admin/adminApi";

const formatDate = (value: string | null | undefined) => value ? new Date(value).toLocaleString() : "Not recorded";

export function FloodEventDetailModal({ eventId, onClose }: { eventId: number | null; onClose: () => void }) {
  const [selectedReport, setSelectedReport] = useState<FloodReport | null>(null);
  const { data, isLoading, isError } = useQuery({ queryKey: ["flood-event-history-detail", eventId], queryFn: () => getFloodEventHistoryDetail(eventId!), enabled: eventId !== null });
  const handleClose = () => { setSelectedReport(null); onClose(); };
  const summaryCards = data ? [
    { Icon: CalendarClock, label: "Officially verified", value: formatDate(data.verified_at) },
    { Icon: Users, label: "Supporting reports", value: String(data.supporting_report_count ?? data.reports.length) },
    { Icon: FileText, label: "Evidence media", value: String(data.media_count ?? 0) },
  ] : [];
  return <Modal isOpen={eventId !== null} onClose={handleClose} title="Flood Event details" bare>
    <div className="w-full max-w-4xl overflow-hidden rounded-2xl bg-white shadow-2xl">
      <div className="flex items-start justify-between border-b border-slate-100 px-5 py-4 sm:px-6"><div><p className="text-xs font-semibold uppercase tracking-wide text-blue-600">Verified incident record</p><h2 className="mt-1 text-xl font-bold text-slate-900">Flood Event #{eventId}</h2></div><Button size="sm" variant="ghost" onClick={handleClose}>Close</Button></div>
      <div className="max-h-[75vh] overflow-y-auto p-5 sm:p-6">
        {isLoading && <p className="py-12 text-center text-sm text-slate-500">Loading protected event evidence…</p>}
        {isError && <p className="rounded-lg bg-red-50 p-4 text-sm text-red-800">Event details could not be loaded. Close this dialog and try again.</p>}
        {data && selectedReport ? <section className="space-y-5"><Button size="sm" variant="ghost" onClick={() => setSelectedReport(null)}><ArrowLeft className="mr-1 h-4 w-4" />Back to event</Button><div><p className="text-xs font-semibold uppercase tracking-wide text-blue-600">Original supporting evidence</p><h3 className="mt-1 text-lg font-bold text-slate-900">Flood Report #{selectedReport.id}</h3></div><div className="grid gap-3 sm:grid-cols-2"><div className="rounded-xl bg-slate-50 p-4"><p className="text-xs text-slate-500">Reporter</p><p className="mt-1 font-semibold text-slate-900">{selectedReport.reporter_name || "System ingestion"}</p><p className="text-sm text-slate-600">{selectedReport.reporter_username ? `@${selectedReport.reporter_username}` : selectedReport.reporter_role || "Contributor"}</p></div><div className="rounded-xl bg-slate-50 p-4"><p className="text-xs text-slate-500">Moderation outcome</p><p className="mt-1 font-semibold capitalize text-slate-900">{selectedReport.status}</p><p className="text-sm text-slate-600">Submitted {formatDate(selectedReport.created_at)}</p></div></div><div><p className="text-sm font-semibold text-slate-900">Description</p><p className="mt-2 rounded-xl bg-slate-50 p-4 text-sm leading-6 text-slate-700">{selectedReport.raw_text || "No written description."}</p></div><div className="grid gap-3 sm:grid-cols-2"><div className="rounded-xl border border-slate-200 p-4"><p className="text-xs text-slate-500">Flood survey</p><p className="mt-1 text-sm text-slate-800">Depth: {selectedReport.depth || "Not specified"}</p><p className="text-sm text-slate-800">Passability: {selectedReport.survey?.passable_vehicles || selectedReport.passable_vehicles || "Not recorded"}</p><p className="text-sm text-slate-800">Hidden hazards: {selectedReport.survey?.hidden_hazards || selectedReport.hidden_hazards || "Not recorded"}</p></div><div className="rounded-xl border border-slate-200 p-4"><p className="text-xs text-slate-500">Exact original geometry</p><pre className="mt-2 max-h-32 overflow-auto whitespace-pre-wrap break-all text-xs text-slate-700">{selectedReport.geometry ? JSON.stringify(selectedReport.geometry) : "No geometry recorded"}</pre></div></div>{selectedReport.media_urls && selectedReport.media_urls.length > 0 && <div><p className="text-sm font-semibold text-slate-900">Evidence media</p><div className="mt-2 flex flex-wrap gap-2">{selectedReport.media_urls.map((url, index) => <a key={url} href={url} target="_blank" rel="noreferrer" className="rounded-lg border border-blue-200 bg-blue-50 px-3 py-2 text-sm font-medium text-blue-700 hover:bg-blue-100">Open evidence {index + 1}</a>)}</div></div>}</section> : data ? <div className="space-y-6">
          <div className="grid gap-3 sm:grid-cols-3">{summaryCards.map(({ Icon, label, value }) => <div key={label} className="rounded-xl bg-slate-50 p-4"><Icon className="h-4 w-4 text-blue-600" /><p className="mt-2 text-xs text-slate-500">{label}</p><p className="mt-1 text-sm font-semibold text-slate-900">{value}</p></div>)}</div>
          <section><h3 className="font-semibold text-slate-900">Affected places</h3><div className="mt-2 flex flex-wrap gap-2">{data.locations.map((location) => <span key={location.id} className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-800"><MapPin className="h-3 w-3" />{location.display_name}</span>)}</div></section>
          <section><h3 className="font-semibold text-slate-900">Incident timeline</h3><ol className="mt-3 space-y-3 border-l border-slate-200 pl-4">{data.timeline.map((entry) => <li key={entry.id}><p className="text-sm text-slate-800">{entry.summary}</p><p className="mt-1 text-xs text-slate-500">{formatDate(entry.occurred_at)}</p></li>)}</ol></section>
          <section><h3 className="font-semibold text-slate-900">Supporting reports</h3><div className="mt-3 divide-y divide-slate-100 rounded-xl border border-slate-200">{data.reports.length === 0 ? <p className="p-4 text-sm text-slate-500">This official event has no public supporting reports.</p> : data.reports.map((report) => <div key={report.id} className="flex items-start justify-between gap-4 p-4"><div><p className="font-medium text-slate-900">Report #{report.id} · {report.reporter_name || "Reporter"}</p><p className="mt-1 text-sm text-slate-600">{report.raw_text || "No written description."}</p><p className="mt-1 text-xs text-slate-500">Submitted {formatDate(report.created_at)}</p></div><div className="flex flex-col items-end gap-2"><span className="rounded-full bg-slate-100 px-2 py-1 text-xs capitalize text-slate-600">{report.status}</span><Button size="sm" variant="outline" onClick={() => setSelectedReport(report)}>View</Button></div></div>)}</div></section>
        </div> : null}
      </div>
    </div>
  </Modal>;
}
