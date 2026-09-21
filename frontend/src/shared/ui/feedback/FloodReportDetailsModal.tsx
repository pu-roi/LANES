"use client";

import { useEffect, useState } from "react";
import { format } from "date-fns";
import { AnimatePresence, motion } from "framer-motion";
import {
  Calendar,
  Car,
  CheckCircle,
  ExternalLink,
  EyeOff,
  FileText,
  Loader2,
  Map as MapIcon,
  MapPin,
  Ruler,
  Shield,
  ShieldCheck,
  User,
  X,
  XCircle,
} from "lucide-react";
import { Button } from "@/shared/ui/forms/Button";
import { MediaViewer } from "./MediaViewer";

export interface FloodReportDetailsGeometry {
  type: string;
  coordinates: unknown;
}

/** A feature-neutral view model so all admin surfaces can share this presentation. */
export interface FloodReportDetails {
  id: number;
  source: string;
  raw_text: string;
  severity: string;
  status: string;
  created_at: string;
  depth?: string | null;
  geometry?: FloodReportDetailsGeometry | null;
  media_urls?: string[];
  zone_id?: number | null;
  barangay?: string | null;
  city?: string | null;
  human_readable_location?: string | null;
  is_bidirectional?: boolean;
  survey?: { passable_vehicles?: string | null; hidden_hazards?: string | null } | null;
  reporter_name?: string | null;
  reporter_username?: string | null;
  reporter_role?: string | null;
  reporter_trust_score?: number | null;
}

interface FloodReportDetailsModalProps {
  report: FloodReportDetails | null;
  isOpen: boolean;
  /** Render inside a parent record instead of as an independent modal. */
  presentation?: "dialog" | "panel";
  onClose: () => void;
  onViewOnMap?: (report: FloodReportDetails) => void;
  onApprove?: (reportId: number) => void;
  onReject?: (reportId: number) => void;
  isApproveLoading?: boolean;
  isRejectLoading?: boolean;
}

const severityBadge = (severity: string) => {
  const labels: Record<string, string> = { low: "Passable (Low)", medium: "Warning (Medium)", high: "Hazardous (High)", extreme: "Impassable (Extreme)" };
  const styles: Record<string, string> = { low: "border-lime-200 bg-lime-100 text-lime-800", medium: "border-yellow-200 bg-yellow-100 text-yellow-800", high: "border-orange-200 bg-orange-100 text-orange-800", extreme: "border-red-200 bg-red-100 text-red-800 animate-pulse" };
  return <span className={`rounded-full border px-2.5 py-1 text-xs font-bold uppercase ${styles[severity] ?? "bg-slate-100 text-slate-800"}`}>{labels[severity] ?? "Unknown"}</span>;
};

const statusBadge = (status: string) => {
  const styles: Record<string, string> = { pending: "border-blue-200 bg-blue-100 text-blue-800", approved: "border-emerald-200 bg-emerald-100 text-emerald-800", rejected: "border-rose-200 bg-rose-100 text-rose-800" };
  return styles[status] ? <span className={`rounded-full border px-2.5 py-1 text-xs font-bold uppercase ${styles[status]}`}>{status}</span> : null;
};

const formatCoordinates = (geometry?: FloodReportDetailsGeometry | null) => {
  if (!geometry?.coordinates) return "No coordinates mapped";
  const findCoordinate = (value: unknown): [number, number] | null => {
    if (!Array.isArray(value)) return null;
    if (typeof value[0] === "number" && typeof value[1] === "number") return [value[0], value[1]];
    return findCoordinate(value[Math.floor(value.length / 2)]);
  };
  const coordinate = findCoordinate(geometry.coordinates);
  if (!coordinate) return geometry.type === "Polygon" ? "Polygon Zone" : "Mapped Coordinates";
  const [lng, lat] = coordinate;
  if (geometry.type === "Point") return `${lat.toFixed(5)}° N, ${lng.toFixed(5)}° E (Point)`;
  const label: Record<string, string> = { LineString: "Road Line", Polygon: "Polygon", MultiLineString: "Road Segments", MultiPolygon: "Polygon Areas" };
  const count = Array.isArray(geometry.coordinates) ? geometry.coordinates.length : 0;
  return `~${lat.toFixed(5)}° N, ${lng.toFixed(5)}° E (${count} ${label[geometry.type] ?? geometry.type})`;
};

export function FloodReportDetailsModal({ report, isOpen, presentation = "dialog", onClose, onViewOnMap, onApprove, onReject, isApproveLoading = false, isRejectLoading = false }: FloodReportDetailsModalProps) {
  const [mediaViewer, setMediaViewer] = useState<{ urls: string[]; initialIndex: number } | null>(null);
  useEffect(() => {
    if (!isOpen) return;
    const closeOnEscape = (event: KeyboardEvent) => { if (event.key === "Escape") onClose(); };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [isOpen, onClose]);

  const isOfficialReporter = Boolean(report?.reporter_role && /Admin|DRRM|Moderator|Officer/i.test(report.reporter_role));
  const canModerate = report?.status === "pending" && onApprove && onReject;
  const handleMapView = () => { if (report && onViewOnMap) { onClose(); onViewOnMap(report); } };
  const isPanel = presentation === "panel";

  return <><AnimatePresence>{isOpen && report && <motion.div aria-labelledby="flood-report-details-title" aria-modal={isPanel ? undefined : "true"} className={isPanel ? "h-full min-h-0 w-full" : "fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-3 backdrop-blur-xs sm:p-4"} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onMouseDown={isPanel ? undefined : onClose} role={isPanel ? "region" : "dialog"}>
    <motion.div className={isPanel ? "relative flex h-full min-h-0 w-full flex-col overflow-hidden border-l border-slate-200 bg-white" : "relative flex max-h-[calc(100dvh-1.5rem)] w-full max-w-2xl flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl sm:max-h-[90vh]"} initial={isPanel ? { opacity: 0, x: 24 } : { opacity: 0, scale: 0.97, y: 12 }} animate={isPanel ? { opacity: 1, x: 0 } : { opacity: 1, scale: 1, y: 0 }} exit={isPanel ? { opacity: 0, x: 24 } : { opacity: 0, scale: 0.97, y: 12 }} transition={{ duration: 0.18 }} onMouseDown={(event) => event.stopPropagation()}>
      <div className="flex items-start justify-between gap-3 border-b border-slate-100 bg-slate-50/80 px-4 py-4 sm:items-center sm:px-6"><div className="flex min-w-0 items-center gap-3"><div className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-blue-600 text-sm font-bold text-white shadow-sm">#{report.id}</div><div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><h2 id="flood-report-details-title" className="text-base font-bold text-slate-900">Flood Report Details</h2>{statusBadge(report.status)}</div><p className="mt-0.5 flex items-center gap-1.5 text-xs text-slate-500"><Calendar className="size-3.5 text-slate-400" />{format(new Date(report.created_at), "MMMM d, yyyy • h:mm a")}</p></div></div><button aria-label="Close flood report details" className="rounded-xl p-2 text-slate-400 transition-colors hover:bg-slate-200/60 hover:text-slate-700" onClick={onClose} type="button"><X className="size-5" /></button></div>
      <div className="space-y-5 overflow-y-auto p-4 sm:p-6">
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200/80 bg-slate-50 p-3"><div className="flex items-center gap-2"><span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Severity:</span>{severityBadge(report.severity)}</div><div className="flex items-center gap-2"><span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Source:</span><span className="rounded-md bg-slate-200/80 px-2.5 py-0.5 text-xs font-bold uppercase text-slate-700">{report.source}</span></div></div>
        <div className="space-y-1.5"><div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-slate-400"><FileText className="size-3.5 text-slate-500" />Verbatim Submission</div><div className="rounded-xl border border-blue-100 bg-blue-50/50 p-4 text-sm font-medium italic leading-relaxed text-slate-800">&ldquo;{report.raw_text}&rdquo;</div></div>
        <div className="grid grid-cols-1 gap-3.5 sm:grid-cols-2"><ReportMetric icon={<Ruler className="size-4" />} iconClassName="bg-blue-100 text-blue-600" label="Water Level" value={report.depth?.replace(/_/g, " ") || "Not specified"} /><ReportMetric capitalize icon={<EyeOff className="size-4" />} iconClassName="bg-amber-100 text-amber-600" label="Submerged Hazards" value={report.survey?.hidden_hazards || "Unsure / None reported"} /><ReportMetric icon={<MapIcon className="size-4" />} iconClassName="bg-violet-100 text-violet-600" label="Road Coverage" value={report.is_bidirectional ? "Both directions" : "One direction"} /><ReportMetric icon={<Car className="size-4" />} iconClassName="bg-emerald-100 text-emerald-600" label="Passable Vehicles" value={report.survey?.passable_vehicles?.replace(/_/g, " ") || "Not specified"} /></div>
        <div className="space-y-2.5 rounded-xl border border-slate-200/70 bg-slate-50/80 p-4"><div className="flex flex-wrap items-center justify-between gap-2"><div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-slate-400"><MapPin className="size-3.5 text-slate-500" />Spatial Location</div>{report.zone_id && <span className="rounded bg-blue-100 px-2 py-0.5 text-[10px] font-bold text-blue-700">Linked to Zone #{report.zone_id}</span>}</div><div className="space-y-1"><div className="text-sm font-bold text-slate-900">{report.barangay ? `Brgy. ${report.barangay}, ${report.city || "Pasig City"}` : report.city ? `${report.city}, Metro Manila` : "Pasig City, Metro Manila"}</div>{report.human_readable_location && <div className="text-xs font-medium text-slate-600">Road / Landmark: {report.human_readable_location}</div>}<div className="flex flex-col justify-between gap-2 pt-1 sm:flex-row sm:items-center sm:gap-3"><div className="max-w-full truncate rounded-lg border border-slate-200 bg-white p-2 font-mono text-xs text-slate-500">{formatCoordinates(report.geometry)}</div>{onViewOnMap && <button className="flex shrink-0 items-center justify-center gap-1.5 rounded-lg border border-blue-100 bg-blue-50 px-2.5 py-1.5 text-xs font-semibold text-blue-600 transition-colors hover:bg-blue-100 hover:text-blue-800" onClick={handleMapView} type="button"><MapIcon className="size-3.5" />View on Map</button>}</div></div></div>
        <div className="flex items-center justify-between gap-3 rounded-xl border border-slate-200/70 bg-slate-50/80 p-4"><div className="flex min-w-0 items-center gap-3"><div className={`flex size-10 shrink-0 items-center justify-center rounded-full ${isOfficialReporter ? "bg-blue-600 text-white" : "bg-slate-200 text-slate-700"}`}>{isOfficialReporter ? <ShieldCheck className="size-5" /> : <User className="size-5" />}</div><div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><span className="truncate text-sm font-bold text-slate-900">{report.reporter_name || "System Ingestion"}</span>{report.reporter_role && <span className="rounded-full border border-blue-200 bg-blue-100 px-2 py-0.5 text-[10px] font-bold uppercase text-blue-700">{report.reporter_role}</span>}</div><span className="text-xs text-slate-500">{report.reporter_username ? `@${report.reporter_username}` : "Verified Citizen Contributor"}</span></div></div>{report.reporter_trust_score != null && <div className="flex shrink-0 flex-col items-end"><span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Trust Score</span><span className="flex items-center gap-1 text-sm font-extrabold text-blue-600"><Shield className="size-3.5 text-blue-500" />{report.reporter_trust_score}%</span></div>}</div>
        {report.media_urls && report.media_urls.length > 0 && <div className="space-y-2"><div className="text-xs font-bold uppercase tracking-wider text-slate-400">Attached Flood Evidence ({report.media_urls.length})</div><div className="grid grid-cols-1 gap-2 sm:grid-cols-2">{report.media_urls.map((url, index) => <button key={url} className="group relative flex max-h-48 min-h-32 items-center justify-center overflow-hidden rounded-xl border border-slate-200 bg-slate-950/5 text-left" onClick={() => setMediaViewer({ urls: report.media_urls!, initialIndex: index })} type="button">{url.match(/\.(mp4|webm|mov|ogg)$/i) || url.includes("/video/upload/") ? <video className="h-full max-h-48 w-full object-cover transition-transform duration-300 group-hover:scale-105" src={url} /> : <img alt={`Flood evidence ${index + 1}`} className="h-full max-h-48 w-full object-cover transition-transform duration-300 group-hover:scale-105" src={url} />}<span className="absolute inset-0 flex items-center justify-center gap-1.5 bg-black/40 text-xs font-semibold text-white opacity-0 backdrop-blur-xs transition-opacity group-hover:opacity-100"><ExternalLink className="size-4" />View</span></button>)}</div></div>}
      </div>
      {(onViewOnMap || canModerate) && <div className="flex flex-col items-center justify-between gap-3 border-t border-slate-100 bg-slate-50/80 px-4 py-4 sm:flex-row sm:px-6">{onViewOnMap && <Button className="flex w-full items-center justify-center gap-2 border-blue-200 text-sm font-semibold text-blue-600 hover:bg-blue-50 sm:w-auto" onClick={handleMapView} variant="outline"><MapIcon className="size-4 text-blue-600" />View on Map (Focus)</Button>}{canModerate && <div className="flex w-full items-center gap-2 sm:ml-auto sm:w-auto"><Button className="flex-1 gap-1.5 border-rose-200 text-sm font-semibold text-rose-600 hover:bg-rose-50 sm:flex-none" disabled={isRejectLoading} onClick={() => onReject(report.id)} variant="outline">{isRejectLoading ? <Loader2 className="size-4 animate-spin" /> : <XCircle className="size-4" />}Reject</Button><Button className="flex-1 gap-1.5 bg-emerald-600 text-sm font-semibold text-white hover:bg-emerald-700 sm:flex-none" disabled={isApproveLoading} onClick={() => onApprove(report.id)}>{isApproveLoading ? <Loader2 className="size-4 animate-spin" /> : <CheckCircle className="size-4" />}Approve</Button></div>}</div>}
    </motion.div>
  </motion.div>}</AnimatePresence><MediaViewer initialIndex={mediaViewer?.initialIndex} isOpen={mediaViewer !== null} mediaUrls={mediaViewer?.urls ?? []} onClose={() => setMediaViewer(null)} /></>;
}

function ReportMetric({ icon, iconClassName, label, value, capitalize = false }: { icon: React.ReactNode; iconClassName: string; label: string; value: string; capitalize?: boolean }) {
  return <div className="flex items-start gap-3 rounded-xl border border-slate-200/70 bg-slate-50/80 p-3.5"><div className={`flex size-8 shrink-0 items-center justify-center rounded-lg ${iconClassName}`}>{icon}</div><div className="flex flex-col"><span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">{label}</span><span className={`text-sm font-bold text-slate-900 ${capitalize ? "capitalize" : ""}`}>{value}</span></div></div>;
}
