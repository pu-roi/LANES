export type FloodSeverity = "low" | "medium" | "high" | "extreme";

export interface FloodDepthSpec {
  id: string;
  label: string;
  severity: FloodSeverity;
  inches: number;
  meters: number;
  centimeters: number;
  formatted: string;
  description: string;
  accessibilityClass: "PATV" | "NPLV" | "NPATV";
}

export const FLOOD_DEPTH_SPECS: Record<string, FloodDepthSpec> = {
  gutter: {
    id: "gutter",
    label: "Gutter",
    severity: "low",
    inches: 8.0,
    meters: 0.20,
    centimeters: 20.32,
    formatted: '8" (0.20m)',
    description: '8" (0.20m)',
    accessibilityClass: "PATV",
  },
  "half-knee": {
    id: "half-knee",
    label: "Half-Knee",
    severity: "low",
    inches: 10.0,
    meters: 0.25,
    centimeters: 25.40,
    formatted: '10" (0.25m)',
    description: '10" (0.25m)',
    accessibilityClass: "PATV",
  },
  "half-tire": {
    id: "half-tire",
    label: "Half-Tire",
    severity: "medium",
    inches: 13.0,
    meters: 0.33,
    centimeters: 33.02,
    formatted: '13" (0.33m)',
    description: '13" (0.33m)',
    accessibilityClass: "NPLV",
  },
  knee: {
    id: "knee",
    label: "Knee",
    severity: "medium",
    inches: 19.0,
    meters: 0.48,
    centimeters: 48.26,
    formatted: '19" (0.48m)',
    description: '19" (0.48m)',
    accessibilityClass: "NPLV",
  },
  tires: {
    id: "tires",
    label: "Tires",
    severity: "high",
    inches: 26.0,
    meters: 0.66,
    centimeters: 66.04,
    formatted: '26" (0.66m)',
    description: '26" (0.66m)',
    accessibilityClass: "NPATV",
  },
  waist: {
    id: "waist",
    label: "Waist",
    severity: "high",
    inches: 37.0,
    meters: 0.94,
    centimeters: 93.98,
    formatted: '37" (0.94m)',
    description: '37" (0.94m)',
    accessibilityClass: "NPATV",
  },
  chest: {
    id: "chest",
    label: "Chest",
    severity: "high",
    inches: 45.0,
    meters: 1.14,
    centimeters: 114.30,
    formatted: '45" (1.14m)',
    description: '45" (1.14m)',
    accessibilityClass: "NPATV",
  },
  neck: {
    id: "neck",
    label: "Neck & Above",
    severity: "extreme",
    inches: 55.0,
    meters: 1.40,
    centimeters: 140.0,
    formatted: '55"+ (1.40m+)',
    description: '55"+ (1.40m+)',
    accessibilityClass: "NPATV",
  },
};

export const FLOOD_DEPTH_OPTIONS: FloodDepthSpec[] = [
  FLOOD_DEPTH_SPECS["gutter"],
  FLOOD_DEPTH_SPECS["half-knee"],
  FLOOD_DEPTH_SPECS["half-tire"],
  FLOOD_DEPTH_SPECS["knee"],
  FLOOD_DEPTH_SPECS["tires"],
  FLOOD_DEPTH_SPECS["waist"],
  FLOOD_DEPTH_SPECS["chest"],
  FLOOD_DEPTH_SPECS["neck"],
];

const DEPTH_ALIASES: Record<string, string> = {
  "neck-and-above": "neck",
  "neck-&-above": "neck",
  "neck and above": "neck",
  "neck & above": "neck",
};

export function getFloodDepthSpec(depth?: string | null): FloodDepthSpec | null {
  if (!depth || depth === "null") return null;
  const normalized = depth.toLowerCase().trim();
  const aliasMatch = DEPTH_ALIASES[normalized] || DEPTH_ALIASES[normalized.replace(/_/g, "-")];
  const key = aliasMatch || normalized.replace(/_/g, "-");
  return FLOOD_DEPTH_SPECS[key] ?? null;
}

export function formatFloodDepth(
  depth?: string | null,
  options?: { fallback?: string; includeMeasurement?: boolean; compact?: boolean }
): string {
  const fallback = options?.fallback ?? "Not specified";
  const includeMeasurement = options?.includeMeasurement ?? true;
  const compact = options?.compact ?? false;

  const spec = getFloodDepthSpec(depth);
  if (!spec) {
    if (!depth || depth === "null") return fallback;
    return depth.replace(/_/g, " ");
  }

  if (!includeMeasurement) return spec.label;
  if (compact) return `${spec.label} (${spec.formatted})`;
  return `${spec.label} • ${spec.formatted}`;
}
