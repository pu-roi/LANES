import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { FloodLocationSummary } from "@/shared/ui";
import { NewsSourceArticle } from "@/features/news/NewsSourceArticle";
import { floodSummaryData } from "@/features/news/newsPresentation";
import { getPlacementPreview, type PlacementEnvelope, type ReviewDetail } from "./reviewApi";

import { SpatialPanelButton as Button } from "../components/FloodRecordSummary";

const reasonLabel = (value: string) => value.replaceAll("_", " ");

export function NewsReviewEvidence({ detail, active, selectedId, onSelect, onPreview, layerError }: {
  detail: ReviewDetail; active: boolean; selectedId: string | null; onSelect: (id: string | null) => void;
  onPreview: (data: PlacementEnvelope | null) => void; layerError: string | null;
}) {
  const news = detail.news!;
  const query = useQuery({ queryKey: ["news-placement", news.item.run_id, news.item.claim_index],
    queryFn: ({ signal }) => getPlacementPreview(news.item.run_id, news.item.claim_index, signal),
    enabled: active, staleTime: 5 * 60_000, retry: false, refetchOnWindowFocus: false });
  useEffect(() => {
    onPreview(active ? query.data ?? null : null);
    return () => onPreview(null);
  }, [active, query.data, onPreview]);
  const preview = query.data?.preview;
  return <div className="space-y-6 p-4">
    <div><p className="text-xs font-semibold uppercase tracking-wide text-blue-700">News claim · inspection only</p>
      <p className="mt-2 text-sm text-amber-800">{news.claim.action_rationale ?? "Incomplete or conflicting flood evidence."}</p>
      <p className="mt-2 text-xs text-slate-500">Placement suggestions do not confirm current flooding or change routing.</p></div>
    <FloodLocationSummary showPublication={false} data={floodSummaryData(news.item.summary, news.captured_input.published_at)} />
    <section aria-label="Reported evidence"><h3 className="text-sm font-semibold text-slate-900">Reported evidence</h3>
      <blockquote className="mt-2 whitespace-pre-wrap break-words text-sm leading-6 text-slate-700">{news.claim.evidence_sentence}</blockquote>
      {!!news.claim.uncertainty_reasons.length && <ul className="mt-2 list-disc space-y-1 pl-5 text-xs text-amber-800">{news.claim.uncertainty_reasons.map((reason) => <li key={reason}>{reasonLabel(reason)}</li>)}</ul>}
    </section>
    <section aria-label="Placement suggestions" className="space-y-3"><h3 className="text-sm font-semibold text-slate-900">Placement suggestions</h3>
      {query.isPending && <p role="status" className="text-sm text-slate-500">Checking placement…</p>}
      {query.isError && <div role="alert" className="space-y-2 text-sm text-red-800"><p>Placement could not be loaded. {query.error.message}</p><p className="text-xs">Requests are limited to three per minute. If limited, wait before retrying.</p><Button variant="outline" size="sm" disabled={query.isFetching} onClick={() => void query.refetch()}>Retry placement</Button></div>}
      {layerError && <p role="alert" className="text-sm text-red-800">{layerError}</p>}
      {preview && <><p className="text-sm text-slate-600">{reasonLabel(preview.reason)}</p>
        {preview.status === "source_unavailable" && <p role="alert" className="text-sm text-amber-800">An analytical source is unavailable. Any shown geometry is an unverified suggestion.</p>}
        {!preview.candidates.length && <p className="text-sm text-slate-500">No supported map geometry. Evidence remains available for review.</p>}
        {preview.candidates_truncated && <p className="text-xs text-amber-800">Showing {preview.candidates.length} of {preview.total_candidate_count} candidates. The candidate set is incomplete.</p>}
        <p className="text-xs text-blue-700">Blue dashed lines: placement suggestions. Select one to inspect; selection does not confirm it.</p>
        {selectedId && <Button variant="ghost" size="sm" onClick={() => onSelect(null)}>Show all suggestions</Button>}
        <div className="divide-y divide-slate-100">{preview.candidates.map((candidate, index) => <div key={candidate.candidate_id} className="py-3">
          <Button variant={selectedId === candidate.candidate_id ? "primary" : "outline"} className="w-full justify-start" aria-pressed={selectedId === candidate.candidate_id} onClick={() => onSelect(candidate.candidate_id)}>Inspect suggestion {index + 1} · {Math.round(candidate.approximate_length_m)} m</Button>
          <p className="mt-2 break-words text-xs text-slate-600">{candidate.kind === "reported_span" ? "Reported span" : "Road section"}{candidate.cross_streets.length ? ` · ${candidate.cross_streets.map((names) => names.join(" / ")).join(" — ")}` : ""}</p>
          {candidate.ambiguous_carriageway && <p className="mt-1 text-xs text-amber-800">Competing carriageways remain unresolved.</p>}
          <dl className="mt-2 space-y-1 text-xs text-slate-600">{[5, 25, 100].map((period) => <div key={period} className="flex justify-between gap-2"><dt>NOAH {period}-year modeled overlap</dt><dd>{candidate.modeled_overlap_fraction[String(period)] == null ? "Unavailable" : `${Math.round(candidate.modeled_overlap_fraction[String(period)] * 100)}%`}</dd></div>)}</dl>
          {preview.history_status === "available" && <details className="mt-2 text-xs text-slate-600"><summary className="min-h-11 cursor-pointer py-3">Pasig DRRMO matching records ({candidate.matching_history.length})</summary>{candidate.matching_history.length ? candidate.matching_history.map((row, rowIndex) => <p key={`${row.source_year}:${row.source_record_no}:${rowIndex}`} className="py-1">{row.source_year} · Record {row.source_record_no} · {[row.barangay, row.street, row.landmark].filter(Boolean).join(" · ")}</p>) : <p>No matching historical rows for this section.</p>}</details>}
        </div>)}</div>
        <p className="text-xs text-slate-500">Pasig DRRMO history: {preview.history_status === "not_applicable" ? "Not applicable to this location." : preview.history_status === "source_unavailable" ? "Unavailable; no historical support can be assumed." : `${preview.unmatched_history.length} unmatched records retained.`} NOAH scenarios and historical records support placement, not live flood status.</p>
        {!!preview.uncertainty_reasons.length && <ul className="list-disc space-y-1 pl-5 text-xs text-amber-800">{preview.uncertainty_reasons.map((reason) => <li key={reason}>{reasonLabel(reason)}</li>)}</ul>}
        <details className="text-xs text-slate-500"><summary className="min-h-11 cursor-pointer py-3">Placement source details</summary><div className="space-y-2 break-all"><p>OSM: {preview.osm_source_id ?? "Unavailable"} · Snapshot: {preview.osm_snapshot_at ?? "Unavailable"}</p><p>NOAH: {preview.noah_attribution ?? "Unavailable"}</p><p>OSM revision: {preview.osm_catalog_sha256 ?? "Unavailable"}</p><p>NOAH revision: {preview.noah_catalog_sha256 ?? "Unavailable"}</p><p>History revision: {preview.history_sha256 ?? "Not applicable"}</p><p>Placement revision: {query.data?.placement_revision}</p><p>Evidence revision: {news.pipeline_version}</p></div></details>
      </>}
    </section>
    <NewsSourceArticle source={news.captured_input} publisher={news.item.publisher} savedAt={news.item.saved_at} articleId={news.item.article_id} />
  </div>;
}
