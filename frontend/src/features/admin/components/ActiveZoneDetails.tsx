"use client";

import { useCallback, useState } from "react";
import { useInfiniteQuery, useQuery, useQueryClient } from "@tanstack/react-query";
import { MapPin, User } from "lucide-react";
import { Button, Tabs } from "@/shared/ui";
import { RecordDetailsDialog } from "@/shared/ui/feedback/RecordDetailsDialog";
import { FloodFacts, FloodSeverityBadge } from "@/shared/ui/feedback/FloodFacts";
import { MediaViewer } from "@/shared/ui/feedback/MediaViewer";
import { apiClient } from "@/lib/apiClient";
import { formatFloodDepth } from "@/lib/floodDepth";
import { getZoneUpdates, ZONE_CONDITIONS, type ZoneEditorProposal } from "@/features/hazards/zoneUpdatesApi";
import type { AvoidanceZone } from "../adminApi";
import { floodRecordTime } from "./FloodRecordSummary";
import { publisherLink } from "@/features/news/newsPresentation";
import { ZoneObservationReview } from "./ZoneObservationReview";

export function ActiveZoneDetails({ zone, initialTab, onClose, onEdit, onViewMap, onDeactivate, editorOpen = false }: { zone: AvoidanceZone; initialTab: "overview" | "updates"; onClose: () => void; onEdit?: (zone: AvoidanceZone, proposal?: ZoneEditorProposal) => void; onViewMap?: (zone: AvoidanceZone) => void; onDeactivate?: () => void; editorOpen?: boolean }) {
  const [tab, setTab] = useState(initialTab);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [media, setMedia] = useState<string[] | null>(null);
  const queryClient = useQueryClient();
  const fresh = useQuery({ queryKey: ["zone-details", zone.id], queryFn: () => apiClient.get<AvoidanceZone>(`/admin/zones/${zone.id}`), refetchInterval: 60000 });
  const current = fresh.data ?? zone;
  const updates = useInfiniteQuery({ queryKey: ["zone-public-updates", zone.id], initialPageParam: undefined as number | undefined,
    queryFn: ({ pageParam }) => getZoneUpdates(zone.id, pageParam), getNextPageParam: page => page.next_before_id ?? undefined, refetchInterval: 30000 });
  const reviewed = async () => { await Promise.all([queryClient.invalidateQueries({ queryKey: ["zone-public-updates", zone.id] }), queryClient.invalidateQueries({ queryKey: ["zone-update-counts"] })]); };
  const close = useCallback(() => { if (!media) onClose(); }, [media, onClose]);
  const records = updates.data?.pages.flatMap(page => page.updates) ?? [];
  const selected = records.find(update => update.id === selectedId);
  const canReview = updates.data?.pages[0].can_review ?? false;
  const coordinates = current.geometry.coordinates[0]?.[0];
  if (editorOpen) return null;
  return <><RecordDetailsDialog title="Flood Zone Details" subtitle={`#${current.id} · ${current.name || "Official flood zone"} · ${current.is_active ? "Active" : "Inactive"}`} closeLabel="Close flood zone details" onClose={close} size={tab === "updates" && selected ? "wide" : "default"} footer={canReview && current.is_active ? <div className="flex flex-wrap gap-2">{onEdit && <Button variant="outline" className="min-h-11" onClick={() => onEdit(current)}>Edit zone</Button>}{tab === "overview" && onDeactivate && <Button variant="outline" className="min-h-11 text-red-700" onClick={onDeactivate}>Deactivate zone</Button>}</div> : undefined}>
    <Tabs tabs={[{ id: "overview", label: "Overview" }, { id: "updates", label: "Community updates" }]} activeTab={tab} onChange={setTab} variant="underline" tabClassName="min-h-11" layoutId={`zone-details-${zone.id}`} />
    {fresh.isError && <div role="alert" className="text-sm text-red-700">Could not refresh official zone details. <Button variant="ghost" size="sm" onClick={() => fresh.refetch()}>Retry</Button></div>}
    {tab === "overview" ? <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200/80 bg-slate-50 p-3"><div className="flex items-center gap-2"><span className="text-xs font-semibold uppercase text-slate-500">Severity:</span><FloodSeverityBadge severity={current.severity} /></div><div className="flex items-center gap-2"><span className="text-xs font-semibold uppercase text-slate-500">Source:</span><span className="rounded-md bg-slate-200/80 px-2 py-1 text-xs font-bold uppercase text-slate-700">{current.report_source?.replaceAll("_", " ") || "Official zone"}</span></div></div>
      {current.admin_notes && <div className="space-y-2"><h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Operational description</h3><p className="whitespace-pre-line break-words rounded-xl border border-blue-100 bg-blue-50/50 p-4 text-sm leading-6 text-slate-800">{current.admin_notes}</p></div>}
      <FloodFacts depth={current.depth} hazards={current.hidden_hazards} vehicles={current.passable_vehicles} bidirectional={current.is_bidirectional} />
      <div className="space-y-2 rounded-xl border border-slate-200/70 bg-slate-50/80 p-4"><h3 className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-slate-400"><MapPin className="size-3.5" />Spatial location</h3><p className="break-words text-sm font-semibold">{current.location_label || "Location name not recorded"}</p><p className="break-words font-mono text-xs text-slate-500">{coordinates ? `${coordinates[1].toFixed(5)}° latitude, ${coordinates[0].toFixed(5)}° longitude · Polygon boundary` : "No coordinates mapped"}</p>{onViewMap && <Button variant="outline" className="min-h-11" onClick={() => { onClose(); onViewMap(current); }}>View on Map</Button>}</div>
      <dl className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">{[["Created", floodRecordTime(current.created_at)], ["Updated", floodRecordTime(current.updated_at)], ["Expires", current.expires_at ? floodRecordTime(current.expires_at) : "No expiry recorded"], ["Status", current.is_active ? "Active" : "Inactive"]].map(([label, value]) => <div key={label}><dt className="text-xs font-semibold text-slate-400">{label}</dt><dd className="mt-1 text-slate-800">{value}</dd></div>)}</dl>
      {current.reporter_name && <div className="flex items-center gap-3 rounded-xl border border-slate-200/70 bg-slate-50/80 p-4"><User className="size-5 text-slate-500" /><div><p className="text-xs font-semibold text-slate-400">Original report contributor</p><p className="text-sm font-bold">{current.reporter_name}</p>{current.reporter_trust_score != null && <p className="text-xs text-slate-500">Current trust score: {current.reporter_trust_score}%</p>}</div></div>}
      {current.original_report_text && current.original_report_text !== current.admin_notes && <div><h3 className="mb-2 text-xs font-bold uppercase text-slate-400">Original report submission</h3><p className="whitespace-pre-line break-words text-sm leading-6 text-slate-700">{current.original_report_text}</p></div>}
      {!!current.news?.length && <section aria-label="Linked source evidence" className="space-y-3"><h3 className="text-xs font-bold uppercase text-slate-400">Linked source evidence</h3>{current.news.map(item => <div key={item.case_id} className="space-y-1 border-b border-slate-100 pb-3 last:border-0"><p className="text-sm font-semibold">{item.source_title}</p><p className="text-xs text-slate-500">{item.source_publisher || "Publisher not recorded"} · {item.observed_at ? `Observed ${floodRecordTime(item.observed_at)}` : "Observation time not stated"}</p>{publisherLink(item.source_url) && <a className="inline-flex min-h-11 items-center text-sm text-blue-600 underline" href={publisherLink(item.source_url)} target="_blank" rel="noopener noreferrer">Open source article</a>}</div>)}</section>}
      {current.merge_rationale && <p className="text-sm text-slate-700">Merge rationale: {current.merge_rationale}</p>}
      <div className="flex flex-wrap gap-2">{!!current.media_urls?.length && <Button variant="outline" className="min-h-11" onClick={() => setMedia(current.media_urls!)}>View official evidence ({current.media_urls.length})</Button>}{!!current.report_media_urls?.length && <Button variant="outline" className="min-h-11" onClick={() => setMedia(current.report_media_urls!)}>View original report evidence ({current.report_media_urls.length})</Button>}</div>
    </div> : <div className="space-y-4"><p className="text-xs leading-5 text-slate-500">Each submission is separate evidence. Compare its location, condition and media; submission time does not prove when the flood was observed.</p>
      {updates.isPending ? <p role="status" className="py-6 text-sm text-slate-500">Loading community updates…</p> : updates.isError ? <div role="alert" className="py-4 text-sm text-red-700">Could not load community updates. <Button variant="outline" size="sm" onClick={() => updates.refetch()}>Retry</Button></div> : <>
        {!records.length && <p className="py-6 text-sm text-slate-500">No community updates for this zone yet.</p>}
        <div className={`grid min-w-0 gap-6 ${selected ? "md:grid-cols-[minmax(0,1fr)_minmax(0,2fr)]" : ""}`}>
          <div className={`min-w-0 ${selected ? "hidden md:sticky md:top-0 md:block md:max-h-[60dvh] md:self-start md:overflow-y-auto" : ""}`}>{records.map(update => <article key={update.id} aria-label={`Public update #${update.id}`} className="space-y-2 border-b border-slate-100 py-4 last:border-0"><div className="flex flex-wrap items-start justify-between gap-2"><h3 className="text-sm font-bold">#{update.id} · {update.author_name}</h3><span className={`rounded px-2 py-1 text-[11px] font-semibold ${update.review_state === "pending" ? "bg-amber-50 text-amber-800" : "bg-slate-100 text-slate-600"}`}>{update.review_state === "pending" ? "Needs review" : update.review_state === "reviewed" ? "Reviewed" : "Dismissed"}</span></div><p className="text-sm font-semibold">{ZONE_CONDITIONS.find(item => item.id === update.condition)?.label}</p><p className="text-xs text-slate-600">{update.condition === "no_floodwater" ? "No visible floodwater at reported spot" : formatFloodDepth(update.depth, { fallback: "Depth not recorded" })}{update.severity && ` · ${update.severity}`}</p><p className="text-xs text-slate-500">Submitted {floodRecordTime(update.submitted_at)} · {update.media_urls.length} attachments</p>{!!update.applications?.length && <p className="text-xs font-semibold text-emerald-700">Used in saved zone edit</p>}<Button variant={selectedId === update.id ? "primary" : "outline"} className="min-h-11" aria-pressed={selectedId === update.id} onClick={() => setSelectedId(update.id)}>Review update #{update.id}</Button></article>)}{updates.hasNextPage && <Button variant="outline" disabled={updates.isFetchingNextPage} onClick={() => updates.fetchNextPage()}>Load older updates</Button>}</div>
          {selected && <div className="min-w-0 space-y-4"><Button variant="ghost" className="min-h-11" onClick={() => setSelectedId(null)}>Back to updates</Button><ZoneObservationReview key={selected.id} update={selected} zone={current} canReview={canReview} onReviewed={reviewed} onMedia={setMedia} onEdit={onEdit} onDeactivate={onDeactivate} /></div>}
        </div>
      </>}
    </div>}

  </RecordDetailsDialog>{media && <MediaViewer mediaUrls={media} isOpen onClose={() => setMedia(null)} />}</>;
}
