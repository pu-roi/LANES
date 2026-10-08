"use client";

import Link from "next/link";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/shared/ui";
import { CaseReviewSuggestion, SuggestionSummary } from "./CaseReviewSuggestion";
import { getSuggestionQueue, suggestionKey } from "./reviewSuggestionApi";

export function ReviewSuggestionQueue() {
  const { user } = useAuth();
  if (!user || !["view", "full"].includes(user.role?.permissions?.reports ?? "") || user.role?.name === "Commuter") return null;
  return <Queue key={user.id} userId={user.id} />;
}

function Queue({ userId }: { userId: number }) {
  const [beforeId, setBeforeId] = useState<number | null>(null);
  const [actionable, setActionable] = useState(true);
  const query = useQuery({ queryKey: [...suggestionKey(userId), "queue", actionable, beforeId], queryFn: () => getSuggestionQueue(beforeId, actionable), retry: false, refetchInterval: 60000 });
  return <section aria-labelledby="ml-review-queue-title" className="space-y-3 border-b border-slate-200 pb-5">
    <div className="flex flex-wrap items-center justify-between gap-3"><div><h2 id="ml-review-queue-title" className="text-lg font-semibold">ML review assistant</h2><p className="text-sm text-slate-600">Saved case suggestions and observations that need staff attention.</p></div><Button size="sm" variant="outline" className="min-h-11" onClick={() => query.refetch()}>Refresh suggestions</Button></div>
    <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={actionable} onChange={event => { setActionable(event.target.checked); setBeforeId(null); }} className="size-4 accent-blue-600" />Needs update or evidence review only</label>
    {query.isPending && <p role="status" className="text-sm text-slate-500">Loading review suggestions…</p>}
    {query.isError && <p role="alert" className="text-sm text-red-700">{query.error.message}</p>}
    {query.data && <>
      {!query.data.cases.length && <p className="text-sm text-slate-500">No matching saved suggestions on this page. Open a report’s Experimental ML review suggestion to get started.</p>}
      {query.data.cases.map(item => <article key={item.report_id} aria-label={`Suggested case ${item.report_id}`} className="space-y-2 border-t border-slate-100 py-3">
        <h3 className="text-sm font-semibold">Report #{item.report_id} · {item.location || "Location not recorded"}</h3><SuggestionSummary item={item} />
        <Link className="inline-flex min-h-11 items-center text-sm text-blue-700 underline" href={`/admin/map?focus_report_id=${item.report_id}&tab=${item.zone_id ? "zones" : "pending"}${item.zone_id ? `&focus_zone_id=${item.zone_id}` : ""}`}>Review evidence on map</Link>
        {item.zone_id !== null && <CaseReviewSuggestion zoneId={item.zone_id} />}
      </article>)}
      <p className="text-xs text-slate-500">Experimental estimates help prioritize checks. Current evidence and the existing clearance process determine flood status.</p>
      <div className="flex flex-wrap gap-2">{beforeId !== null && <Button size="sm" variant="outline" onClick={() => setBeforeId(null)}>Newest suggestions</Button>}{query.data.next_before_id !== null && <Button size="sm" variant="outline" onClick={() => setBeforeId(query.data!.next_before_id)}>Older suggestions</Button>}</div>
    </>}
  </section>;
}
