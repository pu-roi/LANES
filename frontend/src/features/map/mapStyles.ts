/**
 * Centralized Map Styling Tokens & Generators for LANES Maps.
 * Ensures identical colors, zoom thresholds, and layer paint configurations
 * across Public Map and Admin Live Map views.
 */

// 1. Core 4-Tier Severity Fill Colors
export const SEVERITY_COLORS: Record<string, string> = {
  low: "#84cc16",     // Lime
  medium: "#eab308",  // Yellow / Amber
  high: "#f97316",    // Orange
  extreme: "#ef4444", // Red
};

// 2. High-Contrast Darker Border Colors for Map Pin Circles (No white borders)
export const SEVERITY_BORDER_COLORS: Record<string, string> = {
  low: "#4d7c0f",     // Dark Olive
  medium: "#a16207",  // Dark Amber / Gold
  high: "#c2410c",    // Dark Orange / Rust
  extreme: "#991b1b", // Deep Crimson / Maroon
};

// 3. Zoom Thresholds
export const ZOOM_THRESHOLDS = {
  PIN_MAX_ZOOM: 14,      // Pins are visible for zoom <= 14
  DETAILED_MIN_ZOOM: 14, // Detailed auras, lines, and polygons are visible for zoom > 14
};

// 4. Standard Map Pin Paint Definition (City View: Zoom <= 14)
export const PIN_CIRCLE_PAINT: any = {
  "circle-radius": [
    "interpolate", ["linear"], ["zoom"],
    10, 6,
    14, 10,
    18, 16
  ],
  "circle-color": ["get", "color"],
  "circle-opacity": [
    "step", ["zoom"],
    0.85, // below zoom 14 -> 0.85
    14,   // at and above zoom 14 -> 0
    0
  ],
  "circle-stroke-width": [
    "step", ["zoom"],
    2,    // below zoom 14 -> 2
    14,   // at and above zoom 14 -> 0
    0
  ],
  "circle-stroke-color": ["get", "border_color"],
};

// 5. Active Zones: Detailed Street-Level Paint (Zoom > 14)
// Verified Active Zones have exactly TWO visual components:
// 1. Transparent Avoidance Buffer Aura (the 50m PostGIS buffer polygon)
export const ACTIVE_ZONE_POLYGON_FILL_PAINT: any = {
  "fill-color": ["get", "color"],
  "fill-opacity": [
    "step", ["zoom"],
    0,    // below zoom 14 -> 0
    14,   // at and above zoom 14 -> default opacity
    ["case", ["==", ["get", "is_selected"], true], 0.45, 0.25]
  ],
};

// 2. Solid Inner Core Line (the street centerline - bold and clear)
export const ACTIVE_ZONE_ROAD_CORE_PAINT: any = {
  "line-color": ["get", "color"],
  "line-width": [
    "interpolate", ["linear"], ["zoom"],
    14, ["case", ["==", ["get", "is_selected"], true], 12, 9],
    17, ["case", ["==", ["get", "is_selected"], true], 18, 14],
    20, ["case", ["==", ["get", "is_selected"], true], 24, 18]
  ],
  "line-opacity": [
    "step", ["zoom"],
    0,    // below zoom 14 -> 0
    14,   // at and above zoom 14 -> 0.95
    0.95
  ],
};

// 6. Pending Reports: Detailed Street-Level Paint (Zoom > 14)
// Unverified Pending Reports have ONLY pure transparent glowing auras (no borders, no solid inner core)
export const PENDING_REPORT_ROAD_AURA_PAINT: any = {
  "line-color": ["get", "color"],
  "line-width": ["case", ["==", ["get", "is_selected"], true], 32, 24],
  "line-opacity": [
    "step", ["zoom"],
    0,    // below zoom 14 -> 0
    14,   // at and above zoom 14 -> default opacity
    ["case", ["==", ["get", "is_selected"], true], 0.6, 0.35]
  ],
};

export const PENDING_REPORT_POINT_AURA_PAINT: any = {
  "circle-radius": [
    "interpolate", ["linear"], ["zoom"],
    14, ["case", ["==", ["get", "is_selected"], true], 20, 16],
    18, ["case", ["==", ["get", "is_selected"], true], 38, 30]
  ],
  "circle-color": ["get", "color"],
  "circle-opacity": [
    "step", ["zoom"],
    0,    // below zoom 14 -> 0
    14,   // at and above zoom 14 -> default opacity
    ["case", ["==", ["get", "is_selected"], true], 0.55, 0.35]
  ],
  "circle-stroke-width": 0,
};

