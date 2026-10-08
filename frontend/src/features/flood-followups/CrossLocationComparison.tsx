"use client";

import { useQuery } from "@tanstack/react-query";
import { Button } from "@/shared/ui";
import { getCrossLocationPrediction } from "./reviewSuggestionApi";

export function CrossLocationComparison({ zoneId, userId, formatTime }: {
  zoneId: number; userId: number; formatTime: (value: string) => string;
}) {
  const query = useQuery({ queryKey: ["cross-location-prediction", userId, zoneId],
    queryFn: () => getCrossLocationPrediction(zoneId), retry: false, staleTime: 60000, refetchInterval: 60000 });
  const item = query.data;
  const median = item?.quantiles.find(row => row.quantile === .5);
  const lower = item?.quantiles.find(row => row.quantile === .1);
  const upper = item?.quantiles.find(row => row.quantile === .9);
  return <section aria-label="Depth and location research comparison" className="space-y-2 border-t border-slate-100 pt-3 text-xs leading-5">
    <h4 className="font-semibold text-slate-900">Depth and location comparison · research only</h4>
    <p>The candidate shares a depth relationship across locations and restrains local adjustments when evidence is limited. The estimate above still uses the baseline.</p>
    {query.isPending && <p role="status">Loading cross-location comparison…</p>}
    {query.isError && <div role="alert" className="space-y-1 text-red-700"><p>Cross-location comparison unavailable: {query.error.message}</p>
      <Button size="sm" variant="ghost" className="min-h-11" onClick={() => query.refetch()}>Retry comparison</Button></div>}
    {item && <>
      {item.validation_summary && <p className="text-amber-800">{item.validation_summary}</p>}
      {item.reason && <p role="status" className="text-amber-800">{item.reason}</p>}
      {item.status === "research_comparison" && median && <>
        <p className="font-medium text-slate-900">{query.isError ? "Previous comparison:" : "Candidate comparison:"} {formatTime(median.estimated_reported_subsidence_at)} (PHT)</p>
        {lower && upper && <p>Approximate p10–p90 interval: {formatTime(lower.estimated_reported_subsidence_at)} – {formatTime(upper.estimated_reported_subsidence_at)} (PHT)</p>}
        <dl className="grid gap-2 sm:grid-cols-2">
          <div><dt className="font-medium">Frozen source depth</dt><dd>{item.depth_cm} cm · {item.depth_basis === "reported_canonical_gauge_proxy" ? "gauge proxy simulation" : "reported numeric depth"}</dd></div>
          <div><dt className="font-medium">Local outcome support</dt><dd>{item.target_location}: {item.calculation?.location_outcomes ?? 0} shared summaries</dd></div>
          <div><dt className="font-medium">Reference basis</dt><dd>{item.reference_basis === "observed_reference" ? "Recorded wet observation" : "Recording time proxy · actual observation unknown"}</dd></div>
          <div><dt className="font-medium">Information transfer</dt><dd>{item.calculation?.transfer_basis === "partial_pooling" ? "Shared depth relationship with a restrained local adjustment" : "Shared depth relationship with added uncertainty for an unseen location"}</dd></div>
        </dl>
        {item.prediction_as_of_at && <p>Anchored {formatTime(item.prediction_as_of_at)} (PHT) · source record #{item.source_audit_id}.</p>}
        {item.calculation && <p className="break-words font-mono">log-duration centre {item.calculation.log_duration_location.toFixed(4)} · depth contribution {item.calculation.shared_depth_effect.toFixed(4)} · local contribution {item.calculation.local_effect.toFixed(4)} · approximate log spread {item.calculation.predictive_log_scale.toFixed(4)}</p>}
      </>}
      {item.warnings.map(warning => <p key={warning} className="text-amber-800">{warning}</p>)}
      {!!item.trained_locations.length && <p>Training locations: {item.trained_locations.join(", ")}.</p>}
    </>}
  </section>;
}
