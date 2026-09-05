/**
 * Universal Geometry Centroid and Midpoint Utilities for LANES Map Layers.
 * Safely computes representative center coordinates [longitude, latitude]
 * for Points, LineStrings, and Polygon avoidance buffers.
 */

export function computeCenterCoordinate(
  geometry?: any,
  reportGeometry?: any
): [number, number] | null {
  let g = geometry;
  let rg = reportGeometry;
  if (typeof g === "string") {
    try { g = JSON.parse(g); } catch (e) {}
  }
  if (typeof rg === "string") {
    try { rg = JSON.parse(rg); } catch (e) {}
  }

  // 1. If original report geometry is a Point, return directly
  if (rg && rg.type === "Point" && Array.isArray(rg.coordinates)) {
    return [Number(rg.coordinates[0]), Number(rg.coordinates[1])];
  }

  // 2. If report geometry is a LineString, return the middle vertex
  if (rg && rg.type === "LineString" && Array.isArray(rg.coordinates) && rg.coordinates.length > 0) {
    const coords = rg.coordinates;
    const mid = coords[Math.floor(coords.length / 2)];
    return [Number(mid[0]), Number(mid[1])];
  }

  // 2b. If report geometry is a MultiLineString, return the middle vertex of the first line
  if (rg && rg.type === "MultiLineString" && Array.isArray(rg.coordinates) && rg.coordinates[0]?.length > 0) {
    const coords = rg.coordinates[0];
    const mid = coords[Math.floor(coords.length / 2)];
    return [Number(mid[0]), Number(mid[1])];
  }

  // 3. If primary geometry is a Point
  if (g && g.type === "Point" && Array.isArray(g.coordinates)) {
    return [Number(g.coordinates[0]), Number(g.coordinates[1])];
  }

  // 4. If primary geometry is a LineString
  if (g && g.type === "LineString" && Array.isArray(g.coordinates) && g.coordinates.length > 0) {
    const coords = g.coordinates;
    const mid = coords[Math.floor(coords.length / 2)];
    return [Number(mid[0]), Number(mid[1])];
  }

  // 4b. If primary geometry is a MultiLineString
  if (g && g.type === "MultiLineString" && Array.isArray(g.coordinates) && g.coordinates[0]?.length > 0) {
    const coords = g.coordinates[0];
    const mid = coords[Math.floor(coords.length / 2)];
    return [Number(mid[0]), Number(mid[1])];
  }

  // 5. If geometry is a Polygon, compute the arithmetic mean of its outer ring
  if (geometry && geometry.type === "Polygon" && Array.isArray(geometry.coordinates) && geometry.coordinates[0]?.length > 0) {
    const ring = geometry.coordinates[0];
    let sumLng = 0;
    let sumLat = 0;
    ring.forEach((pt: [number, number]) => {
      sumLng += pt[0];
      sumLat += pt[1];
    });
    return [sumLng / ring.length, sumLat / ring.length];
  }

  return null;
}

export interface FlyToFeatureOptions {
  zoom?: number;
  pitch?: number;
  bearing?: number;
  duration?: number;
}

/**
 * Standard Camera Focus Transition for Flood Reports and Avoidance Zones.
 * Automatically computes geometry center and applies uniform 45° angle, zoom 16, and smooth easing.
 */
export function flyToFeature(
  map: any,
  geometry?: { type: string; coordinates: any } | null,
  reportGeometry?: { type: string; coordinates: any } | null,
  options?: FlyToFeatureOptions
): boolean {
  if (!map) return false;
  
  const center = computeCenterCoordinate(geometry, reportGeometry);
  if (!center) return false;

  map.flyTo({
    center,
    zoom: options?.zoom ?? 16,
    pitch: options?.pitch ?? (typeof map.getPitch === "function" ? map.getPitch() : 0),
    bearing: options?.bearing ?? (typeof map.getBearing === "function" ? map.getBearing() : 0),
    duration: options?.duration ?? 1400,
    essential: true,
  });

  return true;
}

/**
 * Standard Camera Focus Transition by direct coordinates.
 */
export function flyToCoordinates(
  map: any,
  coords: [number, number],
  options?: FlyToFeatureOptions
): void {
  if (!map || !coords) return;

  map.flyTo({
    center: coords,
    zoom: options?.zoom ?? 16,
    pitch: options?.pitch ?? (typeof map.getPitch === "function" ? map.getPitch() : 0),
    bearing: options?.bearing ?? (typeof map.getBearing === "function" ? map.getBearing() : 0),
    duration: options?.duration ?? 1400,
    essential: true,
  });
}
