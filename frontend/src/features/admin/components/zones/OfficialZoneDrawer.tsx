"use client";

import React, { useState, useEffect, useCallback } from "react";
import { cn } from "@/lib/utils";
import {
  ShieldCheck,
  ShieldAlert,
  X,
  RotateCcw,
  Plus,
  Send,
  Loader2,
  CheckCircle2,
  ImagePlus,
} from "lucide-react";
import { Button, useToast } from "@/shared/ui";
import { useMapContext } from "@/features/map/MapContext";
import { ZoneDataEditorForm, type ZoneDataEditorValues, VEHICLE_OPTIONS, HAZARD_OPTIONS } from "../ZoneDataEditorForm";
import { GeometryModeSelector } from "./subcomponents/GeometryModeSelector";
import { RoadSegmentPicker } from "./subcomponents/RoadSegmentPicker";
import { DraftZoneCart } from "./subcomponents/DraftZoneCart";
import { useTerraDraw } from "./hooks/useTerraDraw";
import { useZoneDrafts } from "./hooks/useZoneDrafts";
import type { GeometryMode, Severity, ZoneDraftItem } from "./types";
import { updateZone, type AvoidanceZone, type AvoidanceZoneUpdatePayload } from "../../adminApi";

export interface OfficialZoneDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  mapInstance?: any;
  editingZone?: AvoidanceZone | null;
  onAdminSubmit?: (payloads: any[], mediaFiles: File[]) => Promise<void>;
  onZoneUpdated?: () => void;
}

export function OfficialZoneDrawer({
  isOpen,
  onClose,
  mapInstance,
  editingZone = null,
  onAdminSubmit,
  onZoneUpdated,
}: OfficialZoneDrawerProps) {
  const { success, error } = useToast();
  const isEditMode = Boolean(editingZone);

  // Map context for Line mode
  const {
    floodStart,
    floodEnd,
    floodPreviewGeometry,
    floodOppositeGeometry,
    setFloodStart,
    setFloodEnd,
    setFloodStartLabel,
    setFloodEndLabel,
    floodIsBidirectional: isBidirectional,
    setFloodIsBidirectional: setIsBidirectional,
  } = useMapContext();

  // Mode and form states
  const [geometryMode, setGeometryMode] = useState<GeometryMode>("line");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [mediaFiles, setMediaFiles] = useState<File[]>([]);

  // Standalone survey + description state (rendered as separate sections)
  const [passableVehicles, setPassableVehicles] = useState<string[]>(
    editingZone?.passable_vehicles_override ? editingZone.passable_vehicles_override.split(",").filter(Boolean) : []
  );
  const [hiddenHazards, setHiddenHazards] = useState(editingZone?.hidden_hazards_override || "unsure");
  const [adminNotes, setAdminNotes] = useState(editingZone?.admin_notes || "");

  // Core attribute state (managed via ZoneDataEditorForm — depth/severity/bidirectional/buffer)
  const [editorValues, setEditorValues] = useState<ZoneDataEditorValues>({
    name: editingZone?.name || "Official Flood Avoidance Zone",
    severity: (editingZone?.severity_override as Severity) || "medium",
    depth: editingZone?.depth_override || "knee",
    passable_vehicles: editingZone?.passable_vehicles_override ? editingZone.passable_vehicles_override.split(",").filter(Boolean) : [],
    hidden_hazards: editingZone?.hidden_hazards_override || "unsure",
    is_bidirectional: editingZone?.is_bidirectional || false,
    geometry: (editingZone?.geometry as any) || { type: "LineString", coordinates: [] },
    admin_notes: editingZone?.admin_notes || "",
  });

  // TerraDraw hook
  const {
    drawnGeometry,
    drawnFeatures,
    isDrawingMode,
    clearDrawing,
    cancelDrawingMode,
  } = useTerraDraw({
    mapInstance,
    geometryMode,
    severity: editorValues.severity,
    isEnabled: isOpen,
  });

  // Draft Cart hook
  const { drafts, addDraft, removeDraft, clearDrafts } = useZoneDrafts();

  // Sync editingZone when it changes (including standalone survey + description state)
  useEffect(() => {
    if (editingZone) {
      const vehicles = editingZone.passable_vehicles_override
        ? editingZone.passable_vehicles_override.split(",").filter(Boolean)
        : [];
      setPassableVehicles(vehicles);
      setHiddenHazards(editingZone.hidden_hazards_override || "unsure");
      setAdminNotes(editingZone.admin_notes || "");
      setEditorValues({
        name: editingZone.name || `Official Zone #${editingZone.id}`,
        severity: (editingZone.severity_override as Severity) || "medium",
        depth: editingZone.depth_override || "knee",
        passable_vehicles: vehicles,
        hidden_hazards: editingZone.hidden_hazards_override || "unsure",
        is_bidirectional: editingZone.is_bidirectional || false,
        geometry: (editingZone.geometry as any) || { type: "LineString", coordinates: [] },
        admin_notes: editingZone.admin_notes || "",
      });
    }
  }, [editingZone]);

  // Current active geometry
  const currentGeometry = isEditMode
    ? editorValues.geometry
    : drawnFeatures.length > 0
    ? drawnGeometry
    : floodStart && floodEnd
    ? floodPreviewGeometry
    : null;

  const handleResetCurrent = useCallback(() => {
    setFloodStart(null);
    setFloodEnd(null);
    setFloodStartLabel("");
    setFloodEndLabel("");
    setIsBidirectional(false);
    clearDrawing();
    cancelDrawingMode();
  }, [setFloodStart, setFloodEnd, setFloodStartLabel, setFloodEndLabel, setIsBidirectional, clearDrawing, cancelDrawingMode]);

  // Handle Add to Draft Cart (Create mode only)
  const handleAddToDraftQueue = () => {
    if (!currentGeometry) {
      error("Missing Geometry", "Please define a road segment or draw a shape on the map first.");
      return;
    }

    const newDraft: ZoneDraftItem = {
      id: Math.random().toString(36).substring(7),
      geometry: currentGeometry,
      oppositeGeometry: isBidirectional ? floodOppositeGeometry : undefined,
      isBidirectional,
      name: editorValues.name,
      severity: editorValues.severity,
      depth: editorValues.depth,
      passableVehicles: passableVehicles,
      hiddenHazards: hiddenHazards,
      adminNotes: adminNotes,
      startLabel: floodStart?.label,
      endLabel: floodEnd?.label,
    };

    addDraft(newDraft);
    handleResetCurrent();
    success("Queued in Cart", "Hazard added to queue. Add another or publish all.");
  };

  // Handle Submit (Create mode or Edit mode)
  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setIsSubmitting(true);

    try {
      if (isEditMode && editingZone) {
        // Edit Mode: PUT /admin/zones/{id}
        const payload: AvoidanceZoneUpdatePayload = {
          name: editorValues.name,
          severity_override: editorValues.severity,
          depth_override: editorValues.depth,
          passable_vehicles_override: passableVehicles.join(","),
          hidden_hazards_override: hiddenHazards,
          admin_notes: adminNotes.trim(),
        };

        await updateZone(editingZone.id, payload);
        success("Zone Updated", `Official Zone #${editingZone.id} has been saved.`);
        if (onZoneUpdated) onZoneUpdated();
        onClose();
      } else {
        // Create Mode: Build payloads from current form + draft cart
        const payloads: any[] = [];

        // 1. Existing queued drafts
        drafts.forEach((d) => {
          payloads.push({
            name: d.name,
            geometry: d.geometry,
            severity_override: d.severity,
            depth_override: d.depth,
            passable_vehicles_override: d.passableVehicles.length > 0 ? d.passableVehicles.join(",") : undefined,
            hidden_hazards_override: d.hiddenHazards || undefined,
            admin_notes: d.adminNotes.trim() || undefined,
            is_active: true,
          });
        });

        // 2. Current active form if geometry is present
        if (currentGeometry) {
          payloads.push({
            name: editorValues.name,
            geometry: currentGeometry,
            severity_override: editorValues.severity,
            depth_override: editorValues.depth,
            passable_vehicles_override: passableVehicles.length > 0 ? passableVehicles.join(",") : undefined,
            hidden_hazards_override: hiddenHazards || undefined,
            admin_notes: adminNotes.trim() || undefined,
            is_active: true,
          });
        }

        if (payloads.length === 0) {
          error("Nothing to Submit", "Please define at least one road segment or drawn hazard.");
          setIsSubmitting(false);
          return;
        }

        if (onAdminSubmit) {
          await onAdminSubmit(payloads, mediaFiles);
        }

        clearDrafts();
        handleResetCurrent();
        setMediaFiles([]);
        success("Zones Published", `Successfully created ${payloads.length} official avoidance zone(s).`);
        onClose();
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to save avoidance zone.";
      error("Submission Error", msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <aside
      aria-label="Official Avoidance Zone Workspace"
      className="w-full h-full bg-white flex flex-col shrink-0 overflow-hidden select-text"
    >
      {/* DRAWER HEADER */}
      <div className="p-3.5 border-b border-slate-200 flex items-center justify-between bg-slate-50/80 shrink-0">
        <div className="flex items-center gap-2.5">
          <div
            className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-xs shadow-xs text-white ${
              isEditMode ? "bg-amber-600" : "bg-blue-600"
            }`}
          >
            {isEditMode ? <ShieldAlert className="w-4 h-4" /> : <ShieldCheck className="w-4 h-4" />}
          </div>
          <div>
            <h2 className="text-xs font-bold text-slate-800 tracking-tight flex items-center gap-1.5">
              <span>{isEditMode ? `Edit Zone #${editingZone?.id}` : "Create Official Zone"}</span>
              <span
                className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-full ${
                  isEditMode ? "bg-amber-100 text-amber-700" : "bg-blue-100 text-blue-700"
                }`}
              >
                {isEditMode ? "Edit Mode" : "Official DRRMO"}
              </span>
            </h2>
            <p className="text-[11px] text-slate-500 truncate max-w-[260px]">
              {isEditMode
                ? "Update zone severity, clearance, and operational notes"
                : "Define routing detour barrier on Pasig City road graph"}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1">
          {!isEditMode && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={handleResetCurrent}
              className="text-xs text-slate-500 hover:text-slate-800 h-8 px-2 rounded-lg"
              title="Reset current inputs"
            >
              <RotateCcw className="w-3.5 h-3.5 mr-1" />
              Reset
            </Button>
          )}

          {/* Mobile-only close button (hidden on desktop where outer handle is used) */}
          <button
            type="button"
            onClick={onClose}
            className="md:hidden p-1.5 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors"
            title="Close drawer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* DRAWER BODY (Scrollable) */}
      <div className="scrollbar-auto-hide flex-1 overflow-y-auto p-4 space-y-5">
        {/* SPATIAL GEOMETRY DEFINITION (Create mode only) */}
        {!isEditMode && (
          <div className="space-y-3">
            <label className="text-xs font-bold text-slate-700 uppercase tracking-wider block">
              1. Spatial Geometry
            </label>

            <GeometryModeSelector
              geometryMode={geometryMode}
              onChange={setGeometryMode}
              isDrawingMode={isDrawingMode}
              onCancelDrawing={cancelDrawingMode}
            />

            {geometryMode === "line" ? (
              <RoadSegmentPicker
                mapInstance={mapInstance}
                isBidirectional={isBidirectional}
                onBidirectionalChange={setIsBidirectional}
              />
            ) : (
              <div className="p-3 rounded-xl border border-dashed border-slate-300 bg-slate-50 text-center">
                <p className="text-xs text-slate-600 font-medium">
                  {drawnFeatures.length > 0
                    ? `Captured ${drawnFeatures.length} shape(s) on map.`
                    : `Click and draw your ${geometryMode} directly on the map.`}
                </p>
                {drawnFeatures.length > 0 && (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={clearDrawing}
                    className="mt-2 text-xs h-7 px-2.5 rounded-lg text-red-600 border-red-200 hover:bg-red-50"
                  >
                    Clear Drawing
                  </Button>
                )}
              </div>
            )}
          </div>
        )}

        {/* DRAFT CART QUEUE (Create mode) */}
        {!isEditMode && drafts.length > 0 && (
          <DraftZoneCart
            drafts={drafts}
            onRemoveDraft={removeDraft}
            onClearDrafts={clearDrafts}
          />
        )}

        {/* SECTION 2: HAZARD ATTRIBUTES — depth/severity + bidirectional + buffer */}
        <div className="space-y-3 pt-1 border-t border-slate-100">
          <label className="text-xs font-bold text-slate-700 uppercase tracking-wider block">
            {isEditMode ? "Hazard Attributes" : "2. Hazard Attributes"}
          </label>
          <ZoneDataEditorForm
            initialValues={editorValues}
            onChange={setEditorValues}
            readOnlyGeometry={true}
            hideBidirectional={!isEditMode && geometryMode === "line"}
            hideSurvey={true}
            hideDescription={true}
          />
        </div>

        {/* SECTION 3: SURVEY (required) */}
        <div className="space-y-3 pt-1 border-t border-slate-100">
          <label className="text-xs font-bold text-slate-700 uppercase tracking-wider block">
            {isEditMode ? "Survey" : "3. Survey"} <span className="text-red-500">*</span>
          </label>

          {/* Passable Vehicles */}
          <div>
            <label className="text-xs font-semibold text-slate-700 block mb-1">
              Which vehicles can safely pass? <span className="text-red-500">*</span>
            </label>
            <p className="text-[11px] text-slate-400 mb-2">Select all that apply.</p>
            <div className="grid grid-cols-2 gap-2">
              {VEHICLE_OPTIONS.map((v) => {
                const isChecked = passableVehicles.includes(v.id);
                return (
                  <label
                    key={v.id}
                    className={cn(
                      "flex items-center gap-2 rounded-lg border p-2 cursor-pointer transition-colors",
                      isChecked ? "border-blue-400 bg-blue-50" : "border-slate-200 hover:bg-slate-50"
                    )}
                  >
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setPassableVehicles(prev => [...prev, v.id]);
                        } else {
                          setPassableVehicles(prev => prev.filter(x => x !== v.id));
                        }
                      }}
                      className="w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500 focus:ring-2"
                    />
                    <span className={cn("text-xs font-medium", isChecked ? "text-blue-900" : "text-slate-700")}>
                      {v.label}
                    </span>
                  </label>
                );
              })}
            </div>
          </div>

          {/* Hidden Hazards */}
          <div>
            <label className="text-xs font-semibold text-slate-700 block mb-1">
              Are there hidden hazards? <span className="text-red-500">*</span>
            </label>
            <p className="text-[11px] text-slate-400 mb-2">E.g., open manholes, large debris underwater.</p>
            <div className="grid grid-cols-3 gap-2">
              {HAZARD_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setHiddenHazards(opt.value)}
                  className={cn(
                    "rounded-lg border py-2 text-xs font-semibold transition-colors",
                    hiddenHazards === opt.value
                      ? opt.activeClass
                      : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
                  )}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* SECTION 4: PHOTOS & VIDEOS (optional) */}
        <div className="space-y-2 pt-1 border-t border-slate-100">
          <label className="text-xs font-bold text-slate-700 uppercase tracking-wider block">
            {isEditMode ? "Photos & Videos" : "4. Photos & Videos"}{" "}
            <span className="text-[10px] font-normal text-slate-400 normal-case tracking-normal">(Optional)</span>
          </label>

          {mediaFiles.length > 0 && (
            <div className="grid grid-cols-2 gap-2">
              {mediaFiles.map((file, idx) => (
                <div
                  key={idx}
                  className="relative rounded-lg border border-slate-200 bg-slate-50 p-2 flex items-center justify-between group"
                >
                  <span className="text-xs text-slate-600 truncate max-w-[110px]">{file.name}</span>
                  <button
                    type="button"
                    onClick={() => setMediaFiles((prev) => prev.filter((_, i) => i !== idx))}
                    className="p-1 hover:bg-slate-200 rounded-full text-slate-500 transition-colors shrink-0"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          )}

          <label className="flex items-center justify-center w-full rounded-xl border border-dashed border-slate-300 px-3 py-4 bg-slate-50 hover:bg-blue-50 hover:border-blue-300 transition-colors cursor-pointer select-none">
            <div className="flex flex-col items-center gap-1">
              <ImagePlus className="w-5 h-5 text-slate-400 mb-1" />
              <span className="font-medium text-sm text-slate-600">Click to upload media</span>
              <span className="text-[10px] text-slate-400">JPEG, PNG, MP4 up to 10MB</span>
            </div>
            <input
              type="file"
              multiple
              accept="image/*,video/*"
              className="hidden"
              onChange={(e) => {
                if (e.target.files && e.target.files.length > 0) {
                  setMediaFiles((prev) => [...prev, ...Array.from(e.target.files!)]);
                }
                e.target.value = "";
              }}
            />
          </label>
        </div>

        {/* SECTION 5: DESCRIPTION (required) */}
        <div className="space-y-2 pt-1 border-t border-slate-100">
          <label className="text-xs font-bold text-slate-700 uppercase tracking-wider block">
            {isEditMode ? "Description" : "5. Description"} <span className="text-red-500">*</span>
          </label>
          <textarea
            value={adminNotes}
            onChange={(e) => setAdminNotes(e.target.value)}
            placeholder="e.g., Pumping truck stationed on westbound lane. Detour all light vehicles via Shaw Blvd."
            rows={3}
            className="w-full text-xs p-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 resize-none font-medium text-slate-800"
          />
        </div>
      </div>

      {/* DRAWER FOOTER */}
      <div className="p-3.5 border-t border-slate-200 bg-slate-50/90 flex items-center justify-between gap-2 shrink-0">
        {!isEditMode ? (
          <>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleAddToDraftQueue}
              disabled={isSubmitting || !currentGeometry}
              className="flex-1 h-9 rounded-xl text-xs font-semibold border-slate-200 hover:bg-white"
            >
              <Plus className="w-3.5 h-3.5 mr-1" />
              Add to Drafts
            </Button>

            <Button
              type="button"
              size="sm"
              onClick={() => handleSubmit()}
              disabled={isSubmitting || (!currentGeometry && drafts.length === 0)}
              className="flex-1 h-9 rounded-xl text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white shadow-sm"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />
                  Publishing...
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5 mr-1" />
                  {drafts.length > 0
                    ? `Publish All (${drafts.length + (currentGeometry ? 1 : 0)})`
                    : "Publish Zone"}
                </>
              )}
            </Button>
          </>
        ) : (
          <>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onClose}
              disabled={isSubmitting}
              className="flex-1 h-9 rounded-xl text-xs font-semibold"
            >
              Cancel
            </Button>

            <Button
              type="button"
              size="sm"
              onClick={() => handleSubmit()}
              disabled={isSubmitting}
              className="flex-1 h-9 rounded-xl text-xs font-semibold bg-amber-600 hover:bg-amber-700 text-white shadow-sm"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                  Save Changes
                </>
              )}
            </Button>
          </>
        )}
      </div>
    </aside>
  );
}
