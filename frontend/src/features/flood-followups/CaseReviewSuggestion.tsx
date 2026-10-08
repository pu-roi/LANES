"use client";

import { useEffect, useId, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/shared/ui";
import { getZonePrediction, getPredictionFeatures, type CaseReviewSuggestion as CaseSuggestion } from "./reviewSuggestionApi";

export const suggestionTime = (value: string) => new Date(value).toLocaleString("en-PH", { timeZone: "Asia/Manila", dateStyle: "medium", timeStyle: "short" });
export const suggestionStateLabel = {
  no_suggestion: "No saved suggestion", scheduled: "Review scheduled", due: "Needs update",
  evidence_changed: "Evidence changed", followup_received: "New observation to review", evidence_stale: "Needs current evidence", case_closed: "Historical suggestion",
};

export function SuggestionSummary({ item }: { item: CaseSuggestion }) {
  const saved = item.suggestion;
  return <div className="space-y-2 text-sm text-slate-700">
    <p className="font-semibold">{suggestionStateLabel[item.state]}</p>
    {saved && <><p>Suggested review: <strong>{suggestionTime(saved.suggested_review_at)} (PHT)</strong></p>
      <p className="text-xs text-slate-500">Saved {suggestionTime(saved.issued_at)} · Suggestion #{saved.id}</p></>}
    {item.state_reason && <p>{item.state_reason}</p>}
  </div>;
}

export function CaseReviewSuggestion({ zoneId }: { zoneId: number }) {
  const { user } = useAuth();
  const permissions = user?.role?.permissions;
  if (!user || user.role?.name === "Commuter" || !["view", "full"].includes(permissions?.reports ?? "") || !["view", "full"].includes(permissions?.zones ?? "")) return null;
  return <ZonePredictionPanel key={`${user.id}:${zoneId}`} zoneId={zoneId} userId={user.id} />;
}

function remainingLabel(estimate: string, asOf: number) {
  const minutes = Math.ceil((Date.parse(estimate) - asOf) / 60000);
  if (!Number.isFinite(minutes)) return "Remaining time unavailable";
  if (minutes <= 0) return "Estimated time passed — check current conditions";
  const hours = Math.floor(minutes / 60), remainder = minutes % 60;
  return `Approximately ${hours ? `${hours}h${remainder ? ` ${remainder}m` : ""}` : `${remainder}m`} remaining`;
}

function ZonePredictionPanel({ zoneId, userId }: { zoneId: number; userId: number }) {
  const id = useId();
  const [expanded, setExpanded] = useState(false);
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const update = () => setNow(Date.now());
    const timer = window.setInterval(update, 60000);
    window.addEventListener("focus", update);
    return () => { window.clearInterval(timer); window.removeEventListener("focus", update); };
  }, []);
  const query = useQuery({ queryKey: ["zone-subsidence-prediction", userId, zoneId], queryFn: () => getZonePrediction(zoneId), retry: false, refetchInterval: 60000 });
  const inputs = useQuery({ queryKey: ["zone-prediction-features",userId,zoneId],queryFn:()=>getPredictionFeatures(zoneId),enabled:expanded,retry:false,staleTime:60000 });
  const item = query.data;
  const median = item?.quantiles.find(q => q.quantile === .5);
  const lower = item?.quantiles.find(q => q.quantile === .1);
  const upper = item?.quantiles.find(q => q.quantile === .9);
  const simulation = item?.registration_simulation;
  const simulatedMedian = simulation?.quantiles.find(q => q.quantile === .5);
  const simulatedLower = simulation?.quantiles.find(q => q.quantile === .1);
  const simulatedUpper = simulation?.quantiles.find(q => q.quantile === .9);
  const asOf = item ? Date.parse(item.evaluated_at) + Math.max(0, now - query.dataUpdatedAt) : now;
  const labels = { estimated: "", unavailable: "Estimate unavailable", needs_review: "Evidence needs review", expired: "Evidence expired — needs current evidence", inactive: "Flood zone inactive" };
  return <section aria-label={`Automatic subsidence prediction for zone ${zoneId}`} className="space-y-3 border-t border-slate-100 pt-4">
    <div className="flex flex-wrap items-center gap-2"><h3 className="text-sm font-semibold text-slate-900">Estimated subsidence</h3><span className="rounded-full bg-amber-50 px-2 py-0.5 text-[11px] font-semibold text-amber-800">Experimental</span></div>
    {query.isPending && <p role="status" className="text-sm text-slate-500">Calculating from recorded zone evidence…</p>}
    {query.isError && <div role="alert" className="space-y-2 text-sm text-red-700"><p>Prediction unavailable: {query.error.message}</p><Button size="sm" variant="outline" className="min-h-11" onClick={() => query.refetch()}>Retry prediction</Button></div>}
    {item && <div className="space-y-2 text-sm text-slate-700">
      {item.city && !!item.barangays.length && <p className="text-xs text-slate-500">Detected location: {item.barangays.join(" / ")}, {item.city}</p>}
      {labels[item.state] && !simulatedMedian && <p role="status" className="font-semibold">{labels[item.state]}</p>}
      {item.state === "estimated" && median && <>
        <p className="text-base font-semibold text-slate-900">{query.isError ? "Previous estimate:" : "Around"} {suggestionTime(median.estimated_reported_subsidence_at)} (PHT)</p>
        {!query.isError && <p>{remainingLabel(median.estimated_reported_subsidence_at, asOf)}</p>}
        {lower && upper && <p>Model interval: {suggestionTime(lower.estimated_reported_subsidence_at)} – {suggestionTime(upper.estimated_reported_subsidence_at)} (PHT)</p>}
        <p className="text-xs text-slate-500">Forecast anchored {suggestionTime(item.prediction_as_of_at ?? item.evaluated_at)}{item.reference && ` · Observation ${suggestionTime(item.reference.observed_at)}`} (PHT)</p>
      </>}
      {!simulatedMedian && item.reasons.map(reason => <p key={reason} className="text-sm text-amber-800">{reason}</p>)}
      {item.warnings?.map(warning => <p key={warning} className="text-xs text-amber-800">{warning}</p>)}
      {simulation && simulatedMedian && <div aria-label="Registration-based subsidence simulation" className="space-y-2">
        <p className="font-semibold">Subsidence simulation · registration time proxy</p>
        <p className="text-base font-semibold">{query.isError ? "Previous simulation:" : "Around"} {suggestionTime(simulatedMedian.estimated_reported_subsidence_at)} (PHT)</p>
        {!query.isError && <p>{remainingLabel(simulatedMedian.estimated_reported_subsidence_at, asOf)}</p>}
        {simulatedLower && simulatedUpper && <p>Simulation interval: {suggestionTime(simulatedLower.estimated_reported_subsidence_at)} – {suggestionTime(simulatedUpper.estimated_reported_subsidence_at)} (PHT)</p>}
        <p className="text-xs leading-5 text-slate-500">Uses the admin’s flood registration at {suggestionTime(simulation.reference_at)} (PHT), assuming uninterrupted flooding. Actual observation time is unknown; this simulation does not confirm clearance or change expiry.</p>
        {simulation.pooled_geographic_transfer && <p className="text-xs text-amber-800">Pooled Pasig estimate; this barangay has no subsidence outcomes in the training cohort. Location accuracy is unverified.</p>}
      </div>}
      {item.state === "estimated" && <p className="text-xs leading-5 text-slate-500">Assumes uninterrupted flooding since the recorded observation. Accuracy is unverified; the estimate does not confirm clearance or change evidence expiry.</p>}
    </div>}
    {item && <Button variant="ghost" size="sm" className="min-h-11 w-full justify-start px-0 text-blue-700 sm:w-auto" aria-expanded={expanded} aria-controls={`${id}-prediction`} onClick={() => setExpanded(!expanded)}>{expanded ? "Hide calculation details" : "View calculation details"}</Button>}
    {expanded && item && <div id={`${id}-prediction`} className="space-y-3 text-sm text-slate-600">
      <dl className="grid gap-3 sm:grid-cols-2">
        <div><dt className="font-medium">First recorded flooding</dt><dd>{item.reference ? `${suggestionTime(item.reference.observed_at)} (PHT)` : "No qualified observation time"}</dd></div>
        <div><dt className="font-medium">Latest recorded wet evidence</dt><dd>{item.latest_wet ? `${suggestionTime(item.latest_wet.observed_at)} (PHT)` : "No qualified wet evidence"}</dd></div>
        <div><dt className="font-medium">Location resolved from</dt><dd>Saved zone polygon and reviewed barangay boundaries</dd></div>
        {item.coordinates && <div><dt className="font-medium">Point inside zone</dt><dd>{item.coordinates[1].toFixed(5)}° latitude, {item.coordinates[0].toFixed(5)}° longitude</dd></div>}
      </dl>
      {item.evidence.map(evidence => <p className="text-xs" key={`${evidence.source_kind}:${evidence.source_id}`}>{evidence.source_kind === "news_decision" ? "Linked news decision" : "Linked citizen observation"} #{evidence.source_id} · Observed {suggestionTime(evidence.observed_at)} · Available {suggestionTime(evidence.available_at)} (PHT)</p>)}
      {!!item.nearby_report_count && <p className="text-xs">{item.nearby_report_count} nearby report candidates. Distance alone does not link them to this flood episode.</p>}
      {item.model && <><p className="text-xs">The current model uses a pooled duration pattern; it has no learned depth or rainfall effects. Research cohort: {item.model.supported_barangays.join(", ") || "unavailable"}.</p>{item.model.model_sha256 && <p className="break-all text-xs">Model checksum: {item.model.model_sha256}</p>}</>}
      {item.registration_audit_id && <p className="text-xs">Simulation registration record #{item.registration_audit_id}. Recorded time is a proxy, separate from observed wet evidence.</p>}
      <div className="space-y-2 border-t border-slate-100 pt-3">
        <p className="text-xs font-medium">Current model input context</p>
        {inputs.isPending && <p role="status" className="text-xs">Loading model input context…</p>}
        {inputs.isError && <div role="alert" className="text-xs text-red-700"><p>{inputs.error.message}</p><Button size="sm" variant="ghost" className="min-h-11" onClick={()=>inputs.refetch()}>Retry model inputs</Button></div>}
        {inputs.data && <>
          <p className="text-xs">Terrain background: {inputs.data.environment?.elevation_m != null ? `${inputs.data.environment.elevation_m} m (90 m modelled surface)` : "Unavailable"}</p>
          <p className="text-xs">Rainfall background, previous 3 hours: {inputs.data.environment?.rainfall_previous_3h_mm != null ? `${inputs.data.environment.rainfall_previous_3h_mm} mm (coarse weather grid)` : "Unavailable"}</p>
          {[...(inputs.data.errors ?? []),...(inputs.data.environment?.errors ?? [])].map(reason=><p key={reason} className="text-xs text-amber-800">{reason}</p>)}
          <p className="text-xs">Open-Meteo / Copernicus background data. These are not street measurements; the displayed baseline does not yet use terrain or rainfall effects.</p>
        </>}
      </div>
    </div>}
  </section>;
}
