"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ArrowUpRight, ChevronDown } from "lucide-react";
import { Button, RecordTimeline, Skeleton } from "@/shared/ui";
import { getNewsArticle, type NewsArticleDetail, type NewsRun } from "./newsApi";
import { newsDate, processingLabels } from "./newsPresentation";

export function NewsProcessingDetails({ articleId, currentRunId, presentation = "disclosure", onInspectRun }: { articleId: number; currentRunId?: number; presentation?: "disclosure" | "panel"; onInspectRun?: (runId: number, opener: HTMLButtonElement) => void }) {
  const [open, setOpen] = useState(false);
  const [selectedRunId, setSelectedRunId] = useState<number | null>(null);
  const query = useQuery({ queryKey: ["news-article", articleId], queryFn: ({ signal }) => getNewsArticle(articleId, signal), enabled: presentation === "panel" || open, retry: false, refetchOnWindowFocus: false });
  const content = <section aria-label="Processing history" className="space-y-3">
    <div className={presentation === "panel" ? "sticky top-0 z-10 bg-slate-50 pb-3" : ""}><h3 className="text-sm font-bold text-slate-900">Processing history</h3><p className="mt-1 text-xs leading-5 text-slate-500">A record of when this article was extracted.</p>{query.data && <p className="mt-1 text-xs text-slate-500">{query.data.runs.length} of {query.data.history_total} saved records</p>}</div>
    {query.isPending && <div role="status" aria-label="Loading processing history"><Skeleton className="h-16 w-full" /><Skeleton className="mt-3 h-16 w-full" /></div>}
    {query.isError && <><p role="alert" className="text-sm text-red-800">Processing history could not be loaded. {query.error.message}</p><Button size="sm" variant="outline" onClick={() => void query.refetch()}>Retry history</Button></>}
    {query.data && <>
      <RecordTimeline emptyMessage="No processing history recorded." entries={query.data.runs.map((run) => ({
        id: run.id,
        label: processingLabels[run.status],
        timestamp: newsDate(run.completed_at ?? run.started_at ?? run.created_at),
        description: <div className="space-y-1">{run.id === currentRunId && <p className="text-[11px] font-medium text-blue-700">Used for this flood card</p>}<p className="text-xs text-slate-600">{run.attempt_count} attempt{run.attempt_count === 1 ? "" : "s"}{run.result ? ` · ${run.result.claims.length} extracted mention${run.result.claims.length === 1 ? "" : "s"}` : ""}</p>{run.error_code && <p className="break-words text-xs text-red-700">{run.error_code}</p>}{run.result?.is_metadata_only && <p className="text-xs text-amber-800">Article metadata only</p>}{run.result?.errors.length ? <p className="text-xs text-amber-800">Processing issues recorded</p> : null}</div>,
        content: <><Button size="sm" variant="ghost" className="min-h-11 gap-1.5 px-0 text-blue-700" aria-label={!onInspectRun && selectedRunId === run.id ? `Close extraction #${run.id}` : `View extraction #${run.id}`} aria-expanded={onInspectRun ? undefined : selectedRunId === run.id} onClick={(event) => { if (onInspectRun) onInspectRun(run.id, event.currentTarget); else setSelectedRunId((current) => current === run.id ? null : run.id); }}>{!onInspectRun && selectedRunId === run.id ? "Hide record details" : "View details"}{onInspectRun ? <ArrowUpRight aria-hidden="true" className="size-3.5" /> : <ChevronDown aria-hidden="true" className={`size-3.5 transition-transform ${selectedRunId === run.id ? "rotate-180" : ""}`} />}</Button>{!onInspectRun && selectedRunId === run.id && <ExtractionRecord run={run} data={query.data!} isCurrent={run.id === currentRunId} />}</>,
      }))} />
    </>}
  </section>;
  return presentation === "panel" ? content : <details className="text-sm text-slate-600" onToggle={(event) => setOpen(event.currentTarget.open)}><summary className="cursor-pointer py-2 font-semibold">More details</summary>{open && <div className="mt-3">{content}</div>}</details>;
}

function ExtractionRecord({ run, data, isCurrent }: { run: NewsRun; data: NewsArticleDetail; isCurrent: boolean }) {
  const version = data.versions.find((item) => item.id === run.article_version_id);
  return <div className="mt-4 space-y-3 text-xs text-slate-600">
    {run.error_code && <p role="alert" className="break-words text-red-800">Processing failed: {run.error_code}</p>}
    {run.result?.is_metadata_only && <p className="text-amber-800">Only article metadata was processed.</p>}
    {run.result?.errors.length ? <p role="alert" className="text-red-800">Processing issues: {run.result.errors.join("; ")}</p> : null}
    {version && !isCurrent && <><p className="break-words font-semibold text-slate-800">Captured article: {version.input_snapshot.title}</p><p>Article published: {newsDate(version.input_snapshot.published_at)}</p></>}
    {run.result?.claims.length === 0 && <p>No flood locations extracted.</p>}
    {(data.flood_summaries[run.id] ?? []).length > 0 && <details><summary className="min-h-11 cursor-pointer py-3 font-semibold">Extracted locations ({run.result?.claims.length})</summary><ul className="divide-y divide-slate-100">{(data.flood_summaries[run.id] ?? []).map((summary, index) => <li key={index} className="space-y-1 py-3"><h4 className="break-words text-sm font-semibold text-slate-800">{summary.location}</h4>{summary.area && <p className="break-words">{summary.area}</p>}{summary.location_qualifier && <p className="break-words">{summary.location_qualifier}</p>}<dl className="mt-2 space-y-1"><div><dt className="inline text-slate-500">Water level: </dt><dd className="inline">{summary.water_level}</dd></div><div><dt className="inline text-slate-500">Flood time: </dt><dd className="inline">{newsDate(summary.flood_time, "Not stated in article")}</dd></div></dl>{summary.reading_reason && <p className="text-amber-800">Needs checking: {summary.reading_reason}</p>}<details><summary className="min-h-11 cursor-pointer py-3 font-medium">Supporting sentence</summary><blockquote className="whitespace-pre-wrap break-words border-l-2 border-blue-200 pl-3 text-xs leading-6">{run.result?.claims[index]?.evidence_sentence}</blockquote></details></li>)}</ul></details>}
    {version?.input_snapshot.article_text && !isCurrent && <details><summary className="min-h-11 cursor-pointer py-3 font-semibold">Captured article text</summary><p className="mt-2 whitespace-pre-wrap break-words text-sm leading-7">{version.input_snapshot.article_text}</p></details>}
    <details><summary className="min-h-11 cursor-pointer py-3 font-semibold">Technical details</summary><p className="mt-2 break-all">Extraction #{run.id} · Input #{run.article_version_id}<br />{run.pipeline_version}<br />Captured: {newsDate(version?.created_at)}<br />Started: {newsDate(run.started_at)}<br />Completed: {newsDate(run.completed_at)}{run.next_attempt_at && <><br />Next attempt: {newsDate(run.next_attempt_at)}</>}</p></details>
  </div>;
}
