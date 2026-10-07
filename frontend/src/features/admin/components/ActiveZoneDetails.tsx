"use client";

import { useCallback, useState } from "react";
import { useInfiniteQuery, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button, Tabs } from "@/shared/ui";
import { RecordDetailsDialog } from "@/shared/ui/feedback/RecordDetailsDialog";
import { MediaViewer } from "@/shared/ui/feedback/MediaViewer";
import { apiClient } from "@/lib/apiClient";
import { formatFloodDepth } from "@/lib/floodDepth";
import { getZoneUpdates, reviewZoneUpdate, ZONE_CONDITIONS, type ZoneObservation } from "@/features/hazards/zoneUpdatesApi";
import { VEHICLE_OPTIONS } from "@/features/hazards/floodSurvey";
import type { AvoidanceZone } from "../adminApi";
import { floodRecordTime } from "./FloodRecordSummary";

function Observation({ update, canReview, onReviewed, onMedia }: { update: ZoneObservation; canReview: boolean; onReviewed: () => Promise<void>; onMedia: (urls: string[]) => void }) {
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const decide = async (decision: "reviewed" | "dismissed") => {
    setBusy(true); setError("");
    try { await reviewZoneUpdate(update.zone_id, update.id, decision, note); await onReviewed(); }
    catch (failure) { setError(failure instanceof Error ? failure.message : "Could not save the review."); }
    finally { setBusy(false); }
  };
  return <article aria-label={`Public update #${update.id}`} className="space-y-3 border-b border-slate-100 py-4 last:border-0">
    <div className="flex flex-wrap items-center justify-between gap-2"><h3 className="text-sm font-semibold">{ZONE_CONDITIONS.find(item => item.id === update.condition)?.label}</h3><span className={`rounded px-2 py-1 text-[11px] font-semibold ${update.review_state === "pending" ? "bg-amber-50 text-amber-800" : "bg-slate-100 text-slate-600"}`}>{update.review_state === "pending" ? "Needs review" : update.review_state === "reviewed" ? "Reviewed" : "Dismissed"}</span></div>
    <p className="text-xs text-slate-500">By {update.author_name} · {update.observed_at ? `Observed ${floodRecordTime(update.observed_at)}` : "Observation time not recorded"}<span className="block">Submitted {floodRecordTime(update.submitted_at)}</span></p>
    {update.road_start && update.road_end && <div className="space-y-1 text-xs text-slate-700"><p className="font-semibold">Proposed affected road</p><p>Start: {update.start_label} ({update.road_start[1].toFixed(5)}, {update.road_start[0].toFixed(5)})</p><p>End: {update.end_label} ({update.road_end[1].toFixed(5)}, {update.road_end[0].toFixed(5)})</p><p>{update.is_bidirectional ? "Both sides of the road" : "Selected direction"} · {update.proposed_extent?.message}</p><p className="text-slate-500">Verify this proposed extent in Edit zone before changing the official map.</p></div>}
    <dl className="space-y-1 text-xs text-slate-700"><div><dt className="inline font-semibold">Observed spot: </dt><dd className="inline break-words">{update.observed_location}</dd></div><div><dt className="inline font-semibold">Depth: </dt><dd className="inline">{update.condition === "no_floodwater" ? "No visible floodwater at this spot" : formatFloodDepth(update.depth, { fallback: "Unsure" })}</dd></div><div><dt className="inline font-semibold">Hidden hazards: </dt><dd className="inline capitalize">{update.hidden_hazards}</dd></div><div><dt className="inline font-semibold">Observed passing: </dt><dd className="inline">{update.passable_vehicles === null ? "Unsure" : update.passable_vehicles.length === 0 ? "None observed" : update.passable_vehicles.map(value => VEHICLE_OPTIONS.find(option => option.id === value)?.label ?? value).join(", ")}</dd></div>{update.latitude !== null && <div><dt className="inline font-semibold">Coordinates: </dt><dd className="inline">{update.latitude.toFixed(5)}, {update.longitude?.toFixed(5)}</dd></div>}</dl>
    <p className="whitespace-pre-line break-words text-sm leading-6 text-slate-700">{update.description}</p>
    {!!update.media_urls.length && <Button variant="outline" size="sm" className="min-h-11" onClick={() => onMedia(update.media_urls)}>View evidence ({update.media_urls.length})</Button>}
    {update.review && <p className="text-xs text-slate-600">Staff note: {update.review.note} · {floodRecordTime(update.review.reviewed_at)}</p>}
    {canReview && update.review_state === "pending" && <div className="space-y-2"><label className="block text-xs font-semibold" htmlFor={`review-${update.id}`}>Review note<textarea id={`review-${update.id}`} value={note} disabled={busy} maxLength={2000} onChange={event => setNote(event.target.value)} placeholder="Record your assessment and any Edit / Deactivate action taken." rows={2} className="mt-1 w-full rounded-lg border border-slate-200 p-2 text-sm" /></label><div className="flex flex-wrap gap-2"><Button size="sm" className="min-h-11" disabled={busy || note.trim().length < 3} onClick={() => decide("reviewed")}>Mark reviewed</Button><Button variant="outline" size="sm" className="min-h-11" disabled={busy || note.trim().length < 3} onClick={() => decide("dismissed")}>Dismiss with reason</Button></div><p className="text-[11px] text-slate-500">This records a review; use Edit or Deactivate to change the official zone.</p></div>}
    {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
  </article>;
}

export function ActiveZoneDetails({ zone, initialTab, onClose, onEdit }: { zone: AvoidanceZone; initialTab: "overview" | "updates"; onClose: () => void; onEdit?: (zone: AvoidanceZone) => void }) {
  const [tab, setTab] = useState(initialTab);
  const [media, setMedia] = useState<string[] | null>(null);
  const queryClient = useQueryClient();
  const fresh = useQuery({ queryKey: ["zone-details", zone.id], queryFn: () => apiClient.get<AvoidanceZone>(`/admin/zones/${zone.id}`), refetchInterval: 60000 });
  const current = fresh.data ?? zone;
  const updates = useInfiniteQuery({ queryKey: ["zone-public-updates", zone.id], initialPageParam: undefined as number | undefined,
    queryFn: ({ pageParam }) => getZoneUpdates(zone.id, pageParam), getNextPageParam: page => page.next_before_id ?? undefined, refetchInterval: 30000 });
  const reviewed = async () => { await Promise.all([queryClient.invalidateQueries({ queryKey: ["zone-public-updates", zone.id] }), queryClient.invalidateQueries({ queryKey: ["zone-update-counts"] })]); };
  const close = useCallback(() => { if (!media) onClose(); }, [media, onClose]);
  const evidence = [...current.media_urls ?? [], ...current.report_media_urls ?? []];
  return <><RecordDetailsDialog title="Flood Zone Details" subtitle={`${current.name || `Zone #${zone.id}`} · ${current.is_active ? "Active" : "Inactive"}`} closeLabel="Close flood zone details" onClose={close} size="wide">
    <Tabs tabs={[{ id: "overview", label: "Overview" }, { id: "updates", label: "Community updates" }]} activeTab={tab} onChange={setTab} variant="underline" tabClassName="min-h-11" layoutId={`zone-details-${zone.id}`} />
    {tab === "updates" && <p className="text-sm font-semibold text-slate-700">Current official depth: {formatFloodDepth(current.depth)} · {current.is_active ? "Active" : "Inactive"}</p>}
    {fresh.isError && <div role="alert" className="text-sm text-red-700">Could not refresh official zone details. <Button variant="ghost" size="sm" onClick={() => fresh.refetch()}>Retry</Button></div>}
    {tab === "overview" ? <div className="space-y-4"><dl className="grid grid-cols-1 gap-4 text-sm sm:grid-cols-2">{[
      ["Official depth", formatFloodDepth(current.depth)], ["Severity", current.severity],
      ["Vehicles", current.passable_vehicles || "Not recorded"], ["Hidden hazards", current.hidden_hazards || "Not recorded"],
      ["Created", floodRecordTime(current.created_at)], ["Expires", current.expires_at ? floodRecordTime(current.expires_at) : "No expiry recorded"],
      ["Source", current.report_source?.replaceAll("_", " ") || "Official zone"],
    ].map(([label, value]) => <div key={label}><dt className="text-xs font-semibold text-slate-500">{label}</dt><dd className="mt-1 break-words capitalize text-slate-800">{value}</dd></div>)}</dl>{current.admin_notes && <div><p className="text-xs font-semibold text-slate-500">Admin notes</p><p className="mt-1 whitespace-pre-line text-sm">{current.admin_notes}</p></div>}{current.report_text && <p className="text-sm text-slate-700">{current.report_text}</p>}{current.merge_rationale && <p className="text-sm text-slate-700">Merge rationale: {current.merge_rationale}</p>}{evidence.length > 0 && <Button variant="outline" className="min-h-11" onClick={() => setMedia(evidence)}>View official evidence ({evidence.length})</Button>}</div>
      : <div><p className="mb-2 text-xs leading-5 text-slate-500">Witness observations are evidence for review. Verify the observed area and time before changing official conditions.</p>{updates.isPending ? <p role="status" className="py-6 text-sm text-slate-500">Loading community updates…</p> : updates.isError ? <div role="alert" className="py-4 text-sm text-red-700">Could not load community updates. <Button variant="outline" size="sm" onClick={() => updates.refetch()}>Retry</Button></div> : <>{updates.data?.pages[0].updates.length === 0 && <p className="py-6 text-sm text-slate-500">No community updates for this zone yet.</p>}{updates.data?.pages.flatMap(page => page.updates).map(update => <Observation key={update.id} update={update} canReview={updates.data.pages[0].can_review} onReviewed={reviewed} onMedia={setMedia} />)}{updates.hasNextPage && <Button variant="outline" disabled={updates.isFetchingNextPage} onClick={() => updates.fetchNextPage()}>Load older updates</Button>}</>}</div>}
    {onEdit && current.is_active && updates.data?.pages[0].can_review && <div className="border-t border-slate-100 pt-3"><Button variant="outline" className="min-h-11" onClick={() => { onClose(); onEdit(current); }}>Edit zone</Button></div>}
  </RecordDetailsDialog>{media && <MediaViewer mediaUrls={media} isOpen onClose={() => setMedia(null)} />}</>;
}
