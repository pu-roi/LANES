"use client";

import { useState } from "react";
import { Button, Checkbox } from "@/shared/ui";
import { FloodSeverityBadge } from "@/shared/ui/feedback/FloodFacts";
import { formatFloodDepth } from "@/lib/floodDepth";
import { formatHazards, formatPassableVehicles } from "@/lib/floodSurvey";
import { prepareZoneUpdateEditor, reviewZoneUpdate, ZONE_CONDITIONS, type ZoneObservation, type ZoneEditorProposal, type ZoneUpdateField } from "@/features/hazards/zoneUpdatesApi";
import type { AvoidanceZone } from "../adminApi";
import { floodRecordTime } from "./FloodRecordSummary";
import { ZoneGeometryComparison } from "./ZoneGeometryComparison";

export function ZoneObservationReview({ update, zone, canReview, onReviewed, onMedia, onEdit, onDeactivate }: { update: ZoneObservation; zone: AvoidanceZone; canReview: boolean; onReviewed: () => Promise<void>; onMedia: (urls: string[]) => void; onEdit?: (zone: AvoidanceZone, proposal?: ZoneEditorProposal) => void; onDeactivate?: () => void }) {
  const [note, setNote] = useState("");
  const [fields, setFields] = useState<ZoneUpdateField[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [clearanceVerified, setClearanceVerified] = useState(false);
  const act = async (action: "reviewed" | "dismissed" | "editor") => {
    setBusy(true); setError("");
    try {
      if (action === "editor") onEdit?.(zone, await prepareZoneUpdateEditor(zone.id, update.id, fields, note));
      else { await reviewZoneUpdate(zone.id, update.id, action, note); await onReviewed(); }
    } catch (failure) { setError(failure instanceof Error ? failure.message : "Could not save the assessment."); }
    finally { setBusy(false); }
  };
  const facts: { field: ZoneUpdateField; label: string; official: string; submitted: string; available: boolean }[] = [
    { field: "depth", label: "Water level", official: formatFloodDepth(zone.depth), submitted: update.condition === "no_floodwater" ? "No visible floodwater at the reported spot" : formatFloodDepth(update.depth, { fallback: "Not recorded" }), available: !!update.depth && update.condition !== "no_floodwater" },
    { field: "passable_vehicles", label: "Passable vehicles", official: formatPassableVehicles(zone.passable_vehicles), submitted: formatPassableVehicles(update.passable_vehicles), available: update.passable_vehicles !== null },
    { field: "hidden_hazards", label: "Submerged hazards", official: formatHazards(zone.hidden_hazards), submitted: formatHazards(update.hidden_hazards), available: ["yes", "no"].includes(update.hidden_hazards) },
    { field: "geometry", label: "Road extent", official: `${zone.report_geometry?.type ?? zone.geometry.type} · current coverage`, submitted: update.proposed_extent ? `${update.proposed_extent.geometry?.type ?? "No geometry"} · ${update.proposed_extent.validation_status}` : "Not recorded", available: update.proposed_extent?.validation_status === "validated" && ["LineString", "MultiLineString"].includes(update.proposed_extent.geometry?.type) },
  ];
  return <section aria-label={`Review update #${update.id}`} className="min-w-0 space-y-5">
    <div className="space-y-2"><h3 className="text-base font-bold text-slate-900">Update #{update.id} · {update.author_name}</h3><p className="text-sm font-semibold">{ZONE_CONDITIONS.find(item => item.id === update.condition)?.label}</p><div className="flex flex-wrap gap-2"><FloodSeverityBadge severity={update.severity} /><span className="rounded bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-600">{update.review_state === "pending" ? "Needs review" : update.review_state === "reviewed" ? "Reviewed" : "Dismissed"}</span></div><p className="text-xs leading-5 text-slate-500">Submitted {floodRecordTime(update.submitted_at)}<br />{update.observed_at ? `Observed ${floodRecordTime(update.observed_at)}` : "Observation time not recorded"}</p></div>
    <div aria-label="Official and submitted conditions" className="space-y-3">
      <div className="hidden grid-cols-2 gap-4 text-xs font-bold uppercase text-slate-500 sm:grid"><span>Current official zone</span><span>Selected community update</span></div>
      {facts.map(fact => <div key={fact.field} className="border-b border-slate-100 pb-3"><h4 className="mb-1 text-xs font-semibold text-slate-500">{fact.label}</h4><div className="grid gap-2 text-sm sm:grid-cols-2 sm:gap-4"><p className="break-words text-slate-700"><span className="block text-[11px] text-slate-500 sm:hidden">Current official zone</span>{fact.official}</p><p className={`break-words ${fact.official !== fact.submitted ? "font-medium text-orange-800" : "text-slate-700"}`}><span className="block text-[11px] text-slate-500 sm:hidden">Selected community update</span>{fact.submitted}</p></div></div>)}
    </div>
    <div><h4 className="mb-1 text-xs font-bold uppercase text-slate-400">Witness description</h4><p className="whitespace-pre-line break-words text-sm leading-6 text-slate-700">{update.description}</p></div>
    <div className="space-y-1 break-words text-xs leading-5 text-slate-600"><h4 className="font-semibold">Submitted location</h4>{update.road_start && update.road_end ? <><p>Start: {update.start_label || "Selected coordinates"} ({update.road_start[1].toFixed(5)}, {update.road_start[0].toFixed(5)})</p><p>End: {update.end_label || "Selected coordinates"} ({update.road_end[1].toFixed(5)}, {update.road_end[0].toFixed(5)})</p><p>{update.is_bidirectional ? "Both directions" : "One direction"}</p></> : <p>{update.observed_location || "Not recorded"}</p>}{update.latitude != null && <p>Reported point: {update.latitude.toFixed(5)}, {update.longitude?.toFixed(5)}</p>}{update.proposed_extent && <p>{update.proposed_extent.message}</p>}</div>
    {update.proposed_extent?.geometry && <ZoneGeometryComparison official={zone.geometry} proposal={update.proposed_extent.geometry} />}
    {!!update.media_urls.length && <Button variant="outline" className="min-h-11" onClick={() => onMedia(update.media_urls)}>View evidence ({update.media_urls.length})</Button>}
    {update.applications?.map(application => <p key={application.id} className="text-xs leading-5 text-emerald-800">Used in saved zone edit · {floodRecordTime(application.saved_at)}<br />Fields: {application.fields.map(field => field.replaceAll("_", " ")).join(", ")}<br />Staff assessment: {application.reason}</p>)}
    {update.review && <p className="text-xs text-slate-600">Staff note: {update.review.note} · {floodRecordTime(update.review.reviewed_at)}</p>}
    {update.condition === "no_floodwater" && <div className="space-y-3 bg-amber-50 p-3 text-sm text-amber-900"><p>A dry spot does not clear the whole zone. Verify all affected roads and directions before deactivating. Use Edit zone for partial coverage changes.</p>{canReview && zone.is_active && onDeactivate && <><Checkbox label="I verified that the entire official zone is clear" checked={clearanceVerified} onChange={event => setClearanceVerified(event.target.checked)} /><Button variant="outline" className="min-h-11" disabled={!clearanceVerified} onClick={onDeactivate}>Assess clearance</Button></>}</div>}
    {canReview && <div className="space-y-3 border-t border-slate-100 pt-4">
      {zone.is_active && onEdit && update.review_state !== "dismissed" && <fieldset disabled={busy} className="space-y-2"><legend className="mb-2 text-sm font-semibold">Choose fields to use in editor</legend>{facts.map(fact => <Checkbox key={fact.field} label={fact.label} description={fact.available ? undefined : "Keep current value; no usable answer provided."} disabled={!fact.available} checked={fields.includes(fact.field)} containerClassName="min-h-11" onChange={event => setFields(previous => event.target.checked ? [...previous, fact.field] : previous.filter(field => field !== fact.field))} />)}<p className="text-xs leading-5 text-slate-500">Your existing edit draft is preserved. Selected fields can be incorporated there after confirmation. Descriptions and media stay as private evidence.</p></fieldset>}
      <label className="block text-xs font-semibold" htmlFor={`review-${update.id}`}>Review note<textarea id={`review-${update.id}`} value={note} disabled={busy} maxLength={2000} onChange={event => setNote(event.target.value)} placeholder="Explain your assessment and the information you intend to use." rows={3} className="mt-1 w-full rounded-lg border border-slate-200 p-2 text-sm" /></label>
      <div className="flex flex-wrap gap-2">{zone.is_active && onEdit && update.review_state !== "dismissed" && <Button className="min-h-11" disabled={busy || !fields.length || note.trim().length < 3} onClick={() => act("editor")}>Use in editor</Button>}{update.review_state === "pending" && <><Button variant="outline" className="min-h-11" disabled={busy || note.trim().length < 3} onClick={() => act("reviewed")}>Mark reviewed</Button><Button variant="outline" className="min-h-11" disabled={busy || note.trim().length < 3} onClick={() => act("dismissed")}>Dismiss with reason</Button></>}</div>
      <p className="text-[11px] leading-5 text-slate-500">Opening the editor or marking reviewed does not apply an update. Only a successful official save records the fields used.</p>
    </div>}
    {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
  </section>;
}
