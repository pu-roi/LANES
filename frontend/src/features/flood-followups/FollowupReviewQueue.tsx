"use client";

import { useId, useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/hooks/useAuth";
import Link from "next/link";
import { Button, Select } from "@/shared/ui";
import { adminFollowupKey, exportFollowupReviewPage, getFollowupReviewPage, ownerFollowupKey, reviewFollowup, type FloodFollowup, type FollowupReviewPayload, type FollowupReviewState } from "./followupApi";

export function FollowupReviewQueue() {
  const { user } = useAuth();
  return user ? <ReviewQueue key={user.id} userId={user.id} canReview={user.role?.permissions?.reports === "full"} /> : null;
}

function ReviewQueue({ userId, canReview }: { userId: number; canReview: boolean }) {
  const queryClient = useQueryClient();
  const [state, setState] = useState<FollowupReviewState | "all">("pending");
  const [beforeId, setBeforeId] = useState<number | null>(null);
  const [message, setMessage] = useState("");
  const [exportError, setExportError] = useState("");
  const [exporting, setExporting] = useState(false);
  const queue = useQuery({
    queryKey: [...adminFollowupKey(userId), state, beforeId],
    queryFn: () => getFollowupReviewPage(state, beforeId),
    retry: false,
  });
  const onReviewed = (item: FloodFollowup) => {
    setMessage(`Follow-up #${item.id} ${item.review_state}. The evidence review has been recorded.`);
    void queryClient.invalidateQueries({ queryKey: adminFollowupKey(userId) });
    void queryClient.invalidateQueries({ queryKey: ownerFollowupKey(item.user_id, item.report_id) });
  };
  const exportPage = async () => {
    setExporting(true);
    setExportError("");
    try {
      await exportFollowupReviewPage(state, beforeId);
    } catch (err) {
      setExportError(err instanceof Error ? err.message : "Could not export this page. Try again.");
    } finally {
      setExporting(false);
    }
  };

  return <section className="space-y-4 border-t border-slate-200 pt-6" aria-labelledby="flood-followup-review-title">
    <div className="space-y-2"><h2 id="flood-followup-review-title" className="text-lg font-semibold text-slate-900">Flood condition follow-ups</h2><p className="text-sm text-slate-600">Review observations linked to the original report’s saved road section. Accepted evidence remains a source claim; this review does not automatically clear a road or admit a training sample.</p></div>
    <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <Select className="sm:max-w-xs" label="Follow-up review state" value={state} onChange={(event) => { setState(String(event.target.value) as typeof state); setBeforeId(null); setMessage(""); setExportError(""); }} options={[{ value: "pending", label: "Pending review" }, { value: "accepted", label: "Accepted" }, { value: "rejected", label: "Rejected" }, { value: "all", label: "All follow-ups" }]} />
      <Button type="button" variant="outline" disabled={exporting || queue.isFetching || !queue.data || queue.isError} onClick={() => void exportPage()}>{exporting ? "Exporting…" : "Export this page"}</Button>
    </div>
    {!canReview && <p className="text-sm text-slate-600">You have view-only access. Full Reports permission is required to review follow-ups.</p>}
    {message && <p role="status" className="text-sm text-emerald-800">{message}</p>}
    {exportError && <p role="alert" className="text-sm text-red-700">{exportError}</p>}
    {queue.isPending && <p role="status" className="text-sm text-slate-500">Loading follow-ups…</p>}
    {queue.isError && <div role="alert" className="space-y-2 text-sm text-red-700"><p>{queue.error.message || "Could not load follow-ups."}</p><Button type="button" size="sm" variant="outline" onClick={() => void queue.refetch()}>Try loading again</Button></div>}
    {queue.data?.follow_ups.length === 0 && <p className="text-sm text-slate-500">No follow-ups match this review state on this page.</p>}
    {queue.data?.follow_ups.map((item) => <FollowupReviewItem key={`${userId}:${item.id}:${item.review_state}`} item={item} userId={userId} canReview={canReview} onReviewed={onReviewed} />)}
    {queue.data && <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <p className="text-xs text-slate-500">Showing up to 100 follow-ups per page.</p>
      <div className="flex gap-2"><Button type="button" variant="outline" size="sm" disabled={beforeId === null || queue.isFetching} onClick={() => { setBeforeId(null); setMessage(""); setExportError(""); }}>Newest records</Button><Button type="button" variant="outline" size="sm" disabled={queue.data.next_before_id === null || queue.isFetching} onClick={() => { setBeforeId(queue.data!.next_before_id); setMessage(""); setExportError(""); }}>Older records</Button></div>
    </div>}
  </section>;
}

function FollowupReviewItem({ item, userId, canReview, onReviewed }: { item: FloodFollowup; userId: number; canReview: boolean; onReviewed: (item: FloodFollowup) => void }) {
  const id = useId();
  const [decision, setDecision] = useState<FollowupReviewPayload["decision"] | "">("");
  const [evidence, setEvidence] = useState("");
  const [sameLocation, setSameLocation] = useState(false);
  const mutation = useMutation({ mutationFn: (payload: FollowupReviewPayload) => reviewFollowup(item.id, payload), retry: false, onSuccess: onReviewed });
  const submitReview = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!decision || mutation.isPending || mutation.isSuccess || (decision === "accepted" && !sameLocation)) return;
    mutation.mutate({ decision, evidence_text: evidence, same_location_verified: sameLocation });
  };
  const location = item.location_snapshot;
  return <article className="space-y-3 rounded-lg bg-white p-4 sm:p-5">
    <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between"><h3 className="font-semibold text-slate-900">Follow-up #{item.id} · Report #{item.report_id}</h3><span className="text-sm capitalize text-slate-700">{item.review_state}</span></div>
    <p className="text-sm font-medium text-slate-800">{item.condition === "still_flooded" ? "Still flooded" : "Flooding has subsided"}</p>
    <dl className="grid min-w-0 gap-x-6 gap-y-2 text-sm sm:grid-cols-2">
      <div><dt className="font-medium text-slate-700">Saved location</dt><dd className="break-words text-slate-600">{[location.human_readable_location, location.barangay, location.city].filter(Boolean).join(" · ") || "Location text unavailable"}</dd></div>
      <div><dt className="font-medium text-slate-700">Original observation</dt><dd className="text-slate-600">{item.original_observed_at ? new Date(item.original_observed_at).toLocaleString() : "Observation time not recorded"}</dd></div>
      <div><dt className="font-medium text-slate-700">Original evidence recorded</dt><dd className="text-slate-600">{item.original_available_at ? new Date(item.original_available_at).toLocaleString() : "Availability not recorded"}</dd></div>
      <div><dt className="font-medium text-slate-700">Follow-up observed</dt><dd className="text-slate-600">{new Date(item.observed_at).toLocaleString()}</dd></div>
      <div><dt className="font-medium text-slate-700">Follow-up submitted</dt><dd className="text-slate-600">{new Date(item.submitted_at).toLocaleString()}</dd></div>
      <div><dt className="font-medium text-slate-700">Reporter</dt><dd className="text-slate-600">User #{item.user_id}</dd></div>
      <div><dt className="font-medium text-slate-700">Water depth</dt><dd className="text-slate-600">{item.depth_cm === null ? "Not supplied" : `${item.depth_cm} cm`}</dd></div>
    </dl>
    <div><p className="text-sm font-medium text-slate-700">Observation and source evidence</p><p className="mt-1 whitespace-pre-wrap break-words text-sm text-slate-600">{item.evidence_text}</p></div>
    {item.source_url?.startsWith("https://") && <a href={item.source_url} target="_blank" rel="noopener noreferrer" className="inline-block break-all text-sm text-blue-700 underline">Open evidence source</a>}
    <p className="text-xs text-slate-500">Reporter confirmed same road section: {item.same_location_confirmed ? "Yes" : "No"}{location.zone_id !== null ? ` · Zone #${location.zone_id}` : ""}{location.event_id !== null ? ` · Event #${location.event_id}` : ""}</p>
    <Link href={`/admin/map?focus_report_id=${item.report_id}&tab=${location.zone_id ? "zones" : "pending"}${location.zone_id ? `&focus_zone_id=${location.zone_id}` : ""}`} className="inline-block text-sm text-blue-700 underline">Inspect the original reported location</Link>
    {location.geometry_sha256 && <details className="text-xs text-slate-500"><summary className="cursor-pointer">Saved section fingerprint</summary><p className="mt-1 break-all">{location.geometry_sha256}</p></details>}
    {item.review && <div className="space-y-1 text-sm text-slate-600"><p className="font-medium text-slate-700">Reviewed {new Date(item.review.reviewed_at).toLocaleString()} by User #{item.review.reviewer_id}</p><p className="whitespace-pre-wrap break-words">{item.review.evidence_text}</p><p>Same road section verified: {item.review.same_location_verified ? "Yes" : "No"}</p></div>}
    {item.review_state === "pending" && item.user_id === userId && <p className="text-sm text-slate-600">Another staff member must review your own follow-up.</p>}
    {item.review_state === "pending" && canReview && item.user_id !== userId && <form onSubmit={submitReview} className="space-y-3 border-t border-slate-100 pt-3">
      <fieldset disabled={mutation.isPending} className="space-y-3">
        <Select className="sm:max-w-xs" label="Evidence review decision" value={decision} onChange={(event) => { mutation.reset(); setDecision(String(event.target.value) as typeof decision); }} options={[{ value: "", label: "Choose a decision" }, { value: "accepted", label: "Accept evidence" }, { value: "rejected", label: "Reject evidence" }]} />
        <div className="space-y-1"><label htmlFor={`${id}-notes`} className="text-sm font-medium text-slate-700">Review evidence and reason</label><textarea id={`${id}-notes`} required minLength={10} maxLength={2000} rows={3} value={evidence} onChange={(event) => { mutation.reset(); setEvidence(event.target.value); }} placeholder="Describe the evidence checked, location match, and decision." className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-100" /></div>
        <label className="flex items-start gap-2 text-sm text-slate-700"><input type="checkbox" required={decision === "accepted"} checked={sameLocation} onChange={(event) => { mutation.reset(); setSameLocation(event.target.checked); }} className="mt-1 h-4 w-4 shrink-0 accent-blue-600" /><span>I verified the evidence concerns the exact same saved road section. Required to accept.</span></label>
      </fieldset>
      {mutation.isError && <p role="alert" className="text-sm text-red-700">{mutation.error.message || "Could not record this review. Try again."}</p>}
      <Button type="submit" className="w-full sm:w-auto" disabled={mutation.isPending || mutation.isSuccess || !decision || (decision === "accepted" && !sameLocation)}>{mutation.isPending ? "Saving review…" : mutation.isSuccess ? "Review saved" : "Save evidence review"}</Button>
    </form>}
  </article>;
}
