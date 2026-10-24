import { AlertTriangle } from "lucide-react";
import type { NewsFloodSummary } from "./newsApi";

const stateLabels = { missing: "Missing", uncertain: "Needs checking", conflicting: "Conflicting" };

/** The backend supplies review decisions; this component only presents them. */
export function NewsVerificationNotice({ summary }: { summary: NewsFloodSummary }) {
  if (!summary.verification_status || summary.verification_status === "not_assessed") {
    return <p className="text-xs text-slate-500">Verification status unavailable for this saved record.</p>;
  }
  if (!summary.verification_issues?.length) return null;
  return <section aria-label="Information needing verification" className="min-w-0 space-y-2">
    <span className="inline-flex max-w-full items-center gap-1.5 rounded-full bg-amber-100 px-2.5 py-1 text-xs font-semibold text-amber-900">
      <AlertTriangle className="size-3.5 shrink-0" aria-hidden="true" />Needs Verification
    </span>
    <ul aria-label="Fields needing verification" className="flex flex-wrap gap-1.5">
      {summary.verification_issues.map(issue => <li key={issue.field} className="min-w-0 max-w-full rounded-md bg-amber-50 px-2 py-1 text-xs leading-5 text-amber-900">
        <span className="break-words font-medium">{issue.label}</span><span> · {stateLabels[issue.state]}</span>
      </li>)}
    </ul>
    <details className="text-xs leading-5 text-slate-600">
      <summary className="min-h-11 cursor-pointer py-3 font-medium text-amber-900 focus-visible:outline-2 focus-visible:outline-blue-500">Why these need checking</summary>
      <ul className="space-y-2 pb-1">{summary.verification_issues.map(issue => <li key={issue.field} className="break-words"><strong>{issue.label}:</strong> {issue.reason}</li>)}</ul>
    </details>
  </section>;
}
