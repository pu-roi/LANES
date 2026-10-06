"use client";

import { useEffect, useId, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useQueryClient } from "@tanstack/react-query";
import { ExternalLink, Newspaper, RefreshCw, X } from "lucide-react";
import { Button } from "@/shared/ui";
import { newsDate, publisherLink } from "./newsPresentation";
import { usePublicNewsAlerts } from "./usePublicNewsAlerts";

export function NewsAlertsPanel({ isMobile, open, onOpen, onClose: close }: { isMobile: boolean; open: boolean; onOpen: () => void; onClose: () => void }) {
  const [page, setPage] = useState(1);
  const queryClient = useQueryClient();
  const changePage = (next: number) => {
    void queryClient.invalidateQueries({ queryKey: ["publicNewsAlerts", next], refetchType: "none" });
    setPage(next);
  };
  const alerts = usePublicNewsAlerts(page, open);
  const titleId = useId();
  const dialog = useRef<HTMLDivElement>(null);
  const closeControl = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    if (!open) return;
    const opener = document.activeElement as HTMLElement | null;
    const originalOverflow = document.body.style.overflow;
    if (isMobile) document.body.style.overflow = "hidden";
    closeControl.current?.querySelector("button")?.focus({ preventScroll: true });
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") { event.preventDefault(); close(); }
      if (!isMobile || event.key !== "Tab") return;
      const controls = Array.from(dialog.current?.querySelectorAll<HTMLElement>('button:not([disabled]), a[href], [tabindex="0"]') ?? []).filter((node) => node.getClientRects().length > 0);
      const first = controls[0], last = controls[controls.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
    };
    document.addEventListener("keydown", onKey);
    return () => {
      if (isMobile) document.body.style.overflow = originalOverflow;
      document.removeEventListener("keydown", onKey);
      requestAnimationFrame(() => {
        if (document.getElementById(titleId)) return;
        if (opener?.isConnected) opener.focus({ preventScroll: true });
        else document.querySelector<HTMLButtonElement>(isMobile ? 'button[title="Report Flood Hazard"]' : 'button[data-news-alert-entry]')?.focus({ preventScroll: true });
      });
    };
  }, [open, isMobile, close, titleId]);

  const panel = <div ref={dialog} role={isMobile ? "dialog" : "region"} aria-modal={isMobile ? true : undefined} aria-labelledby={titleId} className={isMobile
    ? "pointer-events-auto fixed inset-x-0 bottom-[calc(var(--bottom-nav-height)+env(safe-area-inset-bottom))] z-[60] flex max-h-[calc(100dvh-var(--bottom-nav-height)-env(safe-area-inset-bottom)-1rem)] flex-col rounded-t-2xl bg-white shadow-2xl"
    : "pointer-events-auto absolute right-4 top-4 z-[45] flex max-h-[calc(100dvh-7rem)] w-[min(24rem,calc(100vw-380px))] flex-col rounded-xl border border-slate-200 bg-white shadow-xl"}>
    <header className="flex shrink-0 items-center justify-between gap-3 px-4 py-3">
      <h2 id={titleId} className="flex items-center gap-2 font-semibold text-slate-900"><Newspaper className="size-4" aria-hidden="true" />News alerts</h2>
      <span ref={closeControl}><Button variant="ghost" size="sm" className="min-h-11 min-w-11 px-2" aria-label="Close news alerts" onClick={close}><X className="size-5" aria-hidden="true" /></Button></span>
    </header>
    <div className="min-h-0 overflow-y-auto px-4 pb-4">
      <p className="text-xs leading-relaxed text-slate-600">News reports describe reported conditions. Accepted flood zones appear on the map and affect routing. Estimated road corridors use reported locations and flood susceptibility data.</p>
      <div className="my-3 flex items-center justify-between gap-2">
        <p className="text-xs text-slate-500">{alerts.data ? `Server snapshot: ${newsDate(alerts.data.as_of)}` : "Checking news reports"}</p>
        <Button variant="ghost" size="sm" aria-label="Refresh news alerts" disabled={alerts.isFetching || alerts.offline} onClick={() => void alerts.refetch()} className="min-h-11 min-w-11 px-2"><RefreshCw className={`size-4 ${alerts.isFetching ? "animate-spin motion-reduce:animate-none" : ""}`} aria-hidden="true" /></Button>
      </div>
      {alerts.offline && <p role="status" className="mb-3 text-sm text-amber-800">Offline. Current status unavailable. Cached reports are last downloaded information.</p>}
      {alerts.isError && <div role="alert" className="mb-3 text-sm text-red-700"><p>Could not refresh news alerts. Current status unavailable.</p><p className="mt-1 break-words text-xs">{alerts.error instanceof Error ? alerts.error.message : "Please try again."}</p><Button variant="outline" size="sm" onClick={() => void alerts.refetch()} disabled={alerts.offline || alerts.isFetching} className="mt-2 min-h-11">Retry news alerts</Button></div>}
      {alerts.isPending && !alerts.offline && !alerts.isError && <p role="status" className="py-6 text-sm text-slate-600">Loading news alerts…</p>}
      {alerts.data && alerts.currentStatusUnavailable && !alerts.offline && !alerts.isError && <p role="status" className="mb-3 text-sm text-amber-800">Refreshing server status. Last downloaded information is shown below; current status unavailable.</p>}
      {alerts.data?.items.length === 0 && <p className="py-6 text-sm text-slate-600">{alerts.data.total === 0 ? "No published news alerts in this snapshot." : "No news alerts on this page. Return to the previous page for the latest reports."}</p>}
      <ul className="divide-y divide-slate-100">
        {alerts.data?.items.map((alert) => {
          const sourceLink = publisherLink(alert.source_url);
          const unavailable = alerts.currentStatusUnavailable;
          return <li key={`${alert.case_id}:${alert.revision}`} className="py-4">
            <div className="flex flex-wrap items-center justify-between gap-2"><h3 className="break-words text-sm font-semibold text-slate-900">{alert.location_label}</h3><span className={`text-xs font-semibold ${unavailable ? "text-slate-500" : alert.status === "Active" ? "text-orange-700" : alert.status === "Cleared" ? "text-emerald-700" : "text-amber-700"}`}>{unavailable ? `Last downloaded: ${alert.status}` : `News status: ${alert.status}`}</span></div>
            {alert.current_status_unknown && <p className="mt-1 text-xs text-amber-800">Current flooding is unconfirmed.</p>}
            {alert.location_qualifier && <p className="mt-1 text-xs text-slate-600">{alert.location_qualifier}</p>}
            <p className="mt-1 text-xs text-slate-600">{alert.affects_routing && !unavailable && alert.status === "Active" ? (alert.geometry_basis === "estimated_road_corridor" ? "Active zone · Estimated road corridor" : "Active zone · Verified flood footprint") : "No current routing zone confirmed"}</p>
            <dl className="mt-3 grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-xs [&_dd]:min-w-0 [&_dd]:break-words"><dt className="text-slate-500">Reported depth</dt><dd>{alert.depth_label || "Not stated"}</dd><dt className="text-slate-500">Conditions</dt><dd>{alert.condition_label || "Not stated"}</dd><dt className="text-slate-500">Passability</dt><dd>{alert.passability_label || "Not established"}</dd><dt className="text-slate-500">Observed</dt><dd>{newsDate(alert.observed_at, "Not established")}</dd><dt className="text-slate-500">Evidence expiry</dt><dd>{newsDate(alert.expires_at, "Not established")}</dd></dl>
            {alert.evidence_excerpt && <p className="mt-3 break-words text-xs italic text-slate-600">“{alert.evidence_excerpt}”</p>}
            {alert.correction_note && <p className="mt-3 break-words text-xs text-slate-700"><strong>Correction: </strong>{alert.correction_note}</p>}
            {alert.cleared_at && <p className="mt-2 text-xs text-slate-600">Clearance observation: {newsDate(alert.cleared_at)}</p>}
            <p className="mt-3 break-words text-xs text-slate-600">Source: {alert.source_publisher || "News report"}{sourceLink ? <a href={sourceLink} target="_blank" rel="noopener noreferrer" className="mt-1 flex items-start gap-1 text-blue-700 underline underline-offset-2">{alert.source_title}<ExternalLink className="mt-0.5 size-3 shrink-0" aria-hidden="true" /><span className="sr-only"> (opens in a new tab)</span></a> : <span className="mt-1 block">{alert.source_title}</span>}</p>
            <p className="mt-1 text-xs text-slate-500">Published {newsDate(alert.source_published_at, "date not stated")} · Updated {newsDate(alert.updated_at)}</p>
          </li>;
        })}
      </ul>
      {alerts.data && (alerts.data.pages > 1 || page > 1) && <nav aria-label="News alert pages" className="flex items-center justify-between gap-2 pt-3"><Button variant="outline" size="sm" className="min-h-11" disabled={page <= 1 || alerts.isFetching} onClick={() => changePage(page - 1)}>Previous</Button><span className="text-xs text-slate-600">Page {alerts.data.page} · {alerts.data.total} alerts</span><Button variant="outline" size="sm" className="min-h-11" disabled={page >= alerts.data.pages || alerts.isFetching} onClick={() => changePage(page + 1)}>Next</Button></nav>}
    </div>
  </div>;

  return <>
    {!open && !isMobile && <div className="pointer-events-auto absolute right-4 top-4 z-[45]"><Button data-news-alert-entry variant="secondary" className="min-h-11 gap-2 bg-white shadow-md" aria-expanded={false} onClick={onOpen}><Newspaper className="size-4" aria-hidden="true" />News alerts</Button></div>}
    {open && (isMobile ? createPortal(<><div className="fixed inset-0 z-[59] bg-slate-950/40" onClick={close} aria-hidden="true" />{panel}</>, document.body) : panel)}
  </>;
}
