"use client";

import { useCallback, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Eye, FileText, RefreshCw, Search } from "lucide-react";
import { Button, Card, CardContent, Input, Pagination, Select, Skeleton } from "@/shared/ui";
import { getNewsArticles, type NewsArticleFilters } from "./newsApi";
import { bodyLabels, newsDate, processingLabels } from "./newsPresentation";
import { NewsArticleDialog } from "./NewsArticleDialog";

const initialFilters: NewsArticleFilters = { page: 1, search: "", publisher: "", body: "", processing: "", order: "recently_seen" };

export function NewsArticles({ active }: { active: boolean }) {
  const [filters, setFilters] = useState(initialFilters);
  const [search, setSearch] = useState("");
  const [articleId, setArticleId] = useState<number | null>(null);
  const query = useQuery({ queryKey: ["news-articles", filters], queryFn: ({ signal }) => getNewsArticles(filters, signal), enabled: active, retry: false, staleTime: 30_000, refetchOnWindowFocus: false });
  const trigger = useRef<HTMLButtonElement | null>(null);
  const closeDetail = useCallback(() => {
    setArticleId(null);
    trigger.current?.focus({ preventScroll: true });
  }, []);
  const changeFilter = (name: keyof NewsArticleFilters, value: string | number) => setFilters((current) => ({ ...current, [name]: value, page: 1 }));

  return <section aria-label="Articles" className={active ? "space-y-4" : "hidden"}>
    <Card className="shadow-sm"><CardContent className="space-y-4 p-4 sm:p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div><h2 className="font-bold text-gray-900">News articles</h2><p className="mt-1 text-xs text-gray-500">Original publisher stories. Open an article to read it or see the locations it mentions.</p></div>
        <div className="flex gap-2">
          <Button size="sm" variant="ghost" onClick={() => { setSearch(""); setFilters(initialFilters); }}>Clear filters</Button>
          <Button size="sm" variant="outline" onClick={() => void query.refetch()} disabled={query.isFetching} className="gap-1.5"><RefreshCw className="size-3.5" aria-hidden="true" />Refresh articles</Button>
        </div>
      </div>
      <form onSubmit={(event) => { event.preventDefault(); changeFilter("search", search); }} className="flex gap-2">
        <Input aria-label="Search articles" placeholder="Search title or excerpt" maxLength={200} value={search} onChange={(event) => setSearch(event.target.value)} leftIcon={<Search className="size-4" />} />
        <Button size="md" type="submit" variant="outline">Search</Button>
      </form>
      <details className="text-sm text-slate-600"><summary className="cursor-pointer font-semibold">Filter articles</summary><div className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Select label="Publisher" value={filters.publisher} onChange={(event) => changeFilter("publisher", event.target.value)} options={[{ value: "", label: "All publishers" }, ...(query.data?.publishers ?? []).map((item) => ({ value: item.id, label: item.label }))]} />
        <Select label="Article body" value={filters.body} onChange={(event) => changeFilter("body", event.target.value)} options={[{ value: "", label: "All body states" }, ...Object.entries(bodyLabels).map(([value, label]) => ({ value, label }))]} />
        <Select label="Processing status" value={filters.processing} onChange={(event) => changeFilter("processing", event.target.value)} options={[{ value: "", label: "All processing states" }, ...Object.entries(processingLabels).map(([value, label]) => ({ value, label }))]} />
        <Select label="Order articles" value={filters.order} onChange={(event) => changeFilter("order", event.target.value)} options={[{ value: "recently_seen", label: "Recently collected first" }, { value: "publication_newest", label: "Newest publication first" }]} />
      </div></details>
    </CardContent></Card>
    {query.isPending ? <div aria-label="Loading articles" role="status" className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{[0, 1, 2].map((item) => <Card key={item} className="shadow-sm"><CardContent className="space-y-3 p-5"><Skeleton className="h-4 w-28" /><Skeleton className="h-6 w-full" /><Skeleton className="h-20 w-full" /></CardContent></Card>)}</div>
      : query.isError ? <Card className="border-red-200 bg-red-50 shadow-sm"><CardContent className="space-y-3 p-5"><p role="alert" className="text-sm text-red-800">Articles could not be loaded. {query.error.message}</p><Button size="sm" variant="outline" onClick={() => void query.refetch()}>Retry articles</Button></CardContent></Card>
      : query.data && <>
        <p role="status" className="text-xs text-gray-500">{query.data.total} saved article{query.data.total === 1 ? "" : "s"} match these filters · Page {query.data.page} of {query.data.pages}</p>
        {query.data.items.length === 0 ? <Card className="shadow-sm"><CardContent className="flex items-start gap-3 p-6"><FileText className="size-5 shrink-0 text-gray-400" /><div><h3 className="text-sm font-semibold">No saved articles match these filters.</h3><p className="mt-1 text-sm text-gray-500">Only persisted articles appear here. Discovery previews are not saved articles.</p></div></CardContent></Card>
          : <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{query.data.items.map((article) => <Card key={article.id} className="flex flex-col shadow-sm"><CardContent className="flex flex-1 flex-col gap-3 p-5">
            <p className="text-xs font-semibold text-blue-700">{article.publisher}</p>
            <h3 className="break-words text-base font-bold leading-snug">{article.title}</h3>
            {article.excerpt && <p className="line-clamp-2 break-words text-sm leading-6 text-gray-500">{article.excerpt}</p>}
            <dl className="mt-auto space-y-2 text-xs"><div><dt className="text-gray-400">Article published</dt><dd className="mt-0.5 text-gray-700">{newsDate(article.published_at, "Publication time unavailable")}</dd></div><div className="flex flex-wrap gap-2"><dt className="sr-only">Article text and processing</dt>{article.body_status !== "available" && <dd className="rounded-full bg-amber-50 px-2 py-1 text-amber-800">{bodyLabels[article.body_status]}</dd>}<dd className={`rounded-full px-2 py-1 ${article.processing_status === "failed" ? "bg-red-50 text-red-700" : "bg-gray-100 text-gray-700"}`}>{processingLabels[article.processing_status]}</dd></div></dl>
            {article.article_error && <p className="break-words text-xs text-red-700">{article.article_error}</p>}
            <Button size="sm" variant="outline" className="mt-1 w-full gap-2" onClick={(event) => { trigger.current = event.currentTarget; setArticleId(article.id); }} aria-label={`View article: ${article.title}`}><Eye className="size-3.5" aria-hidden="true" />View article</Button>
          </CardContent></Card>)}</div>}
        <Pagination page={query.data.page} totalPages={query.data.pages} disabled={query.isFetching} onPageChange={(page) => setFilters((current) => ({ ...current, page }))} />
      </>}
    {articleId !== null && <NewsArticleDialog key={articleId} articleId={articleId} onClose={closeDetail} />}
  </section>;
}
