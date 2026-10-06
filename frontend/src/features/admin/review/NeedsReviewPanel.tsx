import { useEffect, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, RefreshCw, Search, SlidersHorizontal } from "lucide-react";
import { Input, Select, Pagination } from "@/shared/ui";
import { SpatialPanelButton as Button } from "../components/FloodRecordSummary";
import { PendingReportsPanel } from "../components/PendingReportsPanel";
import type { ComponentProps } from "react";
import { getReviewDetail, getReviewPage, type PlacementEnvelope, type ReviewSource } from "./reviewApi";
import type { FloodReport } from "../adminApi";
import { NewsReviewEvidence } from "./NewsReviewEvidence";
import { ReviewQueueCard } from "./ReviewQueueCard";
import { RelatedReviewReports } from "./RelatedReviewReports";

type ReportActions = Pick<ComponentProps<typeof PendingReportsPanel>, "onInfoClick" | "onOpenMergeWorkspace" | "onRequestReject" | "approveMutation">;

// Keep a selected location visible even when another source has no matching facet.
function locationOptions(label: string, values: string[] = [], selected = "") {
  const displayed = selected && !values.includes(selected) ? [selected, ...values] : values;
  return [{ value: "", label }, ...displayed.map((value) => ({ value, label: value }))];
}

export function NeedsReviewPanel({ active, selectedKey, onSelect, onReport, onPreview, selectedCandidate,
  onCandidate, onCount, layerError, ...actions }: ReportActions & {
  active: boolean; selectedKey: string | null; onSelect: (key: string | null) => void;
  onReport: (report: FloodReport | null) => void; onPreview: (data: PlacementEnvelope | null) => void;
  selectedCandidate: string | null; onCandidate: (id: string | null) => void;
  onCount: (total: number | undefined) => void; layerError: string | null;
}) {
  const [source, setSource] = useState<ReviewSource>("all");
  const [page, setPage] = useState(1);
  const [memberPage, setMemberPage] = useState(1);
  const [search, setSearch] = useState("");
  const [q, setQ] = useState("");
  const [city, setCity] = useState("");
  const [barangay, setBarangay] = useState("");
  const [severity, setSeverity] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  useEffect(() => {
    const timer = setTimeout(() => { setQ(search); setPage(1); }, 300);
    return () => clearTimeout(timer);
  }, [search]);
  const filters = { q, city, barangay, severity };
  const clearFilters = () => { setSearch(""); setQ(""); setCity(""); setBarangay(""); setSeverity(""); setPage(1); };
  const hasFilters = !!(search || city || barangay || severity);
  const queryClient = useQueryClient();
  const opener = useRef<HTMLButtonElement | null>(null);
  const queue = useQuery({ queryKey: ["spatial-review", source, page, filters],
    queryFn: ({ signal }) => getReviewPage(source, page, signal, filters), enabled: active,
    retry: false, refetchInterval: active ? 15_000 : false });
  const detail = useQuery({ queryKey: ["spatial-review-detail", selectedKey],
    queryFn: ({ signal }) => getReviewDetail(selectedKey!, signal), enabled: active && selectedKey !== null,
    retry: false, refetchInterval: active && selectedKey ? 30_000 : false });
  useEffect(() => { onCount(queue.isError ? undefined : queue.data?.counts.all); }, [queue.data, queue.isError, onCount]);
  useEffect(() => {
    onReport(active ? detail.data?.report ?? null : null);
    return () => onReport(null);
  }, [active, detail.data, onReport]);
  useEffect(() => {
    if (!selectedKey) opener.current?.focus();
  }, [selectedKey]);
  const refresh = () => {
    void queryClient.invalidateQueries({ queryKey: ["spatial-review"] });
    void queryClient.invalidateQueries({ queryKey: ["spatial-review-detail"] });
    void queryClient.invalidateQueries({ queryKey: ["spatial-review-members"] });
  };
  return <section aria-label="Needs Review" className="flex min-h-0 flex-1 flex-col overflow-hidden">
    <div className={`${selectedKey ? "hidden" : "flex"} min-h-0 flex-1 flex-col`}>
      <div className="flex items-center gap-2 border-b border-slate-100 p-3"><div className="min-w-0 flex-1">
        <div role="group" aria-label="Review source" className="flex flex-wrap gap-1">{([
          ["all", "All"], ["user_reports", "User Reports"], ["news_claims", "News Claims"],
        ] as const).map(([value, label]) => <Button key={value} size="sm" variant={source === value ? "primary" : "ghost"}
          className="px-2 text-xs" aria-pressed={source === value} onClick={() => { setSource(value); setPage(1); }}>
          {label}{queue.data && !queue.isError && <span className="ml-1">{queue.data.counts[value]}</span>}
        </Button>)}</div></div><Button variant="ghost" className="px-2 max-md:min-w-11" aria-label="Refresh review queue" disabled={queue.isFetching} onClick={refresh}><RefreshCw className="size-4" /></Button></div>
      <div className="min-h-0 flex-1 overflow-y-auto pb-[calc(var(--bottom-nav-height)+env(safe-area-inset-bottom))] md:pb-3">
        <div className="space-y-2 border-b border-slate-100 p-3">
          <div className="flex items-center gap-2"><Input type="search" aria-label="Search review queue" placeholder="Search location, report or evidence" maxLength={120} value={search} onChange={(event) => setSearch(event.target.value)} leftIcon={<Search className="size-4" />} className="text-xs shadow-none" />
            <Button variant="outline" aria-expanded={showFilters} aria-controls="review-filters" onClick={() => setShowFilters(!showFilters)} className="gap-1.5 px-2"><SlidersHorizontal className="size-3.5" />Filters</Button></div>
          {showFilters && <div id="review-filters" className="grid grid-cols-2 gap-2">
            <Select className="[&_button>span]:truncate [&_button>span]:min-w-0 max-md:[&_button]:min-h-11" ariaLabel="Filter by city" label="City" value={city} options={locationOptions("All cities", queue.data?.facets?.cities, city)} onChange={(event) => { setCity(String(event.target.value)); setBarangay(""); setPage(1); }} />
            <Select className="[&_button>span]:truncate [&_button>span]:min-w-0 max-md:[&_button]:min-h-11" ariaLabel="Filter by barangay" label="Barangay" disabled={!city} value={barangay} options={city ? locationOptions("All barangays", queue.data?.facets?.barangays, barangay) : [{ value: "", label: "Select a city first" }]} onChange={(event) => { setBarangay(String(event.target.value)); setPage(1); }} />
            <Select className="[&_button>span]:truncate [&_button>span]:min-w-0 max-md:[&_button]:min-h-11" ariaLabel="Filter by severity" label="Severity" value={severity} options={[{ value: "", label: "All severities" }, { value: "low", label: "Low" }, { value: "medium", label: "Medium" }, { value: "high", label: "High" }, { value: "extreme", label: "Extreme" }, { value: "unknown", label: "Unassessed" }]} onChange={(event) => { setSeverity(String(event.target.value)); setPage(1); }} />
          </div>}
          {hasFilters && <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500"><span>{[city, barangay, severity].filter(Boolean).join(" · ") || "Search applied"}</span><Button variant="ghost" onClick={clearFilters}>Clear filters</Button></div>}
        </div>
        {queue.isPending && <p role="status" className="p-4 text-sm text-slate-500">Loading review queue…</p>}
        {queue.isError && <div role="alert" className="space-y-3 p-4 text-sm text-red-800"><p>Review queue could not be loaded. {queue.error.message}</p><Button variant="outline" onClick={refresh}>Retry review queue</Button></div>}
        {queue.data && !queue.isError && <><p className="px-4 pt-3 text-xs text-slate-500">{queue.data.item_total ?? queue.data.total} reports requiring review · {queue.data.total} review {queue.data.total === 1 ? "card" : "cards"}</p>
          {!queue.data.items.length && <p className="p-6 text-center text-sm text-slate-500">No items need review in this filter.</p>}
          <div className="space-y-3 p-3">{queue.data.items.map((item) => <ReviewQueueCard key={item.key} item={item} onInspect={(key, button) => { opener.current = button; setMemberPage(1); onSelect(key); }} />)}</div>
          <Pagination page={queue.data.page} totalPages={queue.data.pages} onPageChange={setPage} disabled={queue.isFetching} />
        </>}
      </div>
    </div>
    {selectedKey && <div className="flex min-h-0 flex-1 flex-col">
      <div className="flex items-center justify-between gap-2 border-b border-slate-100 px-3 py-2"><Button variant="ghost"  onClick={() => onSelect(null)}><ArrowLeft className="mr-2 size-4" />Back to queue</Button><Button variant="ghost" className="px-2 max-md:min-w-11" aria-label="Refresh review evidence" disabled={detail.isFetching} onClick={() => void detail.refetch()}><RefreshCw className="size-4" /></Button></div>
      {detail.isPending && <p role="status" className="p-4 text-sm text-slate-500">Loading review evidence…</p>}
      {detail.isError && <div role="alert" className="space-y-3 p-4 text-sm text-red-800"><p>Review evidence could not be loaded. {detail.error.message}</p><Button variant="outline" onClick={() => void detail.refetch()}>Retry evidence</Button></div>}
      {detail.data && !detail.isError && <div className="min-h-0 flex-1 overflow-y-auto pb-[calc(var(--bottom-nav-height)+env(safe-area-inset-bottom))] md:pb-3">
        {!detail.data.is_current_review && <p role="status" className="p-4 text-sm text-amber-800">This item no longer belongs to the current review queue. Its preserved evidence remains available for inspection.</p>}
        {detail.data.news && <NewsReviewEvidence key={selectedKey} detail={detail.data} active={active} selectedId={selectedCandidate} onSelect={onCandidate} onPreview={onPreview} layerError={layerError} />}
        {detail.data.report && <section aria-label="User report evidence"><PendingReportsPanel {...actions} pendingLoading={false} pendingReports={[detail.data.report]} filteredPendingReports={[detail.data.report]} selectedReportId={detail.data.report.id} setSelectedReportId={() => undefined} inspectionOnly={!detail.data.is_current_review} hideFilters /></section>}
        {detail.data.report && detail.data.is_current_review && <RelatedReviewReports {...actions} active={active} selectedKey={selectedKey} onSelect={onSelect} page={memberPage} onPageChange={setMemberPage} />}
      </div>}
    </div>}
  </section>;
}
