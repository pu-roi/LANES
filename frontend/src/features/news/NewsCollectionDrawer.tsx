"use client";

import { useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, RefreshCw, Search } from "lucide-react";
import { Button, Input, Pagination, RecordDetailsDialog, Select, Skeleton } from "@/shared/ui";
import { getNewsArticle, getNewsCollection, type NewsCollectionFilters } from "./newsApi";
import { newsDate } from "./newsPresentation";
import { NewsSourceArticle } from "./NewsSourceArticle";
import { NewsProcessingDetails } from "./NewsProcessingDetails";

const initialFilters: NewsCollectionFilters = { page: 1, search: "", publisher: "", status: "attention" };
const statusOptions = [
  { value: "attention", label: "Needs attention" }, { value: "all", label: "All saved articles" },
  { value: "needs_checking", label: "Needs checking" }, { value: "no_locations", label: "No flood locations" },
  { value: "processing_failed", label: "Processing failed" }, { value: "retrieval_failed", label: "Article retrieval failed" },
  { value: "missing_text", label: "Article text missing" }, { value: "waiting", label: "Waiting for processing" },
  { value: "processing", label: "Processing" }, { value: "ready", label: "Locations available" },
];

export function NewsCollectionDrawer({ onClose }: { onClose: () => void }) {
  const [filters, setFilters] = useState(initialFilters);
  const [search, setSearch] = useState("");
  const [articleId, setArticleId] = useState<number | null>(null);
  const opener = useRef<HTMLButtonElement | null>(null);
  const openerId = useRef<number | null>(null);
  const backButton = useRef<HTMLSpanElement | null>(null);
  const query = useQuery({ queryKey: ["news-collection", filters], queryFn: ({ signal }) => getNewsCollection(filters, signal), retry: false, refetchOnWindowFocus: false });
  const changeFilter = (next: Partial<NewsCollectionFilters>) => setFilters((current) => ({ ...current, ...next, page: 1 }));
  return <RecordDetailsDialog title="Collection status" subtitle="Saved articles awaiting processing or needing checking" closeLabel="Close collection status" onClose={onClose} placement="drawer">
    {articleId !== null ? <>
      <span ref={backButton}><Button size="sm" variant="ghost" className="min-h-11 gap-2" onClick={() => { setArticleId(null); requestAnimationFrame(() => opener.current?.focus({ preventScroll: true })); }}><ArrowLeft className="size-4" aria-hidden="true" />Back to collection</Button></span>
      <CollectionArticle articleId={articleId} />
    </> : <>
      {query.data && <p className="text-sm text-slate-600">Across all saved articles: <strong>{query.data.counts.needs_checking}</strong> need checking · <strong>{query.data.counts.no_locations}</strong> have no flood locations · <strong>{query.data.counts.processing_failed}</strong> failed processing.</p>}
      <form className="flex gap-2" onSubmit={(event) => { event.preventDefault(); changeFilter({ search }); }}><Input aria-label="Search collection" placeholder="Search saved articles" maxLength={200} value={search} onChange={(event) => setSearch(event.target.value)} leftIcon={<Search className="size-4" />} /><Button type="submit" variant="outline">Search</Button></form>
      <div className="grid gap-3 sm:grid-cols-2"><Select label="Collection state" value={filters.status} options={statusOptions} onChange={(event) => changeFilter({ status: event.target.value as NewsCollectionFilters["status"] })} /><Select label="Publisher" value={filters.publisher} options={[{ value: "", label: "All publishers" }, ...(query.data?.publishers ?? []).map((item) => ({ value: item.id, label: item.label }))]} onChange={(event) => changeFilter({ publisher: String(event.target.value) })} /></div>
      <div className="flex flex-wrap gap-2"><Button size="sm" variant="ghost" onClick={() => { setFilters(initialFilters); setSearch(""); }}>Clear filters</Button><Button size="sm" variant="outline" className="gap-2" disabled={query.isFetching} onClick={() => void query.refetch()}><RefreshCw className="size-4" aria-hidden="true" />Refresh collection</Button></div>
      {query.isPending && <div role="status" aria-label="Loading collection status" className="space-y-3"><Skeleton className="h-24 w-full" /><Skeleton className="h-24 w-full" /></div>}
      {query.isError && <div className="space-y-3"><p role="alert" className="text-sm text-red-800">Collection status could not be loaded. {query.error.message}</p><Button size="sm" variant="outline" onClick={() => void query.refetch()}>Retry collection</Button></div>}
      {query.data && <>
        <p role="status" className="text-xs text-slate-500">{query.data.total} saved articles match these filters · Page {query.data.page} of {query.data.pages}</p>
        {query.data.items.length === 0 && <p className="text-sm text-slate-500">No saved articles match this collection state.</p>}
        <div className="divide-y divide-slate-100">{query.data.items.map((article) => <article key={article.id} className="space-y-3 py-5 first:pt-0">
          <div className="flex flex-wrap items-center gap-2"><span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700">{article.collection_label}</span><span className="text-xs text-slate-500">{article.publisher}</span></div>
          <h3 className="break-words text-base font-bold leading-snug">{article.title}</h3>
          <p className="text-sm leading-6 text-slate-600">{article.collection_reason}</p>
          <p className="text-xs text-slate-500">{article.location_count} reported locations · {article.questionable_count} mentions need checking<br />Article published: {newsDate(article.published_at, "Not stated")}</p>
          {article.article_error && <p className="break-words text-xs text-red-800">{article.article_error}</p>}
          <span ref={(node) => { if (openerId.current === article.id) opener.current = node?.querySelector("button") ?? null; }}><Button size="sm" variant="outline" className="min-h-11" aria-label={`View article: ${article.title}`} onClick={(event) => { openerId.current = article.id; opener.current = event.currentTarget; setArticleId(article.id); requestAnimationFrame(() => backButton.current?.querySelector("button")?.focus({ preventScroll: true })); }}>View article</Button></span>
        </article>)}</div>
        <Pagination page={query.data.page} totalPages={query.data.pages} disabled={query.isFetching} onPageChange={(page) => setFilters((current) => ({ ...current, page }))} />
      </>}
    </>}
  </RecordDetailsDialog>;
}

function CollectionArticle({ articleId }: { articleId: number }) {
  const query = useQuery({ queryKey: ["news-article", articleId], queryFn: ({ signal }) => getNewsArticle(articleId, signal), retry: false, refetchOnWindowFocus: false });
  if (query.isPending) return <div role="status" aria-label="Loading article"><Skeleton className="h-48 w-full" /></div>;
  if (query.isError) return <div className="space-y-3"><p role="alert" className="text-sm text-red-800">Article details could not be loaded. {query.error.message}</p><Button size="sm" variant="outline" onClick={() => void query.refetch()}>Retry article</Button></div>;
  const data = query.data;
  const latest = data.runs[0];
  const version = data.versions.find((item) => item.id === latest?.article_version_id);
  const source = version?.input_snapshot ?? { ...data.article, publisher: data.article.publisher_source_id };
  return <div className="space-y-5">
    {data.article.article_error && <p role="alert" className="break-words text-sm text-red-800">Latest article retrieval failed: {data.article.article_error}</p>}
    <NewsSourceArticle articleId={articleId} source={source} publisher={data.publisher} savedAt={data.article.first_seen_at} />
    <NewsProcessingDetails articleId={articleId} />
  </div>;
}
