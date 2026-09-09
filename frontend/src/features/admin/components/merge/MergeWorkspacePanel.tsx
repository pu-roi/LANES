"use client";

import React, { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { 
  X, 
  Layers, 
  Sparkles, 
  ArrowRight, 
  ArrowLeft, 
  CheckCircle2, 
  Loader2, 
  AlertTriangle,
  Info,
  ShieldAlert,
  Save,
  Users
} from "lucide-react";
import { Button, useToast } from "@/shared/ui";
import { cn } from "@/lib/utils";
import { 
  getMergeCandidates, 
  mergeReports, 
  type FloodReport, 
  type MergeCandidateItem, 
  type MergeCandidatesListResponse,
  type MergeReportsPayload,
  type AvoidanceZone,
  type ReportGeometry
} from "../../adminApi";
import { ReportComparisonCard } from "./ReportComparisonCard";
import { ConflictResolutionNotice } from "./ConflictResolutionNotice";
import { MergeExplanationBanner } from "./MergeExplanationBanner";
import { ZoneDataEditorForm, type ZoneDataEditorValues } from "../ZoneDataEditorForm";

interface MergeWorkspacePanelProps {
  primaryReport: FloodReport | null;
  isOpen: boolean;
  onClose: () => void;
  onMergeSuccess?: (zone: AvoidanceZone) => void;
  activeZones?: AvoidanceZone[];
  onPreviewChange?: (candidates: MergeCandidateItem[], proposedGeom: ReportGeometry | null) => void;
}

export function MergeWorkspacePanel({
  primaryReport,
  isOpen,
  onClose,
  onMergeSuccess,
  activeZones = [],
  onPreviewChange,
}: MergeWorkspacePanelProps) {
  const queryClient = useQueryClient();
  const { success, error } = useToast();

  // Workflow steps: 1 = Candidate Selection, 2 = Compare & Resolve, 3 = Final Zone Editor
  const [currentStep, setCurrentStep] = useState<1 | 2 | 3>(1);
  const [selectedCandidateIds, setSelectedCandidateIds] = useState<number[]>([]);
  const [targetZoneId, setTargetZoneId] = useState<number | null>(null);

  // Editable final zone state
  const [editorValues, setEditorValues] = useState<ZoneDataEditorValues>({
    severity: "medium",
    depth: "knee",
    passable_vehicles: [],
    hidden_hazards: "unsure",
    is_bidirectional: false,
    geometry: { type: "LineString", coordinates: [] },
    admin_notes: "",
    buffer_radius: 25,
  });

  // Fetch intelligent candidates
  const { 
    data: candidatesData, 
    isLoading: isCandidatesLoading,
    refetch 
  } = useQuery({
    queryKey: ["mergeCandidates", primaryReport?.id],
    queryFn: () => primaryReport ? getMergeCandidates(primaryReport.id) : Promise.reject(),
    enabled: !!primaryReport && isOpen,
  });

  // Auto-initialize form values when candidates data loads
  useEffect(() => {
    if (!primaryReport) return;
    
    // Auto-select candidates with >= 80% match score
    if (candidatesData?.candidates) {
      const topMatches = candidatesData.candidates
        .filter(c => c.match_score >= 80)
        .map(c => c.report_id);
      setSelectedCandidateIds(topMatches);
    }

    const initialGeom = candidatesData?.suggested_merged_geometry || primaryReport.geometry || { type: "LineString", coordinates: [] };
    const isBidir = candidatesData?.is_bidirectional_detected || primaryReport.is_bidirectional || false;

    setEditorValues({
      severity: primaryReport.severity || "medium",
      depth: primaryReport.depth || "knee",
      passable_vehicles: primaryReport.survey?.passable_vehicles ? primaryReport.survey.passable_vehicles.split(",") : [],
      hidden_hazards: (primaryReport.survey?.hidden_hazards as string) || "unsure",
      is_bidirectional: isBidir,
      geometry: initialGeom,
      admin_notes: "",
      buffer_radius: 25,
    });
    setCurrentStep(1);
  }, [primaryReport, candidatesData]);

  // Sync preview layer with selected candidates and proposed geometry
  useEffect(() => {
    if (!onPreviewChange) return;
    if (!candidatesData?.candidates) {
      onPreviewChange([], editorValues.geometry);
      return;
    }
    const activeCandidates = candidatesData.candidates.filter(c => 
      selectedCandidateIds.includes(c.report_id)
    );
    onPreviewChange(activeCandidates, editorValues.geometry);
  }, [selectedCandidateIds, editorValues.geometry, candidatesData, onPreviewChange]);

  // Mutation to execute merge
  const mergeMutation = useMutation({
    mutationFn: (payload: MergeReportsPayload) => mergeReports(payload),
    onSuccess: (data) => {
      success(data.message || "Successfully merged flood reports.");
      queryClient.invalidateQueries({ queryKey: ["adminPendingReports"] });
      queryClient.invalidateQueries({ queryKey: ["adminZones"] });
      if (onMergeSuccess) {
        onMergeSuccess(data.zone);
      }
      onClose();
    },
    onError: (err: any) => {
      error(err.message || "Failed to merge flood reports.");
    },
  });

  if (!isOpen || !primaryReport) return null;

  const toggleCandidate = (id: number) => {
    setSelectedCandidateIds(prev => 
      prev.includes(id) ? prev.filter(item => item !== id) : [...prev, id]
    );
  };

  const handleResolveConflict = (field: string, value: any) => {
    if (field === "severity") {
      setEditorValues(prev => ({ ...prev, severity: value }));
    } else if (field === "depth") {
      setEditorValues(prev => ({ ...prev, depth: value }));
    } else if (field === "passable_vehicles" && typeof value === "string") {
      setEditorValues(prev => ({ ...prev, passable_vehicles: value.split(",") }));
    }
  };

  const handleExecuteMerge = () => {
    const payload: MergeReportsPayload = {
      primary_report_id: primaryReport.id,
      merged_report_ids: selectedCandidateIds,
      target_zone_id: targetZoneId,
      final_data: {
        name: editorValues.name,
        severity: editorValues.severity,
        depth: editorValues.depth,
        passable_vehicles: editorValues.passable_vehicles.join(","),
        hidden_hazards: editorValues.hidden_hazards,
        is_bidirectional: editorValues.is_bidirectional,
        geometry: editorValues.geometry,
        admin_notes: editorValues.admin_notes,
        merge_rationale: `Merged ${1 + selectedCandidateIds.length} reports via Decision #16 engine`,
        buffer_radius: editorValues.buffer_radius,
      }
    };
    mergeMutation.mutate(payload);
  };

  const selectedCandidatesList = (candidatesData?.candidates || []).filter(c => 
    selectedCandidateIds.includes(c.report_id)
  );

  return (
    <aside 
      aria-label="Merge and spatial review workspace"
      className="w-full h-full bg-white flex flex-col shrink-0 overflow-hidden"
    >
      {/* Drawer Header */}
      <div className="p-3.5 border-b border-slate-200 flex items-center justify-between bg-slate-50/80">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-blue-600 text-white flex items-center justify-center font-bold text-xs shadow-xs">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-xs font-bold text-slate-800 tracking-tight flex items-center gap-1.5">
              <span>Review & Merge Flood Reports</span>
              <span className="text-[10px] font-semibold bg-blue-100 text-blue-700 px-1.5 py-0.2 rounded-full">
                Step {currentStep} of 3
              </span>
            </h2>
            <p className="text-[11px] text-slate-500 truncate max-w-[260px]">
              Target: #{primaryReport.id} • {primaryReport.human_readable_location || primaryReport.barangay || "Pasig City"}
            </p>
          </div>
        </div>

        <button 
          onClick={onClose}
          className="w-7 h-7 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 flex items-center justify-center transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Step Tabs Indicator */}
      <div className="grid grid-cols-3 border-b border-slate-200 bg-white text-[11px] font-semibold text-center text-slate-500">
        <button
          onClick={() => setCurrentStep(1)}
          className={cn(
            "py-2 border-b-2 transition-all",
            currentStep === 1 ? "border-blue-600 text-blue-600 font-bold bg-blue-50/30" : "border-transparent hover:text-slate-700"
          )}
        >
          1. Candidates ({selectedCandidateIds.length})
        </button>
        <button
          onClick={() => setCurrentStep(2)}
          className={cn(
            "py-2 border-b-2 transition-all",
            currentStep === 2 ? "border-blue-600 text-blue-600 font-bold bg-blue-50/30" : "border-transparent hover:text-slate-700"
          )}
        >
          2. Comparison
        </button>
        <button
          onClick={() => setCurrentStep(3)}
          className={cn(
            "py-2 border-b-2 transition-all",
            currentStep === 3 ? "border-blue-600 text-blue-600 font-bold bg-blue-50/30" : "border-transparent hover:text-slate-700"
          )}
        >
          3. Zone Editor
        </button>
      </div>

      {/* Drawer Content Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {isCandidatesLoading ? (
          <div className="flex flex-col items-center justify-center h-56 gap-2.5 text-slate-400">
            <Loader2 className="w-7 h-7 animate-spin text-blue-600" />
            <span className="text-xs font-medium">Scanning road topology & Decision #16 traces...</span>
          </div>
        ) : (
          <>
            {/* STEP 1: CANDIDATE SELECTION */}
            {currentStep === 1 && (
              <div className="space-y-3.5">
                {/* Primary Report Card */}
                <ReportComparisonCard report={primaryReport} isPrimary={true} />

                {/* Candidates List Header */}
                <div className="flex items-center justify-between pt-1">
                  <span className="text-xs font-bold text-slate-800">
                    Suggested Merge Candidates ({candidatesData?.candidates.length || 0})
                  </span>
                  <span className="text-[11px] text-slate-500 font-medium">
                    {selectedCandidateIds.length} included
                  </span>
                </div>

                {(!candidatesData?.candidates || candidatesData.candidates.length === 0) ? (
                  <div className="bg-slate-50 border border-dashed border-slate-200 rounded-xl p-6 text-center">
                    <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
                    <h3 className="text-xs font-bold text-slate-700">No Duplicate Reports Found</h3>
                    <p className="text-[11px] text-slate-500 mt-1 max-w-xs mx-auto">
                      This incident appears isolated. You can proceed directly to approve it as a standalone avoidance zone.
                    </p>
                  </div>
                ) : (
                  candidatesData.candidates.map((candidate) => {
                    const isSelected = selectedCandidateIds.includes(candidate.report_id);
                    return (
                      <div key={candidate.report_id} className="space-y-1.5">
                        <MergeExplanationBanner
                          matchScore={candidate.match_score}
                          matchReasons={candidate.match_reasons}
                          isCrowdConsensus={candidate.is_crowd_consensus}
                        />
                        <ReportComparisonCard
                          report={candidate}
                          isSelected={isSelected}
                          onToggleSelect={() => toggleCandidate(candidate.report_id)}
                        />
                      </div>
                    );
                  })
                )}
              </div>
            )}

            {/* STEP 2: REPORT COMPARISON & CONFLICT RESOLUTION */}
            {currentStep === 2 && (
              <div className="space-y-3.5">
                {/* Conflict Warnings */}
                {candidatesData?.detected_conflicts && candidatesData.detected_conflicts.length > 0 && (
                  <ConflictResolutionNotice
                    conflicts={candidatesData.detected_conflicts}
                    onResolveConflict={handleResolveConflict}
                  />
                )}

                <div className="text-xs font-bold text-slate-800 pt-1">
                  Selected Reports for Synthesis ({1 + selectedCandidatesList.length})
                </div>

                {/* Primary Card */}
                <ReportComparisonCard report={primaryReport} isPrimary={true} />

                {/* Selected Candidates */}
                {selectedCandidatesList.map((cand) => (
                  <ReportComparisonCard
                    key={cand.report_id}
                    report={cand}
                    isSelected={true}
                    onToggleSelect={() => toggleCandidate(cand.report_id)}
                  />
                ))}
              </div>
            )}

            {/* STEP 3: FINAL ZONE DATA & GEOMETRY EDITOR */}
            {currentStep === 3 && (
              <div className="space-y-4">
                {/* Target Zone Selection: New vs Merge Into Existing */}
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">
                    Destination Avoidance Zone
                  </label>
                  <select
                    value={targetZoneId ?? ""}
                    onChange={(e) => setTargetZoneId(e.target.value ? Number(e.target.value) : null)}
                    className="w-full text-xs p-2 rounded-lg border border-slate-200 bg-white font-medium text-slate-800"
                  >
                    <option value="">Create a New Official Avoidance Zone</option>
                    {activeZones.map(z => (
                      <option key={z.id} value={z.id}>
                        Merge into Active Zone #{z.id} ({z.severity}{z.depth ? ` • ${z.depth}` : ""})
                      </option>
                    ))}
                  </select>
                </div>

                <ZoneDataEditorForm
                  initialValues={editorValues}
                  onChange={(vals) => setEditorValues(vals)}
                />
              </div>
            )}
          </>
        )}
      </div>

      {/* Drawer Footer Actions */}
      <div className="p-3.5 border-t border-slate-200 bg-slate-50/80 flex items-center justify-between gap-2 shrink-0">
        {currentStep > 1 ? (
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCurrentStep((prev) => (prev - 1) as any)}
            className="text-xs font-semibold"
          >
            <ArrowLeft className="w-3.5 h-3.5 mr-1" />
            Back
          </Button>
        ) : (
          <Button
            variant="outline"
            size="sm"
            onClick={onClose}
            className="text-xs font-semibold text-slate-600"
          >
            Cancel
          </Button>
        )}

        {currentStep < 3 ? (
          <Button
            variant="primary"
            size="sm"
            onClick={() => setCurrentStep((prev) => (prev + 1) as any)}
            className="text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white"
          >
            Next: {currentStep === 1 ? "Review Conflicts" : "Edit Final Zone"}
            <ArrowRight className="w-3.5 h-3.5 ml-1" />
          </Button>
        ) : (
          <Button
            variant="primary"
            size="sm"
            disabled={mergeMutation.isPending}
            onClick={handleExecuteMerge}
            className="text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white shadow-xs"
          >
            {mergeMutation.isPending ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" />
                Merging...
              </>
            ) : (
              <>
                <Save className="w-3.5 h-3.5 mr-1" />
                Confirm & Create Official Zone
              </>
            )}
          </Button>
        )}
      </div>
    </aside>
  );
}
