import { useState, type MouseEvent } from "react";
import { ChevronDown, ChevronUp, UserCheck } from "lucide-react";
import { type AvoidanceZone, type ZoneContributor } from "../adminApi";
import { contributorDetailQuery } from "../zoneQueueApi";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/apiClient";
import { Pagination, FloodReportDetailsModal } from "@/shared/ui";
import type { InspectionPage } from "@/features/flood-history/floodHistoryApi";
import { FloodRecordSummary, SpatialPanelButton } from "./FloodRecordSummary";

export function ZoneContributors({ zone, expanded, selectedId, onToggle, onInspect }: {
  zone: AvoidanceZone; expanded: boolean; selectedId?: number | null;
  onToggle: (event: MouseEvent<HTMLButtonElement>) => void;
  onInspect: (id: number, event: MouseEvent<HTMLButtonElement>) => void;
}) {
  const [page, setPage] = useState(1);
  const [infoId, setInfoId] = useState<number | null>(null);
  const detail = useQuery(contributorDetailQuery(infoId));
  const query = useQuery({ queryKey: ["adminZones", "contributors", zone.id, page],
    queryFn: ({ signal }) => apiClient.get<InspectionPage<ZoneContributor>>(`/admin/zones/${zone.id}/contributors?page=${page}`, { signal }),
    enabled: expanded && (zone.contributor_count ?? 0) > 20, staleTime: 15_000, retry: false });
  const contributors = query.data?.items ?? zone.contributors ?? [];
  const count = zone.contributor_count ?? contributors.length;
  const multiple = count > 1;
  const reporter = <span className="inline-flex items-center gap-1.5 text-xs text-slate-700"><UserCheck className="size-3.5 text-blue-500" />Reported by {zone.reporter_name || "Name unavailable"}{multiple && <span className="text-blue-700">· {count} reports</span>}</span>;
  return <div className="mt-2">
    {multiple ? <SpatialPanelButton variant="ghost" aria-expanded={expanded} onClick={onToggle} className="justify-start gap-1 px-0">{reporter}{expanded ? <ChevronUp className="size-3.5" /> : <ChevronDown className="size-3.5" />}</SpatialPanelButton> : reporter}
    {expanded && multiple && <section aria-label={`Zone #${zone.id} contributing reports`} className="mt-3 space-y-3" onClick={(event) => event.stopPropagation()}>
      {query.isError && <p role="alert" className="text-xs text-red-700">Could not load contributors. <SpatialPanelButton onClick={() => query.refetch()}>Retry contributors</SpatialPanelButton></p>}
      {contributors.map((report) => <article key={report.report_id} className={`p-3 ${selectedId === report.report_id ? "bg-blue-100/70" : "bg-blue-50/60"}`}>
        <FloodRecordSummary title={`Report #${report.report_id}`} severity={report.severity} depth={report.depth} timestamp={report.created_at} text={report.raw_text}
          headingExtra={report.is_primary && <span className="text-[10px] font-semibold text-blue-700">Primary</span>}
          facts={[{ label: "Reported by", value: report.reporter_name }, { label: "Trust score", value: `${report.reporter_trust_score}%` }]}
          actions={<><SpatialPanelButton variant="outline" onClick={event => { event.stopPropagation(); setInfoId(report.report_id); }}>Info for Report #{report.report_id}</SpatialPanelButton><SpatialPanelButton variant="outline" aria-pressed={selectedId === report.report_id} onClick={(event) => onInspect(report.report_id, event)}>{selectedId === report.report_id ? "Restore zone on map" : `Inspect Report #${report.report_id} on map`}</SpatialPanelButton></>} />
      </article>)}
      {query.data && <Pagination page={query.data.page} totalPages={query.data.pages} onPageChange={setPage} disabled={query.isFetching} />}
      {detail.isLoading && <p role="status" className="text-xs text-slate-500">Loading report evidence…</p>}
      {detail.isError && <p role="alert" className="text-xs text-red-700">Could not load report evidence. <SpatialPanelButton onClick={() => detail.refetch()}>Retry evidence</SpatialPanelButton></p>}
    </section>}
    <FloodReportDetailsModal report={detail.data ?? null} isOpen={infoId !== null && !!detail.data} onClose={() => setInfoId(null)} />
  </div>;
}
