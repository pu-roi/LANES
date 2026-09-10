import { SEVERITY_COLORS as MAP_SEVERITY_COLORS, SEVERITY_BORDER_COLORS } from "@/features/map/mapStyles";
import type { ReportGeometry } from "@/features/admin/adminApi";

export type GeometryMode = "line" | "polygon" | "freehand" | "rectangle" | "circle";
export type Severity = "low" | "medium" | "high" | "extreme";
export type ReportVisualOption = "gutter" | "half-knee" | "half-tire" | "knee" | "tires" | "waist" | "chest" | "neck";

export interface VisualOptionItem {
  id: ReportVisualOption;
  severity: Severity;
  label: string;
  description: string;
}

export const VISUAL_OPTIONS: VisualOptionItem[] = [
  { id: "gutter", severity: "low", label: "Gutter", description: "8 inches" },
  { id: "half-knee", severity: "low", label: "Half-Knee", description: "10 inches" },
  { id: "half-tire", severity: "medium", label: "Half-Tire", description: "13 inches" },
  { id: "knee", severity: "medium", label: "Knee", description: "19 inches" },
  { id: "tires", severity: "high", label: "Tires", description: "26 inches" },
  { id: "waist", severity: "high", label: "Waist", description: "37 inches" },
  { id: "chest", severity: "high", label: "Chest", description: "45 inches" },
  { id: "neck", severity: "extreme", label: "Neck & Above", description: "Danger" },
];

export const SEVERITY_COLORS = {
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

export const SEVERITY_DOT_COLORS = {
  low: "bg-[#d8ed34]",
  medium: "bg-amber-400",
  high: "bg-orange-500",
  extreme: "bg-red-600",
};

export const getTerraDrawActiveZoneStyles = (severity: Severity) => {
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

export interface ZoneDraftItem {
  id: string;
  geometry: ReportGeometry | null;
  oppositeGeometry?: ReportGeometry | null;
  isBidirectional: boolean;
  name?: string;
  severity: Severity;
  depth?: string | null;
  passableVehicles: string[];
  hiddenHazards: string;
  adminNotes: string;
  startLabel?: string;
  endLabel?: string;
  roadName?: string | null;
  startCoords?: [number, number];
  endCoords?: [number, number];
  geometryMode?: GeometryMode;
  drawnFeatures?: any[];
  mediaFiles?: File[];
}
