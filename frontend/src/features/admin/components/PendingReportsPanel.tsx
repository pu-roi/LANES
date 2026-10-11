import { FloodRecordSummary, SpatialPanelButton } from "./FloodRecordSummary";
import { Loader2, CheckCircle, Sparkles, X, Check, Info } from "lucide-react";
import type { ApproveReportPayload, FloodReport } from "../adminApi";
import { UseMutationResult } from "@tanstack/react-query";

interface PendingReportsPanelProps {
  hideFilters?: boolean;
  inspectionOnly?: boolean;
  pendingLoading: boolean;
  pendingReports: FloodReport[] | undefined;
  filteredPendingReports: FloodReport[];
  selectedReportId: number | null;
  setSelectedReportId: (id: number | null) => void;
  onInfoClick: (report: FloodReport) => void;
  onOpenMergeWorkspace: (report: FloodReport) => void;
  onRequestReject: (report: FloodReport) => void;
  approveMutation: UseMutationResult<FloodReport, Error, { id: number; payload?: ApproveReportPayload }, unknown>;
}

export function PendingReportsPanel({
  pendingLoading,
  pendingReports,
  filteredPendingReports,
  selectedReportId,
  setSelectedReportId,
  onInfoClick,
  onOpenMergeWorkspace,
  onRequestReject,
  approveMutation,
  inspectionOnly = false,
}: PendingReportsPanelProps) {

  if (pendingLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-48 text-gray-400 gap-2">
        <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
        <span className="text-xs font-medium">Checking moderation queue...</span>
      </div>
    );
  }

  if (!pendingReports || pendingReports.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-48 text-gray-400 gap-2 p-6 text-center">
        <CheckCircle className="w-8 h-8 text-emerald-500" />
        <span className="text-sm font-semibold text-gray-700">Queue is Clear</span>
        <p className="text-xs text-gray-400">No unapproved flood reports require moderation.</p>
      </div>
    );
  }

  return <div className="divide-y divide-gray-100">{filteredPendingReports.map((report) => <div key={report.id}
    className="bg-blue-50/80 p-4"
    onClick={() => setSelectedReportId(selectedReportId === report.id ? null : report.id)}>
    <FloodRecordSummary title={`Report #${report.id}`} severity={report.severity} depth={report.depth}
      timestamp={report.created_at} text={report.raw_text}
      location={[report.human_readable_location || report.road_name, report.barangay ? `Brgy. ${report.barangay}` : null, report.city].filter(Boolean).join(", ") || "Location not specified"}
      aside={<SpatialPanelButton variant="outline" className="gap-1 border-blue-200 px-2 text-blue-600" onClick={(event) => { event.stopPropagation(); onInfoClick(report); }} title="View full report moderation details"><Info className="size-3" />Info</SpatialPanelButton>}
      facts={[
        { label: "Source", value: report.source === "direct_user" ? "User report" : report.source.replaceAll("_", " ") },
        { label: "Reported by", value: report.reporter_name || report.reporter_username || "Name unavailable" },
        ...(report.reporter_trust_score != null ? [{ label: "Trust score", value: `${report.reporter_trust_score}%` }] : []),
        { label: "Vehicles", value: report.passable_vehicles || report.survey?.passable_vehicles || "Not reported" },
        { label: "Hazards", value: report.hidden_hazards || report.survey?.hidden_hazards || "Not reported" },
        { label: "Attachments", value: `${report.media_urls?.length ?? 0} · Open Info to inspect evidence` },
      ]}
      actions={!inspectionOnly && <>
        <SpatialPanelButton variant="outline" className="gap-1 border-blue-200 px-2.5 text-blue-700 hover:bg-blue-50" onClick={() => onOpenMergeWorkspace(report)}><Sparkles className="size-3.5" />Review Merge Suggestions</SpatialPanelButton>
        <SpatialPanelButton variant="outline" className="gap-1 px-2.5" onClick={() => onRequestReject(report)}><X className="size-3.5 text-red-500" />Reject</SpatialPanelButton>
        <SpatialPanelButton className="gap-1 px-3" disabled={approveMutation.isPending} onClick={() => approveMutation.mutate({ id: report.id, payload: { action: "CREATE_NEW" } })} title="Approve this report as a standalone official zone"><Check className="size-3.5" />Approve</SpatialPanelButton>
      </>} />
  </div>)}</div>;
}
