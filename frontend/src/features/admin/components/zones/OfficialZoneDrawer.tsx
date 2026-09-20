"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
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
  FileVideo,
  ImagePlus,
  Route,
} from "lucide-react";
import { Button, ConfirmDialog, useToast } from "@/shared/ui";
import { useMapContext } from "@/features/map/MapContext";
import { useAuth } from "@/hooks/useAuth";
import { ZoneDataEditorForm, type ZoneDataEditorValues, VEHICLE_OPTIONS, HAZARD_OPTIONS } from "../ZoneDataEditorForm";
import { GeometryModeSelector } from "./subcomponents/GeometryModeSelector";
import { RoadSegmentPicker } from "./subcomponents/RoadSegmentPicker";
import { DraftZoneCart } from "./subcomponents/DraftZoneCart";
import { useTerraDraw } from "./hooks/useTerraDraw";
import { useZoneDrafts } from "./hooks/useZoneDrafts";
import type { GeometryMode, Severity, ZoneDraftItem } from "./types";
import type { RouteGeometry } from "@/features/routing/routingApi";
import { addZoneMedia, updateZone, type AvoidanceZone, type AvoidanceZoneUpdatePayload, type LineStringGeometry, type MultiLineStringGeometry, type PolygonGeometry, type MultiPolygonGeometry, type ReportGeometry } from "../../adminApi";
import {
  discardCreateZoneDraft,
  loadCreateZoneDraft,
  removeLegacyCreateZoneDraft,
  saveCreateZoneDraft,
} from "./zoneDraftStorage";
import {
  discardZoneEditDraft,
  areZoneEditValuesEqual,
  getZoneEditBaseline,
  getZoneEditValues,
  hasZoneEditChanges,
  loadZoneEditDraft,
  saveZoneEditDraft,
} from "./zoneEditDraftStorage";

export interface OfficialZoneDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  mapInstance?: any;
  editingZone?: AvoidanceZone | null;
  onAdminSubmit?: (items: ZoneSubmissionItem[]) => Promise<void>;
  onZoneUpdated?: () => void;
  onSwitchWorkspace?: () => void;
  switchWorkspaceLabel?: string;
  onShowMap?: () => void;
}

export interface ZoneSubmissionItem {
  payload: any;
  mediaFiles: File[];
}

interface SelectedMediaItem {
  file: File;
  previewUrl?: string;
}

function formatFileSize(bytes: number) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

type Position = [number, number];

function isPosition(value: unknown): value is Position {
  return Array.isArray(value) && value.length >= 2 &&
    typeof value[0] === "number" && typeof value[1] === "number";
}

function closeRing(ring: unknown): Position[] {
  if (!Array.isArray(ring) || ring.length < 3) {
    return Array.isArray(ring) ? (ring.filter(isPosition) as Position[]) : [];
  }
  const validPositions = ring.filter(isPosition) as Position[];
  if (validPositions.length < 3) return validPositions;
  const [firstLng, firstLat] = validPositions[0];
  const [lastLng, lastLat] = validPositions[validPositions.length - 1];
  return firstLng === lastLng && firstLat === lastLat
    ? validPositions
    : [...validPositions, [firstLng, firstLat]];
}

function normalizePolygonCoordinates(rawCoordinates: unknown): Position[][] {
  if (!Array.isArray(rawCoordinates) || rawCoordinates.length === 0) return [];
  // Case 1: Flat list of positions: [ [lng, lat], [lng, lat], ... ]
  if (isPosition(rawCoordinates[0])) {
    const ring = closeRing(rawCoordinates);
    return ring.length >= 3 ? [ring] : [];
  }
  // Case 2: Array of rings: [ [ [lng, lat], ... ], ... ]
  return (rawCoordinates as unknown[])
    .filter((ring): ring is unknown[] => Array.isArray(ring) && ring.length > 0)
    .map((ring) => closeRing(ring))
    .filter((ring) => ring.length >= 3);
}

/**
 * TerraDraw shape modes can emit a polygon as a flat list of positions.
 * The official-zone endpoint requires standard GeoJSON Polygon/MultiPolygon
 * ring nesting, so normalize it before drafts are saved or submitted.
 */
function normalizeOfficialZoneGeometry(geometry: ReportGeometry): ReportGeometry {
  if (!geometry) return geometry;

  if (geometry.type === "Polygon") {
    return {
      ...geometry,
      coordinates: normalizePolygonCoordinates(geometry.coordinates),
    };
  }

  if (geometry.type === "MultiPolygon") {
    const rawPolygons = Array.isArray(geometry.coordinates) ? geometry.coordinates : [];
    const normalizedPolygons: Position[][][] = [];

    for (const rawPoly of rawPolygons) {
      if (!Array.isArray(rawPoly) || rawPoly.length === 0) continue;
      if (isPosition(rawPoly[0])) {
        const ring = closeRing(rawPoly);
        if (ring.length >= 3) normalizedPolygons.push([ring]);
      } else {
        const polyCoords = normalizePolygonCoordinates(rawPoly);
        if (polyCoords.length > 0) {
          normalizedPolygons.push(polyCoords);
        }
      }
    }

    return {
      ...geometry,
      coordinates: normalizedPolygons,
    };
  }

  return geometry;
}

function buildValidatedRoadCoverage(
  original: ReportGeometry | null,
  opposite: ReportGeometry | null,
  isBidirectional: boolean,
): ReportGeometry | null {
  if (!original || original.type !== "LineString") return original;
  if (!isBidirectional || !opposite || opposite.type !== "LineString") return original;
  return {
    type: "MultiLineString",
    coordinates: [original.coordinates, opposite.coordinates],
  };
}

function isRoadGeometry(geometry: ReportGeometry | null | undefined): geometry is Extract<ReportGeometry, { type: "LineString" | "MultiLineString" }> {
  return geometry?.type === "LineString" || geometry?.type === "MultiLineString";
}

function isEditableZoneGeometry(
  geometry: ReportGeometry | null | undefined,
): geometry is LineStringGeometry | MultiLineStringGeometry | PolygonGeometry | MultiPolygonGeometry {
  return (
    geometry?.type === "LineString" ||
    geometry?.type === "MultiLineString" ||
    geometry?.type === "Polygon" ||
    geometry?.type === "MultiPolygon"
  );
}

function roadEndpoints(geometry: ReportGeometry): { start: Position; end: Position } | null {
  const line = geometry.type === "LineString"
    ? geometry.coordinates
    : geometry.type === "MultiLineString"
    ? geometry.coordinates[0]
    : null;
  if (!line || line.length < 2) return null;
  return { start: line[0], end: line[line.length - 1] };
}

function geometryToTerraFeatures(geometry: ReportGeometry): any[] {
  if (!geometry) return [];
  if (geometry.type === "Polygon") {
    return [{ type: "Feature", id: "saved-zone-area", properties: { mode: "polygon" }, geometry }];
  }
  if (geometry.type === "MultiPolygon") {
    return (geometry.coordinates as any[]).map((polyCoords, idx) => ({
      type: "Feature",
      id: `saved-zone-area-${idx}`,
      properties: { mode: "polygon" },
      geometry: {
        type: "Polygon",
        coordinates: polyCoords,
      },
    }));
  }
  return [];
}

export function OfficialZoneDrawer({
  isOpen,
  onClose,
  mapInstance,
  editingZone = null,
  onAdminSubmit,
  onZoneUpdated,
  onSwitchWorkspace,
  switchWorkspaceLabel,
  onShowMap,
}: OfficialZoneDrawerProps) {
  const { success, error } = useToast();
  const { user, isAuthenticated } = useAuth();
  const isEditMode = Boolean(editingZone);
  const userId = typeof user?.id === "string" || typeof user?.id === "number" ? String(user.id) : null;
  const canPersistDraft = !isEditMode && isAuthenticated && userId !== null;
  const canPersistEdit = isEditMode && isAuthenticated && userId !== null && editingZone !== null;

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
    setActivePoint,
    setIsPickingOnMap,
    restoreFloodReportMapState,
    floodIsBidirectional: isBidirectional,
    setFloodIsBidirectional: setIsBidirectional,
    floodShowMarkers,
    setFloodShowMarkers,
  } = useMapContext();

  // Mode and form states
  const [geometryMode, setGeometryMode] = useState<GeometryMode>("line");
  const [isEditingExistingShape, setIsEditingExistingShape] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isViewingDrafts, setIsViewingDrafts] = useState(false);
  const [isDiscardDialogOpen, setIsDiscardDialogOpen] = useState(false);
  const [editingDraft, setEditingDraft] = useState<ZoneDraftItem | null>(null);
  const [pendingDraftToEdit, setPendingDraftToEdit] = useState<ZoneDraftItem | null>(null);
  const [isSaveBeforeEditDialogOpen, setIsSaveBeforeEditDialogOpen] = useState(false);
  const [isCancelEditDialogOpen, setIsCancelEditDialogOpen] = useState(false);
  const [isDiscardingEdit, setIsDiscardingEdit] = useState(false);
  const [mediaItems, setMediaItems] = useState<SelectedMediaItem[]>([]);
  const createdPreviewUrlsRef = useRef(new Set<string>());
  const mediaFiles = mediaItems.map(({ file }) => file);

  // Standalone survey + description state (rendered as separate sections)
  const [passableVehicles, setPassableVehicles] = useState<string[]>(
    editingZone?.passable_vehicles_override ? editingZone.passable_vehicles_override.split(",").filter(Boolean) : []
  );
  const [hiddenHazards, setHiddenHazards] = useState(editingZone?.hidden_hazards_override || "");
  const [adminNotes, setAdminNotes] = useState(editingZone?.admin_notes || "");

  // Core attribute state (managed via ZoneDataEditorForm — depth/severity/bidirectional/buffer)
  const [editorValues, setEditorValues] = useState<ZoneDataEditorValues>({
    name: editingZone?.name || "Official Flood Avoidance Zone",
    severity: (editingZone?.severity_override as Severity) || "low",
    depth: editingZone?.depth_override || "",
    passable_vehicles: editingZone?.passable_vehicles_override ? editingZone.passable_vehicles_override.split(",").filter(Boolean) : [],
    hidden_hazards: editingZone?.hidden_hazards_override || "",
    is_bidirectional: editingZone?.is_bidirectional || false,
    geometry: (editingZone?.geometry as any) || { type: "LineString", coordinates: [] },
    admin_notes: editingZone?.admin_notes || "",
  });

  // TerraDraw hook
  const {
    drawnGeometry,
    drawnFeatures,
    isDrawingMode,
    drawInstance,
    clearDrawing,
    cancelDrawingMode,
    restoreDrawing,
  } = useTerraDraw({
    mapInstance,
    geometryMode,
    severity: editorValues.severity,
    // Connect Terra Draw only when this drawer is open to prevent multiple
    // drawers from clashing over the same map layers and sources.
    isEnabled: isOpen,
    isInteractive: isOpen,
    isEditingExistingShape,
  });

  // Draft Cart hook
  const { drafts, addDraft, removeDraft, clearDrafts, setDrafts } = useZoneDrafts();

  const hasHydratedDraft = useRef(false);
  const hydratedUserId = useRef<string | null>(null);
  const pendingDrawnFeatures = useRef<any[] | null>(null);
  const suppressNextDraftSave = useRef(false);
  const hasShownPersistenceError = useRef(false);
  const hasShownDrawingRestoreError = useRef(false);
  const hasHydratedEditDraft = useRef(false);
  const hydratedEditKey = useRef<string | null>(null);
  const editBaseline = useRef<ReturnType<typeof getZoneEditBaseline> | null>(null);
  const suppressEditDraftSave = useRef(false);

  const lineSessionCacheRef = useRef<{
    start: { coords: [number, number]; label: string } | null;
    end: { coords: [number, number]; label: string } | null;
    startLabel: string;
    endLabel: string;
    previewGeometry: RouteGeometry | null;
    oppositeGeometry: RouteGeometry | null;
    isBidirectional: boolean;
  }>({
    start: null,
    end: null,
    startLabel: "",
    endLabel: "",
    previewGeometry: null,
    oppositeGeometry: null,
    isBidirectional: false,
  });

  const polygonSessionCacheRef = useRef<{
    features: any[];
    geometry: ReportGeometry | null;
    mode: GeometryMode;
  }>({
    features: [],
    geometry: null,
    mode: "polygon",
  });

  const replaceMediaFiles = useCallback((files: File[]) => {
    createdPreviewUrlsRef.current.forEach((url) => URL.revokeObjectURL(url));
    createdPreviewUrlsRef.current.clear();
    setMediaItems(files.map((file) => {
      const previewUrl = file.type.startsWith("image/") ? URL.createObjectURL(file) : undefined;
      if (previewUrl) createdPreviewUrlsRef.current.add(previewUrl);
      return { file, previewUrl };
    }));
  }, []);

  // Sync editingZone when it changes (including standalone survey + description state)
  useEffect(() => {
    if (editingZone && isOpen) {
      const baseline = getZoneEditBaseline(editingZone);
      const { editorValues: baselineValues, passableVehicles: vehicles } = baseline;
      editBaseline.current = baseline;
      setPassableVehicles(vehicles);
      setHiddenHazards(baseline.hiddenHazards);
      setAdminNotes(baseline.adminNotes);
      const isRoad = isRoadGeometry(baselineValues.geometry);
      setGeometryMode(isRoad ? "line" : "polygon");
      setIsEditingExistingShape(!isRoad);
      setEditorValues(isRoad ? baselineValues : { ...baselineValues, is_bidirectional: false });
      if (isRoad) {
        const endpoints = roadEndpoints(baselineValues.geometry);
        const startPoint = endpoints ? { coords: endpoints.start, label: `${endpoints.start[0].toFixed(5)}, ${endpoints.start[1].toFixed(5)}` } : null;
        const endPoint = endpoints ? { coords: endpoints.end, label: `${endpoints.end[0].toFixed(5)}, ${endpoints.end[1].toFixed(5)}` } : null;
        const prevGeom: RouteGeometry | null = baselineValues.geometry.type === "LineString"
          ? { type: "LineString" as const, coordinates: baselineValues.geometry.coordinates as [number, number][] }
          : null;
        const oppGeom: RouteGeometry | null = baselineValues.geometry.type === "MultiLineString"
          ? { type: "LineString" as const, coordinates: (baselineValues.geometry.coordinates[1] ?? []) as [number, number][] }
          : null;

        lineSessionCacheRef.current = {
          start: startPoint,
          end: endPoint,
          startLabel: startPoint?.label || "",
          endLabel: endPoint?.label || "",
          previewGeometry: prevGeom,
          oppositeGeometry: oppGeom,
          isBidirectional: baselineValues.is_bidirectional,
        };
        polygonSessionCacheRef.current = {
          features: [],
          geometry: null,
          mode: "polygon",
        };

        setFloodShowMarkers(true);
        restoreFloodReportMapState({
          floodStart: startPoint,
          floodEnd: endPoint,
          floodPreviewGeometry: prevGeom,
          floodOppositeGeometry: oppGeom,
          floodIsBidirectional: baselineValues.is_bidirectional,
        });
      } else {
        const polyFeatures = geometryToTerraFeatures(baselineValues.geometry);
        polygonSessionCacheRef.current = {
          features: polyFeatures,
          geometry: baselineValues.geometry,
          mode: "polygon",
        };
        lineSessionCacheRef.current = {
          start: null,
          end: null,
          startLabel: "",
          endLabel: "",
          previewGeometry: null,
          oppositeGeometry: null,
          isBidirectional: false,
        };

        setFloodShowMarkers(false);
        restoreFloodReportMapState({
          floodStart: null,
          floodEnd: null,
          floodPreviewGeometry: null,
          floodOppositeGeometry: null,
          floodIsBidirectional: false,
        });
        pendingDrawnFeatures.current = polyFeatures;
      }
    }
  }, [editingZone, isOpen, restoreFloodReportMapState, setFloodShowMarkers]);

  // Edit Zone is a per-admin local workspace. The server's current version is
  // authoritative if another admin has saved this zone since this draft began.
  useEffect(() => {
    if (!isOpen || !canPersistEdit || !editingZone || !userId) {
      hasHydratedEditDraft.current = false;
      hydratedEditKey.current = null;
      return;
    }

    let cancelled = false;
    const draftKey = `${userId}:${editingZone.id}`;
    hasHydratedEditDraft.current = false;
    hydratedEditKey.current = null;
    void loadZoneEditDraft(userId, editingZone.id).then((draft) => {
      if (cancelled) return;
      const baseline = getZoneEditBaseline(editingZone);
      editBaseline.current = baseline;
      if (
        draft
        && draft.baselineUpdatedAt === editingZone.updated_at
        && areZoneEditValuesEqual(draft.baseline, baseline)
        && hasZoneEditChanges(getZoneEditValues(draft), draft.baseline, draft.mediaFiles)
      ) {
        setEditorValues(draft.editorValues);
        setPassableVehicles(draft.passableVehicles);
        setHiddenHazards(draft.hiddenHazards);
        setAdminNotes(draft.adminNotes);
        replaceMediaFiles(draft.mediaFiles);
        if (isRoadGeometry(draft.editorValues.geometry)) {
          const endpoints = roadEndpoints(draft.editorValues.geometry);
          const startPoint = endpoints ? { coords: endpoints.start, label: `${endpoints.start[0].toFixed(5)}, ${endpoints.start[1].toFixed(5)}` } : null;
          const endPoint = endpoints ? { coords: endpoints.end, label: `${endpoints.end[0].toFixed(5)}, ${endpoints.end[1].toFixed(5)}` } : null;
          const prevGeom: RouteGeometry | null = draft.editorValues.geometry.type === "LineString"
            ? { type: "LineString" as const, coordinates: draft.editorValues.geometry.coordinates as [number, number][] }
            : null;
          const oppGeom: RouteGeometry | null = draft.editorValues.geometry.type === "MultiLineString"
            ? { type: "LineString" as const, coordinates: (draft.editorValues.geometry.coordinates[1] ?? []) as [number, number][] }
            : null;

          lineSessionCacheRef.current = {
            start: startPoint,
            end: endPoint,
            startLabel: startPoint?.label || "",
            endLabel: endPoint?.label || "",
            previewGeometry: prevGeom,
            oppositeGeometry: oppGeom,
            isBidirectional: draft.editorValues.is_bidirectional,
          };
          polygonSessionCacheRef.current = {
            features: [],
            geometry: null,
            mode: "polygon",
          };

          setGeometryMode("line");
          setIsEditingExistingShape(false);
          setFloodShowMarkers(true);
          restoreFloodReportMapState({
            floodStart: startPoint,
            floodEnd: endPoint,
            floodPreviewGeometry: prevGeom,
            floodOppositeGeometry: oppGeom,
            floodIsBidirectional: draft.editorValues.is_bidirectional,
          });
        } else if (draft.editorValues.geometry.type === "Polygon" || draft.editorValues.geometry.type === "MultiPolygon") {
          const polyFeatures = geometryToTerraFeatures(draft.editorValues.geometry);
          polygonSessionCacheRef.current = {
            features: polyFeatures,
            geometry: draft.editorValues.geometry,
            mode: "polygon",
          };
          lineSessionCacheRef.current = {
            start: null,
            end: null,
            startLabel: "",
            endLabel: "",
            previewGeometry: null,
            oppositeGeometry: null,
            isBidirectional: false,
          };

          setGeometryMode("polygon");
          setIsEditingExistingShape(true);
          setFloodShowMarkers(false);
          pendingDrawnFeatures.current = polyFeatures;
        }
        success("Edit Restored", `Your unfinished edits for Zone #${editingZone.id} are ready to continue.`);
      } else if (draft) {
        void discardZoneEditDraft(userId, editingZone.id);
        if (draft.baselineUpdatedAt !== editingZone.updated_at) {
          error("Zone Updated", "Another administrator saved a newer version, so the latest zone details are shown.");
        }
      }
    }).catch((err) => {
      console.error("Failed to restore Edit Zone draft", err);
      if (!cancelled) error("Draft Unavailable", "Your unfinished zone edit could not be restored.");
    }).finally(() => {
      if (!cancelled) {
        hydratedEditKey.current = draftKey;
        hasHydratedEditDraft.current = true;
      }
    });
    return () => { cancelled = true; };
  }, [canPersistEdit, editingZone, error, isOpen, replaceMediaFiles, restoreFloodReportMapState, success, userId]);

  useEffect(() => {
    if (
      !isOpen ||
      isSubmitting ||
      suppressEditDraftSave.current ||
      !canPersistEdit ||
      !editingZone ||
      !userId ||
      !hasHydratedEditDraft.current
    ) return;
    if (hydratedEditKey.current !== `${userId}:${editingZone.id}`) return;
    const values = { editorValues, passableVehicles, hiddenHazards, adminNotes };
    const baseline = editBaseline.current ?? getZoneEditBaseline(editingZone);
    if (!hasZoneEditChanges(values, baseline, mediaFiles)) {
      void discardZoneEditDraft(userId, editingZone.id);
      return;
    }
    void saveZoneEditDraft(userId, editingZone.id, {
      baselineUpdatedAt: editingZone.updated_at,
      baseline,
      editorValues,
      passableVehicles,
      hiddenHazards,
      adminNotes,
      mediaFiles,
    }).catch((err) => {
      console.error("Failed to save Edit Zone draft", err);
      if (!hasShownPersistenceError.current) {
        hasShownPersistenceError.current = true;
        error("Draft Not Saved", "Your unfinished zone edit could not be saved on this device.");
      }
    });
  }, [adminNotes, canPersistEdit, editingZone, editorValues, error, hiddenHazards, isOpen, isSubmitting, mediaFiles, passableVehicles, userId]);

  useEffect(() => () => {
    createdPreviewUrlsRef.current.forEach((url) => URL.revokeObjectURL(url));
    createdPreviewUrlsRef.current.clear();
  }, []);

  const clearCurrentZone = useCallback(() => {
    setGeometryMode("line");
    restoreFloodReportMapState({
      floodStart: null,
      floodEnd: null,
      floodPreviewGeometry: null,
      floodOppositeGeometry: null,
      floodIsBidirectional: false,
    });
    clearDrawing();
    cancelDrawingMode();
    setEditorValues({
      name: "Official Flood Avoidance Zone",
      severity: "low",
      depth: "",
      passable_vehicles: [],
      hidden_hazards: "",
      is_bidirectional: false,
      geometry: { type: "LineString", coordinates: [] },
      admin_notes: "",
    });
    setPassableVehicles([]);
    setHiddenHazards("");
    setAdminNotes("");
    replaceMediaFiles([]);
  }, [cancelDrawingMode, clearDrawing, replaceMediaFiles, restoreFloodReportMapState]);

  const clearCreateWorkspace = useCallback(() => {
    clearCurrentZone();
    setDrafts([]);
    setIsViewingDrafts(false);
    setEditingDraft(null);
  }, [clearCurrentZone, setDrafts]);

  useEffect(() => {
    if (isEditMode || !isOpen) {
      hasHydratedDraft.current = false;
      hydratedUserId.current = null;
      return;
    }
    if (!canPersistDraft || !userId) {
      hasHydratedDraft.current = false;
      hydratedUserId.current = null;
      queueMicrotask(clearCreateWorkspace);
      return;
    }

    let cancelled = false;
    hasHydratedDraft.current = false;
    hydratedUserId.current = null;
    queueMicrotask(clearCreateWorkspace);

    const hydrate = async () => {
      try {
        await removeLegacyCreateZoneDraft();
        const saved = await loadCreateZoneDraft(userId);
        if (cancelled || !saved) return;
        const { active } = saved;
        setGeometryMode(active.geometryMode);
        setEditorValues(active.editorValues);
        setPassableVehicles(active.passableVehicles);
        setHiddenHazards(active.hiddenHazards);
        setAdminNotes(active.adminNotes);
        replaceMediaFiles(active.mediaFiles);
        setDrafts(saved.queuedDrafts);
        pendingDrawnFeatures.current = active.drawnFeatures;
        restoreFloodReportMapState({
          floodStart: active.floodStart,
          floodEnd: active.floodEnd,
          floodPreviewGeometry: active.floodPreviewGeometry,
          floodOppositeGeometry: active.floodOppositeGeometry,
          floodIsBidirectional: active.floodIsBidirectional,
        });
        success("Draft Restored", "Your unfinished official zone is ready to continue.");
      } catch (err) {
        console.error("Failed to restore Create Zone draft", err);
        if (!cancelled) error("Draft Unavailable", "Your saved Create Zone workspace could not be restored.");
      } finally {
        if (!cancelled) {
          hydratedUserId.current = userId;
          hasHydratedDraft.current = true;
        }
      }
    };
    void hydrate();
    return () => { cancelled = true; };
  }, [canPersistDraft, clearCreateWorkspace, error, isEditMode, isOpen, replaceMediaFiles, restoreFloodReportMapState, setDrafts, success, userId]);

  useEffect(() => {
    if (!drawInstance) return;
    if (pendingDrawnFeatures.current) {
      if (restoreDrawing(pendingDrawnFeatures.current)) {
        pendingDrawnFeatures.current = null;
      } else if (!hasShownDrawingRestoreError.current) {
        hasShownDrawingRestoreError.current = true;
        error("Drawing Unavailable", "Your saved zone shape could not be restored. The remaining draft details are still available.");
      }
    } else if (polygonSessionCacheRef.current.features.length > 0 && geometryMode !== "line") {
      restoreDrawing(polygonSessionCacheRef.current.features);
    }
  }, [drawInstance, error, geometryMode, restoreDrawing]);

  const hasMaterialWorkspace = drafts.length > 0 || Boolean(
    floodStart || floodEnd || drawnFeatures.length || mediaFiles.length || adminNotes.trim() ||
    passableVehicles.length || Boolean(hiddenHazards) || Boolean(editorValues.depth) ||
    editorValues.name !== "Official Flood Avoidance Zone" || geometryMode !== "line"
  );
  const hasActiveZoneWork = Boolean(
    floodStart || floodEnd || drawnFeatures.length || mediaFiles.length || adminNotes.trim() ||
    passableVehicles.length || Boolean(hiddenHazards) || Boolean(editorValues.depth) ||
    editorValues.name !== "Official Flood Avoidance Zone"
  );

  useEffect(() => {
    // Create and Edit share MapContext anchors. An inactive Create drawer must
    // never interpret an Edit Zone's anchors as a new Create Zone draft.
    if (!isOpen || !canPersistDraft || !userId || !hasHydratedDraft.current || hydratedUserId.current !== userId) return;
    if (suppressNextDraftSave.current) {
      suppressNextDraftSave.current = false;
      return;
    }
    if (!hasMaterialWorkspace) {
      void discardCreateZoneDraft(userId);
      return;
    }

    void saveCreateZoneDraft(userId, {
      active: {
        floodStart,
        floodEnd,
        floodPreviewGeometry,
        floodOppositeGeometry,
        floodIsBidirectional: isBidirectional,
        geometryMode,
        drawnFeatures,
        editorValues,
        passableVehicles,
        hiddenHazards,
        adminNotes,
        mediaFiles,
      },
      queuedDrafts: drafts,
    }).catch((err) => {
      console.error("Failed to save Create Zone draft", err);
      if (!hasShownPersistenceError.current) {
        hasShownPersistenceError.current = true;
        error("Draft Not Saved", "Your Create Zone workspace could not be saved on this device.");
      }
    });
  }, [adminNotes, canPersistDraft, drafts, drawnFeatures, editorValues, error, floodEnd, floodOppositeGeometry, floodPreviewGeometry, floodStart, geometryMode, hasMaterialWorkspace, hiddenHazards, isBidirectional, isOpen, mediaFiles, passableVehicles, userId]);

  // Current active geometry
  const validatedRoadCoverage = buildValidatedRoadCoverage(
    floodPreviewGeometry as ReportGeometry | null,
    floodOppositeGeometry as ReportGeometry | null,
    isBidirectional,
  );
  const currentGeometry = isEditMode
    ? geometryMode === "line"
      ? (floodStart && floodEnd && validatedRoadCoverage ? validatedRoadCoverage : null)
      : (drawnFeatures.length > 0 && drawnGeometry ? drawnGeometry : null)
    : drawnFeatures.length > 0
    ? drawnGeometry
    : floodStart && floodEnd
    ? validatedRoadCoverage
    : null;
  const isEditableLineGeometry = editorValues.geometry?.type === "LineString" || editorValues.geometry?.type === "MultiLineString";

  // Keep the form/draft payload tied to the geometry currently displayed on
  // the map. This makes a restored polygon vertex edit or a new validated
  // road selection part of the same dirty-state comparison as the attributes.
  useEffect(() => {
    if (!isEditMode || !currentGeometry) return;
    if (JSON.stringify(editorValues.geometry) === JSON.stringify(currentGeometry)) return;
    setEditorValues((current) => ({ ...current, geometry: normalizeOfficialZoneGeometry(currentGeometry) }));
  }, [currentGeometry, editorValues.geometry, isEditMode]);

  const handleResetToBaseline = useCallback(() => {
    if (!editBaseline.current) return;
    const baseline = editBaseline.current;
    const { editorValues: baselineValues, passableVehicles: vehicles } = baseline;
    setPassableVehicles(vehicles);
    setHiddenHazards(baseline.hiddenHazards);
    setAdminNotes(baseline.adminNotes);
    const isRoad = isRoadGeometry(baselineValues.geometry);
    setGeometryMode(isRoad ? "line" : "polygon");
    setIsEditingExistingShape(!isRoad);
    setEditorValues(isRoad ? baselineValues : { ...baselineValues, is_bidirectional: false });

    if (isRoad) {
      const endpoints = roadEndpoints(baselineValues.geometry);
      const startPoint = endpoints ? { coords: endpoints.start, label: `${endpoints.start[0].toFixed(5)}, ${endpoints.start[1].toFixed(5)}` } : null;
      const endPoint = endpoints ? { coords: endpoints.end, label: `${endpoints.end[0].toFixed(5)}, ${endpoints.end[1].toFixed(5)}` } : null;
      const prevGeom: RouteGeometry | null = baselineValues.geometry.type === "LineString"
        ? { type: "LineString" as const, coordinates: baselineValues.geometry.coordinates as [number, number][] }
        : null;
      const oppGeom: RouteGeometry | null = baselineValues.geometry.type === "MultiLineString"
        ? { type: "LineString" as const, coordinates: (baselineValues.geometry.coordinates[1] ?? []) as [number, number][] }
        : null;

      lineSessionCacheRef.current = {
        start: startPoint,
        end: endPoint,
        startLabel: startPoint?.label || "",
        endLabel: endPoint?.label || "",
        previewGeometry: prevGeom,
        oppositeGeometry: oppGeom,
        isBidirectional: baselineValues.is_bidirectional,
      };
      polygonSessionCacheRef.current = {
        features: [],
        geometry: null,
        mode: "polygon",
      };

      clearDrawing();
      setFloodShowMarkers(true);
      restoreFloodReportMapState({
        floodStart: startPoint,
        floodEnd: endPoint,
        floodPreviewGeometry: prevGeom,
        floodOppositeGeometry: oppGeom,
        floodIsBidirectional: baselineValues.is_bidirectional,
      });
    } else {
      const polyFeatures = geometryToTerraFeatures(baselineValues.geometry);
      polygonSessionCacheRef.current = {
        features: polyFeatures,
        geometry: baselineValues.geometry,
        mode: "polygon",
      };
      lineSessionCacheRef.current = {
        start: null,
        end: null,
        startLabel: "",
        endLabel: "",
        previewGeometry: null,
        oppositeGeometry: null,
        isBidirectional: false,
      };

      setFloodShowMarkers(false);
      restoreFloodReportMapState({
        floodStart: null,
        floodEnd: null,
        floodPreviewGeometry: null,
        floodOppositeGeometry: null,
        floodIsBidirectional: false,
      });
      restoreDrawing(polyFeatures);
    }
    success("Reset to Saved", "Zone geometry and values were restored to the currently saved version.");
  }, [clearDrawing, restoreDrawing, restoreFloodReportMapState, setFloodShowMarkers, success]);

  const handleGeometryModeChange = (mode: GeometryMode) => {
    if (mode === geometryMode) return;

    if (geometryMode === "line" && mode !== "line") {
      // Switching from Line to Shape mode (polygon, freehand, rectangle, circle):
      // 1. Cache current Line state so it is NOT lost
      lineSessionCacheRef.current = {
        start: floodStart,
        end: floodEnd,
        startLabel: floodStart?.label || "",
        endLabel: floodEnd?.label || "",
        previewGeometry: floodPreviewGeometry,
        oppositeGeometry: floodOppositeGeometry,
        isBidirectional,
      };

      // 2. Hide pin markers on the map so they don't interfere with drawing/vertex manipulation.
      // Note: We DO NOT clear floodPreviewGeometry from MapContext!
      // This allows the existing saved road line to remain visible on the map as the orange broken reference line (Option 2).
      setFloodShowMarkers(false);
      setActivePoint(null);
      setIsPickingOnMap(false);

      // 3. Restore any previously drawn or cached polygon features in this editing session
      if (polygonSessionCacheRef.current.features.length > 0) {
        restoreDrawing(polygonSessionCacheRef.current.features);
        setIsEditingExistingShape(true);
      } else {
        clearDrawing();
        setIsEditingExistingShape(false);
      }

      setGeometryMode(mode);
    } else if (geometryMode !== "line" && mode === "line") {
      // Switching from Shape mode back to Line mode:
      // 1. Cache current drawn features/geometry so they are NOT lost
      if (drawnFeatures.length > 0) {
        polygonSessionCacheRef.current = {
          features: drawnFeatures,
          geometry: drawnGeometry,
          mode: geometryMode,
        };
      }

      // 2. Clear polygon drawing from canvas while editing road line
      clearDrawing();
      cancelDrawingMode();
      setIsEditingExistingShape(false);

      // 3. Restore cached Line state into MapContext
      const cachedLine = lineSessionCacheRef.current;
      if (cachedLine.start || cachedLine.end || cachedLine.previewGeometry) {
        restoreFloodReportMapState({
          floodStart: cachedLine.start,
          floodEnd: cachedLine.end,
          floodPreviewGeometry: cachedLine.previewGeometry,
          floodOppositeGeometry: cachedLine.oppositeGeometry,
          floodIsBidirectional: cachedLine.isBidirectional,
        });
        if (cachedLine.startLabel) setFloodStartLabel(cachedLine.startLabel);
        if (cachedLine.endLabel) setFloodEndLabel(cachedLine.endLabel);
        setIsBidirectional(cachedLine.isBidirectional);
        setEditorValues((current) => ({ ...current, is_bidirectional: cachedLine.isBidirectional }));
      }

      // 4. Show the pin markers again
      setFloodShowMarkers(true);
      setGeometryMode("line");
    } else {
      // Switching between polygon sub-modes (e.g. polygon -> freehand -> rectangle)
      setGeometryMode(mode);
      if (drawInstance) {
        try {
          drawInstance.setMode(mode);
        } catch {}
      }
    }
  };

  const addMediaFiles = (files: File[]) => {
    const newItems = files.map((file) => {
      const previewUrl = file.type.startsWith("image/") ? URL.createObjectURL(file) : undefined;
      if (previewUrl) createdPreviewUrlsRef.current.add(previewUrl);
      return { file, previewUrl };
    });
    setMediaItems((current) => [...current, ...newItems]);
  };

  const removeMediaFile = (index: number) => {
    setMediaItems((current) => {
      const item = current[index];
      if (item?.previewUrl) {
        URL.revokeObjectURL(item.previewUrl);
        createdPreviewUrlsRef.current.delete(item.previewUrl);
      }
      return current.filter((_, itemIndex) => itemIndex !== index);
    });
  };

  const clearMediaFiles = () => {
    createdPreviewUrlsRef.current.forEach((url) => URL.revokeObjectURL(url));
    createdPreviewUrlsRef.current.clear();
    setMediaItems([]);
  };

  const handleResetCurrent = useCallback(() => {
    setFloodStart(null);
    setFloodEnd(null);
    setFloodStartLabel("");
    setFloodEndLabel("");
    setActivePoint(null);
    setIsPickingOnMap(false);
    setIsBidirectional(false);
    clearDrawing();
    cancelDrawingMode();
  }, [setFloodStart, setFloodEnd, setFloodStartLabel, setFloodEndLabel, setActivePoint, setIsPickingOnMap, setIsBidirectional, clearDrawing, cancelDrawingMode]);

  const handleClearActiveForm = useCallback(() => {
    clearCurrentZone();
    success("Form Cleared", "Your current zone inputs were cleared. Saved drafts are unchanged.");
  }, [clearCurrentZone, success]);

  const handleDiscardWorkspace = async () => {
    if (!canPersistDraft || !userId) return;
    try {
      await discardCreateZoneDraft(userId);
      suppressNextDraftSave.current = true;
      clearCreateWorkspace();
      setIsDiscardDialogOpen(false);
      success("Drafts Discarded", "The saved Create Zone workspace was removed from this device.");
    } catch (err) {
      console.error("Failed to discard Create Zone workspace", err);
      error("Could Not Discard Drafts", "Your saved workspace is still available. Please try again.");
    }
  };

  const handleEditDraft = (draft: ZoneDraftItem) => {
    const coordinates = draft.geometry?.type === "LineString" ? draft.geometry.coordinates as [number, number][] : [];
    const startCoords = draft.startCoords ?? coordinates[0];
    const endCoords = draft.endCoords ?? coordinates[coordinates.length - 1];
    const restoredMode = draft.geometryMode ?? (draft.geometry?.type === "LineString" ? "line" : "polygon");

    setGeometryMode(restoredMode);
    setEditorValues({
      name: draft.name || "Official Flood Avoidance Zone",
      severity: draft.severity,
      depth: draft.depth || "knee",
      passable_vehicles: draft.passableVehicles,
      hidden_hazards: draft.hiddenHazards,
      is_bidirectional: draft.isBidirectional,
      geometry: draft.geometry || { type: "LineString", coordinates: [] },
      admin_notes: draft.adminNotes,
    });
    setPassableVehicles(draft.passableVehicles);
    setHiddenHazards(draft.hiddenHazards);
    setAdminNotes(draft.adminNotes);
    replaceMediaFiles(draft.mediaFiles || []);
    pendingDrawnFeatures.current = draft.drawnFeatures ?? (restoredMode === "line" || !draft.geometry ? [] : [{ type: "Feature", properties: {}, geometry: draft.geometry }]);
    restoreFloodReportMapState({
      floodStart: startCoords ? { coords: startCoords, label: draft.startLabel || `${startCoords[0].toFixed(5)}, ${startCoords[1].toFixed(5)}` } : null,
      floodEnd: endCoords ? { coords: endCoords, label: draft.endLabel || `${endCoords[0].toFixed(5)}, ${endCoords[1].toFixed(5)}` } : null,
      floodPreviewGeometry: restoredMode === "line" ? draft.geometry as typeof floodPreviewGeometry : null,
      floodOppositeGeometry: restoredMode === "line" ? draft.oppositeGeometry as typeof floodOppositeGeometry : null,
      floodIsBidirectional: draft.isBidirectional,
    });
    setEditingDraft(draft);
    removeDraft(draft.id);
    setIsViewingDrafts(false);
  };

  const requestEditDraft = (draft: ZoneDraftItem) => {
    if (hasActiveZoneWork) {
      setPendingDraftToEdit(draft);
      setIsSaveBeforeEditDialogOpen(true);
      return;
    }
    handleEditDraft(draft);
  };

  const cancelDraftEdit = () => {
    if (!editingDraft) return;
    addDraft(editingDraft);
    clearCurrentZone();
    setEditingDraft(null);
    setIsViewingDrafts(true);
  };

  // Handle Add to Draft Cart (Create mode only)
  const handleAddToDraftQueue = () => {
    if (!currentGeometry) {
      error("Missing Geometry", "Please define a road segment or draw a shape on the map first.");
      return;
    }

    const newDraft: ZoneDraftItem = {
      id: editingDraft?.id ?? Math.random().toString(36).substring(7),
      geometry: normalizeOfficialZoneGeometry(currentGeometry),
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
      startCoords: floodStart?.coords,
      endCoords: floodEnd?.coords,
      geometryMode,
      drawnFeatures: geometryMode === "line" ? [] : drawnFeatures,
      mediaFiles: [...mediaFiles],
    };

    addDraft(newDraft);
    clearCurrentZone();
    setEditingDraft(null);
    success(editingDraft ? "Draft Updated" : "Queued in Cart", editingDraft ? "Your saved zone draft was updated." : "Hazard added to queue. Add another or publish all.");
  };

  const saveCurrentThenEditDraft = () => {
    if (!pendingDraftToEdit) return;
    if (!currentGeometry) {
      error("Missing Geometry", "Finish the current zone geometry before switching drafts.");
      return;
    }
    const draftToOpen = pendingDraftToEdit;
    handleAddToDraftQueue();
    setPendingDraftToEdit(null);
    setIsSaveBeforeEditDialogOpen(false);
    handleEditDraft(draftToOpen);
  };

  // Handle Submit (Create mode or Edit mode)
  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setIsSubmitting(true);
    suppressEditDraftSave.current = true;

    try {
      if (isEditMode && editingZone) {
        if (geometryMode === "line") {
          if (!floodStart || !floodEnd || !validatedRoadCoverage) {
            error("Incomplete Road Line", "Please select valid start and end points along a mapped road.");
            setIsSubmitting(false);
            suppressEditDraftSave.current = false;
            return;
          }
        } else {
          if (!drawnGeometry || drawnFeatures.length === 0) {
            error("No Shape Defined", "Please draw a shape on the map or switch back to Road Line mode.");
            setIsSubmitting(false);
            suppressEditDraftSave.current = false;
            return;
          }
        }

        const geometryToSave = geometryMode === "line" ? validatedRoadCoverage : drawnGeometry;

        // Edit Mode: PUT /admin/zones/{id}
        const payload: AvoidanceZoneUpdatePayload = {
          name: editorValues.name,
          severity_override: editorValues.severity,
          depth_override: editorValues.depth,
          passable_vehicles_override: passableVehicles.join(","),
          hidden_hazards_override: hiddenHazards,
          // Showing the public report text in the editor must not turn it into
          // an admin override merely because another field was saved.
          admin_notes: editingZone.admin_notes == null && adminNotes === (editingZone.report_text ?? "")
            ? undefined
            : adminNotes.trim(),
          geometry: isEditableZoneGeometry(geometryToSave)
            ? normalizeOfficialZoneGeometry(geometryToSave) as AvoidanceZoneUpdatePayload["geometry"]
            : undefined,
        };

        await updateZone(editingZone.id, payload);
        if (mediaFiles.length > 0) {
          await addZoneMedia(editingZone.id, mediaFiles);
        }
        if (userId) await discardZoneEditDraft(userId, editingZone.id);
        clearMediaFiles();
        hasHydratedEditDraft.current = false;
        hydratedEditKey.current = null;
        editBaseline.current = null;
        success("Zone Updated", `Official Zone #${editingZone.id} has been saved.`);
        if (onZoneUpdated) onZoneUpdated();
        setFloodShowMarkers(true);
        restoreFloodReportMapState({
          floodStart: null,
          floodEnd: null,
          floodPreviewGeometry: null,
          floodOppositeGeometry: null,
          floodIsBidirectional: false,
        });
        clearDrawing();
        onClose();
      } else {
        // Create Mode: Build payloads from current form + draft cart
        const submissionItems: ZoneSubmissionItem[] = [];

        // 1. Existing queued drafts
        drafts.forEach((d) => {
          submissionItems.push({
            payload: {
              name: d.name,
              geometry: d.geometry ? normalizeOfficialZoneGeometry(d.geometry) : d.geometry,
              severity_override: d.severity,
              depth_override: d.depth,
              passable_vehicles_override: d.passableVehicles.length > 0 ? d.passableVehicles.join(",") : undefined,
              hidden_hazards_override: d.hiddenHazards || undefined,
              admin_notes: d.adminNotes.trim() || undefined,
              is_active: true,
            },
            mediaFiles: d.mediaFiles || [],
          });
        });

        // 2. Current active form if geometry is present
        if (currentGeometry) {
          submissionItems.push({
            payload: {
              name: editorValues.name,
              geometry: normalizeOfficialZoneGeometry(currentGeometry),
              severity_override: editorValues.severity,
              depth_override: editorValues.depth,
              passable_vehicles_override: passableVehicles.length > 0 ? passableVehicles.join(",") : undefined,
              hidden_hazards_override: hiddenHazards || undefined,
              admin_notes: adminNotes.trim() || undefined,
              is_active: true,
            },
            mediaFiles,
          });
        }

        if (submissionItems.length === 0) {
          error("No Zones to Publish", "Please add at least one zone to publish.");
          setIsSubmitting(false);
          suppressEditDraftSave.current = false;
          return;
        }

        if (onAdminSubmit) {
          await onAdminSubmit(submissionItems);
        }

        if (canPersistDraft && userId) {
          try {
            await discardCreateZoneDraft(userId);
            suppressNextDraftSave.current = true;
          } catch (discardError) {
            console.error("Zones published but local Create Zone draft could not be removed", discardError);
            error("Zones Published", "Your zones were published, but the local workspace could not be removed. Please discard it manually.");
          }
        }
        clearCreateWorkspace();
        success("Zones Published", `Successfully created ${submissionItems.length} official avoidance zone(s).`);
        onClose();
      }
    } catch (err: unknown) {
      suppressEditDraftSave.current = false;
      const rawMessage = err instanceof Error ? err.message : "";
      const isGeometryValidationError = /invalid body json|validation errors|geometry\.(polygon|multipolygon)/i.test(rawMessage);
      error(
        "Couldn’t publish zone",
        isGeometryValidationError
          ? "The zone shape could not be read. Please redraw it and try again."
          : rawMessage || "Failed to save the avoidance zone. Please try again."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const confirmCancelEdit = async () => {
    if (!editingZone || !userId) {
      setFloodShowMarkers(true);
      restoreFloodReportMapState({
        floodStart: null,
        floodEnd: null,
        floodPreviewGeometry: null,
        floodOppositeGeometry: null,
        floodIsBidirectional: false,
      });
      clearDrawing();
      setIsCancelEditDialogOpen(false);
      onClose();
      return;
    }
    suppressEditDraftSave.current = true;
    setIsDiscardingEdit(true);
    try {
      await discardZoneEditDraft(userId, editingZone.id);
      clearMediaFiles();
      setFloodShowMarkers(true);
      restoreFloodReportMapState({
        floodStart: null,
        floodEnd: null,
        floodPreviewGeometry: null,
        floodOppositeGeometry: null,
        floodIsBidirectional: false,
      });
      clearDrawing();
      setIsCancelEditDialogOpen(false);
      onClose();
    } catch (discardError) {
      console.error("Failed to discard Edit Zone draft", discardError);
      suppressEditDraftSave.current = false;
      error("Could Not Discard Edit", "Your unfinished edit is still saved on this device. Please try again.");
    } finally {
      setIsDiscardingEdit(false);
    }
  };

  useEffect(() => {
    return () => {
      setFloodShowMarkers(true);
    };
  }, [setFloodShowMarkers]);

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
          {onSwitchWorkspace && switchWorkspaceLabel && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={onSwitchWorkspace}
              className="md:hidden h-7 px-2 text-[10px] font-semibold text-slate-600 hover:bg-slate-100"
            >
              {switchWorkspaceLabel}
            </Button>
          )}
          {onShowMap && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={onShowMap}
              className="md:hidden h-7 px-2 text-[10px] font-semibold text-blue-600 hover:bg-blue-50"
            >
              View Map
            </Button>
          )}
          {/* Close removes this workspace; the outer handle only switches tabs. */}
          <button
            type="button"
            onClick={() => isEditMode ? setIsCancelEditDialogOpen(true) : onClose()}
            className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors"
            title="Close drawer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* DRAWER BODY (Scrollable) */}
      <div className="scrollbar-auto-hide flex-1 overflow-y-auto p-4 space-y-5">
        {!isEditMode && isViewingDrafts ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between gap-2">
              <button
                type="button"
                onClick={() => setIsViewingDrafts(false)}
                className="text-xs font-medium text-slate-500 transition-colors hover:text-slate-800"
              >
                Back to zone
              </button>
            </div>
            <DraftZoneCart
              drafts={drafts}
              onRemoveDraft={removeDraft}
              onEditDraft={requestEditDraft}
              onClearDrafts={() => setIsDiscardDialogOpen(true)}
            />
          </div>
        ) : (
          <>
        {/* SAVED DRAFTS SUMMARY (Create mode) */}
        {!isEditMode && drafts.length > 0 && (
          <div className="flex items-center justify-between border-b border-slate-100 px-1 pb-3">
            <span className="text-sm font-semibold text-slate-800">
              {drafts.length} saved {drafts.length === 1 ? "draft" : "drafts"}
            </span>
            <button
              type="button"
              onClick={() => setIsViewingDrafts(true)}
              className="rounded-full bg-blue-100 px-3 py-1.5 text-xs font-semibold text-blue-700 transition-colors hover:bg-blue-200"
            >
              View drafts
            </button>
          </div>
        )}

        {!isEditMode && editingDraft && (
          <div className="flex items-center justify-between border-b border-slate-100 px-1 pb-3">
            <span className="text-xs font-semibold text-blue-700">Editing saved draft</span>
            <button
              type="button"
              onClick={cancelDraftEdit}
              className="text-xs font-medium text-slate-500 transition-colors hover:text-red-600"
            >
              Cancel edit
            </button>
          </div>
        )}

        {/* SPATIAL GEOMETRY DEFINITION */}
        <div className="space-y-3">
          <div className="flex items-center justify-between gap-3">
            <label className="text-xs font-bold text-slate-700 uppercase tracking-wider block">
              {isEditMode ? "Spatial Geometry" : "1. Spatial Geometry"}
            </label>
            {isEditMode ? (
              <button
                type="button"
                onClick={handleResetToBaseline}
                className="flex shrink-0 items-center gap-1 text-xs font-medium text-slate-500 transition-colors hover:text-amber-700"
                title="Reset this zone back to its saved geometry and values"
              >
                <RotateCcw className="h-3.5 w-3.5" /> Reset to Saved
              </button>
            ) : hasActiveZoneWork && !editingDraft ? (
              <button
                type="button"
                onClick={handleClearActiveForm}
                className="flex shrink-0 items-center gap-1 text-xs font-medium text-slate-500 transition-colors hover:text-red-600"
                title="Clear the current zone form without removing saved drafts"
              >
                <RotateCcw className="h-3.5 w-3.5" /> Clear form
              </button>
            ) : null}
          </div>
          {isEditMode && (
            <div className="rounded-xl border border-slate-200 bg-slate-50/80 p-2.5 flex items-center justify-between gap-2 text-xs">
              <div className="flex items-center gap-2 min-w-0">
                {geometryMode === "line" ? (
                  <Route className="w-4 h-4 text-blue-600 shrink-0" />
                ) : (
                  <span className="text-base leading-none shrink-0">⬡</span>
                )}
                <span className="text-slate-700 font-semibold truncate">
                  {geometryMode === "line" ? "Road Line Mode" : `Shape Mode (${geometryMode})`}
                </span>
              </div>
              {geometryMode === "line" ? (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => handleGeometryModeChange("polygon")}
                  className="h-7 text-xs px-2.5 rounded-lg border-blue-300 text-blue-700 hover:bg-blue-50 font-semibold shrink-0"
                  title="Switch to polygon shape mode while keeping the road line as reference"
                >
                  Change to Polygon
                </Button>
              ) : (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => handleGeometryModeChange("line")}
                  className="h-7 text-xs px-2.5 rounded-lg border-slate-300 text-slate-700 hover:bg-slate-100 font-semibold shrink-0"
                  title="Switch back to road line mode while preserving any drawn shape"
                >
                  Change to Road Line
                </Button>
              )}
            </div>
          )}
          <GeometryModeSelector
            geometryMode={geometryMode}
            onChange={handleGeometryModeChange}
            isDrawingMode={isDrawingMode}
            onCancelDrawing={cancelDrawingMode}
          />
          {geometryMode === "line" ? (
            <>
              <RoadSegmentPicker
                isBidirectional={isBidirectional}
                onBidirectionalChange={(enabled) => {
                  setIsBidirectional(enabled);
                  setEditorValues((current) => ({ ...current, is_bidirectional: enabled }));
                }}
              />
              {(floodStart || floodEnd) && (
                <button type="button" onClick={handleResetCurrent} className="flex items-center gap-1 text-xs font-medium text-slate-500 transition-colors hover:text-red-600">
                  <RotateCcw className="h-3.5 w-3.5" /> Clear locations
                </button>
              )}
            </>
          ) : (
            <div className="p-3 rounded-xl border border-dashed border-slate-300 bg-slate-50 text-center">
              <p className="text-xs text-slate-600 font-medium">
                {drawnFeatures.length > 0 ? "Drag the displayed vertices to refine this area, or redraw to replace it." : `Click and draw your ${geometryMode} directly on the map.`}
              </p>
              {drawnFeatures.length > 0 && (
                <div className="mt-2.5 flex flex-wrap justify-center gap-2">
                  {isEditMode && (
                    <>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => setIsEditingExistingShape(true)}
                        className="h-7 px-2.5 text-xs rounded-lg border-slate-300 text-slate-700 hover:bg-slate-100 font-medium"
                      >
                        Edit Vertices
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          clearDrawing();
                          setIsEditingExistingShape(false);
                          if (drawInstance) {
                            try {
                              drawInstance.setMode(geometryMode);
                            } catch {}
                          }
                        }}
                        className="h-7 px-2.5 text-xs rounded-lg text-amber-700 border-amber-300 hover:bg-amber-50 font-medium"
                      >
                        Redraw Shape
                      </Button>
                    </>
                  )}
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      clearDrawing();
                      setIsEditingExistingShape(false);
                    }}
                    className="h-7 px-2.5 text-xs rounded-lg text-red-600 border-red-200 hover:bg-red-50 font-medium"
                  >
                    Clear Drawing
                  </Button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* SECTION 2: HAZARD ATTRIBUTES — depth/severity + buffer */}
        <div className="space-y-3 pt-1 border-t border-slate-100">
          <label className="text-xs font-bold text-slate-700 uppercase tracking-wider block">
            {isEditMode ? "Hazard Attributes" : "2. Hazard Attributes"}
          </label>
          <ZoneDataEditorForm
            initialValues={editorValues}
            onChange={setEditorValues}
            readOnlyGeometry={true}
            hideBidirectional={true}
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

          {isEditMode && editingZone?.report_media_urls && editingZone.report_media_urls.length > 0 && (
            <div className="space-y-2">
              <p className="text-[11px] font-semibold text-slate-600">Original report evidence</p>
              <div className="grid gap-2 sm:grid-cols-2">
                {editingZone.report_media_urls.map((url, index) => {
                  const isVideo = /\.(mp4|webm|mov)(?:\?|$)/i.test(url) || url.includes("/video/");
                  return (
                    <a
                      key={url}
                      href={url}
                      target="_blank"
                      rel="noreferrer"
                      className="overflow-hidden rounded-lg border border-slate-200 bg-slate-50 transition-colors hover:border-blue-300"
                    >
                      {isVideo ? (
                        <video src={url} preload="metadata" controls className="h-24 w-full bg-slate-900 object-cover" />
                      ) : (
                        <img src={url} alt={`Original report evidence ${index + 1}`} className="h-24 w-full object-cover" />
                      )}
                      <p className="truncate px-2 py-1.5 text-[10px] font-medium text-slate-600">Original evidence {index + 1}</p>
                    </a>
                  );
                })}
              </div>
              <p className="text-[10px] text-slate-400">Original evidence is preserved; uploads below add new zone evidence.</p>
            </div>
          )}

          {mediaItems.length > 0 && (
            <div className="space-y-2" aria-live="polite">
              <p className="flex items-center gap-1.5 text-[11px] font-semibold text-emerald-700">
                <CheckCircle2 className="h-3.5 w-3.5" />
                {mediaItems.length} {mediaItems.length === 1 ? "file" : "files"} ready to publish
              </p>
              <div className="grid gap-2 sm:grid-cols-2">
                {mediaItems.map(({ file, previewUrl }, index) => (
                  <div
                    key={`${file.name}-${file.lastModified}-${index}`}
                    className="flex min-w-0 items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 p-2"
                  >
                    {previewUrl ? (
                      <img
                        src={previewUrl}
                        alt={`Selected ${file.name}`}
                        className="h-11 w-11 shrink-0 rounded-md object-cover ring-1 ring-slate-200"
                      />
                    ) : (
                      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-md bg-violet-100 text-violet-700">
                        <FileVideo className="h-5 w-5" />
                      </div>
                    )}
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-xs font-medium text-slate-700" title={file.name}>{file.name}</p>
                      <p className="text-[10px] text-slate-500">{file.type.startsWith("video/") ? "Video" : "Image"} · {formatFileSize(file.size)}</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeMediaFile(index)}
                      aria-label={`Remove ${file.name}`}
                      className="shrink-0 rounded-full p-1 text-slate-500 transition-colors hover:bg-slate-200 hover:text-slate-700"
                    >
                      <X className="h-3.5 w-3.5" />
                    </button>
                  </div>
                ))}
              </div>
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
                  addMediaFiles(Array.from(e.target.files));
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
          </>
        )}
      </div>

      <ConfirmDialog
        isOpen={isDiscardDialogOpen}
        title="Discard Create Zone drafts?"
        message="Remove the saved zones, current geometry, notes, and media from this device? Published zones stay."
        confirmLabel="Discard all"
        variant="destructive"
        size="sm"
        onConfirm={() => void handleDiscardWorkspace()}
        onCancel={() => setIsDiscardDialogOpen(false)}
      />
      <ConfirmDialog
        isOpen={isSaveBeforeEditDialogOpen}
        title="Save current zone first?"
        message="Your current zone has changes. Add it to drafts before opening another saved draft."
        confirmLabel="Save and edit"
        size="sm"
        onConfirm={saveCurrentThenEditDraft}
        onCancel={() => {
          setPendingDraftToEdit(null);
          setIsSaveBeforeEditDialogOpen(false);
        }}
      />
      <ConfirmDialog
        isOpen={isCancelEditDialogOpen}
        title="Discard unfinished edit?"
        message="Your local changes and attached media for this zone will be removed. The published zone will not change."
        confirmLabel="Discard edit"
        variant="destructive"
        size="sm"
        isLoading={isDiscardingEdit}
        onConfirm={() => void confirmCancelEdit()}
        onCancel={() => setIsCancelEditDialogOpen(false)}
      />

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
              {editingDraft ? "Save Draft Changes" : "Add to Drafts"}
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
              onClick={() => setIsCancelEditDialogOpen(true)}
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
