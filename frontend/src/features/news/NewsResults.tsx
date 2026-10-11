"use client";

import { useCallback, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Info, RefreshCw, Search } from "lucide-react";
import { Button, Card, CardContent, Input, Pagination, Select, Skeleton } from "@/shared/ui";
import { getNewsResults, type NewsResultFilters, type NewsResultItem } from "./newsApi";
import { newsDate } from "./newsPresentation";
import { NewsResultDialog } from "./NewsResultDialog";

const initialFilters: NewsResultFilters = { page: 1, search: "", publisher: "", condition: "", placement: "", order: "extraction_newest" };
const conditionOptions = [{ value: "active", label: "Flooding reported" }, { value: "rising", label: "Water rising" }, { value: "receding", label: "Water receding" }, { value: "subsided", label: "Floodwater subsided" }, { value: "unknown", label: "Condition not stated" }];
const placementOptions = [{ value: "bounded_candidate", label: "Needs map confirmation" }, { value: "ambiguous", label: "Several map locations" }, { value: "unresolved", label: "Exact location unknown" }, { value: "source_unavailable", label: "Map data unavailable" }, { value: "not_recorded", label: "Not checked" }];

export function NewsResults({ active, defaultSearch = "" }: { active: boolean; defaultSearch?: string }) {
  const [filters, setFilters] = useState({ ...initialFilters, search: defaultSearch });
  const [search, setSearch] = useState(defaultSearch);
  const [selected, setSelected] = useState<NewsResultItem | null>(null);
  const trigger = useRef<HTMLButtonElement | null>(null);
  const query = useQuery({ queryKey: ["news-results", filters], queryFn: ({ signal }) => getNewsResults(filters, signal), enabled: active, retry: false, staleTime: 30_000, refetchOnWindowFocus: false });
  const closeDetail = useCallback(() => { setSelected(null); trigger.current?.focus({ preventScroll: true }); }, []);
  const changeFilter = (name: keyof NewsResultFilters, value: string | number) => setFilters((current) => ({ ...current, [name]: value, page: 1 }));
  return <section aria-label="Flood Locations" className={active ? "space-y-4" : "hidden"}>
    <Card className="shadow-sm"><CardContent className="space-y-4 p-4 sm:p-5">
      <div className="flex flex-wrap items-start justify-between gap-3"><h2 className="font-bold text-gray-900">Reported flood locations</h2><div className="flex gap-2"><Button size="sm" variant="ghost" onClick={() => { setSearch(""); setFilters(initialFilters); }}>Clear filters</Button><Button size="sm" variant="outline" className="gap-1.5" disabled={query.isFetching} onClick={() => void query.refetch()}><RefreshCw className="size-3.5" aria-hidden="true" />Refresh</Button></div></div>
      <form onSubmit={(event) => { event.preventDefault(); changeFilter("search", search); }} className="flex gap-2"><Input aria-label="Search flood locations" placeholder="Search a location or article" maxLength={200} value={search} onChange={(event) => setSearch(event.target.value)} leftIcon={<Search className="size-4" />} /><Button type="submit" variant="outline" size="md">Search</Button></form>
      <details className="text-sm text-slate-600"><summary className="cursor-pointer font-semibold">Filter flood locations</summary><div className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Select label="Publisher" value={filters.publisher} onChange={(event) => changeFilter("publisher", event.target.value)} options={[{ value: "", label: "All publishers" }, ...(query.data?.publishers ?? []).map((item) => ({ value: item.id, label: item.label }))]} />
        <Select label="Condition in article" value={filters.condition} onChange={(event) => changeFilter("condition", event.target.value)} options={[{ value: "", label: "All conditions" }, ...conditionOptions]} />
        <Select label="Map location" value={filters.placement} onChange={(event) => changeFilter("placement", event.target.value)} options={[{ value: "", label: "All locations" }, ...placementOptions]} />
        <Select label="Order locations" value={filters.order} onChange={(event) => changeFilter("order", event.target.value)} options={[{ value: "extraction_newest", label: "Recently processed" }, { value: "publication_newest", label: "Newest articles" }]} />
      </div></details>
    </CardContent></Card>
    {query.isPending && active && <div role="status" aria-label="Loading flood locations" className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{[0, 1, 2].map((id) => <Skeleton key={id} className="h-52 w-full" />)}</div>}
    {query.isError && <Card><CardContent className="space-y-3 p-5"><p role="alert" className="text-sm text-red-800">Flood locations could not be loaded. {query.error.message}</p><Button variant="outline" size="sm" onClick={() => void query.refetch()}>Retry locations</Button></CardContent></Card>}
    {query.data && <>
      <p role="status" className="text-xs text-slate-500">{query.data.total} reported flood locations · Page {query.data.page} of {query.data.pages}. Flood times refer to the article’s observations; they do not confirm flooding now.</p>
      {query.data.items.length === 0 ? <Card><CardContent className="p-6 text-sm text-slate-500">No reported flood locations match these filters. Open Collection status for articles awaiting processing or needing checking.</CardContent></Card> : <div className="grid items-stretch gap-4 md:grid-cols-2 xl:grid-cols-3">{query.data.items.map((result) => <Card key={result.key} className="shadow-sm"><CardContent className="flex h-full flex-col gap-3 p-4 sm:p-5">
        <div><h3 className="break-words text-base font-bold leading-snug">{result.summary.location}</h3>{result.summary.area && <p className="mt-1 break-words text-sm text-slate-500">{result.summary.area}</p>}{result.summary.location_qualifier && <p className="mt-1 break-words text-sm text-slate-600">{result.summary.location_qualifier}</p>}</div>
        <dl className="space-y-2"><div><dt className="text-xs text-slate-400">Water level</dt><dd className="mt-0.5 text-sm font-bold text-blue-700">{result.summary.water_level}</dd></div><div><dt className="text-xs text-slate-400">{result.summary.flood_time_label}</dt><dd className="mt-0.5 text-sm text-slate-700">{newsDate(result.summary.flood_time, "Not stated in article")}</dd></div></dl>
        <p className="text-xs text-slate-500">{result.summary.condition}</p>
        <p className="mt-auto text-xs text-slate-500">{result.publisher} · Article published {newsDate(result.published_at, "at an unknown time")}</p>
        <Button size="sm" variant="outline" className="min-h-11 w-full gap-2" aria-label={`Info: ${result.summary.location}, ${result.publisher}, ${newsDate(result.summary.flood_time, "time not stated")}`} onClick={(event) => { trigger.current = event.currentTarget; setSelected(result); }}><Info className="size-3.5" aria-hidden="true" />Info</Button>
      </CardContent></Card>)}</div>}
      <Pagination page={query.data.page} totalPages={query.data.pages} disabled={query.isFetching} onPageChange={(page) => setFilters((current) => ({ ...current, page }))} />
    </>}
    {selected && <NewsResultDialog key={selected.key} runId={selected.run_id} claimIndex={selected.claim_index} onClose={closeDetail} />}
  </section>;
}
