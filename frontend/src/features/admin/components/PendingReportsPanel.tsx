import React from "react";
import { Loader2, CheckCircle, MapPin, Sparkles, X, Check, Info } from "lucide-react";
import { Button } from "@/shared/ui";
import { Select } from "@/shared/ui";
import type { ApproveReportPayload, FloodReport } from "../adminApi";
import { UseMutationResult } from "@tanstack/react-query";

interface PendingReportsPanelProps {
  pendingLoading: boolean;
  pendingReports: FloodReport[] | undefined;
  filteredPendingReports: FloodReport[];
  selectedReportId: number | null;
  setSelectedReportId: (id: number | null) => void;
  onInfoClick: (report: FloodReport) => void;
  onOpenMergeWorkspace: (report: FloodReport) => void;
  rejectMutation: UseMutationResult<FloodReport, Error, number, unknown>;
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
  rejectMutation,
  approveMutation,
}: PendingReportsPanelProps) {

  const [filterSeverity, setFilterSeverity] = React.useState<string>("all");
  const [minTrustScore, setMinTrustScore] = React.useState<number>(0);

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

  // Apply Troll Filters
  const displayedReports = filteredPendingReports.filter(r => {
    if (filterSeverity !== "all" && r.severity?.toLowerCase() !== filterSeverity) return false;
    // (In the future, r.user.trust_score should be passed. For now, assume a mock trust score or ignore)
    return true; 
  });

  return (
    <div className="flex-1 overflow-hidden flex flex-col">
      {/* Troll Filtration Controls */}
      <div className="p-3 bg-white border-b border-gray-100 flex gap-2 shrink-0">
        <div className="flex-1">
          <Select 
            value={filterSeverity} 
            onChange={(e) => setFilterSeverity(e.target.value as string)}
            options={[
              { label: "All Severities", value: "all" },
              { label: "Extreme", value: "extreme" },
              { label: "High", value: "high" },
              { label: "Medium", value: "medium" },
              { label: "Low", value: "low" }
            ]}
          />
        </div>
        <div className="flex-1">
          <Select 
            value={minTrustScore} 
            onChange={(e) => setMinTrustScore(Number(e.target.value))}
            options={[
              { label: "Any Trust Score", value: 0 },
              { label: "Trusted (\u003E 50)", value: 50 },
              { label: "Verified (\u003E 80)", value: 80 }
            ]}
          />
        </div>
      </div>

      <div className="scrollbar-auto-hide flex-1 overflow-y-auto divide-y divide-gray-100">
        {displayedReports.length === 0 ? (
          <div className="p-6 text-center text-gray-400 text-xs">No reports match the current filters.</div>
        ) : displayedReports.map((report: FloodReport) => {
        const isSelected = selectedReportId === report.id;

        return (
          <div
            key={report.id}
            onClick={() => setSelectedReportId(isSelected ? null : report.id)}
            className={`p-4 transition-all cursor-pointer hover:bg-slate-50/80 ${
              isSelected ? "bg-blue-50/80 ring-2 ring-blue-500/30" : ""
            }`}
          >
            <div className="flex items-start justify-between gap-3 mb-2">
              <div className="flex items-center gap-2">
                <span className="font-bold text-sm text-gray-900">Report #{report.id}</span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-extrabold uppercase tracking-wide border ${
                  report.severity?.toLowerCase() === "low"
                    ? "bg-lime-100 text-lime-800 border-lime-300"
                    : report.severity?.toLowerCase() === "medium"
                    ? "bg-amber-100 text-amber-800 border-amber-300"
                    : report.severity?.toLowerCase() === "high"
                    ? "bg-orange-100 text-orange-800 border-orange-300"
                    : "bg-red-100 text-red-800 border-red-300 animate-pulse"
                }`}>
                  {report.severity}
                </span>
                {report.depth && (
                  <span className="px-2 py-0.5 rounded bg-blue-100 text-blue-700 text-[10px] font-medium">
                    {report.depth}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] text-gray-400 font-medium">
                  {new Date(report.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </span>
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); onInfoClick(report); }}
                  className="flex items-center gap-1 px-2 py-0.5 text-[11px] font-semibold text-blue-600 hover:text-blue-800 bg-blue-50 hover:bg-blue-100 border border-blue-200/80 rounded-md transition-colors shadow-xs"
                  title="View full report moderation details"
                >
                  <Info className="w-3 h-3" />
                  <span>Info</span>
                </button>
              </div>
            </div>

            <p className="text-xs text-slate-700 font-medium line-clamp-2 mb-2">
              &ldquo;{report.raw_text}&rdquo;
            </p>

            <div className="flex items-center gap-1.5 text-xs text-gray-500 mb-3">
              <MapPin className="w-3.5 h-3.5 text-gray-400 shrink-0" />
              <span className="truncate">
                {report.barangay ? `Brgy. ${report.barangay}, ${report.city || "Pasig"}` : (report.city || "Pasig City")}
              </span>
            </div>

            {/* Quick Moderation Actions */}
            <div className="flex flex-wrap items-center justify-end gap-2 pt-2 border-t border-gray-100" onClick={(e) => e.stopPropagation()}>
              <Button
                size="sm"
                variant="outline"
                onClick={() => onOpenMergeWorkspace(report)}
                className="h-7 text-xs px-2.5 text-blue-700 border-blue-200 hover:bg-blue-50 rounded-lg"
                title="Ask the intelligent matching engine for possible reports from the same incident"
              >
                <Sparkles className="w-3.5 h-3.5 mr-1" /> Review Merge Suggestions
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => rejectMutation.mutate(report.id)}
                disabled={rejectMutation.isPending}
                className="h-7 text-xs px-2.5 text-gray-600 hover:bg-gray-100 rounded-lg"
              >
                <X className="w-3.5 h-3.5 mr-1 text-red-500" /> Reject
              </Button>
              
              <Button
                size="sm"
                variant="primary"
                onClick={() => approveMutation.mutate({ id: report.id, payload: { action: "CREATE_NEW" } })}
                disabled={approveMutation.isPending}
                className="h-7 text-xs px-3 rounded-lg shadow-sm"
                title="Approve this report as a standalone official zone"
              >
                <Check className="w-3.5 h-3.5 mr-1" /> Approve
              </Button>
            </div>
          </div>
        );
      })}
      </div>
    </div>
  );
}
