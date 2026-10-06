import { useQuery } from "@tanstack/react-query";
import type { ComponentProps } from "react";
import { Pagination } from "@/shared/ui";
import { SpatialPanelButton as Button } from "../components/FloodRecordSummary";
import { PendingReportsPanel } from "../components/PendingReportsPanel";
import { getReviewDetail, getReviewMembers, type ReviewItem } from "./reviewApi";

type ReportActions = Pick<ComponentProps<typeof PendingReportsPanel>, "onInfoClick" | "onOpenMergeWorkspace" | "onRequestReject" | "approveMutation">;

function RelatedReport({ item, active, onSelect, ...actions }: ReportActions & {
  item: ReviewItem; active: boolean; onSelect: (key: string) => void;
}) {
  const detail = useQuery({ queryKey: ["spatial-review-detail", item.key],
    queryFn: ({ signal }) => getReviewDetail(item.key, signal), enabled: active,
    retry: false, refetchInterval: active ? 30_000 : false });
  const report = detail.data?.report;
  return <section aria-label={`${item.title} evidence`}>
    {detail.isPending && <p role="status" className="p-4 text-xs text-slate-500">Loading {item.title}…</p>}
    {detail.isError && <div role="alert" className="space-y-2 p-4 text-xs text-red-800"><p>{item.title} could not be loaded. {detail.error.message}</p><Button variant="outline" size="sm" onClick={() => void detail.refetch()}>Retry {item.title}</Button></div>}
    {detail.data && !detail.isError && report && <>
      {!detail.data.is_current_review && <p role="status" className="px-4 pt-3 text-xs text-amber-800">This report no longer belongs to the current review queue.</p>}
      <PendingReportsPanel {...actions} pendingLoading={false} pendingReports={[report]} filteredPendingReports={[report]}
        selectedReportId={null} setSelectedReportId={(id) => { if (id !== null) onSelect(`user_report:${id}`); }}
        inspectionOnly={!detail.data.is_current_review} hideFilters />
    </>}
  </section>;
}

export function RelatedReviewReports({ active, selectedKey, onSelect, page, onPageChange, ...actions }: ReportActions & {
  active: boolean; selectedKey: string; onSelect: (key: string) => void;
  page: number; onPageChange: (page: number) => void;
}) {
  const members = useQuery({ queryKey: ["spatial-review-members", selectedKey, page],
    queryFn: ({ signal }) => getReviewMembers(selectedKey, page, signal), enabled: active,
    retry: false, refetchInterval: active ? 15_000 : false });
  const rows = members.data?.items ?? [];
  if (members.data && !members.isError && members.data.total <= 1) return null;

  return <section aria-label="Related reports" className="border-t border-slate-100">
    <div className="px-4 py-3">
    <h3 className="text-sm font-semibold text-slate-900">Related reports</h3>
    <p className="mt-1 text-xs leading-5 text-slate-500">{members.data?.group_reason}</p>
    </div>
    {members.isPending && <p role="status" className="py-3 text-xs text-slate-500">Loading related reports…</p>}
    {members.isError && <div role="alert" className="space-y-2 py-3 text-xs text-red-800"><p>{members.error.message}</p><Button variant="outline" size="sm" onClick={() => void members.refetch()}>Retry related reports</Button></div>}
    {!members.isError && <div className="space-y-3">{rows.map((row) => row.key !== selectedKey && <RelatedReport key={row.key} item={row} active={active} onSelect={onSelect} {...actions} />)}</div>}
    {members.data && members.data.pages > 1 && !members.isError && <div className="max-md:[&_button]:min-h-11"><Pagination page={members.data.page} totalPages={members.data.pages} onPageChange={onPageChange} disabled={members.isFetching} /></div>}
  </section>;
}
