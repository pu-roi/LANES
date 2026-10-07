"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import {
  CheckCircle,
  Loader2,
  Navigation2,
  HelpCircle,
  X,
  ArrowLeft,
  ShieldCheck,
  Pencil,
  Trash2,
} from "lucide-react";
import { Button, ConfirmDialog, LoadingOverlay, Panel } from "@/shared/ui";
import { MapPickerMobileOverlay } from "@/features/map/MapPickerMobileOverlay";
import { useToast } from "@/shared/ui";
import { LocationInputGroup } from "@/shared/ui";
import { cn } from "@/lib/utils";
import { FloodDepthField, FloodMediaField, FloodDescriptionField, FloodSurveyFields, FloodSurveyLauncher, floodDepthColors } from "./FloodReportFields";
import { useFloodMedia } from "./useFloodMedia";
import { ZoneUpdateForm } from "./ZoneUpdateForm";
import { FloodReportLoginGate } from "./FloodReportLoginGate";
import type { ZoneCondition, ZoneUpdateContext } from "./zoneUpdatesApi";
import { apiClient } from "@/lib/apiClient";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import { useAuth } from "@/hooks/useAuth";
import { getCurrentLocation } from "@/features/geocoding/geocodingApi";
import { useMapContext, type ActivePoint, type DraftReport } from "@/features/map/MapContext";
import {
  discardFloodReportDraft,
  hasFloodReportPanelState,
  hasMeaningfulFloodReportDraft,
  loadFloodReportDraft,
  removeLegacyFloodReportDrafts,
  saveFloodReportDraft,
} from "./floodReportDraftStorage";

import { FLOOD_DEPTH_OPTIONS, formatFloodDepth } from "@/lib/floodDepth";

// ── Types ──────────────────────────────────────────────────────────────────────

interface FloodReportPanelProps {
  zoneUpdate?: { zone: ZoneUpdateContext; condition: ZoneCondition; key: string } | null;
  onReturnToReport?: () => void;
  isOpen: boolean;
  onClose: () => void;
  isAdminMode?: boolean;
  onAdminSubmit?: (formData: FormData) => Promise<void>;
}

type Severity = "low" | "medium" | "high" | "extreme";
type ReportVisualOption = "gutter" | "half-knee" | "half-tire" | "knee" | "tires" | "waist" | "chest" | "neck";

const VISUAL_OPTIONS = FLOOD_DEPTH_OPTIONS;

export function FloodReportPanel({ isOpen, onClose, isAdminMode = false, onAdminSubmit, zoneUpdate, onReturnToReport }: FloodReportPanelProps) {
  const isMobile = useMediaQuery("(max-width: 640px), (pointer: coarse)");
  const { user, isAuthenticated } = useAuth();
  const userId = typeof user?.id === "string" || typeof user?.id === "number" ? String(user.id) : null;
  const canPersistDraft = !isAdminMode && isAuthenticated && userId !== null;

  // Map context
  const {
    floodStart,
    floodEnd,
    activePoint,
    isPickingOnMap,
    setActivePoint,
    setIsPickingOnMap,
    setFloodStart,
    setFloodEnd,
    setFloodStartLabel,
    setFloodEndLabel,
    restoreFloodReportMapState,
    activePanel,
    setActivePanel,
    floodIsBidirectional: isBidirectional,
    setFloodIsBidirectional: setIsBidirectional,
    draftReports = [],
    setDraftReports,
    floodPreviewGeometry,
    floodOppositeGeometry,
    floodPreviewStatus,
    floodPreviewMessage,
  } = useMapContext();

  // Form state
  const [startInput, setStartInput] = useState("");
  const [endInput, setEndInput] = useState("");
  const [visualOption, setVisualOption] = useState<ReportVisualOption | null>(null);
  const [passableVehicles, setPassableVehicles] = useState<string[]>([]);
  const [hiddenHazards, setHiddenHazards] = useState<"yes" | "no" | "unsure" | null>(null);
  const [showSurvey, setShowSurvey] = useState(false);
  const [description, setDescription] = useState("");
  const media = useFloodMedia();
  const { mediaFiles, setMediaFiles, clearMediaFiles } = media;
  const [isPublic, setIsPublic] = useState(false);
  const [step, setStep] = useState<1 | 2>(1);
  const [isViewingDrafts, setIsViewingDrafts] = useState(false);
  const [editingDraft, setEditingDraft] = useState<DraftReport | null>(null);
  const isCollapsed = activePanel !== "flood";

  // Submission state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isUpdatingZone, setIsUpdatingZone] = useState(false);
  const [isDiscardDialogOpen, setIsDiscardDialogOpen] = useState(false);
  const [discardUpdateKey, setDiscardUpdateKey] = useState<string | null>(null);
  const { success, error } = useToast();

  // Account-private draft hydration and persistence. Never read a device-wide draft
  // for an unauthenticated or different account.
  const hasHydratedForm = useRef(false);
  const hydratedUserId = useRef<string | null>(null);
  const hasShownPersistenceError = useRef(false);
  const suppressNextDraftSave = useRef(false);

  const clearInMemoryDraft = useCallback(() => {
    setDraftReports([]);
    restoreFloodReportMapState({
      floodStart: null,
      floodEnd: null,
      floodPreviewGeometry: null,
      floodOppositeGeometry: null,
      floodIsBidirectional: false,
    });
    setStartInput("");
    setEndInput("");
    setVisualOption(null);
    setPassableVehicles([]);
    setHiddenHazards(null);
    setShowSurvey(false);
    setDescription("");
    clearMediaFiles();
    setIsPublic(false);
    setStep(1);
  }, [clearMediaFiles, restoreFloodReportMapState, setDraftReports]);

  useEffect(() => {
    if (!canPersistDraft || !userId) {
      hasHydratedForm.current = false;
      hydratedUserId.current = null;
      queueMicrotask(clearInMemoryDraft);
      return;
    }

    let cancelled = false;
    hasHydratedForm.current = false;
    hydratedUserId.current = null;
    queueMicrotask(clearInMemoryDraft);

    const loadFormState = async () => {
      try {
        await removeLegacyFloodReportDrafts();
        const saved = await loadFloodReportDraft(userId);
        if (cancelled || !saved) return;
        if (!hasMeaningfulFloodReportDraft(saved)) {
          await discardFloodReportDraft(userId);
          return;
        }

        const { active } = saved;
        setStartInput(active.startInput);
        setEndInput(active.endInput);
        setVisualOption(active.visualOption as ReportVisualOption | null);
        setPassableVehicles(active.passableVehicles);
        setHiddenHazards(active.hiddenHazards);
        setShowSurvey(active.showSurvey);
        setDescription(active.description);
        setMediaFiles(active.mediaFiles);
        setIsPublic(active.isPublic);
        setStep(active.step);
        setDraftReports(saved.queuedDrafts);
        restoreFloodReportMapState({
          floodStart: active.floodStart,
          floodEnd: active.floodEnd,
          floodPreviewGeometry: active.floodPreviewGeometry,
          floodOppositeGeometry: active.floodOppositeGeometry,
          floodIsBidirectional: active.floodIsBidirectional,
        });
        success("Draft Restored", "Your unfinished flood report is ready to continue.");
      } catch (err) {
        console.error("Failed to load account flood-report draft", err);
        if (!cancelled) error("Draft Unavailable", "Your saved flood-report draft could not be restored.");
      } finally {
        if (!cancelled) {
          hydratedUserId.current = userId;
          hasHydratedForm.current = true;
        }
      }
    };
    void loadFormState();

    return () => {
      cancelled = true;
    };
  }, [canPersistDraft, clearInMemoryDraft, error, restoreFloodReportMapState, setDraftReports, success, userId]);

  useEffect(() => {
    if (!canPersistDraft || !userId || !hasHydratedForm.current || hydratedUserId.current !== userId) return;
    if (suppressNextDraftSave.current) {
      suppressNextDraftSave.current = false;
      return;
    }

    const draft = {
      active: {
        floodStart,
        floodEnd,
        floodPreviewGeometry,
        floodOppositeGeometry,
        floodIsBidirectional: isBidirectional,
        startInput,
        endInput,
        visualOption,
        passableVehicles,
        hiddenHazards,
        showSurvey,
        description,
        mediaFiles,
        isPublic,
        step,
      },
      queuedDrafts: draftReports,
    };

    const persist = hasMeaningfulFloodReportDraft(draft)
      ? saveFloodReportDraft(userId, draft)
      : discardFloodReportDraft(userId);

    void persist.catch((err) => {
      console.error("Failed to save account flood-report draft", err);
      if (!hasShownPersistenceError.current) {
        hasShownPersistenceError.current = true;
        error("Draft Not Saved", "Your changes could not be saved on this device.");
      }
    });
  }, [canPersistDraft, description, draftReports, endInput, error, floodEnd, floodOppositeGeometry, floodPreviewGeometry, floodStart, hiddenHazards, isBidirectional, isPublic, mediaFiles, passableVehicles, showSurvey, startInput, step, userId, visualOption]);

  // ── Map-pick: listen to the shared map-center-changed event ────────────────
  const [mapCenter, setMapCenter] = useState<[number, number] | null>(null);

  useEffect(() => {
    const handleCenter = (e: Event) => {
      setMapCenter((e as CustomEvent<[number, number]>).detail);
    };
    window.addEventListener("map-center-changed", handleCenter);
    return () => window.removeEventListener("map-center-changed", handleCenter);
  }, []);

  useEffect(() => {
    if (floodStart?.label) setStartInput(floodStart.label);
  }, [floodStart?.label]);

  useEffect(() => {
    if (floodEnd?.label) setEndInput(floodEnd.label);
  }, [floodEnd?.label]);

  const clearForm = () => {
    restoreFloodReportMapState({
      floodStart: null,
      floodEnd: null,
      floodPreviewGeometry: null,
      floodOppositeGeometry: null,
      floodIsBidirectional: false,
    });
    setStartInput("");
    setEndInput("");
    setFloodStartLabel("");
    setFloodEndLabel("");
    setDescription("");
    setVisualOption(null);
    setPassableVehicles([]);
    setHiddenHazards(null);
    clearMediaFiles();
    setIsPublic(false);
    setShowSurvey(false);
    setStep(1);
    setEditingDraft(null);
  };

  const resetEntireFloodReport = () => {
    suppressNextDraftSave.current = true;
    setDraftReports([]);
    clearForm();
    setIsViewingDrafts(false);
    setActivePoint(null);
    setIsPickingOnMap(false);
  };

  const clearCurrentFloodReportPage = () => {
    if (isViewingDrafts) {
      setDraftReports([]);
      setIsViewingDrafts(false);
      setIsDiscardDialogOpen(false);
      return;
    }

    if (step === 1) {
      restoreFloodReportMapState({
        floodStart: null,
        floodEnd: null,
        floodPreviewGeometry: null,
        floodOppositeGeometry: null,
        floodIsBidirectional: false,
      });
      setStartInput("");
      setEndInput("");
      setFloodStartLabel("");
      setFloodEndLabel("");
      setVisualOption(null);
      setActivePoint(null);
      setIsPickingOnMap(false);
    } else {
      setPassableVehicles([]);
      setHiddenHazards(null);
      setShowSurvey(false);
      setDescription("");
      clearMediaFiles();
      setIsPublic(false);
    }

    setIsDiscardDialogOpen(false);
  };

  const discardDraft = async () => {
    if (!canPersistDraft || !userId) {
      resetEntireFloodReport();
      setIsDiscardDialogOpen(false);
      return;
    }

    try {
      await discardFloodReportDraft(userId);
      resetEntireFloodReport();
      setIsDiscardDialogOpen(false);
      success("Draft Discarded", "Your saved flood-report draft was removed from this device.");
    } catch (err) {
      console.error("Failed to discard account flood-report draft", err);
      error("Could Not Discard Draft", "Your saved draft is still available. Please try again.");
    }
  };

  const handlePickOnMap = (target: ActivePoint) => {
    setActivePoint(target);
    setIsPickingOnMap(true);
  };

  const confirmMapLocation = useCallback(() => {
    if (!activePoint || !mapCenter) return;
    const label = `${mapCenter[0].toFixed(5)}, ${mapCenter[1].toFixed(5)}`;
    if (activePoint === "flood_start") {
      setFloodStart(mapCenter, label);
      setStartInput(label);
      setActivePoint("flood_end");
    } else if (activePoint === "flood_end") {
      setFloodEnd(mapCenter, label);
      setEndInput(label);
      setActivePoint(null);
      setIsPickingOnMap(false);
      setActivePanel(null);
    }
  }, [activePoint, mapCenter, setFloodStart, setFloodEnd, setActivePoint, setIsPickingOnMap, setActivePanel]);

  // ── Current location helper ────────────────────────────────────────────────
  const handleUseCurrent = async (target: ActivePoint) => {
    try {
      const coords = await getCurrentLocation();
      const label = "Current Location";
      if (target === "start" || target === "flood_start") {
        setFloodStart(coords, label);
        setStartInput(label);
      } else {
        setFloodEnd(coords, label);
        setEndInput(label);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Unable to retrieve your location";
      error("Location Error", message);
    }
  };

  const handleSwapDirection = useCallback(() => {
    if (!floodStart || !floodEnd) return;
    const previousStartInput = startInput;
    const previousEndInput = endInput;
    setFloodStart(floodEnd.coords, floodEnd.label);
    setFloodEnd(floodStart.coords, floodStart.label);
    setStartInput(previousEndInput || floodEnd.label);
    setEndInput(previousStartInput || floodStart.label);
    setActivePoint(null);
    setIsPickingOnMap(false);
  }, [endInput, floodEnd, floodStart, setActivePoint, setFloodEnd, setFloodStart, setIsPickingOnMap, startInput]);

  // ── Draft & Submit ─────────────────────────────────────────────────────────

  const handleDraftRoad = () => {
    if (!floodStart || !floodEnd || !floodPreviewGeometry) return;
    if (!visualOption) {
      error("Flood Severity Required", "Select the observed flood depth before saving this road.");
      return;
    }
    if (!passableVehicles.length || !hiddenHazards) {
      error("Missing Information", "Please complete the Community Survey before drafting.");
      return;
    }

    const selectedOption = VISUAL_OPTIONS.find((opt) => opt.id === visualOption);
    if (!selectedOption) {
      error("Flood Severity Required", "Select a valid flood depth before saving this road.");
      return;
    }
    const severity = selectedOption.severity;
    const depth = selectedOption.id;

    const newDraft = {
      id: editingDraft?.id ?? Math.random().toString(36).substring(7),
      geometry: floodPreviewGeometry,
      oppositeGeometry: floodOppositeGeometry,
      isBidirectional,
      severity,
      depth,
      description,
      mediaFiles: [...mediaFiles],
      startLabel: startInput,
      endLabel: endInput,
      roadName: null,
      startCoords: floodStart?.coords,
      endCoords: floodEnd?.coords,
      passableVehicles: [...passableVehicles],
      hiddenHazards: hiddenHazards,
      isPublic: isPublic,
    };

    setDraftReports((prev) => [...prev, newDraft]);
    clearForm();

    success(editingDraft ? "Draft Updated" : "Road Saved", editingDraft ? "Your saved report draft was updated." : "Road added to your draft list. You can add another or submit all.");
  };

  const handleEditDraft = (draft: DraftReport) => {
    restoreFloodReportMapState({
      floodStart: draft.startCoords ? { coords: draft.startCoords, label: draft.startLabel } : null,
      floodEnd: draft.endCoords ? { coords: draft.endCoords, label: draft.endLabel } : null,
      floodPreviewGeometry: draft.geometry,
      floodOppositeGeometry: draft.oppositeGeometry,
      floodIsBidirectional: draft.isBidirectional,
    });
    setStartInput(draft.startLabel || "");
    setEndInput(draft.endLabel || "");
    setDescription(draft.description);
    const option = VISUAL_OPTIONS.find((item) => item.id === draft.depth)
      || VISUAL_OPTIONS.find((item) => item.severity === draft.severity && item.label === draft.depth)
      || VISUAL_OPTIONS.find((item) => item.severity === draft.severity);
    setVisualOption((option?.id as ReportVisualOption | undefined) ?? null);
    setPassableVehicles(draft.passableVehicles || []);
    setHiddenHazards(draft.hiddenHazards || null);
    setIsPublic(draft.isPublic || false);
    setMediaFiles(draft.mediaFiles || []);
    setEditingDraft(draft);
    setDraftReports((previous) => previous.filter((item) => item.id !== draft.id));
    setIsViewingDrafts(false);
    setStep(2);
  };

  const cancelDraftEdit = () => {
    if (!editingDraft) return;
    setDraftReports((previous) => [...previous, editingDraft]);
    clearForm();
    setIsViewingDrafts(true);
  };

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();

    // Determine what to submit (all drafts + current form if valid)
    const formsToSubmit: FormData[] = [];

    // Helper to create FormData
    const createFormData = (data: any) => {
      const fd = new FormData();
      fd.append("raw_text", data.description.trim());
      fd.append("source", "direct_user");
      fd.append("severity", data.severity);
      if (data.depth) fd.append("depth", data.depth);
      if (data.humanReadableLocation) fd.append("human_readable_location", data.humanReadableLocation);
      fd.append("is_public", data.isPublic.toString());
      fd.append("is_bidirectional", data.isBidirectional.toString());
      const coverageGeometry = data.isBidirectional && data.oppositeGeometry
        ? {
            type: "MultiLineString",
            coordinates: [data.geometry.coordinates, data.oppositeGeometry.coordinates],
          }
        : data.geometry;
      fd.append("geometry", JSON.stringify(coverageGeometry));
      fd.append(
        "survey_data",
        JSON.stringify({
          passable_vehicles: data.passableVehicles,
          hidden_hazards: data.hiddenHazards,
        })
      );
      if (data.mediaFiles && data.mediaFiles.length > 0) {
        data.mediaFiles.forEach((file: File) => {
          fd.append("media", file);
        });
      }
      return fd;
    };

    // 1. Pack drafts
    draftReports.forEach((draft) => {
      const draftHint = draft.startLabel && /[a-zA-Z]/.test(draft.startLabel) ? draft.startLabel : undefined;
      formsToSubmit.push(
        createFormData({
          description: draft.description,
          severity: draft.severity,
          depth: draft.depth,
          humanReadableLocation: draftHint,
          isPublic: isPublic, // Shared across batch
          isBidirectional: draft.isBidirectional,
          geometry: draft.geometry,
          oppositeGeometry: draft.oppositeGeometry,
          passableVehicles: draft.passableVehicles?.join(",") || null,
          hiddenHazards: draft.hiddenHazards || "unsure",
          mediaFiles: draft.mediaFiles,
        })
      );
    });

    // 2. Pack current form if filled
    const isCurrentFormFilled = !!floodStart && !!floodEnd && !!visualOption && description.trim().length > 0 && passableVehicles.length > 0 && hiddenHazards !== null && floodPreviewGeometry;
    
    if (isCurrentFormFilled) {
      const selectedOption = VISUAL_OPTIONS.find((opt) => opt.id === visualOption);
      if (!selectedOption) {
        error("Flood Severity Required", "Select a valid flood depth before submitting this report.");
        return;
      }
      const currentHint = startInput && /[a-zA-Z]/.test(startInput) ? startInput : undefined;
      formsToSubmit.push(
        createFormData({
          description: description,
          severity: selectedOption.severity,
          depth: selectedOption.id,
          humanReadableLocation: currentHint,
          isPublic: isPublic,
          isBidirectional: isBidirectional,
          geometry: floodPreviewGeometry,
          oppositeGeometry: floodOppositeGeometry,
          passableVehicles: passableVehicles.join(", "),
          hiddenHazards: hiddenHazards,
          mediaFiles: mediaFiles,
        })
      );
    }

    if (formsToSubmit.length === 0) {
      error("Empty", "No valid reports to submit.");
      return;
    }

    setIsSubmitting(true);
    let automaticallyApproved = false;
    let automationUnavailable = false;
    try {
      if (isAdminMode && onAdminSubmit) {
        for (const fd of formsToSubmit) {
           await onAdminSubmit(fd);
        }
      } else {
        const results = await Promise.all(formsToSubmit.map((fd) => apiClient.post<{ id: number; status: string; automatic_review_reason?: string }>("/reports", fd)));
        automaticallyApproved = results.some((result) => result.status === "approved");
        automationUnavailable = results.some((result) => result.automatic_review_reason === "automatic_approval_unavailable");
      }

      // Reset everything
      setDraftReports([]);
      clearForm();
      if (canPersistDraft && userId) {
        try {
          await discardFloodReportDraft(userId);
          suppressNextDraftSave.current = true;
        } catch (discardError) {
          console.error("Submitted reports but could not remove local draft", discardError);
          error("Reports Submitted", "Your reports were submitted, but the local draft could not be removed. Please discard it manually.");
        }
      }
      
      success(isAdminMode ? "Zones Created" : "Reports Submitted", isAdminMode ? "Official zones are now active." : automaticallyApproved ? "Eligible reports were automatically approved. Check My Reports for each report status." : "Thank you! Your reports are now in review.");
      if (automationUnavailable) error("Automatic Approval Unavailable", "Your report was saved and remains available for staff review.");
      if (onClose) onClose();
    } catch (err: unknown) {
      console.error("Error submitting flood reports:", err);
      error("Submission Failed", err instanceof Error ? err.message : "Failed to submit some reports. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const isSurveyComplete = passableVehicles.length > 0 && hiddenHazards !== null;
  const canSubmitCurrent = !!floodStart && !!floodEnd && !!visualOption && description.trim().length > 0 && isSurveyComplete;
  const canSubmitAny = (draftReports.length > 0) || canSubmitCurrent;

  // ── Mobile map-pick overlay ────────────────────────────────────────────────
  if (!zoneUpdate && isMobile && isPickingOnMap && (activePoint === "flood_start" || activePoint === "flood_end")) {
    return (
      <MapPickerMobileOverlay 
        onCancel={() => {
          setIsPickingOnMap(false);
          if (!floodStart && !floodEnd) setActivePoint(null);
        }}
        onConfirm={confirmMapLocation}
        confirmText={`Set ${activePoint === "flood_start" ? "Flood Start" : "Flood End"}`}
      />
    );
  }

  // ── Shared form body ───────────────────────────────────────────────────────
  const currentDraftContent = {
    active: {
      floodStart,
      floodEnd,
      floodPreviewGeometry,
      floodOppositeGeometry,
      floodIsBidirectional: isBidirectional,
      startInput,
      endInput,
      visualOption,
      passableVehicles,
      hiddenHazards,
      showSurvey,
      description,
      mediaFiles,
      isPublic,
      step,
    },
    queuedDrafts: draftReports,
  };
  const hasPanelState = hasFloodReportPanelState(currentDraftContent);

  const requestClear = () => {
    setIsDiscardDialogOpen(true);
  };

  const formBody = (!isAuthenticated && !isAdminMode) ? (
    <FloodReportLoginGate />
  ) : (
    <form
      onSubmit={handleSubmit}
      className="relative flex flex-col"
      aria-busy={floodPreviewStatus === "loading"}
    >
      <LoadingOverlay
        isVisible={floodPreviewStatus === "loading" && Boolean(floodStart && floodEnd)}
        message="Verifying the selected road and traffic directions…"
        variant="absolute"
        blocking
      />
      {isAdminMode && (
        <div className="flex items-center gap-3 px-1 mb-4 mt-2 border-b border-gray-100 pb-3">
          <div className="w-9 h-9 rounded-full bg-blue-50 text-blue-700 flex items-center justify-center font-bold text-sm ring-1 ring-blue-100/50 uppercase">
            {user?.profile?.first_name?.charAt(0) || user?.username?.charAt(0) || 'A'}
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-1.5">
              <p className="text-sm font-semibold text-gray-900">
                {user?.profile?.first_name ? `${user.profile.first_name} ${user.profile.last_name || ''}`.trim() : user?.username || 'DRRMO Admin'}
              </p>
              <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
            </div>
            <p className="text-[11px] font-medium text-gray-500">
              Official DRRMO Account
            </p>
          </div>
        </div>
      )}

      {!isViewingDrafts && draftReports.length > 0 && (
        <div className="mb-4 flex items-center justify-between border-b border-gray-100 px-1 pb-3">
          <span className="text-sm font-semibold text-gray-800">
            {draftReports.length} saved {draftReports.length === 1 ? "draft" : "drafts"}
          </span>
          <button
            type="button"
            onClick={() => setIsViewingDrafts(true)}
            className="rounded-full bg-purple-100 px-3 py-1.5 text-xs font-semibold text-purple-700 transition-colors hover:bg-purple-200"
          >
            View drafts
          </button>
        </div>
      )}

      {!isViewingDrafts && hasPanelState && (
        <div className="flex justify-end">
          <button
            type="button"
            onClick={requestClear}
            className="text-xs font-medium text-gray-500 transition-colors hover:text-red-600"
          >
            Clear
          </button>
        </div>
      )}

      {isViewingDrafts && (
        <div className="flex flex-col flex-1 animate-in fade-in zoom-in-95 duration-200 min-h-[300px]">
           <div className="mb-4 flex items-center justify-between gap-2">
             <div className="flex min-w-0 items-center gap-2">
             <button type="button" onClick={() => setIsViewingDrafts(false)} className="p-1.5 bg-gray-100 hover:bg-gray-200 rounded-full text-gray-700 transition-colors">
               <ArrowLeft className="w-4 h-4" />
             </button>
             <h3 className="font-bold text-gray-900 text-lg">Saved Drafts</h3>
             </div>
             <button
               type="button"
               onClick={requestClear}
               className="shrink-0 text-xs font-medium text-gray-500 transition-colors hover:text-red-600"
             >
               Clear
             </button>
           </div>
           
           <div className="space-y-3 overflow-y-auto pr-1 flex-1 pb-20">
              {draftReports.map((draft) => (
                 <div key={draft.id} className="bg-white border border-gray-200 rounded-xl p-3 shadow-sm relative group">
                    <div className="absolute top-3 right-3 flex gap-1">
                       <button 
                         type="button" 
                         onClick={() => handleEditDraft(draft)}
                         className="p-1.5 bg-blue-50 text-blue-600 hover:bg-blue-100 rounded-md transition-colors"
                         title="Edit Draft"
                       >
                         <Pencil className="w-3.5 h-3.5" />
                       </button>
                       <button 
                         type="button" 
                         onClick={() => {
                           const newDrafts = draftReports.filter(r => r.id !== draft.id);
                           setDraftReports(newDrafts);
                           if (newDrafts.length === 0) setIsViewingDrafts(false);
                         }}
                         className="p-1.5 bg-red-50 text-red-600 hover:bg-red-100 rounded-md transition-colors"
                         title="Delete Draft"
                       >
                         <Trash2 className="w-3.5 h-3.5" />
                       </button>
                    </div>
                    
                    <h4 className="font-bold text-gray-800 text-sm pr-16 truncate">{draft.startLabel || "Unknown Road"}</h4>
                    <p className="text-xs text-gray-500 mt-1 line-clamp-2">{draft.description || "No description provided."}</p>
                    <div className="mt-3 flex items-center gap-2">
                       <span className={cn("px-2 py-0.5 rounded text-[10px] font-bold uppercase", floodDepthColors[draft.severity as Severity]?.[0])}>
                         {draft.severity} • {formatFloodDepth(draft.depth, { compact: true })}
                       </span>
                    </div>
                 </div>
              ))}
           </div>
           
           <div className="absolute bottom-0 left-0 right-0 p-4 bg-white/95 backdrop-blur-md border-t border-gray-100 rounded-b-2xl shadow-[0_-4px_16px_rgba(0,0,0,0.04)]">
             <Button
                type="submit"
                disabled={draftReports.length === 0 || isSubmitting}
                className="w-full bg-orange-500 hover:bg-orange-600 text-white font-semibold h-10 rounded-xl"
              >
                {isSubmitting ? (
                  <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Submitting...</>
                ) : (
                  <>Submit All {draftReports.length} Drafts <CheckCircle className="w-4 h-4 ml-1.5" /></>
                )}
              </Button>
           </div>
        </div>
      )}

      {!isViewingDrafts && step === 1 && (
        <div className="space-y-4 animate-in fade-in slide-in-from-right-4 duration-300">
          <LocationInputGroup
            startInput={startInput}
            setStartInput={(val) => { setStartInput(val); setIsPickingOnMap(false); }}
            endInput={endInput}
            setEndInput={(val) => { setEndInput(val); setIsPickingOnMap(false); }}
            activePoint={activePoint}
            setActivePoint={setActivePoint}
            startPointId="flood_start"
            endPointId="flood_end"
            onStartSelect={(s) => { setFloodStart([s.lng, s.lat], s.label); setStartInput(s.label); setActivePoint("flood_end"); setIsPickingOnMap(false); }}
            onEndSelect={(s) => { setFloodEnd([s.lng, s.lat], s.label); setEndInput(s.label); setActivePoint(null); setIsPickingOnMap(false); }}
            onStartClear={() => { setFloodStart(null); setStartInput(""); setFloodStartLabel(""); setActivePoint("flood_start"); setIsPickingOnMap(false); }}
            onEndClear={() => { setFloodEnd(null); setEndInput(""); setFloodEndLabel(""); setActivePoint("flood_end"); setIsPickingOnMap(false); }}
            onStartChange={setFloodStartLabel}
            onEndChange={setFloodEndLabel}
            onPickOnMap={(target) => handlePickOnMap(target)}
            onUseCurrentLocation={handleUseCurrent}
            canSwap={Boolean(floodStart && floodEnd)}
            onSwap={handleSwapDirection}
            startPlaceholder="e.g. Ortigas Ave, Pasig (Start)"
            endPlaceholder="e.g. C. Raymundo Ave (End)"
          />
          
          {/* Bidirectional Toggle */}
          <label className="flex items-start gap-2 mb-4 px-1 group cursor-pointer select-none">
             <div className="flex h-5 items-center mt-0.5">
                <input
                  type="checkbox"
                  checked={isBidirectional}
                  onChange={(e) => setIsBidirectional(e.target.checked)}
                  className="w-4 h-4 rounded border-gray-300 text-orange-600 focus:ring-orange-600 focus:ring-2 pointer-events-auto cursor-pointer"
                />
              </div>
              <div className="flex flex-col">
                <span className="text-[13px] font-semibold text-gray-800 group-hover:text-gray-900 transition-colors">
                  Affects both sides of the road (2-way)
                </span>
                <span className="text-[11px] text-gray-500 leading-tight pr-4">
                  Keep checked if the flood blocks traffic in both directions. The system will automatically verify 1-way streets.
                </span>
              </div>
          </label>

          {floodPreviewStatus !== "loading" && floodPreviewMessage && floodStart && floodEnd && (
            <p
              role={floodPreviewStatus === "error" ? "alert" : "status"}
              className={cn(
                "rounded-lg px-3 py-2 text-[11px] leading-relaxed",
                floodPreviewStatus === "validated"
                  ? "bg-emerald-50 text-emerald-800"
                  : "bg-amber-50 text-amber-800"
              )}
            >
              {floodPreviewMessage}
            </p>
          )}

          <FloodDepthField value={visualOption} onChange={value => setVisualOption(value as ReportVisualOption | null)} />

          {/* Info Card */}
          <div className="bg-orange-50/70 border border-orange-100/50 rounded-xl p-3 text-[11px] leading-relaxed text-orange-950 space-y-1 shadow-sm">
            <div className="flex items-center gap-1.5 font-bold text-orange-800 mb-0.5">
              <HelpCircle className="w-3.5 h-3.5" />
              <span>Detour & Routing Tips</span>
            </div>
            <p>
              🚦 <strong>Road Rules:</strong> Snaps to streets (respects one-ways & divided lanes).
            </p>
            <p>
              🟠 <strong>Orange Line:</strong> Shows the segment that will be blocked in the system.
            </p>
          </div>

          <div className="sticky bottom-0 -mx-4 -mb-4 px-4 py-3 bg-white/95 backdrop-blur-md border-t border-gray-100 mt-auto z-30 shadow-[0_-4px_16px_rgba(0,0,0,0.04)] rounded-b-2xl">
            <Button
              type="button"
              disabled={!floodStart || !floodEnd || !visualOption || floodPreviewStatus === "loading"}
              onClick={() => setStep(2)}
              className="w-full bg-gray-900 hover:bg-gray-800 text-white font-semibold shadow-sm h-10 rounded-xl"
            >
              Next Step
            </Button>
          </div>
        </div>
      )}

      {!isViewingDrafts && step === 2 && !showSurvey && (
        <div className="space-y-4 animate-in fade-in slide-in-from-left-4 duration-300">
          <FloodSurveyLauncher complete={isSurveyComplete} onOpen={() => setShowSurvey(true)} />

          <FloodMediaField media={media} />
          <FloodDescriptionField value={description} onChange={setDescription} placeholder={isAdminMode ? "Enter official DRRMO statement, detour instructions, or zone details..." : "Describe the flood conditions (e.g., impassable to motorcycles, water is moving fast)"} />

          {/* Community Feed Sharing */}
          <div className="space-y-2 pt-2 border-t border-gray-100">
            <label className="flex items-start gap-2 cursor-pointer group">
              <div className="flex h-5 items-center">
                <input
                  type="checkbox"
                  checked={isPublic}
                  onChange={(e) => setIsPublic(e.target.checked)}
                  className="w-4 h-4 rounded border-gray-300 text-orange-600 focus:ring-orange-600 focus:ring-2"
                />
              </div>
              <div className="flex flex-col">
                <span className="text-sm font-medium text-gray-800 group-hover:text-gray-900">
                  Share in Community Feed
                </span>
              </div>
            </label>
            {isPublic && (
              <div className="bg-blue-50/70 border border-blue-100/50 rounded-lg p-3 text-[11px] leading-relaxed text-blue-900 space-y-1">
                <p>
                  This report will be shared publicly in the Community Feed immediately after submission. It will not appear as an official flood zone on the map unless an administrator approves it. Please ensure that the information provided is accurate and does not contain sensitive or personal information.
                </p>
              </div>
            )}
          </div>

          <div className="sticky bottom-0 -mx-4 -mb-4 px-4 py-3 bg-white/95 backdrop-blur-md border-t border-gray-100 mt-auto flex flex-col gap-2 z-30 shadow-[0_-4px_16px_rgba(0,0,0,0.04)] rounded-b-2xl">
            <Button
              type="button"
              variant="outline"
              disabled={!canSubmitCurrent || isSubmitting}
              onClick={handleDraftRoad}
              className="w-full h-10 rounded-xl font-medium border-orange-200 text-orange-700 hover:bg-orange-50"
            >
              Save & Add Another Road
            </Button>
            <div className="flex gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setStep(1)}
                className="flex-[1] h-10 rounded-xl font-medium"
              >
                Back
              </Button>
              <Button
                type="submit"
                disabled={!canSubmitAny}
                className="flex-[2] bg-orange-500 hover:bg-orange-600 focus:ring-orange-400 text-white font-semibold shadow-sm h-10 rounded-xl"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  <>
                    Submit All ({draftReports.length + (canSubmitCurrent ? 1 : 0)})
                    <CheckCircle className="w-4 h-4 ml-1.5" />
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      )}

      {!isViewingDrafts && step === 2 && showSurvey && (
        <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300 flex flex-col">
          {/* Survey Header */}
          <div className="flex items-center gap-2 pb-2 border-b border-gray-100">
            <button
              type="button"
              onClick={() => setShowSurvey(false)}
              className="p-1.5 -ml-1.5 text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded-full transition-colors"
              title="Back to report"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
            <h3 className="text-sm font-bold text-gray-800">Community Survey</h3>
          </div>

          <FloodSurveyFields vehicles={passableVehicles} onVehiclesChange={value => setPassableVehicles(value ?? [])} hazards={hiddenHazards} onHazardsChange={setHiddenHazards} />

          <div className="sticky bottom-0 -mx-4 -mb-4 px-4 py-3 bg-white/95 backdrop-blur-md border-t border-gray-100 mt-auto z-30 shadow-[0_-4px_16px_rgba(0,0,0,0.04)] rounded-b-2xl">
            <Button type="button" onClick={() => setShowSurvey(false)} className="w-full bg-gray-900 hover:bg-gray-800 text-white font-semibold h-10 rounded-xl">
              Done & Return
            </Button>
          </div>
        </div>
      )}
    </form>
  );

  if (!zoneUpdate && isMobile && isPickingOnMap && (activePoint === "flood_start" || activePoint === "flood_end")) {
    return (
      <MapPickerMobileOverlay 
        onCancel={() => {
          setIsPickingOnMap(false);
          setActivePoint(null);
        }}
        onConfirm={confirmMapLocation}
        confirmText={`Set ${activePoint === "flood_start" ? "Flood Start" : "Flood End"}`}
      />
    );
  }

  // Hide the panel body on mobile while picking if we were just returning null
  if (!zoneUpdate && isMobile && isPickingOnMap) return null;

  return (
    <Panel
      title={isAdminMode ? "Create Official Zone" : "Report Flood"}
      icon={isAdminMode ? <ShieldCheck className="h-4 w-4 text-blue-600" /> : <Navigation2 className="h-4 w-4 text-orange-600 rotate-180" />}
      iconBgClassName={isAdminMode ? "bg-blue-100" : "bg-orange-100"}
      headerActions={zoneUpdate && isAuthenticated && onReturnToReport ? (
        <Button
          type="button"
          variant="ghost"
          size="sm"
          disabled={isUpdatingZone}
          className="min-h-11 whitespace-nowrap px-2 text-xs text-gray-500"
          onPointerDown={event => event.stopPropagation()}
          onClick={event => { event.stopPropagation(); setDiscardUpdateKey(zoneUpdate.key); }}
        >
          New report
        </Button>
      ) : !zoneUpdate && !isViewingDrafts && editingDraft ? (
        <button
          type="button"
          onClick={(event) => {
            event.stopPropagation();
            cancelDraftEdit();
          }}
          className="rounded-md px-1.5 py-1 text-xs font-medium text-gray-500 transition-colors hover:bg-red-50 hover:text-red-600"
          title="Return this draft to Saved Drafts without applying changes"
        >
          Cancel edit
        </button>
      ) : undefined}
      isCollapsed={isCollapsed}
      onCollapseToggle={() => setActivePanel(isCollapsed ? "flood" : null)}
      isMobile={isMobile}
      isOpen={isOpen}
      onClose={() => { if (!isUpdatingZone) onClose(); }}
      mobileClassName={zoneUpdate ? "z-[60]" : undefined}
      mobileHeight={`${isAuthenticated ? "min(520px" : "min(440px"}, calc(100dvh - 80px - var(--bottom-nav-height) - env(safe-area-inset-bottom, 0px)))`}
      anchor="right"
      initialPosition={{ x: 16, y: 80 }}
      panelId="flood_report"
    >
      {zoneUpdate ? (isAuthenticated ? <ZoneUpdateForm key={zoneUpdate.key} zone={zoneUpdate.zone} initialCondition={zoneUpdate.condition} onClose={onClose} onSubmittingChange={setIsUpdatingZone} /> : <FloodReportLoginGate redirect={`/map?zone_update=${zoneUpdate.zone.id}&zone_condition=${zoneUpdate.condition}`} />) : formBody}
      <ConfirmDialog
        isOpen={!!zoneUpdate && isAuthenticated && discardUpdateKey === zoneUpdate.key}
        title="Discard this update?"
        message="Your current Flood Zone update fields and attachments will be lost. Your unfinished flood report will be kept."
        confirmLabel="Discard"
        cancelLabel="Keep editing"
        variant="destructive"
        isLoading={isUpdatingZone}
        onConfirm={() => {
          if (isUpdatingZone || !zoneUpdate || discardUpdateKey !== zoneUpdate.key) return;
          setDiscardUpdateKey(null);
          onReturnToReport?.();
        }}
        onCancel={() => setDiscardUpdateKey(null)}
      />
      <ConfirmDialog
        isOpen={isDiscardDialogOpen}
        title="Clear flood-report panel?"
        message="Clear only what is on this page, or remove the entire unfinished report and its queued drafts? Submitted reports stay."
        confirmLabel="Clear all"
        confirmVariant="outline"
        secondaryLabel="Clear this page"
        onSecondary={clearCurrentFloodReportPage}
        secondaryVariant="danger"
        size="sm"
        onConfirm={() => void discardDraft()}
        onCancel={() => setIsDiscardDialogOpen(false)}
      />
    </Panel>
  );
}
