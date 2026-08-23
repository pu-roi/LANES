import React from "react";
import Link from "next/link";
import { Loader2, CheckCircle, MapPin, AlertTriangle, Merge, X, Check, Info, ExternalLink } from "lucide-react";
import { Button } from "@/shared/ui/Button";
import { Select } from "@/shared/ui/Select";
import type { FloodReport, NearbyZone } from "../adminApi";
import { UseMutationResult } from "@tanstack/react-query";

interface PendingReportsPanelProps {
  pendingLoading: boolean;
  pendingReports: FloodReport[] | undefined;
  filteredPendingReports: FloodReport[];
  selectedReportId: number | null;
  setSelectedReportId: (id: number | null) => void;
  onInfoClick: (report: FloodReport) => void;
  batchCandidates: FloodReport[];
  batchSelectedIds: number[];
  setBatchSelectedIds: (ids: number[]) => void;
  nearbyZones: NearbyZone[] | undefined;
  setTargetZoneId: (id: number | null) => void;
  setMergeModalOpen: (open: boolean) => void;
  rejectMutation: UseMutationResult<any, Error, number, unknown>;
  approveMutation: UseMutationResult<any, Error, { id: number; payload?: any }, unknown>;
}

export function PendingReportsPanel({
  pendingLoading,
  pendingReports,
  filteredPendingReports,
  selectedReportId,
  setSelectedReportId,
  onInfoClick,
  batchCandidates,
  batchSelectedIds,
  setBatchSelectedIds,
  nearbyZones,
  setTargetZoneId,
  setMergeModalOpen,
  rejectMutation,
  approveMutation,
}: PendingReportsPanelProps) {

  const [filterSeverity, setFilterSeverity] = React.useState<string>("all");
  const [minTrustScore, setMinTrustScore] = React.useState<number>(0);

  // If there is a selected report, check if it has batch candidates (duplicates).
  // If it does, we MUST enforce merging before approving.
  const hasDuplicatesToMerge = selectedReportId !== null && batchCandidates.length > 0;

  const toggleBatchSelection = (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    if (batchSelectedIds.includes(id)) {
      setBatchSelectedIds(batchSelectedIds.filter(i => i !== id));
    } else {
      setBatchSelectedIds([...batchSelectedIds, id]);
    }
  };

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

      <div className="flex-1 overflow-y-auto divide-y divide-gray-100">
        {displayedReports.length === 0 ? (
          <div className="p-6 text-center text-gray-400 text-xs">No reports match the current filters.</div>
        ) : displayedReports.map((report: FloodReport) => {
        const isSelected = selectedReportId === report.id;
        const hasNearby = isSelected && nearbyZones && nearbyZones.length > 0;
        
        // If this report is selected, and it has duplicates, we disable approve
        const isApprovalBlockedByDuplicates = isSelected && hasDuplicatesToMerge;

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
                {/* Batch Merge Checkbox */}
                {(selectedReportId === null || report.id !== selectedReportId) && (
                  <input 
                    type="checkbox" 
                    checked={batchSelectedIds.includes(report.id)}
                    onChange={(e) => toggleBatchSelection(e as any, report.id)}
                    onClick={(e) => e.stopPropagation()}
                    className="w-3.5 h-3.5 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                  />
                )}
                
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
              "{report.raw_text}"
            </p>

            <div className="flex items-center gap-1.5 text-xs text-gray-500 mb-3">
              <MapPin className="w-3.5 h-3.5 text-gray-400 shrink-0" />
              <span className="truncate">{report.barangay ? `Brgy. ${report.barangay}, Pasig` : "Pasig City"}</span>
            </div>

            {/* Nearby Zone Alert Badge (Merging with existing active zones) */}
            {hasNearby && (
              <div className="mb-3 p-2.5 bg-amber-50 border border-amber-200/70 rounded-xl flex items-center justify-between text-xs text-amber-800 animate-fade-in">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                  <span>Nearby Active Zone ({nearbyZones[0].distance_meters}m away)</span>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={(e) => {
                    e.stopPropagation();
                    setTargetZoneId(nearbyZones[0].id);
                    setMergeModalOpen(true);
                  }}
                  className="h-6 text-[11px] px-2 border-amber-300 bg-white hover:bg-amber-100 text-amber-900"
                >
                  <Merge className="w-3 h-3 mr-1" /> Merge
                </Button>
              </div>
            )}

            {/* Duplicate Pending Reports Alert Badge */}
            {isApprovalBlockedByDuplicates && (
              <div className="mb-3 p-3 bg-rose-50 border border-rose-200/70 rounded-xl flex flex-col text-xs text-rose-800 animate-fade-in gap-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
                    <span className="font-bold">Duplicate Reports ({batchCandidates.length + 1} Total)</span>
                  </div>
                  <span className="text-[10px] px-1.5 py-0.5 bg-rose-200 text-rose-800 rounded font-extrabold uppercase">
                    Merge Required
                  </span>
                </div>

                {/* Inline Preview of matching duplicate candidates */}
                <div className="divide-y divide-rose-100 bg-white/80 p-2 rounded-lg border border-rose-100 max-h-36 overflow-y-auto">
                  {batchCandidates.map((cand) => (
                    <div key={cand.id} className="py-1.5 first:pt-0 last:pb-0 flex flex-col gap-0.5 text-[11px]">
                      <div className="flex items-center justify-between text-rose-950 font-semibold">
                        <span>Report #{cand.id}</span>
                        <span className="text-[10px] text-gray-400 font-normal">
                          {new Date(cand.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                        </span>
                      </div>
                      <p className="text-gray-600 line-clamp-1 italic">
                        "{cand.raw_text}"
                      </p>
                    </div>
                  ))}
                </div>

                <div className="flex justify-end pt-1">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={(e) => {
                      e.stopPropagation();
                      setTargetZoneId(null); 
                      setMergeModalOpen(true);
                    }}
                    className="h-7 text-xs px-3 border-rose-300 bg-white hover:bg-rose-100 text-rose-900 font-semibold shadow-sm"
                  >
                    <Merge className="w-3.5 h-3.5 mr-1 text-rose-600" /> Review & Merge All ({batchCandidates.length + 1})
                  </Button>
                </div>
              </div>
            )}

            {/* Quick Moderation Actions */}
            <div className="flex items-center justify-end gap-2 pt-2 border-t border-gray-100" onClick={(e) => e.stopPropagation()}>
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
                disabled={approveMutation.isPending || (isSelected && hasDuplicatesToMerge)}
                className={`h-7 text-xs px-3 rounded-lg shadow-sm ${
                  (isSelected && hasDuplicatesToMerge) ? "opacity-50 cursor-not-allowed" : ""
                }`}
                title={(isSelected && hasDuplicatesToMerge) ? "Merge duplicates first" : "Approve as new zone"}
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
