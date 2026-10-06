"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Calendar, Clock, ExternalLink, FileText } from "lucide-react";
import { Button, FloodDetailMetric } from "@/shared/ui";
import { getNewsArticle, type CapturedInput } from "./newsApi";
import { newsDate, publisherLink } from "./newsPresentation";

export function NewsSourceArticle({ source, publisher, savedAt, articleId, presentation = "inspection" }: { source: CapturedInput; publisher: string; savedAt: string; articleId: number; presentation?: "inspection" | "reader" }) {
  const [collectionOpen, setCollectionOpen] = useState(false);
  const reader = presentation === "reader";
  const [textOpen, setTextOpen] = useState(reader);
  const query = useQuery({ queryKey: ["news-article", articleId], queryFn: ({ signal }) => getNewsArticle(articleId, signal), enabled: collectionOpen, retry: false, refetchOnWindowFocus: false });
  const href = publisherLink(source.canonical_url);
  return <section aria-label="Source article" className={reader ? "space-y-5" : "space-y-4"}>
    <div className="space-y-2">{reader && <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-blue-700"><FileText className="size-3.5" aria-hidden="true" />{publisher}</p>}<h3 className={`break-words font-bold text-slate-900 ${reader ? "text-xl leading-7 sm:text-2xl sm:leading-8" : "text-lg leading-snug"}`}>{source.title}</h3>{!reader && <p className="text-sm text-slate-500">{publisher}</p>}</div>
    {reader ? <div className="space-y-4 border-b border-slate-100 pb-5">
      <dl className="grid gap-x-6 gap-y-3 sm:grid-cols-2"><div><dt className="flex items-center gap-1.5 text-xs text-slate-500"><Calendar className="size-3.5 text-slate-400" aria-hidden="true" />Article published</dt><dd className="mt-1 text-sm font-medium text-slate-800">{newsDate(source.published_at, "Not stated in article")}</dd></div><div><dt className="flex items-center gap-1.5 text-xs text-slate-500"><Clock className="size-3.5 text-slate-400" aria-hidden="true" />Saved in LANES</dt><dd className="mt-1 text-sm font-medium text-slate-800">{newsDate(savedAt)}</dd></div></dl>
      <div className="flex flex-wrap items-center justify-between gap-3">{href && <a href={href} target="_blank" rel="noopener noreferrer" className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-blue-50 px-3 text-xs font-semibold text-blue-700 transition-colors hover:bg-blue-100 focus-visible:outline-2 focus-visible:outline-blue-500">Read on {publisher}<ExternalLink className="size-3.5" aria-hidden="true" /></a>}<p className="text-xs text-slate-500">Philippine time · UTC+8</p></div>
    </div> : <><div className="grid gap-3 sm:grid-cols-2">
      <FloodDetailMetric icon={<Calendar className="size-4" />} iconClassName="bg-blue-100 text-blue-600" label="Article published" value={newsDate(source.published_at, "Not stated in article")} />
      <FloodDetailMetric icon={<Clock className="size-4" />} iconClassName="bg-violet-100 text-violet-600" label="Saved in LANES" value={newsDate(savedAt)} />
    </div>
    <p className="text-xs text-slate-500">Times shown in Philippine time. Publication and saving dates are separate from the flood observation time.</p>
    {href && <a href={href} target="_blank" rel="noopener noreferrer" className="inline-flex min-h-11 items-center gap-1.5 text-sm font-semibold text-blue-700 underline underline-offset-4">Read on {publisher}<ExternalLink className="size-3.5" aria-hidden="true" /></a>}
    </>}
    {source.excerpt && (!reader || !source.article_text) && <p className="break-words text-sm leading-6 text-slate-600">{source.excerpt}</p>}
    {source.article_text ? reader ? <article aria-label="Full article text" className="space-y-3"><h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500">Full article text</h4><p className="whitespace-pre-wrap break-words text-[15px] leading-8 text-slate-700">{source.article_text}</p></article> : <details open={textOpen} onToggle={(event) => setTextOpen(event.currentTarget.open)} className="text-sm text-slate-600"><summary className="min-h-11 cursor-pointer py-3 font-semibold text-slate-800">Full article text</summary><p className="mt-2 whitespace-pre-wrap break-words leading-7">{source.article_text}</p></details> : <p className="text-sm text-amber-800">Full article text unavailable.</p>}
    <details onToggle={(event) => setCollectionOpen(event.currentTarget.open)} className="text-sm text-slate-600"><summary className="min-h-11 cursor-pointer py-3 font-semibold">Collection details</summary>
      {collectionOpen && <div className="mt-3 space-y-2 break-words text-xs">
        {query.isPending && <p role="status">Loading collection details…</p>}
        {query.isError && <><p role="alert" className="text-red-800">Collection details could not be loaded. {query.error.message}</p><Button size="sm" variant="outline" onClick={() => void query.refetch()}>Retry collection details</Button></>}
        {query.data && <><p>First saved: {newsDate(query.data.article.first_seen_at)}</p><p>Last seen: {newsDate(query.data.article.last_seen_at)}</p><p>Latest retrieval attempt: {newsDate(query.data.article.fetched_at)}</p>{query.data.article.article_error && <p role="alert" className="text-red-800">Retrieval failed: {query.data.article.article_error}</p>}{query.data.article.feed_entries.length ? query.data.article.feed_entries.map((entry, index) => <p key={index} className="break-all">Feed: {entry.feed_url}<br />GUID: {entry.feed_guid}</p>) : <p>No feed provenance recorded.</p>}<p>Retrieval attempt history is unavailable.</p></>}
      </div>}
    </details>
  </section>;
}
