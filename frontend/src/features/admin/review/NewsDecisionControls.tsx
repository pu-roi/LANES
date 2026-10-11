"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Input, Select } from "@/shared/ui";
import { SpatialPanelButton as Button } from "../components/FloodRecordSummary";
import { newsDate } from "@/features/news/newsPresentation";
import { getNewsDecisionHistory, previewNewsDecision, submitNewsDecision, type NewsClaimDetail,
  type NewsDecisionOperation, type NewsDecisionRequest, type NewsDecisionEffect } from "./reviewApi";

const labels: Record<NewsDecisionOperation, string> = {
  correct: "Correct using audited evidence", defer: "Defer review", reject: "Reject / withdraw",
  reopen: "Reopen for review", clear: "Record matched clearance",
};

export function NewsDecisionControls({ claim }: { claim: NewsClaimDetail }) {
  const client = useQueryClient();
  const [operation, setOperation] = useState<NewsDecisionOperation | "">("");
  const [reason, setReason] = useState("");
  const [correction, setCorrection] = useState("");
  const [evaluation, setEvaluation] = useState("");
  const [deferred, setDeferred] = useState("");
  const [prepared, setPrepared] = useState<NewsDecisionRequest | null>(null);
  const [effect, setEffect] = useState<NewsDecisionEffect | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const resetPreview = () => { setPrepared(null); setEffect(null); setError(null); setSuccess(null); };
  const refresh = async () => {
    await Promise.all([
      client.invalidateQueries({ queryKey: ["spatial-review"] }),
      client.invalidateQueries({ queryKey: ["spatial-review-detail"] }),
      client.invalidateQueries({ queryKey: ["spatial-review-members"] }),
      client.invalidateQueries({ queryKey: ["publicNewsAlerts"] }),
      client.invalidateQueries({ queryKey: ["activeZones"] }),
      client.invalidateQueries({ queryKey: ["activeZonesMap"] }),
      client.invalidateQueries({ queryKey: ["adminZones"] }),
    ]);
  };
  const check = async () => {
    if (!operation) return;
    setBusy(true); setError(null); setSuccess(null);
    try {
      const request: NewsDecisionRequest = { request_id: crypto.randomUUID(), expected_revision: claim.revision,
        operation, reason, ...(evaluation ? { evaluation_id: Number(evaluation) } : {}),
        ...(correction && operation === "correct" ? { public_correction: correction } : {}),
        ...(deferred && operation === "defer" ? { deferred_until: new Date(deferred).toISOString() } : {}) };
      const preview = await previewNewsDecision(claim.case_id, request);
      setPrepared(request); setEffect(preview);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "This decision could not be checked. Nothing was saved.");
    } finally { setBusy(false); }
  };
  const submit = async () => {
    if (!prepared || !effect) return;
    setBusy(true); setError(null);
    try {
      const saved = await submitNewsDecision(claim.case_id, prepared);
      setSuccess(`Decision saved at revision ${saved.revision}.`);
      setPrepared(null); setEffect(null);
      await refresh();
    } catch (caught) {
      // Resolve an uncertain response by the same durable request identity.
      // A retry preserves the UUID and expected revision, preventing duplicates.
      try {
        const history = await getNewsDecisionHistory(claim.case_id);
        const saved = history.items.find((item) => item.request_id === prepared.request_id);
        if (saved) {
          setSuccess(`Decision saved at revision ${saved.revision}.`);
          setPrepared(null); setEffect(null); await refresh();
        } else {
          setError(`${caught instanceof Error ? caught.message : "The decision could not be saved."} Your draft is retained. Refresh evidence if the revision changed; retry uses the same request ID.`);
        }
      } catch {
        setError("Could not confirm whether the decision was saved. Your draft is retained. Retry uses the same request ID; refresh evidence before changing it.");
      }
    } finally { setBusy(false); }
  };
  const evidenceChoices = (claim.evaluation_options ?? []).filter((item) => operation === "clear"
    ? item.condition === "subsided" : ["active", "rising"].includes(item.condition));
  return <section aria-label="News decisions" className="space-y-3">
    <h3 className="text-sm font-semibold text-slate-900">News decision · revision {claim.revision}</h3>
    {!claim.allowed_actions.length && <p className="text-xs text-slate-500">Decision access is read-only.</p>}
    {!!claim.allowed_actions.length && <form className="space-y-3" onSubmit={(event) => { event.preventDefault(); void check(); }}>
      <fieldset disabled={busy} className="space-y-3">
        <Select label="Decision" ariaLabel="News decision" value={operation} options={[
          { value: "", label: "Choose a decision" }, ...claim.allowed_actions.map((value) => ({ value, label: labels[value] }))
        ]} onChange={(event) => { setOperation(String(event.target.value) as NewsDecisionOperation); setEvaluation(""); resetPreview(); }} />
        <label className="block text-xs font-medium text-slate-700">Internal reason
          <textarea aria-label="Internal news decision reason" required minLength={3} maxLength={2000} rows={3}
            value={reason} onChange={(event) => { setReason(event.target.value); resetPreview(); }}
            className="mt-1 w-full rounded-lg border border-slate-300 bg-white p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </label>
        {operation === "defer" && <Input label="Review again after" aria-label="Review again after" type="datetime-local" required
          value={deferred} onChange={(event) => { setDeferred(event.target.value); resetPreview(); }} />}
        {(operation === "correct" || operation === "clear") && <Select label="Audited evidence" ariaLabel="Audited evidence" value={evaluation}
          options={[{ value: "", label: "Choose audited evidence" }, ...evidenceChoices.map((item) => ({ value: String(item.evaluation_id),
            label: `Run ${item.run_id} · ${item.condition} · ${newsDate(item.observed_at)}` }))]}
          onChange={(event) => { setEvaluation(String(event.target.value)); resetPreview(); }} />}
        {operation === "correct" && <Input label="Public correction (optional)" aria-label="Public correction" maxLength={500}
          value={correction} onChange={(event) => { setCorrection(event.target.value); resetPreview(); }} />}
        <p className="text-xs text-slate-500">Internal reasons stay staff-only. Correction and clearance require audited source evidence.</p>
        <Button type="submit" variant="outline" disabled={!operation || ((operation === "correct" || operation === "clear") && !evaluation)}>
          {busy ? "Checking…" : "Check decision effect"}
        </Button>
      </fieldset>
    </form>}
    {effect && prepared && <div className="space-y-2 bg-slate-50 p-3 text-xs text-slate-700">
      <p>Server effect: {effect.status ?? effect.public_state.replaceAll("_", " ")} · {effect.review_state.replaceAll("_", " ")}</p>
      <p>Routing: {effect.affects_routing ? "zone coverage affected" : "no new routing zone"}. {effect.reason_code.replaceAll("_", " ")}</p>
      {prepared.expected_revision !== claim.revision && <p role="alert" className="text-amber-800">Evidence changed since this check. Check the decision again.</p>}
      <Button variant="primary" disabled={busy || prepared.expected_revision !== claim.revision} onClick={() => void submit()}>
        {busy ? "Saving…" : "Save news decision"}
      </Button>
    </div>}
    {error && <p role="alert" className="break-words text-xs text-red-800">{error}</p>}
    {success && <p role="status" className="text-xs text-emerald-800">{success}</p>}
    {!!claim.decisions.length && <details className="text-xs text-slate-600"><summary className="min-h-11 cursor-pointer py-3">Decision history ({claim.decisions.length} recent)</summary>
      <ol className="space-y-2">{claim.decisions.map((item) => <li key={item.id}>Revision {item.revision} · {item.operation} · {item.reason_code.replaceAll("_", " ")} · {newsDate(item.decided_at)}</li>)}</ol>
    </details>}
  </section>;
}
