import { useCallback, useEffect, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { usePathname } from "next/navigation";
import { ArrowLeft, RefreshCw, Shield } from "lucide-react";
import { Pagination } from "@/shared/ui";
import { SpatialPanelButton as Button, floodRecordTime } from "./FloodRecordSummary";
import { SpatialGroupCard } from "./SpatialGroupCard";
import { SpatialQueueFilters } from "./SpatialQueueFilters";
import { ActiveZoneRecords, type ActiveZoneRecordsProps } from "./ActiveZoneRecords";
import { getZoneMembers, getZoneQueue, type ZoneQueueItem, type ZoneSource } from "../zoneQueueApi";
import type { AvoidanceZone } from "../adminApi";

const sourceLabels: Record<string, string> = { all: "All", user_reports: "User Reports", news: "News", official: "Official", other: "Other" };

export function ActiveZonesPanel({ activeOnly, setActiveOnly, page, setPage, onRecords, onCount, onRequestBulkDeactivate, onViewGroupOnMap, onOverview, visible = true, ...records }: Omit<ActiveZoneRecordsProps,
  "zones" | "listLoading" | "isPlaceholderData" | "totalPages" | "page" | "setPage"> & {
  activeOnly: boolean; setActiveOnly: (value: boolean) => void; page: number; setPage: (value: number) => void;
  onRecords: (zones: AvoidanceZone[]) => void;
  onCount?: (count: number) => void;
  onRequestBulkDeactivate: () => void;
  onViewGroupOnMap: (group: ZoneQueueItem) => void;
  onOverview?: () => void;
  visible?: boolean;
}) {
  const active = usePathname() === "/admin/map" && visible;
  const queryClient = useQueryClient();
  const [source, setSource] = useState<ZoneSource>("all");
  const [search, setSearch] = useState("");
  const [q, setQ] = useState("");
  const [city, setCity] = useState("");
  const [barangay, setBarangay] = useState("");
  const [severity, setSeverity] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const [groupId, setGroupId] = useState<number | null>(() => activeOnly ? records.selectedZoneId : null);
  const [memberPage, setMemberPage] = useState<number | null>(() => records.selectedZoneId === null ? 1 : null);
  const opener = useRef<HTMLButtonElement | null>(null);
  const queueScroll = useRef<HTMLDivElement | null>(null);
  const queueScrollTop = useRef(0);
  const handledMapId = useRef<number | null>(records.selectedZoneId);
  const filters = { source, q, city, barangay, severity };
  useEffect(() => {
    if (search === q) return;
    const timer = setTimeout(() => { setQ(search); setPage(1); }, 300);
    return () => clearTimeout(timer);
  }, [search, q, setPage]);
  const queue = useQuery({ queryKey: ["adminZones", "queue", activeOnly, page, filters],
    queryFn: ({ signal }) => getZoneQueue(activeOnly, page, filters, signal), enabled: active && groupId === null,
    retry: false, staleTime: 15_000, refetchInterval: active && groupId === null ? 15_000 : false });
  const members = useQuery({ queryKey: ["adminZones", "members", groupId, memberPage],
    queryFn: ({ signal }) => getZoneMembers(groupId!, memberPage, signal), enabled: active && activeOnly && groupId !== null,
    retry: false, staleTime: 15_000, refetchInterval: active && activeOnly && groupId !== null ? 15_000 : false });
  const visibleZones = activeOnly ? (groupId !== null && !members.isError ? members.data?.zones : undefined) : !queue.isError ? queue.data?.zones : undefined;
  useEffect(() => { if (activeOnly && queue.data && !queue.isError) onCount?.(queue.data.counts.all); }, [activeOnly, queue.data, queue.isError, onCount]);
  useEffect(() => { if (members.data?.zone_total !== undefined && !members.isError) onCount?.(members.data.zone_total); }, [members.data, members.isError, onCount]);
  useEffect(() => { onRecords(visibleZones ?? []); }, [visibleZones, onRecords]);
  // Resolve map picks and report handoffs from any member ID, independent of pagination.
  useEffect(() => {
    if (records.selectedZoneId === null) { handledMapId.current = null; return; }
    if (!activeOnly || records.selectedZoneId === null || records.selectedZoneId === handledMapId.current) return;
    const zoneId = records.selectedZoneId;
    if (groupId !== null && members.data?.zones.some(zone => zone.id === zoneId)) {
      handledMapId.current = zoneId;
      return;
    }
    const frame = requestAnimationFrame(() => {
      handledMapId.current = zoneId;
      setGroupId(zoneId);
      setMemberPage(null);
    });
    return () => cancelAnimationFrame(frame);
  }, [activeOnly, records.selectedZoneId, groupId, members.data]);
  const refresh = useCallback(() => { void queryClient.invalidateQueries({ queryKey: ["adminZones"] }); }, [queryClient]);
  const clearFilters = () => { setSearch(""); setQ(""); setCity(""); setBarangay(""); setSeverity(""); setPage(1); };
  const changeMode = (value: boolean) => { setActiveOnly(value); setPage(1); setGroupId(null); if (value) onOverview?.(); };
  const inspecting = activeOnly && groupId !== null;
  return <section aria-label="Active Zones" className="flex min-h-0 flex-1 flex-col overflow-hidden">
    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 p-3">
      <div className="flex flex-wrap gap-1"><Button variant={activeOnly ? "primary" : "ghost"} aria-pressed={activeOnly} onClick={() => changeMode(true)}>Active Only</Button><Button variant={!activeOnly ? "primary" : "ghost"} aria-pressed={!activeOnly} onClick={() => changeMode(false)}>All History</Button></div>
      <div className="flex gap-1">{records.onCreateOfficialZone && <Button variant="outline" className="gap-1 md:hidden" onClick={records.onCreateOfficialZone}><Shield className="size-3.5" />Create</Button>}<Button variant="ghost" aria-label="Refresh zones" disabled={queue.isFetching || (inspecting && members.isFetching)} onClick={refresh}><RefreshCw className="size-4" /></Button></div>
    </div>
    {records.selectedIds.length > 0 && <div className="flex flex-wrap items-center gap-2 border-b border-slate-100 px-3 py-2 text-xs">
      <span>{records.selectedIds.length} selected zones</span><Button variant="danger" onClick={onRequestBulkDeactivate}>Deactivate Selected</Button><Button variant="ghost" onClick={() => records.setSelectedIds([])}>Clear selection</Button>
    </div>}
    <div className={`${inspecting ? "hidden" : "flex"} min-h-0 flex-1 flex-col`}>
      <div role="group" aria-label="Zone source" className="flex flex-wrap gap-1 border-b border-slate-100 p-3">{(Object.keys(sourceLabels) as ZoneSource[]).map(value => <Button key={value} variant={source === value ? "primary" : "ghost"} aria-pressed={source === value} className="px-2 text-xs" onClick={() => { setSource(value); setPage(1); }}>{sourceLabels[value]}{queue.data && !queue.isError && <span className="ml-1">{queue.data.counts[value]}</span>}</Button>)}</div>
      <div ref={queueScroll} className={`${activeOnly ? "overflow-y-auto" : "overflow-hidden"} flex min-h-0 flex-1 flex-col pb-[calc(var(--bottom-nav-height)+env(safe-area-inset-bottom))] md:pb-0`}>
        <SpatialQueueFilters id="zone-filters" searchLabel={activeOnly ? "Search active zones" : "Search zone history"} search={search} onSearch={setSearch}
          city={city} onCity={value => { setCity(value); setBarangay(""); setPage(1); }}
          barangay={barangay} onBarangay={value => { setBarangay(value); setPage(1); }}
          severity={severity} onSeverity={value => { setSeverity(value); setPage(1); }}
          expanded={showFilters} onExpanded={setShowFilters} facets={queue.data?.facets} onClear={clearFilters} />
        {queue.isPending && <p role="status" className="p-4 text-sm text-slate-500">{activeOnly ? "Loading active zones…" : "Loading zone history…"}</p>}
        {queue.isError && <div role="alert" className="space-y-2 p-4 text-sm text-red-800"><p>{activeOnly ? "Active zones could not be loaded." : "Zone history could not be loaded."} {queue.error.message}</p><Button variant="outline" onClick={refresh}>Retry zones</Button></div>}
        {queue.data && !queue.isError && <>
          <p className="px-4 pt-3 text-xs text-slate-500">{queue.data.item_total} zones · {queue.data.total} {activeOnly ? (queue.data.total === 1 ? "zone card" : "zone cards") : "history entries"}</p>
          {activeOnly ? <>
            {!queue.data.items.length && <p className="p-6 text-center text-sm text-slate-500">No zones match this view.</p>}
            <div className="space-y-3 p-3">{queue.data.items.map(item => <SpatialGroupCard key={item.zone_id}
              label={`Active zones: ${item.location} · ${item.member_count} zones`} inspectLabel={`Inspect zone group: ${item.location}`}
              sourceLabel={item.sources.map(value => sourceLabels[value] || value).join(" · ")} icon={Shield} tone="zone"
              location={item.location} area={item.area_summary} count={item.member_count} countLabel="zones" timestamp={item.queued_at}
              severities={item.severity_levels} depths={item.depth_levels} onInspect={button => { opener.current = button; queueScrollTop.current = queueScroll.current?.scrollTop ?? 0; setGroupId(item.zone_id); setMemberPage(1); onViewGroupOnMap(item); }}>
              <span className="line-clamp-2 break-words text-xs leading-5 text-slate-700">{item.evidence}</span>
              <span className="text-[10px] text-slate-500">Latest zone: {floodRecordTime(item.queued_at)}</span>
              <span className="break-words text-xs leading-5 text-slate-600">{item.member_count} {item.member_count === 1 ? "zone" : "related zones"} · Inspect each zone for evidence and actions.</span>
            </SpatialGroupCard>)}</div>
            <Pagination page={queue.data.page} totalPages={queue.data.pages} onPageChange={setPage} disabled={queue.isFetching} />
          </> : <ActiveZoneRecords {...records} onCreateOfficialZone={undefined} zones={queue.data.zones} listLoading={false} isPlaceholderData={false} page={queue.data.page} setPage={setPage} totalPages={queue.data.pages} />}
        </>}
      </div>
    </div>
    {inspecting && <div className="flex min-h-0 flex-1 flex-col">
      <div className="border-b border-slate-100 px-3 py-2"><Button variant="ghost" onClick={() => { setGroupId(null); onOverview?.(); requestAnimationFrame(() => { if (queueScroll.current) queueScroll.current.scrollTop = queueScrollTop.current; opener.current?.focus({ preventScroll: true }); }); }}><ArrowLeft className="mr-2 size-4" />Back to zones</Button></div>
      {members.isPending && <p role="status" className="p-4 text-sm text-slate-500">Loading grouped zones…</p>}
      {members.isError && <div role="alert" className="space-y-2 p-4 text-sm text-red-800"><p>{members.error.message}</p><Button variant="outline" onClick={() => void members.refetch()}>Retry zone group</Button><p className="text-xs text-slate-600">Membership may have changed after expiry or deactivation. Return to zones to see the updated list.</p></div>}
      {members.data && !members.isError && <><p className="px-4 py-3 text-xs leading-5 text-slate-600">{members.data.total} {members.data.total === 1 ? "zone" : "related zones"} · {members.data.group_reason}</p><ActiveZoneRecords {...records} onCreateOfficialZone={undefined} zones={members.data.zones} listLoading={false} isPlaceholderData={false} page={members.data.page} setPage={setMemberPage} totalPages={members.data.pages} /></>}
    </div>}
  </section>;
}
