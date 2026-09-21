"use client";

import { useEffect, useState } from "react";
import { format } from "date-fns";
import { AnimatePresence, motion } from "framer-motion";
import { AlertTriangle, Calendar, Car, ExternalLink, EyeOff, FileText, Image as ImageIcon, Layers, Loader2, MapPin, RotateCcw, Ruler, Trash2, X } from "lucide-react";
import { Button } from "@/shared/ui/forms/Button";
import { MediaViewer } from "./MediaViewer";

export interface FloodZoneContributorDetails {
  report_id: number;
  reporter_name: string;
  reporter_trust_score: number;
  raw_text: string;
  created_at: string;
}

/** A feature-neutral view model for archived flood-zone details. */
export interface FloodZoneDetails {
  id: number;
  report_id: number;
  name?: string | null;
  created_at: string;
  severity: string;
  depth?: string | null;
  passable_vehicles?: string | null;
  hidden_hazards?: string | null;
  admin_notes?: string | null;
  merge_rationale?: string | null;
  media_urls?: string[];
  report_media_urls?: string[];
  contributors?: FloodZoneContributorDetails[];
}

interface FloodZoneDetailsModalProps {
  zone: FloodZoneDetails | null;
  isOpen: boolean;
  onClose: () => void;
  onRestore?: (zone: FloodZoneDetails) => void;
  onHardDelete?: (zone: FloodZoneDetails) => void;
  isRestoring?: boolean;
}

const severityBadge = (severity: string) => {
  const labels: Record<string, string> = { low: "Passable (Low)", medium: "Warning (Medium)", high: "Hazardous (High)", extreme: "Impassable (Extreme)" };
  const styles: Record<string, string> = { low: "border-lime-200 bg-lime-100 text-lime-800", medium: "border-amber-200 bg-amber-100 text-amber-800", high: "border-orange-200 bg-orange-100 text-orange-800", extreme: "border-red-200 bg-red-100 text-red-800 animate-pulse" };
  return <span className={`rounded-full border px-2.5 py-1 text-xs font-bold uppercase ${styles[severity.toLowerCase()] ?? "border-slate-200 bg-slate-100 text-slate-700"}`}>{labels[severity.toLowerCase()] ?? severity}</span>;
};

export function FloodZoneDetailsModal({ zone, isOpen, onClose, onRestore, onHardDelete, isRestoring = false }: FloodZoneDetailsModalProps) {
  const [mediaViewer, setMediaViewer] = useState<{ urls: string[]; initialIndex: number } | null>(null);
  useEffect(() => {
    if (!isOpen) return;
    const closeOnEscape = (event: KeyboardEvent) => { if (event.key === "Escape") onClose(); };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [isOpen, onClose]);

  const mediaItems = zone ? [...new Map([...zone.media_urls || [], ...zone.report_media_urls || []].filter(Boolean).map((url) => [url, url])).values()] : [];

  return <><AnimatePresence>{isOpen && zone && <motion.div aria-labelledby="flood-zone-details-title" aria-modal="true" className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-3 backdrop-blur-xs sm:p-4" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onMouseDown={onClose} role="dialog">
    <motion.div className="relative flex max-h-[calc(100dvh-1.5rem)] w-full max-w-2xl flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl sm:max-h-[90vh]" initial={{ opacity: 0, scale: 0.97, y: 12 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.97, y: 12 }} transition={{ duration: 0.18 }} onMouseDown={(event) => event.stopPropagation()}>
      <div className="flex items-start justify-between gap-3 border-b border-slate-100 bg-slate-50/80 px-4 py-4 sm:items-center sm:px-6"><div className="flex min-w-0 items-center gap-3"><div className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-blue-600 text-sm font-bold text-white shadow-sm">#{zone.id}</div><div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><h2 id="flood-zone-details-title" className="text-base font-bold text-slate-900">Flood Zone Details</h2><span className="rounded-full border border-slate-200 bg-slate-100 px-2.5 py-1 text-xs font-bold uppercase text-slate-600">Archived</span></div><p className="mt-0.5 flex items-center gap-1.5 text-xs text-slate-500"><Calendar className="size-3.5 text-slate-400" />Created {format(new Date(zone.created_at), "MMMM d, yyyy • h:mm a")}</p></div></div><button aria-label="Close flood zone details" className="rounded-xl p-2 text-slate-400 transition-colors hover:bg-slate-200/60 hover:text-slate-700" onClick={onClose} type="button"><X className="size-5" /></button></div>
      <div className="space-y-5 overflow-y-auto p-4 sm:p-6">
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200/80 bg-slate-50 p-3"><div className="flex items-center gap-2"><span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Severity:</span>{severityBadge(zone.severity)}</div><div className="flex items-center gap-2"><span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Source:</span><span className="rounded-md bg-slate-200/80 px-2.5 py-0.5 text-xs font-bold uppercase text-slate-700">Official zone</span></div></div>
        <div className="space-y-1.5"><div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-slate-400"><MapPin className="size-3.5 text-slate-500" />Spatial Record</div><div className="rounded-xl border border-blue-100 bg-blue-50/50 p-4 text-sm font-medium leading-relaxed text-slate-800">{zone.name || `Avoidance Zone #${zone.id}`}<span className="mt-1 block text-xs font-normal text-slate-600">Linked flood report #{zone.report_id}</span></div></div>
        <div className="grid grid-cols-1 gap-3.5 sm:grid-cols-2"><ZoneMetric icon={<Ruler className="size-4" />} iconClassName="bg-blue-100 text-blue-600" label="Estimated Depth" value={zone.depth?.replace(/_/g, " ") || "Not specified"} /><ZoneMetric icon={<EyeOff className="size-4" />} iconClassName="bg-amber-100 text-amber-600" label="Hidden Hazards" value={zone.hidden_hazards || "None reported"} /><div className="sm:col-span-2"><ZoneMetric icon={<Car className="size-4" />} iconClassName="bg-emerald-100 text-emerald-600" label="Passable Vehicles" value={zone.passable_vehicles?.replace(/_/g, " ") || "Not specified"} /></div></div>
        {zone.admin_notes && <DetailNote icon={<AlertTriangle className="size-3.5" />} label="Admin Notes" className="border-amber-200/80 bg-amber-50/60 text-amber-950">{zone.admin_notes}</DetailNote>}
        {zone.merge_rationale && <DetailNote icon={<Layers className="size-3.5" />} label="Merge Rationale" className="border-violet-200/80 bg-violet-50/60 text-violet-950">{zone.merge_rationale}</DetailNote>}
        {mediaItems.length > 0 && <div className="space-y-2"><div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-slate-400"><ImageIcon className="size-3.5 text-slate-500" />Attached Evidence ({mediaItems.length})</div><div className="grid grid-cols-1 gap-2 sm:grid-cols-2">{mediaItems.map((url, index) => <button key={url} className="group relative flex min-h-32 items-center justify-center overflow-hidden rounded-xl border border-slate-200 bg-slate-950/5" onClick={() => setMediaViewer({ urls: mediaItems, initialIndex: index })} type="button">{/\.(mp4|webm|mov|ogg)(?:\?|$)/i.test(url) || url.includes("/video/") ? <video className="h-full max-h-48 w-full object-cover transition-transform duration-300 group-hover:scale-105" preload="metadata" src={url} /> : <img alt={`Flood zone evidence ${index + 1}`} className="h-full max-h-48 w-full object-cover transition-transform duration-300 group-hover:scale-105" src={url} />}<span className="absolute inset-0 flex items-center justify-center gap-1.5 bg-black/40 text-xs font-semibold text-white opacity-0 backdrop-blur-xs transition-opacity group-hover:opacity-100"><ExternalLink className="size-4" />View</span></button>)}</div></div>}
        {zone.contributors && zone.contributors.length > 0 && <div className="space-y-2"><div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-slate-400"><FileText className="size-3.5 text-slate-500" />Associated Reports ({zone.contributors.length})</div><div className="space-y-2">{zone.contributors.map((contributor) => <div key={contributor.report_id} className="flex items-start justify-between gap-3 rounded-xl border border-slate-200/70 bg-slate-50/80 p-3"><div className="min-w-0"><p className="text-sm font-bold text-slate-900">Report #{contributor.report_id}</p><p className="mt-0.5 truncate text-xs text-slate-600">{contributor.raw_text || "No report text"}</p><p className="mt-1 text-xs text-slate-500">By {contributor.reporter_name} · Trust {contributor.reporter_trust_score}</p></div><span className="shrink-0 text-[10px] text-slate-400">{format(new Date(contributor.created_at), "MMM d, yyyy")}</span></div>)}</div></div>}
      </div>
      {(onHardDelete || onRestore) && <div className="flex flex-col gap-2 border-t border-slate-100 bg-slate-50/80 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">{onHardDelete && <Button className="w-full gap-1.5 border-red-200 text-red-600 hover:bg-red-50 sm:w-auto" onClick={() => onHardDelete(zone)} size="sm" variant="outline"><Trash2 className="size-3.5" />Delete Permanently</Button>}{onRestore && <Button className="w-full gap-1.5 bg-blue-600 text-white hover:bg-blue-700 sm:ml-auto sm:w-auto" disabled={isRestoring} onClick={() => onRestore(zone)} size="sm">{isRestoring ? <Loader2 className="size-3.5 animate-spin" /> : <RotateCcw className="size-3.5" />}Restore & Reactivate Zone</Button>}</div>}
    </motion.div>
  </motion.div>}</AnimatePresence><MediaViewer initialIndex={mediaViewer?.initialIndex} isOpen={mediaViewer !== null} mediaUrls={mediaViewer?.urls ?? []} onClose={() => setMediaViewer(null)} /></>;
}

function ZoneMetric({ icon, iconClassName, label, value }: { icon: React.ReactNode; iconClassName: string; label: string; value: string }) {
  return <div className="flex items-start gap-3 rounded-xl border border-slate-200/70 bg-slate-50/80 p-3.5"><div className={`flex size-8 shrink-0 items-center justify-center rounded-lg ${iconClassName}`}>{icon}</div><div><span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">{label}</span><p className="text-sm font-bold capitalize text-slate-900">{value}</p></div></div>;
}

function DetailNote({ icon, label, className, children }: { icon: React.ReactNode; label: string; className: string; children: React.ReactNode }) {
  return <div className={`space-y-1 rounded-xl border p-3.5 text-xs ${className}`}><span className="flex items-center gap-1.5 font-bold uppercase tracking-wider">{icon}{label}</span><p className="whitespace-pre-wrap">{children}</p></div>;
}
