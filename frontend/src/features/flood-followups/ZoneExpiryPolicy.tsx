"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/apiClient";
import { Button } from "@/shared/ui";

type ExpiryPolicy = {
  automatic_expiry_enabled: boolean; pasig_ml_expiry_enabled: boolean;
  method: "fixed" | "fixed_fallback" | "ml_pooled" | "ml_cross_location" | "pending_sync";
  deadline: string | null; reason: string | null; reference_basis: string | null;
  experimental: boolean; accuracy_verified: false; expires_as: "Unconfirmed";
  zone_is_active?: boolean; prediction_as_of_at?: string | null;
  quantiles?: { quantile: number; estimated_reported_subsidence_at: string }[];
};

export default function ZoneExpiryPolicy({ zoneId, userId }: { zoneId: number; userId: number }) {
  const query = useQuery({ queryKey: ["zoneExpiryPolicy", userId, zoneId],
    queryFn: () => apiClient.get<ExpiryPolicy>(`/admin/zones/${zoneId}/expiry-policy`),
    staleTime: 30_000, refetchInterval: 60_000, retry: false });
  const item = query.data;
  const median = item?.quantiles?.find(q => q.quantile === .5);
  const lower = item?.quantiles?.find(q => q.quantile === .1);
  const upper = item?.quantiles?.find(q => q.quantile === .9);
  const time = (stamp: string) => new Date(stamp).toLocaleString("en-PH", { timeZone: "Asia/Manila" });
  return <div className="space-y-1 text-sm" aria-label="Automatic zone expiry">
    <p className="font-medium text-slate-800">Automatic zone expiry</p>
    {query.isPending && <p role="status">Loading expiry policy…</p>}
    {query.isError && <div role="alert" className="text-red-700"><p>{query.error.message || "Expiry policy is unavailable."}</p><Button variant="ghost" size="sm" onClick={() => query.refetch()}>Retry expiry policy</Button></div>}
    {item && <>
      <p>{!item.automatic_expiry_enabled ? "Paused" : item.method === "ml_cross_location" ? "ML · depth and cross-location estimate" : item.method === "ml_pooled" ? "ML · pooled Pasig duration estimate" : item.method === "pending_sync" ? "Waiting for policy synchronization" : item.method === "fixed_fallback" ? (item.deadline ? "Fixed timer · ML unavailable" : "ML unavailable · no saved deadline") : "Fixed timer"}</p>
      <p>{item.deadline ? `Deadline: ${time(item.deadline)} (PHT)` : "No automatic deadline recorded"}</p>
      {median && <div className="space-y-1 pt-2" aria-label="Saved ML subsidence estimate">
        <p className="font-medium text-slate-800">Saved ML subsidence estimate</p>
        <p>Around <strong>{time(median.estimated_reported_subsidence_at)} (PHT)</strong></p>
        {lower && upper && <p className="text-xs text-slate-600">Model interval: {time(lower.estimated_reported_subsidence_at)} – {time(upper.estimated_reported_subsidence_at)} (PHT)</p>}
        {item.prediction_as_of_at && <p className="text-xs text-slate-600">Forecast anchored {time(item.prediction_as_of_at)} (PHT). Expiry uses the upper estimate.</p>}
        {item.zone_is_active === false && <p className="text-xs text-slate-600">This zone is inactive. The saved forecast remains available for review.</p>}
      </div>}
      {item.reason && <p className="text-xs text-slate-600">{item.reason}</p>}
      {item.reference_basis?.endsWith("proxy") && <p className="text-xs text-amber-800">Uses a recording-time proxy; the actual flood observation time is unknown.</p>}
      {item.experimental && <p className="text-xs text-amber-800">Experimental ML expiry. Accuracy is unverified. Expiry marks conditions Unconfirmed; it does not confirm clearance.</p>}
    </>}
  </div>;
}
