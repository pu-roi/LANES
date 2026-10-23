"use client";

import { parseUtcDate } from "@/lib/utils";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { useQuery } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import { Calendar, X } from "lucide-react";
import { Button } from "@/shared/ui";
import { getFloodEventHistoryDetail } from "./floodHistoryApi";
import type { HistoricalMapFocusTarget } from "./floodHistoryApi";
import { FloodEventDetailsTabs } from "./FloodEventDetailsTabs";

const formatDate = (value: string | null | undefined) => value ? new Intl.DateTimeFormat("en-PH", { timeZone: "Asia/Manila", month: "short", day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit" }).format(parseUtcDate(value) || new Date(value)) : "Not recorded";
type DetailTab = "overview" | "official-history" | "reports";

export function FloodEventDetailModal({ eventId, datasetId, onClose, onFocusHistoricalMap }: { eventId: number | null; datasetId?: string; onClose: () => void; onFocusHistoricalMap: (target: HistoricalMapFocusTarget) => void }) {
  const [activeTab, setActiveTab] = useState<DetailTab>("overview");
  const { data, isLoading, isError, refetch } = useQuery({ queryKey: ["flood-event-history", "detail", eventId, datasetId], queryFn: () => getFloodEventHistoryDetail(eventId!, datasetId), enabled: eventId !== null, staleTime: 30_000, retry: false });
  const handleClose = () => { setActiveTab("overview"); onClose(); };
  const focusHistoricalMap = (target: HistoricalMapFocusTarget) => { handleClose(); onFocusHistoricalMap(target); };
  useEffect(() => {
    if (eventId === null) return;
    const closeOnEscape = (event: KeyboardEvent) => { if (event.key === "Escape" && !event.defaultPrevented) { setActiveTab("overview"); onClose(); } };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [eventId, onClose]);
  return typeof document !== "undefined" ? createPortal(<AnimatePresence>{eventId !== null && <motion.div aria-labelledby="flood-event-details-title" aria-modal="true" className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/60 p-3 backdrop-blur-xs sm:p-4" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onMouseDown={handleClose} role="dialog">
    <motion.div className="relative flex max-h-[calc(100dvh-1.5rem)] w-full max-w-4xl flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl sm:max-h-[90vh]" initial={{ opacity: 0, scale: 0.97, y: 12 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.97, y: 12 }} transition={{ duration: 0.18 }} onMouseDown={(event) => event.stopPropagation()}>
      <div className="flex items-start justify-between gap-3 border-b border-slate-100 bg-slate-50/80 px-4 py-4 sm:items-center sm:px-6"><div className="flex min-w-0 items-center gap-3"><div className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-blue-600 text-sm font-bold text-white shadow-sm">#{eventId}</div><div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><h2 id="flood-event-details-title" className="text-base font-bold text-slate-900">Flood Event Details</h2>{data && <span className={`rounded-full border px-2.5 py-1 text-xs font-bold uppercase ${data.status === "active" ? "border-emerald-200 bg-emerald-100 text-emerald-800" : "border-slate-200 bg-slate-100 text-slate-700"}`}>{data.status}</span>}</div><p className="mt-0.5 flex items-center gap-1.5 text-xs text-slate-500"><Calendar className="size-3.5 text-slate-400" />{data ? `${data.duration_basis ? "Record created" : "Verified"} ${formatDate(data.verified_at)}` : "Loading verified incident"}</p></div></div><button aria-label="Close flood event details" className="rounded-xl p-2 text-slate-400 transition-colors hover:bg-slate-200/60 hover:text-slate-700" onClick={handleClose} type="button"><X className="size-5" /></button></div>
      <div className={`min-h-0 flex-1 p-5 pb-[calc(1.25rem+env(safe-area-inset-bottom))] sm:p-6 ${activeTab === "reports" ? "overflow-y-auto lg:flex lg:flex-col lg:overflow-hidden" : "overflow-y-auto"}`}>
        {isLoading && <p className="py-12 text-center text-sm text-slate-500">Loading protected event evidence…</p>}
        {isError && <p role="alert" className="rounded-lg bg-red-50 p-4 text-sm text-red-800">Event details could not be loaded. <Button variant="outline" size="sm" onClick={() => void refetch()}>Retry event details</Button></p>}
        {data && <FloodEventDetailsTabs activeTab={activeTab} data={data} onChangeTab={setActiveTab} onFocusHistoricalMap={focusHistoricalMap} />}
      </div>
    </motion.div>
  </motion.div>}</AnimatePresence>, document.body) : null;
}
