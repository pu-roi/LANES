"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Button, Pagination, Skeleton } from "@/shared/ui";
import { getNewsTelemetry, type TelemetryKind } from "./newsApi";
import { newsDate, publisherLink } from "./newsPresentation";

export function NewsTelemetryHistory({ kind }: { kind: TelemetryKind }) {
  const [page, setPage] = useState(1);
  const query = useQuery({ queryKey: ["news-telemetry", kind, page], queryFn: ({ signal }) => getNewsTelemetry(kind, page, signal), staleTime: 30_000, retry: false, refetchOnWindowFocus: false });
  const label = kind === "discovery" ? "Discovery history" : "Fallback history";
  return <section aria-label={label} className="space-y-3 border-t border-slate-100 pt-5">
    <div className="flex flex-wrap items-center justify-between gap-3"><h3 className="text-sm font-bold text-slate-900">{label}</h3><Button size="sm" variant="outline" className="min-h-11" disabled={query.isFetching} onClick={() => void query.refetch()}>Refresh {label.toLowerCase()}</Button></div>
    <p className="text-xs leading-5 text-slate-500">Records begin after telemetry is enabled. Earlier attempts are not backfilled. Refresh reads saved history.</p>
    {query.isPending && <Skeleton className="h-24 w-full" aria-label={`Loading ${label.toLowerCase()}`} />}
    {query.isError && <p role="alert" className="text-sm text-red-800">{label} could not be loaded. {query.error.message} Use Refresh to retry.</p>}
    {query.data && <><p className="text-xs text-slate-500">{query.data.total} recorded attempts. Completion records the collection or lookup outcome; it does not confirm a flood.</p>{!query.data.items.length && <p className="text-sm text-slate-500">No {label.toLowerCase()} recorded yet.</p>}<div className="divide-y divide-slate-100">{query.data.items.map((item) => <article key={item.id} className="space-y-3 py-4">
      <div className="flex flex-wrap items-center justify-between gap-2"><h4 className="text-sm font-semibold text-slate-900">{kind === "discovery" ? `${item.trigger === "staff" ? "Staff" : "Collector"} discovery` : `Article #${item.article_id} lookup`}</h4><span className="text-xs font-semibold capitalize text-slate-700">{item.status}</span></div>
      <dl className="grid gap-2 text-xs sm:grid-cols-2"><div><dt className="text-slate-500">Started</dt><dd className="mt-1 text-slate-700">{newsDate(item.started_at)}</dd></div><div><dt className="text-slate-500">Finished</dt><dd className="mt-1 text-slate-700">{item.finished_at ? newsDate(item.finished_at) : "Not recorded; outcome unresolved"}</dd></div></dl>
      {item.error_code && <p className="break-words text-xs text-red-800">Recorded issue: {item.error_code.replaceAll("_", " ")}</p>}
      {item.retry_after_seconds !== null && <p className="text-xs text-slate-500">Provider retry delay recorded: {item.retry_after_seconds} seconds. This is the original response, not a live countdown.</p>}
      {kind === "discovery" && <details><summary className="min-h-11 cursor-pointer py-3 text-xs font-semibold text-slate-600">Feed outcomes ({item.feeds.length})</summary><div className="space-y-4">{item.feeds.map((feed) => <div key={`${feed.source_id}:${feed.feed_url}`} className="space-y-1 text-xs leading-5 text-slate-600"><p className="break-words font-semibold">{feed.source_id} · {feed.status}</p><SafeLead url={feed.feed_url} /><p>Entries seen: {feed.entries_seen} · Candidates saved: {feed.candidates_saved}</p><p>Body errors: {feed.body_errors} · Scope unresolved: {feed.scope_unresolved}</p>{feed.error_code && <p className="text-red-800">{feed.error_code.replaceAll("_", " ")}</p>}</div>)}</div></details>}
      {kind === "fallback" && <details><summary className="min-h-11 cursor-pointer py-3 text-xs font-semibold text-slate-600">Alternate leads ({item.leads.length}) · {item.retrieve_articles ? "Body retrieval requested" : "Link search only"}</summary><div className="space-y-4">{item.leads.map((lead) => <div key={lead.ordinal} className="space-y-1 text-xs leading-5 text-slate-600"><SafeLead url={lead.article_url} /><p>{lead.source_id ?? "Publisher not matched"} · {lead.retrieval_status.replaceAll("_", " ")}</p>{lead.assessment && <p>Assessment: {lead.assessment.replaceAll("_", " ")}</p>}{lead.error_code && <p className="text-red-800">{lead.error_code.replaceAll("_", " ")}</p>}</div>)}</div><p className="mt-3 text-xs text-slate-500">An alternate lead does not independently confirm this flood.</p></details>}
    </article>)}</div><Pagination page={query.data.page} totalPages={query.data.pages} disabled={query.isFetching} onPageChange={setPage} /></>}
  </section>;
}

function SafeLead({ url }: { url: string }) {
  const href = publisherLink(url);
  return href ? <a href={href} target="_blank" rel="noopener noreferrer" className="inline-block min-h-11 break-all py-2 text-blue-700 underline underline-offset-4">{url}</a> : <span className="break-all">{url}</span>;
}
