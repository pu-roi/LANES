"use client";

import { useEffect, useId, useRef, useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/hooks/useAuth";
import { Button, Input, Select } from "@/shared/ui";
import { getOwnerFollowups, ownerFollowupKey, submitFollowup, type FollowupCondition, type FollowupSubmissionPayload } from "./followupApi";

export function FollowupSubmission({ reportId }: { reportId: number }) {
  const { user } = useAuth();
  // Remount draft state when the authenticated account changes.
  return user ? <OwnerFollowupPanel key={`${user.id}:${reportId}`} reportId={reportId} userId={user.id} /> : null;
}

function OwnerFollowupPanel({ reportId, userId }: { reportId: number; userId: number }) {
  const queryClient = useQueryClient();
  const id = useId();
  const [expanded, setExpanded] = useState(false);
  const [condition, setCondition] = useState<FollowupCondition | "">("");
  const [observedAt, setObservedAt] = useState("");
  const [evidence, setEvidence] = useState("");
  const [depth, setDepth] = useState("");
  const [source, setSource] = useState("");
  const [sameLocation, setSameLocation] = useState(false);
  const [timezone, setTimezone] = useState("device local timezone");
  const [error, setError] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const attempt = useRef<FollowupSubmissionPayload | null>(null);
  const queryKey = ownerFollowupKey(userId, reportId);
  const followups = useQuery({ queryKey, queryFn: () => getOwnerFollowups(reportId), enabled: expanded, retry: false });
  useEffect(() => { setTimezone(Intl.DateTimeFormat().resolvedOptions().timeZone); }, []);
  const mutation = useMutation({
    mutationFn: (payload: FollowupSubmissionPayload) => submitFollowup(reportId, payload),
    retry: false,
    onSuccess: () => {
      setSubmitted(true);
      setError("");
      void queryClient.invalidateQueries({ queryKey });
      void queryClient.invalidateQueries({ queryKey: ["flood-follow-ups", "admin"] });
    },
    onError: (err) => setError(err instanceof Error ? err.message : "Could not save this follow-up. Try again."),
  });
  const draftChanged = () => {
    attempt.current = null;
    setSubmitted(false);
    setError("");
  };
  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!condition || !sameLocation || !followups.data?.can_submit || mutation.isPending || submitted) return;
    try {
      if (!attempt.current) {
        attempt.current = {
          request_id: crypto.randomUUID(),
          condition,
          observed_at: new Date(observedAt).toISOString(),
          evidence_text: evidence,
          depth_cm: depth === "" ? null : Number(depth),
          source_url: source === "" ? null : source,
          same_location_confirmed: true,
        };
      }
      setError("");
      mutation.mutate(attempt.current);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Choose a valid observation date and time.");
    }
  };

  return <section className="mt-4 space-y-3" aria-label={`Follow-ups for report ${reportId}`}>
    <Button type="button" variant="outline" size="sm" className="w-full sm:w-auto" aria-expanded={expanded} aria-controls={`${id}-panel`} onClick={() => setExpanded(!expanded)}>
      {expanded ? "Hide follow-ups" : "Record or view a flood follow-up"}
    </Button>
    {expanded && <div id={`${id}-panel`} className="space-y-4">
      <p className="text-sm text-slate-600">Record whether flooding remains or has subsided on this report’s exact road section. Each observation goes to staff for evidence review.</p>
      {followups.isPending && <p role="status" className="text-sm text-slate-500">Loading follow-ups…</p>}
      {followups.isError && <div role="alert" className="space-y-2 text-sm text-red-700"><p>{followups.error.message || "Could not load follow-ups."}</p><Button type="button" variant="outline" size="sm" onClick={() => void followups.refetch()}>Try loading again</Button></div>}
      {submitted && <p role="status" className="text-sm text-emerald-800">Follow-up saved and pending staff review. Recording this observation does not automatically clear the map.</p>}
      {followups.data && !followups.data.can_submit && <p role="status" className="text-sm text-slate-700">{followups.data.ineligibility_reason || "This report is not eligible for follow-up submission."}</p>}
      {followups.data?.can_submit && <form onSubmit={onSubmit} onChange={draftChanged} className="space-y-3">
        <fieldset disabled={mutation.isPending} className="space-y-3">
          <div className="grid min-w-0 gap-3 sm:grid-cols-2">
            <Select label="Observed condition" ariaLabel="Observed flood condition" value={condition} onChange={(event) => { draftChanged(); setCondition(String(event.target.value) as FollowupCondition); }} options={[{ value: "", label: "Choose a condition" }, { value: "still_flooded", label: "Still flooded" }, { value: "subsided", label: "Flooding has subsided" }]} />
            <Input type="datetime-local" label={`Observed at (${timezone})`} aria-label={`Observation date and time in ${timezone}`} required value={observedAt} onChange={(event) => setObservedAt(event.target.value)} />
          </div>
          <p className="text-xs text-slate-500">Enter when you observed the condition. The selected local time is sent with its timezone as UTC.</p>
          <div className="space-y-1"><label htmlFor={`${id}-evidence`} className="text-sm font-medium text-slate-700">What you observed and the evidence source</label><textarea id={`${id}-evidence`} required minLength={10} maxLength={2000} rows={3} value={evidence} onChange={(event) => setEvidence(event.target.value)} placeholder="Describe this road section, the condition, and how you confirmed it." className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-100" /></div>
          <div className="grid min-w-0 gap-3 sm:grid-cols-2">
            <Input type="number" min={0} max={1000} step="any" label="Water depth in cm (Optional)" aria-label="Water depth in centimetres, optional" value={depth} onChange={(event) => setDepth(event.target.value)} />
            <Input type="url" pattern="https://.*" maxLength={500} label="Evidence link (Optional)" aria-label="HTTPS evidence link, optional" placeholder="https://…" value={source} onChange={(event) => setSource(event.target.value)} />
          </div>
          <label className="flex items-start gap-2 text-sm text-slate-700"><input type="checkbox" required checked={sameLocation} onChange={(event) => setSameLocation(event.target.checked)} className="mt-1 h-4 w-4 shrink-0 accent-blue-600" /><span>I confirm this observation concerns the exact same road section as my original report.</span></label>
        </fieldset>
        {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
        <Button type="submit" className="w-full sm:w-auto" disabled={mutation.isPending || !condition || !sameLocation || submitted}>{mutation.isPending ? "Saving…" : submitted ? "Follow-up saved" : error && attempt.current ? "Retry same follow-up" : "Submit follow-up for review"}</Button>
      </form>}
      {followups.data && <div className="space-y-3">
        <h4 className="text-sm font-semibold text-slate-900">Recorded follow-ups</h4>
        {followups.data.follow_ups.length === 0 && <p className="text-sm text-slate-500">No follow-ups recorded yet.</p>}
        {followups.data.follow_ups.map((item) => <article key={item.id} className="space-y-1 border-t border-slate-100 pt-3 text-sm">
          <p className="font-medium text-slate-800">{item.condition === "still_flooded" ? "Still flooded" : "Flooding has subsided"} · <span className="capitalize">{item.review_state}</span></p>
          <p className="text-xs text-slate-500">Observed {new Date(item.observed_at).toLocaleString()} · Submitted {new Date(item.submitted_at).toLocaleString()}</p>
          <p className="whitespace-pre-wrap break-words text-slate-700">{item.evidence_text}</p>
          {item.depth_cm !== null && <p className="text-slate-600">Water depth: {item.depth_cm} cm</p>}
          {item.source_url?.startsWith("https://") && <a href={item.source_url} target="_blank" rel="noopener noreferrer" className="inline-block break-all text-blue-700 underline">Evidence source</a>}
          {item.review && <p className="whitespace-pre-wrap break-words text-slate-600">Staff review: {item.review.evidence_text}</p>}
        </article>)}
        {followups.data.follow_ups.length >= 100 && <p className="text-xs text-slate-500">Showing the latest 100 follow-ups.</p>}
      </div>}
    </div>}
  </section>;
}
