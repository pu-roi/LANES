"use client";

import { parseUtcDate } from "@/lib/utils";

import { useEffect, useRef, useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { CalendarClock, Eye, Filter, Map as MapIcon, Search, TableProperties, Timer } from "lucide-react";
import { Button, Card, CardContent, DatePicker, Input, Pagination, Select, Tabs } from "@/shared/ui";
import { FloodEventDetailModal } from "./FloodEventDetailModal";
import dynamic from "next/dynamic";
import { getFloodEventHistoryPage, type FloodEventRecord, type FloodHistoryFilters, type HistoricalMapFocusTarget } from "./floodHistoryApi";
import { formatFloodDepth } from "@/lib/floodDepth";
import { useMediaQuery } from "@/hooks/useMediaQuery";

const initialFilters: FloodHistoryFilters = { status: "all", severity: "", dateFrom: "", dateTo: "", barangay: "", road: "", search: "" };
const HistoricalEventsMap = dynamic(() => import("./HistoricalEventsMap").then(module => module.HistoricalEventsMap), {
  ssr: false,
  loading: () => <div role="status" className="flex h-[22rem] items-center justify-center rounded-xl border border-slate-200 bg-slate-100 text-sm text-slate-500 lg:h-full lg:min-h-[38rem]">Loading historical map…</div>,
});
const formatDate = (value: string | null | undefined) => value ? new Intl.DateTimeFormat("en-PH", { timeZone: "Asia/Manila", month: "short", day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit" }).format(parseUtcDate(value) || new Date(value)) : "—";
const formatDuration = (minutes: number | null | undefined) => minutes === null || minutes === undefined ? "Ongoing" : minutes < 60 ? `${minutes} min` : `${Math.floor(minutes / 60)}h ${minutes % 60}m`;
const places = (event: FloodEventRecord) => event.locations.map((location) => location.display_name).join(" · ") || "Location not recorded";

export function FloodEventRecords({ active = true }: { active?: boolean }) {
  const [filters, setFilters] = useState(initialFilters);
  const [textFilters, setTextFilters] = useState({ search: "", road: "", barangay: "" });
  const [selectedEventId, setSelectedEventId] = useState<number | null>(null);
  const [detailEventId, setDetailEventId] = useState<number | null>(null);
  const [mapFocusTarget, setMapFocusTarget] = useState<HistoricalMapFocusTarget | null>(null);
  const [mobileView, setMobileView] = useState<"map" | "list">("list");
  const listScroll = useRef<HTMLDivElement>(null);
  const [listRequest, setListRequest] = useState<{ page: number; focusId: number | null }>({ page: 1, focusId: null });
  const desktop = useMediaQuery("(min-width: 1024px)");
  const [mapMounted, setMapMounted] = useState(false);
  useEffect(() => { if (!active || (!desktop && mobileView !== "map")) return;
    const frame = requestAnimationFrame(() => setMapMounted(true));
    return () => cancelAnimationFrame(frame);
  }, [active, desktop, mobileView]);
  const listQuery = useQuery({ queryKey: ["flood-event-history", "records", filters, listRequest],
    queryFn: ({ signal }) => getFloodEventHistoryPage(filters, listRequest.page, listRequest.focusId, signal),
    placeholderData: keepPreviousData, retry: false, staleTime: 30_000, enabled: active });
  const listPage = listQuery.data;
  const isListLoading = listQuery.isPending || listQuery.isPlaceholderData;
  const changePage = (page: number) => { setListRequest({ page, focusId: null }); if (listScroll.current) listScroll.current.scrollTop = 0; };
  const clearSelection = () => { changePage(1); setSelectedEventId(null); setMapFocusTarget(null); };
  const changeFilter = <K extends keyof FloodHistoryFilters>(key: K, value: FloodHistoryFilters[K]) => {
    if (key === "search" || key === "road" || key === "barangay") {
      setTextFilters(current => ({ ...current, [key]: value }));
      if (key !== "search" || !String(value).startsWith("@")) return;
    }
    setFilters((current) => ({ ...current, [key]: value })); clearSelection();
  };
  useEffect(() => {
    if (textFilters.search === filters.search && textFilters.road === filters.road && textFilters.barangay === filters.barangay) return;
    const timer = setTimeout(() => { setFilters(current => ({ ...current, ...textFilters }));
      setListRequest({ page: 1, focusId: null }); setSelectedEventId(null); setMapFocusTarget(null);
      if (listScroll.current) listScroll.current.scrollTop = 0;
    }, 300);
    return () => clearTimeout(timer);
  }, [textFilters, filters.search, filters.road, filters.barangay]);
  const selectEvent = (eventId: number, fromMap = false) => {
    setSelectedEventId(eventId); setMapFocusTarget(null); setMobileView("list");
    if (fromMap) { setListRequest({ page: 1, focusId: eventId }); if (listScroll.current) listScroll.current.scrollTop = 0; }
  };
  const focusHistoricalMap = (target: HistoricalMapFocusTarget) => {
    if (!target.cameraOnly) setSelectedEventId(target.eventId);
    setMapFocusTarget(target); setMobileView("map");
  };
  useEffect(() => {
    if (!listScroll.current || selectedEventId === null || isListLoading) return;
    const selected = listScroll.current.querySelector<HTMLElement>(`[data-event-id="${selectedEventId}"]`);
    if (!selected) return;
    const parent = listScroll.current.getBoundingClientRect(), item = selected.getBoundingClientRect();
    if (item.top < parent.top) listScroll.current.scrollTop += item.top - parent.top;
    else if (item.bottom > parent.bottom) listScroll.current.scrollTop += item.bottom - parent.bottom;
  }, [listPage, selectedEventId, isListLoading]);

  return <section className="space-y-4">
    <Card className="shadow-sm"><CardContent className="space-y-4 p-4"><div className="flex items-start justify-between gap-3"><div><h2 className="text-sm font-bold uppercase tracking-wider text-slate-900">Flood Event Records</h2><p className="mt-1 text-xs text-slate-500">Distinct verified incidents; supporting reports remain separate evidence.</p></div><Button variant="ghost" size="sm" onClick={() => { setFilters(initialFilters); setTextFilters({ search: "", road: "", barangay: "" }); clearSelection(); }}><Filter className="mr-1 h-4 w-4" />Clear filters</Button></div><div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7"><Input aria-label="Search events" containerClassName="xl:col-span-2" leftIcon={<Search className="h-4 w-4" />} value={textFilters.search.startsWith("@multiple") ? "" : textFilters.search} onChange={(event) => changeFilter("search", event.target.value)} placeholder="Search place" /><Select ariaLabel="Event status" options={[{ value: "all", label: "All statuses" }, { value: "active", label: "Active" }, { value: "ended", label: "Ended" }]} value={filters.status} onChange={(event) => changeFilter("status", event.target.value as FloodHistoryFilters["status"])} /><Select ariaLabel="Peak severity" options={[{ value: "", label: "All severity" }, { value: "low", label: "Low" }, { value: "medium", label: "Medium" }, { value: "high", label: "High" }, { value: "extreme", label: "Extreme" }]} value={filters.severity} onChange={(event) => changeFilter("severity", event.target.value as FloodHistoryFilters["severity"])} /><Input aria-label="Barangay" value={textFilters.barangay} onChange={(event) => changeFilter("barangay", event.target.value)} placeholder="Barangay" /><Input aria-label="Road or street" value={textFilters.road} onChange={(event) => changeFilter("road", event.target.value)} placeholder="Road / street" /><Select ariaLabel="Location recurrence" options={[{ value: "all", label: "All locations" }, { value: "multiple", label: "Multiple places" }]} value={filters.search.startsWith("@multiple") ? "multiple" : "all"} onChange={(event) => changeFilter("search", event.target.value === "multiple" ? "@multiple" : "")} /><DatePicker emptyDisplay="From date" ariaLabel="Event date from" value={filters.dateFrom} onChange={(event) => changeFilter("dateFrom", event.target.value)} /><DatePicker emptyDisplay="To date" ariaLabel="Event date to" value={filters.dateTo} onChange={(event) => changeFilter("dateTo", event.target.value)} align="right" /></div></CardContent></Card>
    <Tabs tabs={[{ id: "list", label: "List", icon: TableProperties }, { id: "map", label: "Map", icon: MapIcon }]} activeTab={mobileView} onChange={setMobileView} variant="pills" layoutId="flood-history-mobile-view" fullWidth className="lg:hidden" />
    <div data-testid="flood-event-records-layout" className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]"><div className={mobileView === "list" ? "hidden lg:block" : "block"}>{mapMounted && <HistoricalEventsMap filterKey={JSON.stringify(filters)} visible={active && (desktop || mobileView === "map")} filters={filters} focusTarget={mapFocusTarget} selectedEventId={selectedEventId} onSelectEvent={(id) => selectEvent(id, true)} />}</div><div role="region" aria-label="Flood event list" className={`min-w-0 ${mobileView === "map" ? "hidden lg:block" : "block"}`}><Card className="shadow-sm"><div ref={listScroll} className="max-h-[38rem] overflow-y-auto" aria-busy={listQuery.isFetching}>{listQuery.isError ? <div role="alert" className="space-y-2 p-4 text-sm text-red-800"><p>Flood Event cards could not be loaded. {listQuery.error.message}</p><Button size="sm" variant="outline" onClick={() => void listQuery.refetch()}>Retry records</Button></div> : listQuery.isPending ? <p className="p-10 text-center text-sm text-slate-500">Loading records…</p> : !listPage?.items.length ? <p className="p-10 text-center text-sm text-slate-500">No verified Flood Events match these filters.</p> : listPage.items.map((event) => <article key={event.id} data-event-id={event.id} className={`border-b border-slate-100 p-4 last:border-0 ${event.id === selectedEventId ? "bg-blue-50/70" : "hover:bg-slate-50"}`}><button onClick={() => selectEvent(event.id)} className="w-full text-left"><div className="flex items-start justify-between gap-3"><div><p className="font-semibold text-slate-900">Flood Event #{event.id}</p><p className="mt-1 text-sm text-slate-600">{places(event)}</p></div><span className={`rounded-full px-2 py-1 text-xs font-medium capitalize ${event.status === "ended" ? "bg-slate-100 text-slate-700" : "bg-emerald-50 text-emerald-700"}`}>{event.status}</span></div><div className="mt-3 grid grid-cols-2 gap-x-3 gap-y-2 text-xs text-slate-500"><span className="flex items-center gap-1"><CalendarClock className="h-3.5 w-3.5" />First report {formatDate(event.first_reported_at)}</span><span className="text-right">Verified {formatDate(event.verified_at)}</span><span className="flex items-center gap-1"><Timer className="h-3.5 w-3.5" />{event.status === "ended" ? `Ended ${formatDate(event.ended_at)}` : "Still active"}</span><span className="text-right">Duration {formatDuration(event.duration_minutes)}</span><span>Peak {event.peak_severity}{event.peak_depth ? ` · ${formatFloodDepth(event.peak_depth, { compact: true })}` : ""}</span><span className="text-right">{event.supporting_report_count ?? 0} supporting reports</span><span>{event.zone_count ?? event.zones?.length ?? 0} source zones</span><span className="text-right">{event.reporter_count ?? 0} reporting users</span></div></button><Button size="sm" variant="ghost" className="mt-3" onClick={() => setDetailEventId(event.id)}><Eye className="mr-1 h-4 w-4" />View event</Button></article>)}</div></Card>{listPage && !listQuery.isError && <div role="region" aria-label="Flood event pagination" className="mt-3 min-w-0 [&>div:last-child>div:last-child]:flex-wrap [&>div:last-child>div:last-child]:gap-2"><p role="status" className="px-1 text-xs text-slate-500">{listPage.total} {listPage.total === 1 ? "event" : "events"} · Up to 20 per page · Page {listPage.page} of {listPage.pages}{listQuery.isFetching ? " · Updating…" : ""}</p><Pagination page={listPage.page} totalPages={listPage.pages} onPageChange={changePage} disabled={listQuery.isFetching} /></div>}</div></div>
    <FloodEventDetailModal eventId={detailEventId} onClose={() => setDetailEventId(null)} onFocusHistoricalMap={focusHistoricalMap} />
  </section>;
}
