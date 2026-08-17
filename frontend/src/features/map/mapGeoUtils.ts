/**
 * Universal Geometry Centroid and Midpoint Utilities for LANES Map Layers.
 * Safely computes representative center coordinates [longitude, latitude]
 * for Points, LineStrings, and Polygon avoidance buffers.
 */

export function computeCenterCoordinate(
  geometry?: { type: string; coordinates: any } | null,
  reportGeometry?: { type: string; coordinates: any } | null
): [number, number] | null {
  // 1. If original report geometry is a Point, return directly
  if (reportGeometry && reportGeometry.type === "Point" && Array.isArray(reportGeometry.coordinates)) {
    return [reportGeometry.coordinates[0], reportGeometry.coordinates[1]];
  }

  // 2. If report geometry is a LineString, return the middle vertex
  if (reportGeometry && reportGeometry.type === "LineString" && Array.isArray(reportGeometry.coordinates) && reportGeometry.coordinates.length > 0) {
    const coords = reportGeometry.coordinates;
    const mid = coords[Math.floor(coords.length / 2)];
    return [mid[0], mid[1]];
  }

  // 3. If primary geometry is a Point
  if (geometry && geometry.type === "Point" && Array.isArray(geometry.coordinates)) {
    return [geometry.coordinates[0], geometry.coordinates[1]];
  }

  // 4. If primary geometry is a LineString
  if (geometry && geometry.type === "LineString" && Array.isArray(geometry.coordinates) && geometry.coordinates.length > 0) {
    const coords = geometry.coordinates;
    const mid = coords[Math.floor(coords.length / 2)];
    return [mid[0], mid[1]];
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
