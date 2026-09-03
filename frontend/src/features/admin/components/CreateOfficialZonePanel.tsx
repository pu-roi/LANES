"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import {
  TerraDraw,
  TerraDrawPolygonMode,
  TerraDrawRectangleMode,
  TerraDrawCircleMode,
  TerraDrawFreehandMode
} from "terra-draw";
import { TerraDrawMapLibreGLAdapter } from "terra-draw-maplibre-gl-adapter";
import maplibregl from "maplibre-gl";
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
  Route,
  Hexagon,
  Square,
  Circle,
  Pencil,
  Trash2,
  Plus
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
import { SEVERITY_COLORS as MAP_SEVERITY_COLORS, SEVERITY_BORDER_COLORS } from "@/features/map/mapStyles";

// ── Types ──────────────────────────────────────────────────────────────────────

interface FloodReportPanelProps {
  isOpen: boolean;
  onClose: () => void;
  isAdminMode?: boolean;
  onAdminSubmit?: (formData: FormData) => Promise<void>;
  mapInstance?: any; // any to avoid maplibre-gl typing errors if not imported yet
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

const getTerraDrawActiveZoneStyles = (severity: Severity) => {
  const fillColor = (MAP_SEVERITY_COLORS[severity] || "#84cc16") as `#${string}`;
  const outlineColor = (SEVERITY_BORDER_COLORS[severity] || "#4d7c0f") as `#${string}`;
  return {
    fillColor,
    fillOpacity: 0.25,
    outlineColor,
    outlineWidth: 2.5,
    outlineOpacity: 0.85,
    closingPointColor: outlineColor,
    closingPointWidth: 8,
    closingPointOutlineColor: "#ffffff",
    closingPointOutlineWidth: 2,
    closingPointOpacity: 1,
    snappingPointColor: outlineColor,
    snappingPointWidth: 8,
    snappingPointOutlineColor: "#ffffff",
    snappingPointOutlineWidth: 2,
    snappingPointOpacity: 1,
    coordinatePointColor: outlineColor,
    coordinatePointWidth: 6,
    coordinatePointOutlineColor: "#ffffff",
    coordinatePointOutlineWidth: 2,
    coordinatePointOpacity: 1,
  };
};



// ── Main component ─────────────────────────────────────────────────────────────

export function CreateOfficialZonePanel({ isOpen, onClose, isAdminMode = false, onAdminSubmit, mapInstance }: FloodReportPanelProps) {
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
  const [zoneName, setZoneName] = useState("");
  const [zoneStatus, setZoneStatus] = useState<"active" | "scheduled">("active");
  const [step, setStep] = useState<1 | 2>(1);
  const isCollapsed = activePanel !== "flood";

  // Submission state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { success, error } = useToast();

  // Hydration logic
  const hasHydratedForm = useRef(false);

  useEffect(() => {
    const loadFormState = async () => {
      try {
        const savedTextState = localStorage.getItem("lanes_admin_flood_form_text");
        if (savedTextState) {
          const parsed = JSON.parse(savedTextState);
          if (parsed.zoneName) setZoneName(parsed.zoneName);
          if (parsed.zoneStatus) setZoneStatus(parsed.zoneStatus);
          if (parsed.description) setDescription(parsed.description);
          if (parsed.visualOption) setVisualOption(parsed.visualOption);
          if (parsed.passableVehicles) setPassableVehicles(parsed.passableVehicles);
          if (parsed.hiddenHazards) setHiddenHazards(parsed.hiddenHazards);
          if (parsed.isPublic !== undefined) setIsPublic(parsed.isPublic);
          if (parsed.showSurvey !== undefined) setShowSurvey(parsed.showSurvey);
          if (parsed.step) setStep(parsed.step);
        }

        const savedFiles = await get("lanes_admin_flood_form_files");
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
        zoneName,
        zoneStatus,
        description,
        visualOption,
        passableVehicles,
        hiddenHazards,
        isPublic,
        showSurvey,
        step
      };
      localStorage.setItem("lanes_admin_flood_form_text", JSON.stringify(state));
    } catch (e) {}
  }, [zoneName, zoneStatus, description, visualOption, passableVehicles, hiddenHazards, isPublic, showSurvey, step]);

  useEffect(() => {
    if (!hasHydratedForm.current) return;
    try {
      set("lanes_admin_flood_form_files", mediaFiles).catch(console.error);
    } catch (e) {}
  }, [mediaFiles]);

  // Drawing state - default to "line" (standard road segment mode)
  type GeometryMode = "line" | "polygon" | "freehand" | "rectangle" | "circle";
  const [geometryMode, setGeometryMode] = useState<GeometryMode>("line");
  const [drawInstance, setDrawInstance] = useState<any>(null);
  const [drawnGeometry, setDrawnGeometry] = useState<any>(null);
  const [drawnFeatures, setDrawnFeatures] = useState<any[]>([]);
  const [isDrawingMode, setIsDrawingMode] = useState(false);

  // Initialize Terra Draw
  const drawRef = useRef<TerraDraw | null>(null);

  useEffect(() => {
    if (!mapInstance) return;
    
    // Only initialize once
    if (drawRef.current) return;

    const initDraw = () => {
      // Create adapter and draw instance
      const adapter = new TerraDrawMapLibreGLAdapter({ map: mapInstance });
      
      const selectedOption = VISUAL_OPTIONS.find((opt) => opt.id === visualOption);
      const initialSeverity: Severity = selectedOption ? selectedOption.severity : "low";
      const initialStyles = getTerraDrawActiveZoneStyles(initialSeverity);

      const draw = new TerraDraw({
        adapter,
        modes: [
          new TerraDrawPolygonMode({ pointerDistance: 45, styles: initialStyles as any }),
          new TerraDrawFreehandMode({ pointerDistance: 45, styles: initialStyles as any }),
          new TerraDrawRectangleMode({ pointerDistance: 45, styles: initialStyles as any }),
          new TerraDrawCircleMode({ pointerDistance: 45, styles: initialStyles as any })
        ]
      });
      
      draw.start();
      drawRef.current = draw;
      setDrawInstance(draw);

      // Listen for drawing changes
      draw.on('change', () => {
        const snapshot = draw.getSnapshot();
        setDrawnFeatures(snapshot);
        if (snapshot.length === 1) {
          setDrawnGeometry(snapshot[0].geometry);
        } else if (snapshot.length > 1) {
          const multiPolyCoords = snapshot
            .map((f: any) => f.geometry?.coordinates)
            .filter(Boolean);
          setDrawnGeometry({
            type: "MultiPolygon",
            coordinates: multiPolyCoords,
          });
        } else {
          setDrawnGeometry(null);
        }
      });
    };

    if (mapInstance.isStyleLoaded()) {
      initDraw();
    } else {
      mapInstance.once('styledata', initDraw);
    }

    return () => {
      // Cleanup
      if (drawRef.current) {
        try {
          if (drawRef.current.enabled) {
            drawRef.current.stop();
          }
        } catch (e) {
          console.warn("TerraDraw stop warning:", e);
        }
        drawRef.current = null;
        setDrawInstance(null);
      }
    };
  }, [mapInstance]);

  // Mode switching - controlled explicitly by the user's selected mode and open state
  useEffect(() => {
    if (!drawRef.current) return;
    
    // If the panel is closed or we are in "line" mode, do not activate map drawing
    if (isCollapsed || geometryMode === "line") {
      try {
        if (drawRef.current.getMode() !== "static") {
          drawRef.current.setMode("static");
        }
      } catch {}
      setIsDrawingMode(false);
      return;
    }
    
    if (geometryMode === "polygon") {
      drawRef.current.setMode("polygon");
      setIsDrawingMode(true);
    } else if (geometryMode === "freehand") {
      drawRef.current.setMode("freehand");
      setIsDrawingMode(true);
    } else if (geometryMode === "rectangle") {
      drawRef.current.setMode("rectangle");
      setIsDrawingMode(true);
    } else if (geometryMode === "circle") {
      drawRef.current.setMode("circle");
      setIsDrawingMode(true);
    } else {
      drawRef.current.setMode("static");
      setIsDrawingMode(false);
    }
  }, [geometryMode, isCollapsed, drawInstance]);

  // Dynamically update Terra Draw styling when the selected severity / visual option changes
  const selectedVisualOption = VISUAL_OPTIONS.find((opt) => opt.id === visualOption);
  const currentSeverity: Severity = selectedVisualOption ? selectedVisualOption.severity : "low";

  useEffect(() => {
    if (!drawRef.current || !drawRef.current.enabled) return;

    const styles = getTerraDrawActiveZoneStyles(currentSeverity);
    try {
      drawRef.current.updateModeOptions("polygon", { styles: styles as any });
      drawRef.current.updateModeOptions("freehand", { styles: styles as any });
      drawRef.current.updateModeOptions("rectangle", { styles: styles as any });
      drawRef.current.updateModeOptions("circle", { styles: styles as any });
    } catch (err) {
      console.warn("Error updating TerraDraw styles:", err);
    }
  }, [currentSeverity, drawInstance]);

  const handleRemoveFeature = (id: string | number) => {
    if (!drawRef.current) return;
    try {
      drawRef.current.removeFeatures([id]);
      const updated = drawRef.current.getSnapshot();
      setDrawnFeatures(updated);
      if (updated.length === 1) {
        setDrawnGeometry(updated[0].geometry);
      } else if (updated.length > 1) {
        const multiPolyCoords = updated
          .map((f: any) => f.geometry?.coordinates)
          .filter(Boolean);
        setDrawnGeometry({
          type: "MultiPolygon",
          coordinates: multiPolyCoords,
        });
      } else {
        setDrawnGeometry(null);
      }
    } catch (err) {
      console.warn("Failed to remove feature:", err);
    }
  };

  const handleRemoveRoadSegment = () => {
    setFloodStart(null);
    setFloodEnd(null);
    setStartInput("");
    setEndInput("");
  };

  const handleClearAllFeatures = () => {
    if (drawRef.current) {
      try {
        drawRef.current.clear();
      } catch (err) {
        console.warn("Failed to clear features:", err);
      }
    }
    setDrawnFeatures([]);
    setDrawnGeometry(null);
    setFloodStart(null);
    setFloodEnd(null);
    setStartInput("");
    setEndInput("");
  };

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
    setActivePoint(target);
    setIsPickingOnMap(true);
  };

  // Direct map click to select point when picking on map is active
  useEffect(() => {
    if (!mapInstance || !isPickingOnMap || !activePoint) return;

    const handleMapClick = (e: any) => {
      const coords: [number, number] = [e.lngLat.lng, e.lngLat.lat];
      const label = `${coords[0].toFixed(5)}, ${coords[1].toFixed(5)}`;
      
      if (activePoint === "flood_start") {
        setFloodStart(coords, label);
        setStartInput(label);
        setActivePoint("flood_end");
      } else if (activePoint === "flood_end") {
        setFloodEnd(coords, label);
        setEndInput(label);
        setActivePoint(null);
        setIsPickingOnMap(false);
      }
    };

    mapInstance.on("click", handleMapClick);
    mapInstance.getCanvas().style.cursor = "crosshair";

    return () => {
      mapInstance.off("click", handleMapClick);
      mapInstance.getCanvas().style.cursor = "";
    };
  }, [mapInstance, isPickingOnMap, activePoint, setFloodStart, setFloodEnd, setActivePoint, setIsPickingOnMap]);

  // Markers for floodStart and floodEnd matching user-side FloodReportPanel
  const startMarkerRef = useRef<any>(null);
  const endMarkerRef = useRef<any>(null);

  useEffect(() => {
    if (!mapInstance) return;

    startMarkerRef.current?.remove();
    startMarkerRef.current = null;

    if (floodStart) {
      startMarkerRef.current = new maplibregl.Marker({ color: "#f97316" })
        .setLngLat(floodStart.coords)
        .addTo(mapInstance);
    }
  }, [mapInstance, floodStart]);

  useEffect(() => {
    if (!mapInstance) return;

    endMarkerRef.current?.remove();
    endMarkerRef.current = null;

    if (floodEnd) {
      endMarkerRef.current = new maplibregl.Marker({ color: "#991b1b" })
        .setLngLat(floodEnd.coords)
        .addTo(mapInstance);
    }
  }, [mapInstance, floodEnd]);

  // Draw the preview of the blocked road segment line (matching MapCanvas)
  // Draw the preview of the blocked road segment line (matching MapCanvas)
  useEffect(() => {
    if (!mapInstance || !mapInstance.isStyleLoaded()) return;

    const PREVIEW_SOURCE = "admin-flood-preview-source";
    const PREVIEW_LAYER = "admin-flood-preview-layer";

    if (mapInstance.getLayer(PREVIEW_LAYER)) mapInstance.removeLayer(PREVIEW_LAYER);
    if (mapInstance.getSource(PREVIEW_SOURCE)) mapInstance.removeSource(PREVIEW_SOURCE);

    if (!floodPreviewGeometry) return;

    mapInstance.addSource(PREVIEW_SOURCE, {
      type: "geojson",
      data: {
        type: "Feature",
        properties: {},
        geometry: floodPreviewGeometry,
      },
    });

    const activeColor = MAP_SEVERITY_COLORS[currentSeverity] || "#84cc16";

    mapInstance.addLayer({
      id: PREVIEW_LAYER,
      type: "line",
      source: PREVIEW_SOURCE,
      layout: { "line-join": "round", "line-cap": "round" },
      paint: {
        "line-color": activeColor,
        "line-width": 6,
        "line-dasharray": [2, 2],
        "line-opacity": 0.85,
      },
    });

    return () => {
      try {
        if (mapInstance.getLayer(PREVIEW_LAYER)) mapInstance.removeLayer(PREVIEW_LAYER);
        if (mapInstance.getSource(PREVIEW_SOURCE)) mapInstance.removeSource(PREVIEW_SOURCE);
      } catch {}
    };
  }, [mapInstance, floodPreviewGeometry, geometryMode, currentSeverity]);

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
    }
  }, [activePoint, mapCenter, setFloodStart, setFloodEnd, setActivePoint, setIsPickingOnMap]);

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
    if (!((floodStart && floodEnd && floodPreviewGeometry) || drawnFeatures.length > 0)) {
       return;
    }

    if (!passableVehicles.length || !hiddenHazards) {
      error("Missing Information", "Please complete the Community Survey before drafting.");
      return;
    }

    const selectedOption = VISUAL_OPTIONS.find((opt) => opt.id === visualOption);
    const severity = selectedOption ? selectedOption.severity : "low";
    const depth = selectedOption ? selectedOption.label : "";

    let draftGeometry = null;
    let draftBi = false;
    
    if (drawnFeatures.length > 0) {
      draftGeometry = drawnGeometry;
    } else {
      draftGeometry = floodPreviewGeometry;
      draftBi = isBidirectional;
    }

    const newDraft = {
      id: Math.random().toString(36).substring(7),
      geometry: draftGeometry,
      oppositeGeometry: floodOppositeGeometry,
      isBidirectional: draftBi,
      severity,
      depth,
      description,
      mediaFiles: [...mediaFiles],
      startLabel: startInput,
      endLabel: endInput,
      roadName: null,
    };

    setDraftReports((prev) => [...prev, newDraft]);

    // Reset current form for next draft
    setFloodStart(null);
    setFloodEnd(null);
    setStartInput("");
    setEndInput("");
    setDescription("");
    setVisualOption(null);
    setPassableVehicles([]);
    setHiddenHazards(null);
    setMediaFiles([]);
    setShowSurvey(false);
    setIsBidirectional(false);
    
    if (drawRef.current) {
      drawRef.current.clear();
      setDrawnFeatures([]);
      setDrawnGeometry(null);
    }

    setStep(1);

    success("Road Saved", "Road added to your draft list. You can add another or submit all.");
  };

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();

    if (!((floodStart && floodEnd) || drawnFeatures.length > 0 || draftReports.length > 0)) {
      error("Missing Information", "Please define a road segment or draw at least one shape on the map.");
      return;
    }

    const isCurrentFormFilled = ((!!floodStart && !!floodEnd && !!floodPreviewGeometry) || drawnFeatures.length > 0) && passableVehicles.length > 0 && hiddenHazards !== null;

    if (!isCurrentFormFilled && draftReports.length === 0) {
      error("Missing Information", "Please complete the Community Survey before submitting.");
      return;
    }

    setIsSubmitting(true);
    try {
      const payloadsToSubmit: any[] = [];
      const formsToSubmit: FormData[] = [];

      const selectedOption = VISUAL_OPTIONS.find((opt) => opt.id === visualOption);
      const severity = selectedOption ? selectedOption.severity : "low";
      const depth = selectedOption ? selectedOption.label : null;

      // Helper to create FormData (for non-admin fallback if needed, though this is admin mode)
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
        if (isAdminMode && onAdminSubmit) {
          payloadsToSubmit.push({
            name: zoneName.trim() || undefined,
            geometry: draft.geometry,
            severity_override: draft.severity,
            depth_override: draft.depth,
            admin_notes: draft.description.trim() || undefined,
            is_active: zoneStatus === "active"
          });
        } else {
          formsToSubmit.push(
            createFormData({
              description: draft.description,
              severity: draft.severity,
              depth: draft.depth,
              isPublic: isPublic,
              isBidirectional: draft.isBidirectional,
              geometry: draft.geometry,
              passableVehicles: null,
              hiddenHazards: "unsure",
              mediaFiles: draft.mediaFiles,
            })
          );
        }
      });

      // 2. Pack current form
      if (isCurrentFormFilled) {
        let finalGeometry = null;
        let isBi = false;

        if (drawnFeatures.length > 0) {
          finalGeometry = drawnGeometry;
        } else if (floodStart && floodEnd) {
          finalGeometry = floodPreviewGeometry;
          isBi = isBidirectional;
        }

        if (finalGeometry) {
          if (isAdminMode && onAdminSubmit) {
            payloadsToSubmit.push({
              name: zoneName.trim() || undefined,
              geometry: finalGeometry,
              severity_override: severity,
              depth_override: depth,
              admin_notes: description.trim() || undefined,
              is_active: zoneStatus === "active"
            });
          } else {
            formsToSubmit.push(
              createFormData({
                description: description,
                severity: severity,
                depth: depth,
                isPublic: isPublic,
                isBidirectional: isBi,
                geometry: finalGeometry,
                passableVehicles: passableVehicles.join(", "),
                hiddenHazards: hiddenHazards,
                mediaFiles: mediaFiles,
              })
            );
          }
        }
      }

      if (payloadsToSubmit.length === 0 && formsToSubmit.length === 0) {
        error("Empty", "No valid reports to submit.");
        return;
      }

      if (isAdminMode && onAdminSubmit) {
        for (const payload of payloadsToSubmit) {
          await onAdminSubmit(payload);
        }
      } else {
        await Promise.all(
          formsToSubmit.map((fd) => apiClient.post<{ id: number }>("/reports", fd))
        );
      }

      // Reset form
      setDraftReports([]);
      setFloodStart(null);
      setFloodEnd(null);
      setDescription("");
      setVisualOption(null);
      setPassableVehicles([]);
      setHiddenHazards(null);
      setMediaFiles([]);
      setZoneName("");
      setZoneStatus("active");
      setShowSurvey(false);
      setIsBidirectional(false);
      setStep(1);
      
      success(isAdminMode ? "Zones Created" : "Reports Submitted", isAdminMode ? "Official zones are now active." : "Thank you! Your reports are now in review.");
      if (onClose) onClose();
    } catch (err: unknown) {
      console.error("Error submitting flood report:", err);
      error("Submission Failed", "Failed to submit some reports. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const isSurveyComplete = passableVehicles.length > 0 && hiddenHazards !== null;
  const hasGeometry = geometryMode === "line" ? (!!floodStart && !!floodEnd) : !!drawnGeometry;
  const canSubmitCurrent = hasGeometry && description.trim().length > 0 && isSurveyComplete && (!isAdminMode || zoneName.trim().length > 0);
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
    ? (geometryMode === "line" ? (floodStart || floodEnd) : drawnGeometry) 
    : showSurvey
      ? (passableVehicles.length > 0 || hiddenHazards !== null)
      : (description.trim() !== "" || mediaFiles.length > 0 || visualOption !== "gutter" || isPublic || passableVehicles.length > 0 || hiddenHazards !== null);

  const clearButton =
    showClear ? (
      <button
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          if (step === 1) {
            if (geometryMode === "line") {
              setFloodStart(null);
              setFloodEnd(null);
              setStartInput("");
              setEndInput("");
            } else {
              if (drawRef.current) drawRef.current.clear();
              setDrawnGeometry(null);
            }
          } else {
            if (showSurvey) {
              setPassableVehicles([]);
              setHiddenHazards(null);
            } else {
              setVisualOption("gutter");
              setPassableVehicles([]);
              setHiddenHazards(null);
              setMediaFiles([]);
              setIsPublic(false);
              setZoneName("");
              setZoneStatus("active");
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
      <Link href="/profile" className="w-full mt-4">
        <Button className="w-full">Go to Login</Button>
      </Link>
    </div>
  ) : (
    <>
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
      {step === 1 && (
        <div className="space-y-4 animate-in fade-in slide-in-from-right-4 duration-300">
          
          {draftReports.length > 0 && (
            <div className="mb-4 bg-blue-50 rounded-xl p-3 border border-blue-100">
              <h4 className="text-[11px] uppercase tracking-wider font-bold text-blue-800 mb-2">Drafted Zones ({draftReports.length})</h4>
              <div className="space-y-1.5 max-h-[120px] overflow-y-auto pr-1">
                {draftReports.map((draft, idx) => (
                  <div key={draft.id} className="bg-white rounded-lg p-2 border border-blue-100/50 shadow-sm flex items-center justify-between text-xs">
                    <div className="truncate flex-1 min-w-0 pr-2">
                       <span className="font-semibold text-gray-800 truncate block">{draft.startLabel || "Polygon Zone"}</span>
                       <span className="text-gray-500 text-[10px] truncate block">{draft.severity.toUpperCase()} • {draft.depth}</span>
                    </div>
                    <button 
                      type="button" 
                      onClick={() => setDraftReports(prev => prev.filter(r => r.id !== draft.id))}
                      className="text-gray-400 hover:text-red-500 shrink-0 p-1"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
          {/* Geometry Selector */}
          <div className="grid grid-cols-5 gap-1.5 mb-4">
            <button
              type="button"
              onClick={() => {
                setGeometryMode("line");
                if (drawRef.current) {
                  drawRef.current.setMode("static");
                }
              }}
              className={cn("flex flex-col items-center gap-1.5 p-2 rounded-xl border-2 transition-all", geometryMode === "line" ? "border-blue-500 bg-blue-50 text-blue-700" : "border-gray-100 bg-white hover:bg-gray-50 text-gray-500")}
            >
              <Route className="w-4 h-4" />
              <span className="text-[9px] font-bold uppercase tracking-wider">Line</span>
            </button>
            <button
              type="button"
              onClick={() => {
                setGeometryMode("polygon");
                if (drawRef.current) {
                  drawRef.current.setMode("polygon");
                }
              }}
              className={cn("flex flex-col items-center gap-1.5 p-2 rounded-xl border-2 transition-all", geometryMode === "polygon" ? "border-blue-500 bg-blue-50 text-blue-700" : "border-gray-100 bg-white hover:bg-gray-50 text-gray-500")}
            >
              <Hexagon className="w-4 h-4" />
              <span className="text-[9px] font-bold uppercase tracking-wider">Polygon</span>
            </button>
            <button
              type="button"
              onClick={() => {
                setGeometryMode("freehand");
                if (drawRef.current) {
                  drawRef.current.setMode("freehand");
                }
              }}
              className={cn("flex flex-col items-center gap-1.5 p-2 rounded-xl border-2 transition-all", geometryMode === "freehand" ? "border-blue-500 bg-blue-50 text-blue-700" : "border-gray-100 bg-white hover:bg-gray-50 text-gray-500")}
            >
              <Pencil className="w-4 h-4" />
              <span className="text-[9px] font-bold uppercase tracking-wider">Freehand</span>
            </button>
            <button
              type="button"
              onClick={() => {
                setGeometryMode("rectangle");
                if (drawRef.current) {
                  drawRef.current.setMode("rectangle");
                }
              }}
              className={cn("flex flex-col items-center gap-1.5 p-2 rounded-xl border-2 transition-all", geometryMode === "rectangle" ? "border-blue-500 bg-blue-50 text-blue-700" : "border-gray-100 bg-white hover:bg-gray-50 text-gray-500")}
            >
              <Square className="w-4 h-4" />
              <span className="text-[9px] font-bold uppercase tracking-wider">Rect</span>
            </button>
            <button
              type="button"
              onClick={() => {
                setGeometryMode("circle");
                if (drawRef.current) {
                  drawRef.current.setMode("circle");
                }
              }}
              className={cn("flex flex-col items-center gap-1.5 p-2 rounded-xl border-2 transition-all", geometryMode === "circle" ? "border-blue-500 bg-blue-50 text-blue-700" : "border-gray-100 bg-white hover:bg-gray-50 text-gray-500")}
            >
              <Circle className="w-4 h-4" />
              <span className="text-[9px] font-bold uppercase tracking-wider">Circle</span>
            </button>
          </div>

          {geometryMode === "line" ? (
            <>
            {/* Location Inputs (Timeline Style) */}
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
          
          {/* Bidirectional Toggle for Line Mode */}
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
          </>
          ) : (
            <div className="flex flex-col items-center justify-center py-5 text-center bg-slate-50 rounded-xl border border-slate-200 border-dashed">
              <Crosshair className="w-6 h-6 text-slate-400 mb-1.5" />
              <h3 className="text-xs font-bold text-slate-700 mb-0.5">Draw on Map ({geometryMode})</h3>
              <p className="text-[11px] text-slate-500 px-4 max-w-xs">
                Click points on the map to draw your {geometryMode}. You can combine multiple shapes & road segments in this single zone.
              </p>
            </div>
          )}

          {/* Unified Shapes in this Zone Manager Card */}
          {(drawnFeatures.length > 0 || (floodStart && floodEnd)) && (
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-3.5 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-emerald-600" />
                  <span className="text-xs font-bold text-slate-800">
                    Shapes in this Zone ({drawnFeatures.length + (floodStart && floodEnd ? 1 : 0)})
                  </span>
                </div>
                <button
                  type="button"
                  onClick={handleClearAllFeatures}
                  className="text-[11px] font-semibold text-rose-600 hover:text-rose-700 bg-rose-50 hover:bg-rose-100 px-2 py-0.5 rounded-md transition-colors"
                >
                  Clear All
                </button>
              </div>

              {/* List of shapes & road segment */}
              <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
                {/* 1. Road Segment (if defined) */}
                {floodStart && floodEnd && (
                  <div className="flex items-center justify-between bg-white border border-slate-200/80 rounded-lg px-2.5 py-1.5 text-xs text-slate-700 shadow-2xs">
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="w-4 h-4 rounded-full bg-slate-100 flex items-center justify-center text-[10px] font-bold text-slate-600 shrink-0">
                        1
                      </span>
                      <Route className="w-3.5 h-3.5 text-orange-600 shrink-0" />
                      <span className="font-medium text-[11px] truncate">
                        Road Segment: {startInput || "Start"} ➔ {endInput || "End"}
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={handleRemoveRoadSegment}
                      className="p-1 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded transition-colors shrink-0 ml-2"
                      title="Remove road segment"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}

                {/* 2. Drawn Shapes */}
                {drawnFeatures.map((feature, idx) => {
                  const mode = feature.properties?.mode || "polygon";
                  const itemIndex = (floodStart && floodEnd ? 1 : 0) + idx + 1;
                  return (
                    <div
                      key={feature.id || idx}
                      className="flex items-center justify-between bg-white border border-slate-200/80 rounded-lg px-2.5 py-1.5 text-xs text-slate-700 shadow-2xs"
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        <span className="w-4 h-4 rounded-full bg-slate-100 flex items-center justify-center text-[10px] font-bold text-slate-600 shrink-0">
                          {itemIndex}
                        </span>
                        {mode === "rectangle" ? (
                          <Square className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                        ) : mode === "circle" ? (
                          <Circle className="w-3.5 h-3.5 text-indigo-600 shrink-0" />
                        ) : mode === "freehand" ? (
                          <Pencil className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                        ) : (
                          <Hexagon className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                        )}
                        <span className="font-medium capitalize text-[11px] truncate">
                          {mode === "rectangle" ? "Rectangle / Square" : mode === "circle" ? "Circle" : mode === "freehand" ? "Freehand Shape" : "Custom Polygon"}
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleRemoveFeature(feature.id)}
                        className="p-1 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded transition-colors shrink-0 ml-2"
                        title="Remove this shape"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  );
                })}
              </div>

              {/* Helper hint */}
              <div className="pt-2 border-t border-slate-200/70 text-center">
                <p className="text-[11px] text-slate-500">
                  💡 Select any tool above (<span className="font-semibold text-slate-700">Line, Polygon, Rect, Circle, Freehand</span>) to add more segments or shapes.
                </p>
              </div>
            </div>
          )}
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
              disabled={!((floodStart && floodEnd) || drawnFeatures.length > 0)}
              onClick={() => setStep(2)}
              className="w-full bg-gray-900 hover:bg-gray-800 text-white font-semibold shadow-sm h-10 rounded-xl"
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

          {isAdminMode && (
            <>
              {/* Zone Name */}
              <div className="space-y-1.5">
                <label className="text-sm font-semibold text-gray-800 block mb-1.5">
                  Zone Name <span className="text-red-500">*</span>
                </label>
                <Input
                  placeholder="e.g. C. Raymundo Deep Flood"
                  value={zoneName}
                  onChange={(e) => setZoneName(e.target.value)}
                  className="w-full bg-white"
                />
              </div>

              {/* Status */}
              <div className="space-y-1.5">
                <label className="text-sm font-semibold text-gray-800 block mb-1.5">
                  Status <span className="text-red-500">*</span>
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setZoneStatus("active")}
                    className={cn(
                      "rounded-md border py-2 text-sm font-medium transition-colors",
                      zoneStatus === "active"
                        ? "bg-green-50 border-green-300 text-green-700"
                        : "bg-white border-gray-200 text-gray-600 hover:bg-gray-50"
                    )}
                  >
                    Active Now
                  </button>
                  <button
                    type="button"
                    onClick={() => setZoneStatus("scheduled")}
                    className={cn(
                      "rounded-md border py-2 text-sm font-medium transition-colors",
                      zoneStatus === "scheduled"
                        ? "bg-blue-50 border-blue-300 text-blue-700"
                        : "bg-white border-gray-200 text-gray-600 hover:bg-gray-50"
                    )}
                  >
                    Scheduled
                  </button>
                </div>
              </div>
            </>
          )}

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

          {/* Community Feed Sharing - Only for normal users */}
          {!isAdminMode && (
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
          )}

          <div className="sticky bottom-0 -mx-4 -mb-4 px-4 py-3 bg-white/95 backdrop-blur-md border-t border-gray-100 mt-auto flex flex-col gap-2 z-30 shadow-[0_-4px_16px_rgba(0,0,0,0.04)] rounded-b-2xl">
            <Button
              type="button"
              variant="outline"
              disabled={!canSubmitCurrent || isSubmitting}
              onClick={handleDraftRoad}
              className="w-full h-10 rounded-xl font-medium border-orange-200 text-orange-700 hover:bg-orange-50"
            >
              Add Another Zone to Report
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
          
          <div className="sticky bottom-0 -mx-4 -mb-4 px-4 py-3 bg-white/95 backdrop-blur-md border-t border-gray-100 mt-auto z-30 shadow-[0_-4px_16px_rgba(0,0,0,0.04)] rounded-b-2xl">
            <Button type="button" onClick={() => setShowSurvey(false)} className="w-full bg-gray-900 hover:bg-gray-800 text-white font-semibold h-10 rounded-xl">
              Done & Return
            </Button>
          </div>
        </div>
      )}
    </form>
    </>
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
  // We don't return null for isDrawingMode because we need the floating banner (which is inside formBody) to render.
  if (isMobile && isPickingOnMap) return null;

  return (
    <>
      {/* Floating Map Instructions Banner rendered in bottom center of the map container */}
      {isDrawingMode && (
        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-50 pointer-events-auto animate-in fade-in slide-in-from-bottom-3 duration-200">
          <div className="flex items-center gap-3 bg-white/95 backdrop-blur-md px-4 py-2.5 rounded-full shadow-2xl border border-gray-200/90 text-gray-800 ring-1 ring-black/5">
            <div className="bg-blue-50 p-1.5 rounded-full text-blue-600 flex items-center justify-center">
              <Crosshair className="w-4 h-4 animate-pulse" />
            </div>
            <div className="flex flex-col">
              <span className="text-xs font-bold text-gray-900 capitalize">
                Drawing {geometryMode}
              </span>
              <span className="text-[11px] text-gray-500 font-medium">
                {geometryMode === "freehand"
                  ? "Click & drag on the map to draw"
                  : geometryMode === "circle"
                  ? "Click center & drag radius to draw"
                  : "Click on map to place points. Double-click to finish."}
              </span>
            </div>
            <button
              type="button"
              onClick={() => {
                if (drawRef.current) {
                  drawRef.current.setMode("static");
                  setIsDrawingMode(false);
                }
              }}
              className="ml-2 p-1.5 rounded-full text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors"
              title="Cancel drawing"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      <Panel
        title={isAdminMode ? "Create Official Zone" : "Report Flood"}
        icon={isAdminMode ? <ShieldCheck className="h-4 w-4 text-blue-600" /> : <Navigation2 className="h-4 w-4 text-orange-600 rotate-180" />}
        iconBgClassName={isAdminMode ? "bg-blue-100" : "bg-orange-100"}
        isCollapsed={isCollapsed}
        onCollapseToggle={() => {
          setActivePanel(isCollapsed ? "flood" : null);
        }}
        isMobile={isMobile}
        isOpen={isOpen}
        onClose={onClose}
        anchor="left"
        initialPosition={{ x: 16, y: 80 }}
        headerActions={clearButton}
        panelId="flood_report"
      >
        {formBody}
      </Panel>
    </>
  );
}
