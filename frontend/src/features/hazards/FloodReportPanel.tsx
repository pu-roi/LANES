"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import {
  CircleDot,
  Flag,
  Crosshair,
  MapPin,
  Check,
  CheckCircle,
  Loader2,
  Navigation2,
  HelpCircle,
  ImagePlus,
  X,
  ArrowLeft,
  User,
  ShieldCheck,
  Pencil,
  Trash2,
} from "lucide-react";
import { get, set } from "idb-keyval";
import Link from "next/link";
import { Input } from "@/shared/ui/Input";
import { Button } from "@/shared/ui/Button";
import { Select } from "@/shared/ui/Select";
import { MapPickerMobileOverlay } from "@/features/map/MapPickerMobileOverlay";
import { Panel } from "@/shared/ui/Panel";
import { useToast } from "@/shared/ui";
import { LocationAutocomplete } from "@/shared/ui/LocationAutocomplete";
import { cn, getBearing } from "@/lib/utils";
import { apiClient } from "@/lib/apiClient";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import { useAuth } from "@/hooks/useAuth";
import { getCurrentLocation } from "@/features/geocoding/geocodingApi";
import type { LocationSuggestion } from "@/features/geocoding/types";
import { useMapContext, type ActivePoint } from "@/features/map/MapContext";
import { getRoute } from "@/features/routing/routingApi";

// ── Types ──────────────────────────────────────────────────────────────────────

interface FloodReportPanelProps {
  isOpen: boolean;
  onClose: () => void;
  isAdminMode?: boolean;
  onAdminSubmit?: (formData: FormData) => Promise<void>;
}

type Severity = "low" | "medium" | "high" | "extreme";
type ReportVisualOption = "gutter" | "half-knee" | "half-tire" | "knee" | "tires" | "waist" | "chest" | "neck";

const SEVERITY_COLORS = {
  low: {
    pill: "border-lime-300 text-lime-700 bg-lime-50 hover:bg-lime-100",
    active: "border-lime-400 bg-lime-100 text-lime-800 ring-2 ring-lime-300/50",
  },
  medium: {
    pill: "border-amber-300 text-amber-700 bg-amber-50 hover:bg-amber-100",
    active: "border-amber-400 bg-amber-100 text-amber-800 ring-2 ring-amber-300/50",
  },
  high: {
    pill: "border-orange-300 text-orange-700 bg-orange-50 hover:bg-orange-100",
    active: "border-orange-400 bg-orange-100 text-orange-800 ring-2 ring-orange-300/50",
  },
  extreme: {
    pill: "border-red-300 text-red-700 bg-red-50 hover:bg-red-100",
    active: "border-red-400 bg-red-100 text-red-800 ring-2 ring-red-300/50",
  },
};

const SEVERITY_DOT_COLORS = {
  low: "bg-[#d8ed34]", // 80% yellow, 20% green
  medium: "bg-amber-400",
  high: "bg-orange-500",
  extreme: "bg-red-600",
};

const VISUAL_OPTIONS: {
  id: ReportVisualOption;
  severity: Severity;
  label: string;
  description: string;
}[] = [
  { id: "gutter", severity: "low", label: "Gutter", description: "8 inches" },
  { id: "half-knee", severity: "low", label: "Half-Knee", description: "10 inches" },
  { id: "half-tire", severity: "medium", label: "Half-Tire", description: "13 inches" },
  { id: "knee", severity: "medium", label: "Knee", description: "19 inches" },
  { id: "tires", severity: "high", label: "Tires", description: "26 inches" },
  { id: "waist", severity: "high", label: "Waist", description: "37 inches" },
  { id: "chest", severity: "high", label: "Chest", description: "45 inches" },
  { id: "neck", severity: "extreme", label: "Neck & Above", description: "Danger" },
];



// ── Main component ─────────────────────────────────────────────────────────────

export function FloodReportPanel({ isOpen, onClose, isAdminMode = false, onAdminSubmit }: FloodReportPanelProps) {
  const isMobile = useMediaQuery("(max-width: 640px), (pointer: coarse)");
  const { user, isAuthenticated } = useAuth();

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
    activePanel,
    setActivePanel,
    floodIsBidirectional: isBidirectional,
    setFloodIsBidirectional: setIsBidirectional,
    draftReports = [],
    setDraftReports,
    floodPreviewGeometry,
    floodOppositeGeometry
  } = useMapContext();

  // Form state
  const [startInput, setStartInput] = useState("");
  const [endInput, setEndInput] = useState("");
  const [visualOption, setVisualOption] = useState<ReportVisualOption | null>("gutter");
  const [passableVehicles, setPassableVehicles] = useState<string[]>([]);
  const [hiddenHazards, setHiddenHazards] = useState<"yes" | "no" | "unsure" | null>(null);
  const [showSurvey, setShowSurvey] = useState(false);
  const [description, setDescription] = useState("");
  const [mediaFiles, setMediaFiles] = useState<File[]>([]);
  const [isPublic, setIsPublic] = useState(false);
  const [step, setStep] = useState<1 | 2>(1);
  const [isViewingDrafts, setIsViewingDrafts] = useState(false);
  const [editingDraft, setEditingDraft] = useState<DraftReport | null>(null);
  const isCollapsed = activePanel !== "flood";

  // Submission state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { success, error } = useToast();

  // Hydration logic
  const hasHydratedForm = useRef(false);

  useEffect(() => {
    const loadFormState = async () => {
      try {
        const savedTextState = localStorage.getItem("lanes_active_flood_form_text");
        if (savedTextState) {
          const parsed = JSON.parse(savedTextState);
          if (parsed.description) setDescription(parsed.description);
          if (parsed.visualOption) setVisualOption(parsed.visualOption);
          if (parsed.passableVehicles) setPassableVehicles(parsed.passableVehicles);
          if (parsed.hiddenHazards) setHiddenHazards(parsed.hiddenHazards);
          if (parsed.isPublic !== undefined) setIsPublic(parsed.isPublic);
          if (parsed.showSurvey !== undefined) setShowSurvey(parsed.showSurvey);
          if (parsed.step) setStep(parsed.step);
        }

        const savedFiles = await get("lanes_active_flood_form_files");
        if (savedFiles && Array.isArray(savedFiles)) {
          setMediaFiles(savedFiles);
        }
      } catch (e) {
        console.error("Failed to load active form state", e);
      } finally {
        hasHydratedForm.current = true;
      }
    };
    loadFormState();
  }, []);

  useEffect(() => {
    if (!hasHydratedForm.current) return;
    try {
      const state = {
        description,
        visualOption,
        passableVehicles,
        hiddenHazards,
        isPublic,
        showSurvey,
        step
      };
      localStorage.setItem("lanes_active_flood_form_text", JSON.stringify(state));
    } catch (e) {}
  }, [description, visualOption, passableVehicles, hiddenHazards, isPublic, showSurvey, step]);

  useEffect(() => {
    if (!hasHydratedForm.current) return;
    try {
      set("lanes_active_flood_form_files", mediaFiles).catch(console.error);
    } catch (e) {}
  }, [mediaFiles]);

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
    setFloodStart(null);
    setFloodEnd(null);
    setStartInput("");
    setEndInput("");
    setFloodStartLabel("");
    setFloodEndLabel("");
    setDescription("");
    setVisualOption("gutter");
    setPassableVehicles([]);
    setHiddenHazards(null);
    setMediaFiles([]);
    setIsPublic(false);
    setShowSurvey(false);
    setIsBidirectional(false);
    setStep(1);
    setEditingDraft(null);
  };

  const handlePickOnMap = (target: "flood_start" | "flood_end") => {
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
  const handleUseCurrent = async (target: "start" | "end") => {
    try {
      const coords = await getCurrentLocation();
      const label = "Current Location";
      if (target === "start") {
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
  // ── Draft & Submit ─────────────────────────────────────────────────────────

  const handleDraftRoad = () => {
    if (!floodStart || !floodEnd || !floodPreviewGeometry) return;
    if (!passableVehicles.length || !hiddenHazards) {
      error("Missing Information", "Please complete the Community Survey before drafting.");
      return;
    }

    const selectedOption = VISUAL_OPTIONS.find((opt) => opt.id === visualOption);
    const severity = selectedOption ? selectedOption.severity : "low";
    const depth = selectedOption ? selectedOption.label : "";

    const newDraft = {
      id: Math.random().toString(36).substring(7),
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

    success("Road Saved", "Road added to your draft list. You can add another or submit all.");
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
      fd.append("is_public", data.isPublic.toString());
      fd.append("is_bidirectional", data.isBidirectional.toString());
      fd.append("geometry", JSON.stringify(data.geometry));
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
      formsToSubmit.push(
        createFormData({
          description: draft.description,
          severity: draft.severity,
          depth: draft.depth,
          isPublic: isPublic, // Shared across batch
          isBidirectional: draft.isBidirectional,
          geometry: draft.geometry,
          passableVehicles: null, // Let's just pass null for drafts for now
          hiddenHazards: "unsure",
          mediaFiles: draft.mediaFiles,
        })
      );
    });

    // 2. Pack current form if filled
    const isCurrentFormFilled = !!floodStart && !!floodEnd && description.trim().length > 0 && passableVehicles.length > 0 && hiddenHazards !== null && floodPreviewGeometry;
    
    if (isCurrentFormFilled) {
      const selectedOption = VISUAL_OPTIONS.find((opt) => opt.id === visualOption);
      formsToSubmit.push(
        createFormData({
          description: description,
          severity: selectedOption ? selectedOption.severity : "low",
          depth: selectedOption ? selectedOption.label : "",
          isPublic: isPublic,
          isBidirectional: isBidirectional,
          geometry: floodPreviewGeometry,
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
    try {
      if (isAdminMode && onAdminSubmit) {
        for (const fd of formsToSubmit) {
           await onAdminSubmit(fd);
        }
      } else {
        await Promise.all(
          formsToSubmit.map((fd) => apiClient.post<{ id: number }>("/reports", fd))
        );
      }

      // Reset everything
      setDraftReports([]);
      clearForm();
      
      success(isAdminMode ? "Zones Created" : "Reports Submitted", isAdminMode ? "Official zones are now active." : "Thank you! Your reports are now in review.");
      if (onClose) onClose();
    } catch (err: unknown) {
      console.error("Error submitting flood reports:", err);
      error("Submission Failed", "Failed to submit some reports. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const isSurveyComplete = passableVehicles.length > 0 && hiddenHazards !== null;
  const canSubmitCurrent = !!floodStart && !!floodEnd && description.trim().length > 0 && isSurveyComplete;
  const canSubmitAny = (draftReports.length > 0) || canSubmitCurrent;

  // ── Mobile map-pick overlay ────────────────────────────────────────────────
  if (isMobile && isPickingOnMap && (activePoint === "flood_start" || activePoint === "flood_end")) {
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
  const showClear = step === 1 
    ? (floodStart || floodEnd) 
    : showSurvey
      ? (passableVehicles.length > 0 || hiddenHazards !== null)
      : (description.trim() !== "" || mediaFiles.length > 0 || visualOption !== "gutter" || isPublic || passableVehicles.length > 0 || hiddenHazards !== null);

  const clearButton =
    editingDraft && !isViewingDrafts ? (
      <button
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          setDraftReports(prev => [...prev, editingDraft]);
          clearForm();
        }}
        className="text-[11px] font-medium text-blue-600 hover:text-blue-800 transition-colors px-2 py-1 mr-1 underline"
      >
        Cancel Edit
      </button>
    ) : showClear ? (
      <button
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          if (step === 1) {
            setFloodStart(null);
            setFloodEnd(null);
            setStartInput("");
            setEndInput("");
            setFloodStartLabel("");
            setFloodEndLabel("");
          } else {
            if (showSurvey) {
              setPassableVehicles([]);
              setHiddenHazards(null);
            } else {
              setVisualOption("gutter");
              setPassableVehicles([]);
              setHiddenHazards(null);
              setDescription("");
              setMediaFiles([]);
              setIsPublic(false);
            }
          }
        }}
        className="text-[11px] font-medium text-gray-500 hover:text-red-600 transition-colors px-2 py-1 mr-1"
        title={step === 1 ? "Clear locations" : "Clear details"}
      >
        Clear
      </button>
    ) : undefined;

  const formBody = (!isAuthenticated && !isAdminMode) ? (
    <div className="flex flex-col items-center justify-center h-full p-6 text-center space-y-4">
      <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center text-orange-500 mb-2 mt-8">
        <User className="w-8 h-8" />
      </div>
      <h3 className="text-lg font-bold text-gray-900">Login Required</h3>
      <p className="text-sm text-gray-500">
        You need to be logged in to report a flood and help the community.
      </p>
      <Link href="/login?redirect=%2Fmap%3Faction%3Dreport" className="w-full mt-4">
        <Button className="w-full">Go to Login</Button>
      </Link>
    </div>
  ) : (
    <form onSubmit={handleSubmit} className="flex flex-col">
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
        <div className="flex justify-between items-center mb-4 px-1">
          <span className="text-sm font-semibold text-gray-800">You have {draftReports.length} saved draft(s)</span>
          <button 
            type="button" 
            onClick={() => setIsViewingDrafts(true)}
            className="text-xs font-semibold bg-purple-100 text-purple-700 hover:bg-purple-200 px-3 py-1.5 rounded-full transition-colors flex items-center gap-1"
          >
            View Drafts
          </button>
        </div>
      )}

      {isViewingDrafts && (
        <div className="flex flex-col flex-1 animate-in fade-in zoom-in-95 duration-200 min-h-[300px]">
           <div className="flex items-center gap-2 mb-4">
             <button type="button" onClick={() => setIsViewingDrafts(false)} className="p-1.5 bg-gray-100 hover:bg-gray-200 rounded-full text-gray-700 transition-colors">
               <ArrowLeft className="w-4 h-4" />
             </button>
             <h3 className="font-bold text-gray-900 text-lg">Saved Drafts</h3>
           </div>
           
           <div className="space-y-3 overflow-y-auto pr-1 flex-1 pb-20">
              {draftReports.map((draft) => (
                 <div key={draft.id} className="bg-white border border-gray-200 rounded-xl p-3 shadow-sm relative group">
                    <div className="absolute top-3 right-3 flex gap-1">
                       <button 
                         type="button" 
                         onClick={() => {
                            if (draft.startCoords) setFloodStart(draft.startCoords, draft.startLabel);
                            if (draft.endCoords) setFloodEnd(draft.endCoords, draft.endLabel);
                            setStartInput(draft.startLabel || "");
                            setEndInput(draft.endLabel || "");
                            setDescription(draft.description);
                            const opt = VISUAL_OPTIONS.find(o => o.severity === draft.severity && o.label === draft.depth) || VISUAL_OPTIONS.find(o => o.severity === draft.severity);
                            setVisualOption(opt ? opt.id : null);
                            setIsBidirectional(draft.isBidirectional);
                            setMediaFiles(draft.mediaFiles || []);
                            setPassableVehicles(draft.passableVehicles || []);
                            setHiddenHazards(draft.hiddenHazards || null);
                            setIsPublic(draft.isPublic || false);
                            
                            setEditingDraft(draft);
                            setDraftReports(prev => prev.filter(r => r.id !== draft.id));
                            setIsViewingDrafts(false);
                            setStep(2);
                         }}
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
                       <span className={cn("px-2 py-0.5 rounded text-[10px] font-bold uppercase", SEVERITY_COLORS[draft.severity as Severity]?.pill)}>
                         {draft.severity} • {draft.depth}
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
          <div className="flex items-center mb-2">
            {/* Left Icons */}
            <div className="flex flex-col items-center justify-center gap-1 w-5 mr-2 relative z-10 shrink-0">
              <CircleDot className="w-3.5 h-3.5 text-green-600 shrink-0 bg-white" />
              <div className="w-[2px] h-5 bg-gray-200 border-l border-dashed border-gray-300" />
              <MapPin className="w-4 h-4 text-red-500 shrink-0 bg-white" />
            </div>

            {/* Inputs */}
            <div className="flex-1 flex flex-col gap-1.5 relative z-20 min-w-0">
              <div
                className={cn("w-full rounded-lg transition-all bg-gray-50 border", activePoint === "flood_start" ? "border-orange-400 ring-2 ring-orange-100 bg-white shadow-sm relative z-30" : "border-transparent relative z-10")}
                onClick={() => setActivePoint("flood_start")}
              >
                <LocationAutocomplete
                  value={startInput}
                  onChange={(val) => { setStartInput(val); setFloodStartLabel(val); }}
                  onSelect={(s) => {
                    setFloodStart([s.lng, s.lat], s.label);
                    setStartInput(s.label);
                    setActivePoint("flood_end");
                  }}
                  onClear={() => { setFloodStart(null); setStartInput(""); setFloodStartLabel(""); }}
                  placeholder="e.g. Ortigas Ave, Pasig (Start)"
                  className="[&_input]:border-none [&_input]:h-9 [&_input]:bg-transparent [&_input]:text-sm [&_input]:font-medium"
                  renderTopOptions={
                    <>
                      <li>
                        <button
                          type="button"
                          className="flex w-full items-start gap-2 px-3 py-3 text-left text-sm hover:bg-orange-50 transition-colors border-b border-gray-100"
                          onMouseDown={(e) => e.preventDefault()}
                          onClick={() => handlePickOnMap("flood_start")}
                        >
                          <div className="bg-orange-100 p-1.5 rounded-full shrink-0">
                            <Crosshair className="h-4 w-4 text-orange-700" />
                          </div>
                          <span className="flex flex-col justify-center h-7 font-semibold text-orange-700">Choose on Map</span>
                        </button>
                      </li>
                      <li>
                        <button
                          type="button"
                          className="flex w-full items-start gap-2 px-3 py-3 text-left text-sm hover:bg-orange-50 transition-colors border-b border-gray-100 mb-1"
                          onMouseDown={(e) => e.preventDefault()}
                          onClick={() => handleUseCurrent("start")}
                        >
                          <div className="bg-gray-100 p-1.5 rounded-full shrink-0">
                            <MapPin className="h-4 w-4 text-gray-700" />
                          </div>
                          <span className="flex flex-col justify-center h-7 font-semibold text-gray-800">Use Current Location</span>
                        </button>
                      </li>
                    </>
                  }
                />
              </div>
              <div
                className={cn("w-full rounded-lg transition-all bg-gray-50 border", activePoint === "flood_end" ? "border-red-400 ring-2 ring-red-100 bg-white shadow-sm relative z-30" : "border-transparent relative z-10")}
                onClick={() => setActivePoint("flood_end")}
              >
                <LocationAutocomplete
                  value={endInput}
                  onChange={(val) => { setEndInput(val); setFloodEndLabel(val); }}
                  onSelect={(s) => {
                    setFloodEnd([s.lng, s.lat], s.label);
                    setEndInput(s.label);
                  }}
                  onClear={() => { setFloodEnd(null); setEndInput(""); setFloodEndLabel(""); }}
                  placeholder="e.g. C. Raymundo Ave (End)"
                  className="[&_input]:border-none [&_input]:h-9 [&_input]:bg-transparent [&_input]:text-sm [&_input]:font-medium"
                  renderTopOptions={
                    <>
                      <li>
                        <button
                          type="button"
                          className="flex w-full items-start gap-2 px-3 py-3 text-left text-sm hover:bg-red-50 transition-colors border-b border-gray-100"
                          onMouseDown={(e) => e.preventDefault()}
                          onClick={() => handlePickOnMap("flood_end")}
                        >
                          <div className="bg-red-100 p-1.5 rounded-full shrink-0">
                            <Crosshair className="h-4 w-4 text-red-700" />
                          </div>
                          <span className="flex flex-col justify-center h-7 font-semibold text-red-700">Choose on Map</span>
                        </button>
                      </li>
                      <li>
                        <button
                          type="button"
                          className="flex w-full items-start gap-2 px-3 py-3 text-left text-sm hover:bg-red-50 transition-colors border-b border-gray-100 mb-1"
                          onMouseDown={(e) => e.preventDefault()}
                          onClick={() => handleUseCurrent("end")}
                        >
                          <div className="bg-gray-100 p-1.5 rounded-full shrink-0">
                            <MapPin className="h-4 w-4 text-gray-700" />
                          </div>
                          <span className="flex flex-col justify-center h-7 font-semibold text-gray-800">Use Current Location</span>
                        </button>
                      </li>
                    </>
                  }
                />
              </div>
            </div>
          </div>
          
          {/* Bidirectional Toggle */}
          <div className="flex items-start gap-2 mb-4 px-1 group cursor-pointer" onClick={() => setIsBidirectional(!isBidirectional)}>
             <div className="flex h-5 items-center mt-0.5">
                <input
                  type="checkbox"
                  checked={isBidirectional}
                  onChange={(e) => { e.stopPropagation(); setIsBidirectional(e.target.checked); }}
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
          </div>

          {/* Severity selector */}
          <div className="space-y-1">
            <label className="text-sm font-semibold text-gray-800 block mb-1.5">
              Flood Severity <span className="text-red-500 ml-0.5">*</span>
            </label>
            <div className="grid grid-cols-4 gap-2">
              {VISUAL_OPTIONS.map((opt) => {
                const colors = SEVERITY_COLORS[opt.severity];
                return (
                  <button
                    key={opt.id}
                    type="button"
                    onClick={() => setVisualOption(opt.id)}
                    className={cn(
                      "flex flex-col items-center gap-0.5 rounded-lg border px-2 py-2 text-xs font-semibold transition-all",
                      visualOption === opt.id ? colors.active : colors.pill
                    )}
                  >
                    <div className={cn("w-3.5 h-3.5 rounded-sm mb-0.5 shadow-sm shadow-black/10", SEVERITY_DOT_COLORS[opt.severity])}></div>
                    <span>{opt.label}</span>
                    <span className="font-normal text-[10px] opacity-75">{opt.description}</span>
                  </button>
                );
              })}
            </div>
          </div>

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
              disabled={!floodStart || !floodEnd}
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
          {/* Survey link */}
          <div className="py-2 border-b border-gray-100 flex items-center justify-between">
            <div className="flex flex-col">
              <span className="text-sm font-semibold text-gray-800 flex items-center gap-1.5">
                Community Survey <span className="text-red-500">*</span>
                {isSurveyComplete && (
                  <CheckCircle className="w-3.5 h-3.5 text-green-500" />
                )}
              </span>
              <span className="text-[11px] text-gray-500">
                {isSurveyComplete ? "Survey complete. Thank you!" : "Required to submit report"}
              </span>
            </div>
            <button
              type="button"
              onClick={() => setShowSurvey(true)}
              className="text-xs font-medium text-orange-600 bg-orange-50 hover:bg-orange-100 px-3 py-1.5 rounded-full transition-colors"
            >
              Take Survey
            </button>
          </div>

          {/* Media Upload */}
          <div className="space-y-1.5">
            <label className="text-sm font-semibold text-gray-800 flex items-center justify-between mb-1.5">
              <span>Photos & Videos <span className="text-gray-400 font-normal ml-1">(Optional)</span></span>
            </label>
            
            {mediaFiles.length > 0 && (
              <div className="grid grid-cols-2 gap-2 mb-2">
                {mediaFiles.map((file, idx) => (
                  <div key={idx} className="relative rounded-md border border-gray-200 bg-gray-50 p-2 flex items-center justify-between group">
                    <span className="text-xs text-gray-600 truncate max-w-[120px]">{file.name}</span>
                    <button 
                      type="button" 
                      onClick={() => setMediaFiles(prev => prev.filter((_, i) => i !== idx))}
                      className="p-1 hover:bg-gray-200 rounded-full text-gray-500 transition-colors"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            )}
            
            <label className="flex items-center justify-center w-full rounded-md border border-dashed border-gray-300 px-3 py-4 bg-gray-50 hover:bg-orange-50 hover:border-orange-300 transition-colors cursor-pointer select-none text-sm text-gray-500">
              <div className="flex flex-col items-center gap-1">
                <ImagePlus className="w-5 h-5 text-gray-400 mb-1" />
                <span className="font-medium text-gray-600">Click to upload media</span>
                <span className="text-[10px] text-gray-400">JPEG, PNG, MP4 up to 10MB</span>
              </div>
              <input 
                type="file" 
                multiple
                accept="image/*,video/*" 
                className="hidden" 
                onChange={(e) => {
                  if (e.target.files && e.target.files.length > 0) {
                    setMediaFiles(prev => [...prev, ...Array.from(e.target.files!)]);
                  }
                  e.target.value = ''; // Reset to allow selecting the same file again
                }}
              />
            </label>
          </div>

          {/* Description */}
          <div className="space-y-1.5">
            <label className="text-sm font-semibold text-gray-800 block mb-1.5">
              Description <span className="text-red-500">*</span>
            </label>
            <textarea
              placeholder={isAdminMode ? "Enter official DRRMO statement, detour instructions, or zone details..." : "Describe the flood conditions (e.g., impassable to motorcycles, water is moving fast)"}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full rounded-md border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-orange-400/30 focus:border-orange-400 resize-none"
            />
          </div>

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
                  This report may be shared publicly in the Community Feed after it has been reviewed and approved by an administrator. Please ensure that the information provided is accurate and does not contain sensitive or personal information.
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

          <div className="space-y-2">
            <label className="text-sm font-semibold text-gray-800 block mb-1.5">
              Which vehicles can safely pass? <span className="text-red-500">*</span>
            </label>
            <p className="text-xs text-gray-500 mb-2">Select all that apply.</p>
            <div className="grid grid-cols-2 gap-2">
              {[
                "Pedestrians",
                "Bicycles / E-Bikes",
                "Motorcycles",
                "Sedans / Hatchbacks",
                "SUVs / Pickups",
                "Large Trucks / Buses",
              ].map((vehicle) => {
                const isChecked = passableVehicles.includes(vehicle);
                return (
                  <label
                    key={vehicle}
                    className={cn(
                      "flex items-center gap-2 rounded-lg border p-2 cursor-pointer transition-colors",
                      isChecked ? "border-orange-400 bg-orange-50" : "border-gray-200 hover:bg-gray-50"
                    )}
                  >
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setPassableVehicles((prev) => [...prev, vehicle]);
                        } else {
                          setPassableVehicles((prev) => prev.filter((v) => v !== vehicle));
                        }
                      }}
                      className="w-4 h-4 rounded border-gray-300 text-orange-600 focus:ring-orange-600 focus:ring-2"
                    />
                    <span className={cn("text-xs font-medium", isChecked ? "text-orange-900" : "text-gray-700")}>
                      {vehicle}
                    </span>
                  </label>
                );
              })}
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-semibold text-gray-800 flex items-center justify-between">
              <span>Are there hidden hazards? <span className="text-red-500 ml-0.5">*</span></span>
            </label>
            <p className="text-xs text-gray-500 mb-2">E.g., open manholes, large debris underwater.</p>
            <div className="grid grid-cols-3 gap-2">
              {[
                { value: "yes", label: "Yes", activeClass: "bg-red-50 border-red-300 text-red-700" },
                { value: "no", label: "No", activeClass: "bg-green-50 border-green-300 text-green-700" },
                { value: "unsure", label: "Unsure", activeClass: "bg-gray-100 border-gray-300 text-gray-700" }
              ].map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setHiddenHazards(opt.value as any)}
                  className={cn(
                    "rounded-md border py-2 text-sm font-medium transition-colors",
                    hiddenHazards === opt.value
                      ? opt.activeClass
                      : "bg-white border-gray-200 text-gray-600 hover:bg-gray-50"
                  )}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
          
          <div className="sticky bottom-0 -mx-4 -mb-4 px-4 py-3 bg-white/95 backdrop-blur-md border-t border-gray-100 mt-auto z-30 shadow-[0_-4px_16px_rgba(0,0,0,0.04)] rounded-b-2xl">
            <Button type="button" onClick={() => setShowSurvey(false)} className="w-full bg-gray-900 hover:bg-gray-800 text-white font-semibold h-10 rounded-xl">
              Done & Return
            </Button>
          </div>
        </div>
      )}
    </form>
  );

  if (isMobile && isPickingOnMap && (activePoint === "flood_start" || activePoint === "flood_end")) {
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
  if (isMobile && isPickingOnMap) return null;

  return (
    <Panel
      title={isAdminMode ? "Create Official Zone" : "Report Flood"}
      icon={isAdminMode ? <ShieldCheck className="h-4 w-4 text-blue-600" /> : <Navigation2 className="h-4 w-4 text-orange-600 rotate-180" />}
      iconBgClassName={isAdminMode ? "bg-blue-100" : "bg-orange-100"}
      isCollapsed={isCollapsed}
      onCollapseToggle={() => setActivePanel(isCollapsed ? "flood" : null)}
      isMobile={isMobile}
      isOpen={isOpen}
      onClose={onClose}
      anchor="right"
      initialPosition={{ x: 16, y: 80 }}
      headerActions={clearButton}
      panelId="flood_report"
    >
      {formBody}
    </Panel>
  );
}
