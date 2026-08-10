"use client";

import { useState, useEffect, useCallback } from "react";
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
} from "lucide-react";
import Link from "next/link";
import { Input } from "@/shared/ui/Input";
import { Button } from "@/shared/ui/Button";
import { Select } from "@/shared/ui/Select";
import { MapPickerMobileOverlay } from "@/features/map/MapPickerMobileOverlay";
import { Panel } from "@/shared/ui/Panel";
import { useToast } from "@/shared/ui";
import { LocationAutocomplete } from "@/shared/ui/LocationAutocomplete";
import { cn } from "@/lib/utils";
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


// ── Point selector sub-component ─────────────────────────────────────────────

const POINT_COLORS = {
  start: {
    accent: "border-orange-200",
    stripe: "from-orange-500 to-amber-400",
    bg: "bg-orange-50",
    text: "text-orange-700",
    icon: "text-orange-500",
    label: "Flood Start",
  },
  end: {
    accent: "border-red-200",
    stripe: "from-red-500 to-rose-400",
    bg: "bg-red-50",
    text: "text-red-700",
    icon: "text-red-600",
    label: "Flood End",
  },
} as const;

function PointSelector({
  point,
  label,
  isActive,
  isSet,
  onActivate,
  onLabelChange,
  onSelect,
  onUseCurrent,
  onClear,
}: {
  point: "start" | "end";
  label: string;
  isActive: boolean;
  isSet: boolean;
  onActivate: () => void;
  onLabelChange: (value: string) => void;
  onSelect: (suggestion: LocationSuggestion) => void;
  onUseCurrent: () => void;
  onClear: () => void;
}) {
  const colors = POINT_COLORS[point];
  const Icon = point === "start" ? CircleDot : Flag;

  const renderTopOptions = () => (
    <>
      <li>
        <button
          type="button"
          className="flex w-full items-start gap-2 px-3 py-3 text-left text-sm hover:bg-orange-50 transition-colors border-b border-gray-100"
          onMouseDown={(e) => e.preventDefault()}
          onClick={onActivate}
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
          onClick={onUseCurrent}
        >
          <div className="bg-gray-100 p-1.5 rounded-full shrink-0">
            <MapPin className="h-4 w-4 text-gray-700" />
          </div>
          <span className="flex flex-col justify-center h-7 font-semibold text-gray-800">Use Current Location</span>
        </button>
      </li>
    </>
  );

  return (
    <div
      className={cn(
        "rounded-xl border bg-white transition-all",
        isActive
          ? "shadow-md border-orange-200 ring-1 ring-orange-100"
          : colors.accent
      )}
    >
      {/* Top accent stripe */}
      <div
        className={cn(
          "h-[3px] w-full bg-gradient-to-r rounded-t-xl",
          isActive ? "from-orange-500 to-amber-400" : colors.stripe
        )}
      />

      {/* Row label */}
      <div className="flex items-center justify-between px-3 pt-2 pb-1">
        <div className="flex items-center gap-1.5">
          <Icon className={cn("h-4 w-4", colors.icon)} />
          <span className={cn("text-xs font-semibold uppercase tracking-wide", colors.text)}>
            {colors.label}
          </span>
          {isSet && (
            <span className="flex items-center gap-0.5 text-[10px] font-medium text-green-600 bg-green-100 px-1.5 py-0.5 rounded-full">
              <Check className="h-3 w-3" />
              Set
            </span>
          )}
        </div>
      </div>

      {/* Autocomplete search */}
      <div className="px-3 pb-2.5 mt-1">
        <LocationAutocomplete
          value={label}
          onChange={onLabelChange}
          onSelect={onSelect}
          onClear={onClear}
          placeholder={point === "start" ? "e.g. Ortigas Ave, Pasig" : "e.g. C. Raymundo Ave"}
          className="[&_input]:h-9"
          renderTopOptions={renderTopOptions()}
        />
      </div>
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────────

export function FloodReportPanel({ isOpen, onClose }: FloodReportPanelProps) {
  const isMobile = useMediaQuery("(max-width: 640px), (pointer: coarse)");
  const { isAuthenticated } = useAuth();

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
  } = useMapContext();

  // Form state
  const [startInput, setStartInput] = useState("");
  const [endInput, setEndInput] = useState("");
  const [visualOption, setVisualOption] = useState<ReportVisualOption>("gutter");
  const [passableVehicles, setPassableVehicles] = useState<string[]>([]);
  const [hiddenHazards, setHiddenHazards] = useState<"yes" | "no" | "unsure" | "">("");
  const [showSurvey, setShowSurvey] = useState(false);
  const [description, setDescription] = useState("");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [isPublic, setIsPublic] = useState(false);
  const [step, setStep] = useState<1 | 2>(1);
  const isCollapsed = activePanel !== "flood";

  // Submission state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { success, error } = useToast();

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

  const handlePickOnMap = (target: "flood_start" | "flood_end") => {
    if (activePoint === target) {
      setActivePoint(null);
      setIsPickingOnMap(false);
    } else {
      setActivePoint(target);
      setIsPickingOnMap(true);
    }
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

  // ── Submit ─────────────────────────────────────────────────────────────────
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!floodStart || !floodEnd) {
      error("Missing Information", "Please set both the Flood Start and Flood End locations.");
      return;
    }
    if (!passableVehicles.length || !hiddenHazards) {
      error("Missing Information", "Please complete the Community Survey before submitting.");
      return;
    }

    setIsSubmitting(true);
    try {
      // 1. Get the actual road geometry between the two points, ignoring any existing active floods
      const routeResult = await getRoute(floodStart.coords, floodEnd.coords, true);
      const roadGeometry = routeResult.routes[0]?.geometry;

      // 2. Map visual option to backend severity
      const selectedOption = VISUAL_OPTIONS.find((opt) => opt.id === visualOption);
      const severity = selectedOption ? selectedOption.severity : "low";
      const depth = selectedOption ? selectedOption.label : null;

      // 3. Submit as multipart/form-data
      const formData = new FormData();
      formData.append("raw_text", description.trim());
      formData.append("source", "direct_user");
      formData.append("severity", severity);
      if (depth) {
        formData.append("depth", depth);
      }
      formData.append("is_public", isPublic.toString());
      formData.append("geometry", JSON.stringify(roadGeometry));
      formData.append(
        "survey_data",
        JSON.stringify({
          passable_vehicles: passableVehicles.length > 0 ? passableVehicles.join(", ") : null,
          hidden_hazards: hiddenHazards,
        })
      );
      if (imageFile) {
        formData.append("image", imageFile);
      }

      await apiClient.post<{ id: number }>("/reports", formData);

      // Reset form
      setFloodStart(null);
      setFloodEnd(null);
      setStartInput("");
      setEndInput("");
      setVisualOption("gutter");
      setPassableVehicles([]);
      setHiddenHazards("");
      setDescription("");
      setImageFile(null);
      setIsPublic(false);
      setStep(1);
      success("Report Submitted", "Flood report submitted successfully. It is now pending admin review.");
    } catch (err: unknown) {
      console.error("Error submitting flood report:", err);
      error("Submission Failed", "Failed to submit the report. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const isSurveyComplete = passableVehicles.length > 0 && hiddenHazards !== "";
  const canSubmit = !!floodStart && !!floodEnd && description.trim().length > 0 && isSurveyComplete && !isSubmitting;

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
      ? (passableVehicles.length > 0 || hiddenHazards !== "")
      : (description.trim() !== "" || imageFile !== null || visualOption !== "gutter" || isPublic || passableVehicles.length > 0 || hiddenHazards !== "");

  const clearButton =
    showClear ? (
      <button
        onClick={(e) => {
          e.preventDefault();
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
              setHiddenHazards("");
            } else {
              setVisualOption("gutter");
              setPassableVehicles([]);
              setHiddenHazards("");
              setDescription("");
              setImageFile(null);
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

  const formBody = !isAuthenticated ? (
    <div className="flex flex-col items-center justify-center h-full p-6 text-center space-y-4">
      <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center text-orange-500 mb-2 mt-8">
        <User className="w-8 h-8" />
      </div>
      <h3 className="text-lg font-bold text-gray-900">Login Required</h3>
      <p className="text-sm text-gray-500">
        You need to be logged in to report a flood and help the community.
      </p>
      <Link href="/profile" className="w-full mt-4">
        <Button className="w-full">Go to Login</Button>
      </Link>
    </div>
  ) : (
    <form onSubmit={handleSubmit} className="flex flex-col">
      {step === 1 && (
        <div className="space-y-4 animate-in fade-in slide-in-from-right-4 duration-300">
          {/* Point selectors */}
          <PointSelector
            point="start"
            label={startInput}
            isActive={activePoint === "flood_start"}
            isSet={!!floodStart}
            onActivate={() => handlePickOnMap("flood_start")}
            onLabelChange={(val) => { setStartInput(val); setFloodStartLabel(val); }}
            onSelect={(s) => {
              setFloodStart([s.lng, s.lat], s.label);
              setStartInput(s.label);
              setActivePoint("flood_end");
            }}
            onUseCurrent={() => handleUseCurrent("start")}
            onClear={() => { setFloodStart(null); setStartInput(""); setFloodStartLabel(""); }}
          />

          <PointSelector
            point="end"
            label={endInput}
            isActive={activePoint === "flood_end"}
            isSet={!!floodEnd}
            onActivate={() => handlePickOnMap("flood_end")}
            onLabelChange={(val) => { setEndInput(val); setFloodEndLabel(val); }}
            onSelect={(s) => {
              setFloodEnd([s.lng, s.lat], s.label);
              setEndInput(s.label);
            }}
            onUseCurrent={() => handleUseCurrent("end")}
            onClear={() => { setFloodEnd(null); setEndInput(""); setFloodEndLabel(""); }}
          />

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

          <div className="sticky bottom-0 left-0 right-0 bg-white pt-3 pb-4 border-t border-gray-100 mt-auto">
            <Button
              type="button"
              disabled={!floodStart || !floodEnd}
              onClick={() => setStep(2)}
              className="w-full bg-gray-900 hover:bg-gray-800 text-white font-semibold shadow-sm"
            >
              Next Step
            </Button>
          </div>
        </div>
      )}

      {step === 2 && !showSurvey && (
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

          {/* Image Upload */}
          <div className="space-y-1.5">
            <label className="text-sm font-semibold text-gray-800 block mb-1.5">
              Photo <span className="text-gray-400 font-normal ml-1">(Optional)</span>
            </label>
            {imageFile ? (
              <div className="relative rounded-md border border-gray-200 bg-gray-50 p-2 flex items-center justify-between">
                <span className="text-xs text-gray-600 truncate max-w-[200px]">{imageFile.name}</span>
                <button 
                  type="button" 
                  onClick={() => setImageFile(null)}
                  className="p-1 hover:bg-gray-200 rounded-full text-gray-500 transition-colors"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            ) : (
              <label className="flex items-center justify-center w-full rounded-md border border-dashed border-gray-300 px-3 py-4 bg-gray-50 hover:bg-orange-50 hover:border-orange-300 transition-colors cursor-pointer select-none text-sm text-gray-500">
                <div className="flex flex-col items-center gap-1">
                  <ImagePlus className="w-5 h-5 text-gray-400 mb-1" />
                  <span className="font-medium text-gray-600">Click to upload an image</span>
                  <span className="text-[10px] text-gray-400">JPEG, PNG up to 5MB</span>
                </div>
                <input 
                  type="file" 
                  accept="image/*" 
                  className="hidden" 
                  onChange={(e) => {
                    if (e.target.files && e.target.files.length > 0) {
                      setImageFile(e.target.files[0]);
                    }
                  }}
                />
              </label>
            )}
          </div>

          {/* Description */}
          <div className="space-y-1.5">
            <label className="text-sm font-semibold text-gray-800 block mb-1.5">
              Description <span className="text-red-500">*</span>
            </label>
            <textarea
              placeholder="Describe the flood conditions (e.g., impassable to motorcycles, water is moving fast)"
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

          <div className="sticky bottom-0 left-0 right-0 bg-white pt-3 pb-4 border-t border-gray-100 mt-auto flex gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => setStep(1)}
              className="flex-1"
            >
              Back
            </Button>
            <Button
              type="submit"
              disabled={!canSubmit}
              className="flex-[2] bg-orange-500 hover:bg-orange-600 focus:ring-orange-400 text-white font-semibold shadow-sm"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Submitting...
                </>
              ) : (
                "Submit Report"
              )}
            </Button>
          </div>
        </div>
      )}

      {step === 2 && showSurvey && (
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
          
          <div className="sticky bottom-0 left-0 right-0 bg-white pt-3 pb-4 border-t border-gray-100 mt-auto">
            <Button type="button" onClick={() => setShowSurvey(false)} className="w-full bg-gray-900 hover:bg-gray-800 text-white font-semibold">
              Done & Return
            </Button>
          </div>
        </div>
      )}
    </form>
  );

  return (
    <Panel
      title="Report Flood"
      icon={<Navigation2 className="h-4 w-4 text-orange-600 rotate-180" />}
      iconBgClassName="bg-orange-100"
      isCollapsed={isCollapsed}
      onCollapseToggle={() => setActivePanel(isCollapsed ? "flood" : null)}
      isMobile={isMobile}
      isOpen={isOpen}
      onClose={onClose}
      anchor="right"
      initialPosition={{ x: 16, y: 80 }}
      headerActions={clearButton}
    >
      {formBody}
    </Panel>
  );
}
