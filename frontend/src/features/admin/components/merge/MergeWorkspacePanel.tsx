"use client";

import React, { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { Map as MapLibreMap } from "maplibre-gl";
import { ArrowLeft, ArrowRight, CheckCircle2, Layers, Loader2, MapPinned, RefreshCw, Save, ShieldCheck, X } from "lucide-react";
import { Button, useToast } from "@/shared/ui";
import { cn } from "@/lib/utils";
import { useMapContext } from "@/features/map/MapContext";
import {
  getMergeCandidates,
  mergeReports,
  type AvoidanceZone,
  type FloodReport,
  type MergeCandidateItem,
  type MergeConflict,
  type MergeReportsPayload,
  type ReportGeometry,
} from "../../adminApi";
import { ZoneDataEditorForm, type ZoneDataEditorValues } from "../ZoneDataEditorForm";
import { GeometryModeSelector } from "../zones/subcomponents/GeometryModeSelector";
import { RoadSegmentPicker } from "../zones/subcomponents/RoadSegmentPicker";
import { useTerraDraw } from "../zones/hooks/useTerraDraw";
import type { GeometryMode } from "../zones/types";
import { ConflictResolutionNotice } from "./ConflictResolutionNotice";
import { ReportComparisonCard } from "./ReportComparisonCard";
import { ReportComparisonMatrix } from "./ReportComparisonMatrix";

interface MergeWorkspacePanelProps {
  primaryReport: FloodReport | null;
  isOpen: boolean;
  onClose: () => void;
  onShowMap?: () => void;
  onMergeSuccess?: (zone: AvoidanceZone) => void;
  activeZones?: AvoidanceZone[];
  mapInstance?: MapLibreMap | null;
  onPreviewChange?: (candidates: MergeCandidateItem[], proposedGeom: ReportGeometry | null) => void;
}

type WorkflowStep = 1 | 2 | 3 | 4;
const STEP_LABELS = ["Candidates", "Compare", "Edit zone", "Confirm"] as const;

function emptyLine(): ReportGeometry {
  return { type: "LineString", coordinates: [] };
}

function hasUsableGeometry(geometry: ReportGeometry): boolean {
  if (geometry.type === "Point") return geometry.coordinates.length === 2;
  if (geometry.type === "LineString") return geometry.coordinates.length >= 2;
  if (geometry.type === "MultiLineString") return geometry.coordinates.some((line) => line.length >= 2);
  if (geometry.type === "Polygon") return geometry.coordinates.some((ring) => ring.length >= 4);
  return geometry.coordinates.some((polygon) => polygon.some((ring) => ring.length >= 4));
}

function getLineCoordinates(geometry: ReportGeometry | null): [number, number][] {
  if (!geometry) return [];
  if (geometry.type === "LineString") return geometry.coordinates;
  if (geometry.type === "MultiLineString") return geometry.coordinates[0] || [];
  return [];
}

function mergeLineGeometry(primary: ReportGeometry, opposite: ReportGeometry | null, isBidirectional: boolean): ReportGeometry {
  if (!isBidirectional || !opposite || primary.type !== "LineString" || opposite.type !== "LineString") return primary;
  return { type: "MultiLineString", coordinates: [primary.coordinates, opposite.coordinates] };
}

export function MergeWorkspacePanel({
  primaryReport,
  isOpen,
  onClose,
  onShowMap,
  onMergeSuccess,
  activeZones = [],
  mapInstance = null,
  onPreviewChange,
}: MergeWorkspacePanelProps) {
  const queryClient = useQueryClient();
  const { success, error: showError } = useToast();
  const {
    floodStart,
    floodEnd,
    floodPreviewGeometry,
    floodOppositeGeometry,
    setFloodStart,
    setFloodEnd,
    setFloodStartLabel,
    setFloodEndLabel,
    floodIsBidirectional,
    setFloodIsBidirectional,
  } = useMapContext();

  const [currentStep, setCurrentStep] = useState<WorkflowStep>(1);
  const [selectedCandidateIds, setSelectedCandidateIds] = useState<number[]>([]);
  const [targetZoneId, setTargetZoneId] = useState<number | null>(null);
  const [geometryMode, setGeometryMode] = useState<GeometryMode>("line");
  const [editorValues, setEditorValues] = useState<ZoneDataEditorValues>(() => ({
    severity: primaryReport?.severity || "medium",
    depth: primaryReport?.depth || "knee",
    passable_vehicles: primaryReport?.survey?.passable_vehicles?.split(",").filter(Boolean) || [],
    hidden_hazards: primaryReport?.survey?.hidden_hazards || "unsure",
    is_bidirectional: primaryReport?.is_bidirectional || false,
    geometry: primaryReport?.geometry || emptyLine(),
    admin_notes: "",
  }));

  const { drawnGeometry, drawnFeatures, isDrawingMode, clearDrawing, cancelDrawingMode } = useTerraDraw({
    mapInstance,
    geometryMode,
    severity: editorValues.severity,
    isEnabled: isOpen && currentStep === 3,
  });

  const {
    data: candidatesData,
    isLoading: isCandidatesLoading,
    isError: isCandidatesError,
    error: candidatesError,
    refetch,
  } = useQuery({
    queryKey: ["mergeCandidates", primaryReport?.id],
    queryFn: () => {
      if (!primaryReport) throw new Error("Select a primary report first.");
      return getMergeCandidates(primaryReport.id);
    },
    enabled: Boolean(primaryReport && isOpen),
    retry: 1,
  });

  const selectedCandidates = useMemo(
    () => (candidatesData?.candidates || []).filter((candidate) => selectedCandidateIds.includes(candidate.report_id)),
    [candidatesData?.candidates, selectedCandidateIds],
  );

  const selectedConflicts = useMemo(() => {
    const unique = new Map<string, MergeConflict>();
    selectedCandidates.flatMap((candidate) => candidate.conflicts || []).forEach((conflict) => {
      unique.set(`${conflict.field}:${conflict.message}:${String(conflict.suggested_value)}`, conflict);
    });
    return Array.from(unique.values());
  }, [selectedCandidates]);

  useEffect(() => {
    onPreviewChange?.(isOpen ? selectedCandidates : [], isOpen ? editorValues.geometry : null);
  }, [editorValues.geometry, isOpen, onPreviewChange, selectedCandidates]);

  useEffect(() => {
    if (isOpen) return;
    cancelDrawingMode();
    setFloodStart(null);
    setFloodEnd(null);
    setFloodStartLabel("");
    setFloodEndLabel("");
    setFloodIsBidirectional(false);
  }, [cancelDrawingMode, isOpen, setFloodEnd, setFloodEndLabel, setFloodIsBidirectional, setFloodStart, setFloodStartLabel]);

  useEffect(() => {
    if (currentStep !== 3 || geometryMode !== "line" || !floodStart || !floodEnd || !floodPreviewGeometry) return;
    const nextGeometry = mergeLineGeometry(
      floodPreviewGeometry as ReportGeometry,
      floodOppositeGeometry as ReportGeometry | null,
      floodIsBidirectional,
    );
    // MapContext is an external map controller; synchronizing its routed preview is intentional.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setEditorValues((previous) => ({ ...previous, geometry: nextGeometry, is_bidirectional: floodIsBidirectional }));
  }, [currentStep, floodEnd, floodIsBidirectional, floodOppositeGeometry, floodPreviewGeometry, floodStart, geometryMode]);

  useEffect(() => {
    if (currentStep !== 3 || geometryMode === "line" || !drawnGeometry) return;
    // Terra Draw is an external canvas controller; synchronize its completed shape into form state.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setEditorValues((previous) => ({ ...previous, geometry: drawnGeometry }));
  }, [currentStep, drawnGeometry, geometryMode]);

  const handleClose = () => {
    cancelDrawingMode();
    setFloodStart(null);
    setFloodEnd(null);
    setFloodStartLabel("");
    setFloodEndLabel("");
    setFloodIsBidirectional(false);
    onPreviewChange?.([], null);
    onClose();
  };

  const mergeMutation = useMutation({
    mutationFn: (payload: MergeReportsPayload) => mergeReports(payload),
    onSuccess: (data) => {
      success("Reports Merged", data.message || "The official avoidance zone was published.");
      queryClient.invalidateQueries({ queryKey: ["adminPendingReports"] });
      queryClient.invalidateQueries({ queryKey: ["adminZones"] });
      onMergeSuccess?.(data.zone);
      handleClose();
    },
    onError: (mutationError: unknown) => {
      showError("Merge Failed", mutationError instanceof Error ? mutationError.message : "The reports could not be merged.");
    },
  });

  if (!isOpen || !primaryReport) return null;

  const toggleCandidate = (id: number) => {
    setSelectedCandidateIds((previous) => previous.includes(id) ? previous.filter((item) => item !== id) : [...previous, id]);
  };

  const handleResolveConflict = (field: string, value: unknown) => {
    if (field === "severity" && ["low", "medium", "high", "extreme"].includes(String(value))) {
      setEditorValues((previous) => ({ ...previous, severity: String(value) as ZoneDataEditorValues["severity"] }));
    } else if (field === "depth") {
      setEditorValues((previous) => ({ ...previous, depth: String(value) }));
    } else if (field === "passable_vehicles") {
      setEditorValues((previous) => ({ ...previous, passable_vehicles: String(value).split(",").filter(Boolean) }));
    }
  };

  const loadProposalIntoLineEditor = () => {
    const coordinates = getLineCoordinates(editorValues.geometry);
    if (coordinates.length < 2) {
      showError("Line Unavailable", "The current proposal is not a routed line. Choose a shape tool or place new endpoints.");
      return;
    }
    setFloodStart(coordinates[0], "Proposed start");
    setFloodEnd(coordinates[coordinates.length - 1], "Proposed end");
    setFloodIsBidirectional(editorValues.is_bidirectional);
  };

  const validateFinalData = (): boolean => {
    if (!hasUsableGeometry(editorValues.geometry)) {
      showError("Geometry Required", "Define a valid road segment or draw one hazard boundary before continuing.");
      return false;
    }
    if (editorValues.passable_vehicles.length === 0) {
      showError("Passability Required", "Select at least one vehicle or traveler type that can safely pass.");
      return false;
    }
    if (!editorValues.admin_notes.trim()) {
      showError("Description Required", "Add a short operational description for the final official zone.");
      return false;
    }
    return true;
  };

  const handleNext = () => {
    if (currentStep === 1 && selectedCandidateIds.length === 0) {
      showError("Choose a Report", "Select at least one suggested report to create a multi-report merge.");
      return;
    }
    if (currentStep === 3 && !validateFinalData()) return;
    setCurrentStep((currentStep + 1) as WorkflowStep);
  };

  const handleExecuteMerge = () => {
    if (selectedCandidateIds.length === 0 || !validateFinalData()) return;
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
        admin_notes: editorValues.admin_notes.trim(),
        merge_rationale: `Admin confirmed reports ${[primaryReport.id, ...selectedCandidateIds].join(", ")} after intelligent candidate review`,
      },
    };
    mergeMutation.mutate(payload);
  };

  return (
    <aside aria-label="Merge and spatial review workspace" className="flex h-full w-full shrink-0 flex-col overflow-hidden bg-white">
      <div className="flex shrink-0 items-center justify-between border-b border-slate-200 bg-slate-50/80 p-3.5">
        <div className="flex min-w-0 items-center gap-2">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-600 text-white shadow-xs"><Layers className="h-4 w-4" /></div>
          <div className="min-w-0">
            <h2 className="truncate text-xs font-bold text-slate-800">Review Merge Suggestions</h2>
            <p className="truncate text-[11px] text-slate-500">Primary #{primaryReport.id} · {primaryReport.human_readable_location || primaryReport.barangay || "Pasig City"}</p>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-1">
          {onShowMap && (
            <Button type="button" variant="ghost" size="sm" onClick={onShowMap} className="h-8 px-2 text-[11px] md:hidden">
              <MapPinned className="mr-1 h-3.5 w-3.5" /> Map
            </Button>
          )}
          <button type="button" onClick={handleClose} className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-200" aria-label="Close merge workspace"><X className="h-4 w-4" /></button>
        </div>
      </div>

      <div className="grid shrink-0 grid-cols-4 border-b border-slate-200 bg-white text-center text-[10px] font-semibold text-slate-500">
        {STEP_LABELS.map((label, index) => {
          const step = (index + 1) as WorkflowStep;
          return (
            <button key={label} type="button" onClick={() => step < currentStep && setCurrentStep(step)} disabled={step > currentStep} className={cn(
              "border-b-2 px-1 py-2 transition-colors",
              currentStep === step ? "border-blue-600 bg-blue-50/40 font-bold text-blue-700" : "border-transparent",
              step < currentStep && "hover:text-slate-800",
              step > currentStep && "cursor-not-allowed opacity-60",
            )}>{step}. {label}</button>
          );
        })}
      </div>

      <div className="scrollbar-auto-hide flex-1 space-y-4 overflow-y-auto p-3.5 sm:p-4">
        {isCandidatesLoading ? (
          <div className="flex h-56 flex-col items-center justify-center gap-2.5 text-center text-slate-500">
            <Loader2 className="h-7 w-7 animate-spin text-blue-600" />
            <span className="text-xs font-medium">Checking road identity, overlap, direction, and report time…</span>
          </div>
        ) : isCandidatesError ? (
          <div className="rounded-xl border border-red-200 bg-red-50 p-5 text-center">
            <h3 className="text-sm font-bold text-red-800">Suggestions could not be loaded</h3>
            <p className="mt-1 text-xs text-red-700">{candidatesError instanceof Error ? candidatesError.message : "The matching service returned an unexpected error."}</p>
            <Button type="button" variant="outline" size="sm" onClick={() => refetch()} className="mt-3 border-red-200 text-red-700"><RefreshCw className="mr-1 h-3.5 w-3.5" /> Retry</Button>
          </div>
        ) : (
          <>
            {currentStep === 1 && (
              <div className="space-y-5">
                <header className="border-b border-slate-200 pb-3">
                  <h3 className="text-sm font-bold text-slate-900">Choose reports from the same flood event</h3>
                  <p className="mt-1 text-[11px] leading-relaxed text-slate-500">The system ranks suggestions using road, overlap, direction, and timing. Check only the reports that belong together; their original details remain unchanged.</p>
                </header>

                <section aria-labelledby="base-report-heading">
                  <div className="mb-2 flex items-center gap-2">
                    <span className="flex h-5 w-5 items-center justify-center rounded-full bg-blue-600 text-[10px] font-bold text-white">1</span>
                    <h3 id="base-report-heading" className="text-xs font-bold uppercase tracking-wider text-slate-700">Base report</h3>
                  </div>
                  <ReportComparisonCard report={primaryReport} isPrimary />
                </section>

                <section aria-labelledby="suggested-matches-heading" className="border-t border-slate-200 pt-4">
                  <div className="mb-1.5 flex items-center justify-between gap-3">
                    <div className="flex min-w-0 items-center gap-2">
                      <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-violet-600 text-[10px] font-bold text-white">2</span>
                      <h3 id="suggested-matches-heading" className="truncate text-xs font-bold uppercase tracking-wider text-slate-700">Suggested matches</h3>
                    </div>
                    <span className="shrink-0 rounded-full bg-violet-100 px-2 py-0.5 text-[10px] font-bold text-violet-700">{selectedCandidateIds.length} of {candidatesData?.total_candidates || 0} included</span>
                  </div>
                  <p className="mb-3 pl-7 text-[11px] text-slate-500">Each report includes its own match score and supporting evidence.</p>
                {!candidatesData?.candidates.length ? (
                  <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-6 text-center">
                    <CheckCircle2 className="mx-auto mb-2 h-8 w-8 text-emerald-500" />
                    <h3 className="text-xs font-bold text-slate-700">No matches were suggested</h3>
                    <p className="mx-auto mt-1 max-w-xs text-[11px] text-slate-500">Close this workspace to approve, reject, or defer the primary report normally.</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {candidatesData.candidates.map((candidate) => {
                      const isSelected = selectedCandidateIds.includes(candidate.report_id);
                      return (
                        <ReportComparisonCard
                          key={candidate.report_id}
                          report={candidate}
                          isSelected={isSelected}
                          onToggleSelect={() => toggleCandidate(candidate.report_id)}
                          matchScore={candidate.match_score}
                          matchReasons={candidate.match_reasons}
                          isCrowdConsensus={candidate.is_crowd_consensus}
                        />
                      );
                    })}
                  </div>
                )}
                </section>
              </div>
            )}

            {currentStep === 2 && (
              <div className="space-y-3.5">
                <div><h3 className="text-xs font-bold text-slate-800">Compare original submissions</h3><p className="mt-1 text-[11px] text-slate-500">Review values field by field. Original reports remain unchanged after merging.</p></div>
                <ConflictResolutionNotice conflicts={selectedConflicts} onResolveConflict={handleResolveConflict} />
                <ReportComparisonMatrix primaryReport={primaryReport} candidates={selectedCandidates} />
              </div>
            )}

            {currentStep === 3 && (
              <div className="space-y-5">
                <section className="space-y-3">
                  <div><h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">1. Final spatial geometry</h3><p className="mt-1 text-[11px] text-slate-500">Keep the primary geometry or redefine the official routing boundary using the shared zone tools.</p></div>
                  <GeometryModeSelector geometryMode={geometryMode} onChange={(mode) => { setGeometryMode(mode); if (mode !== "line") setFloodIsBidirectional(false); }} isDrawingMode={isDrawingMode} onCancelDrawing={cancelDrawingMode} />
                  {geometryMode === "line" ? (
                    <div className="space-y-3">
                      <Button type="button" variant="outline" size="sm" onClick={loadProposalIntoLineEditor} className="w-full text-xs"><MapPinned className="mr-1 h-3.5 w-3.5" /> Edit current proposal with Start / End</Button>
                      <RoadSegmentPicker isBidirectional={floodIsBidirectional} onBidirectionalChange={setFloodIsBidirectional} />
                    </div>
                  ) : (
                    <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-3 text-center">
                      <p className="text-xs font-medium text-slate-600">{drawnFeatures.length ? "The drawn boundary is now the final proposed geometry." : `Draw one ${geometryMode} boundary directly on the map.`}</p>
                      {drawnFeatures.length > 0 && <Button type="button" variant="outline" size="sm" onClick={clearDrawing} className="mt-2 border-red-200 text-red-600">Clear drawing</Button>}
                    </div>
                  )}
                </section>
                <section className="space-y-3 border-t border-slate-100 pt-4">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">2. Final operational information</h3>
                  <ZoneDataEditorForm initialValues={editorValues} onChange={setEditorValues} hideBidirectional />
                </section>
                <section className="space-y-1.5 border-t border-slate-100 pt-4">
                  <label htmlFor="merge-target-zone" className="text-xs font-semibold text-slate-700">Destination avoidance zone</label>
                  <select id="merge-target-zone" value={targetZoneId ?? ""} onChange={(event) => setTargetZoneId(event.target.value ? Number(event.target.value) : null)} className="w-full rounded-lg border border-slate-200 bg-white p-2 text-xs font-medium text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500">
                    <option value="">Create a new official avoidance zone</option>
                    {activeZones.map((zone) => <option key={zone.id} value={zone.id}>Zone #{zone.id} · {zone.name || zone.severity || "Active incident"}</option>)}
                  </select>
                </section>
              </div>
            )}

            {currentStep === 4 && (
              <div className="space-y-4">
                <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-emerald-900"><div className="flex items-center gap-2 text-xs font-bold"><ShieldCheck className="h-4 w-4" /> Ready for final confirmation</div><p className="mt-1 text-[11px]">This publishes operational zone data only. Original user reports and Community Feed posts remain unchanged.</p></div>
                <dl className="divide-y divide-slate-100 rounded-xl border border-slate-200 bg-white text-xs">
                  <div className="flex justify-between gap-4 p-3"><dt className="text-slate-500">Reports included</dt><dd className="text-right font-semibold text-slate-800">#{[primaryReport.id, ...selectedCandidateIds].join(", #")}</dd></div>
                  <div className="flex justify-between gap-4 p-3"><dt className="text-slate-500">Suggestions excluded</dt><dd className="font-semibold text-slate-800">{Math.max(0, (candidatesData?.total_candidates || 0) - selectedCandidateIds.length)}</dd></div>
                  <div className="flex justify-between gap-4 p-3"><dt className="text-slate-500">Destination</dt><dd className="text-right font-semibold text-slate-800">{targetZoneId ? `Existing zone #${targetZoneId}` : "New official zone"}</dd></div>
                  <div className="flex justify-between gap-4 p-3"><dt className="text-slate-500">Depth / severity</dt><dd className="font-semibold capitalize text-slate-800">{editorValues.depth.replace(/-/g, " ")} · {editorValues.severity}</dd></div>
                  <div className="flex justify-between gap-4 p-3"><dt className="text-slate-500">Passable</dt><dd className="max-w-[60%] text-right font-semibold text-slate-800">{editorValues.passable_vehicles.join(", ")}</dd></div>
                  <div className="flex justify-between gap-4 p-3"><dt className="text-slate-500">Geometry</dt><dd className="font-semibold text-slate-800">{editorValues.geometry.type}</dd></div>
                  <div className="flex justify-between gap-4 p-3"><dt className="text-slate-500">Contributor credit</dt><dd className="font-semibold text-slate-800">+5 trust per unique reporter</dd></div>
                </dl>
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-[11px] text-slate-600"><strong className="text-slate-800">Operational description:</strong> {editorValues.admin_notes}</div>
              </div>
            )}
          </>
        )}
      </div>

      <div className="flex shrink-0 items-center justify-between gap-2 border-t border-slate-200 bg-slate-50/90 p-3.5 pb-[calc(0.875rem+env(safe-area-inset-bottom))]">
        <Button type="button" variant="outline" size="sm" onClick={currentStep === 1 ? handleClose : () => setCurrentStep((currentStep - 1) as WorkflowStep)} disabled={mergeMutation.isPending} className="text-xs font-semibold">
          {currentStep === 1 ? "Cancel" : <><ArrowLeft className="mr-1 h-3.5 w-3.5" /> Back</>}
        </Button>
        {currentStep < 4 ? (
          <Button type="button" variant="primary" size="sm" onClick={handleNext} disabled={isCandidatesLoading || isCandidatesError || (currentStep === 1 && selectedCandidateIds.length === 0)} className="bg-blue-600 text-xs font-semibold text-white hover:bg-blue-700">
            {currentStep === 1 ? "Compare Selected" : currentStep === 2 ? "Edit Final Zone" : "Review Confirmation"}<ArrowRight className="ml-1 h-3.5 w-3.5" />
          </Button>
        ) : (
          <Button type="button" variant="primary" size="sm" onClick={handleExecuteMerge} disabled={mergeMutation.isPending} className="bg-emerald-600 text-xs font-semibold text-white hover:bg-emerald-700">
            {mergeMutation.isPending ? <><Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" /> Publishing…</> : <><Save className="mr-1 h-3.5 w-3.5" /> Confirm & Publish</>}
          </Button>
        )}
      </div>
    </aside>
  );
}
