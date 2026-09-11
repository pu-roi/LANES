/**
 * Universal Geometry Centroid and Midpoint Utilities for LANES Map Layers.
 * Safely computes representative center coordinates [longitude, latitude]
 * for Points, road geometries, and Polygon avoidance buffers.
 */

type Coordinate = [number, number];

function isCoordinate(value: unknown): value is Coordinate {
  return Array.isArray(value)
    && value.length >= 2
    && Number.isFinite(Number(value[0]))
    && Number.isFinite(Number(value[1]));
}

function segmentLengthMeters(first: Coordinate, second: Coordinate): number {
  const meanLatitude = ((first[1] + second[1]) / 2) * (Math.PI / 180);
  const longitudeDistance = (second[0] - first[0]) * 111_000 * Math.cos(meanLatitude);
  const latitudeDistance = (second[1] - first[1]) * 111_000;
  return Math.hypot(longitudeDistance, latitudeDistance);
}

function lineMidpoint(coordinates: unknown): { coordinate: Coordinate; length: number } | null {
  if (!Array.isArray(coordinates)) return null;
  const line = coordinates.filter(isCoordinate);
  if (line.length === 0) return null;
  if (line.length === 1) return { coordinate: line[0], length: 0 };

  const lengths = line.slice(1).map((coordinate, index) => segmentLengthMeters(line[index], coordinate));
  const totalLength = lengths.reduce((total, length) => total + length, 0);
  if (totalLength === 0) return { coordinate: line[0], length: 0 };

  const halfway = totalLength / 2;
  let traversed = 0;
  for (let index = 0; index < lengths.length; index += 1) {
    const segmentLength = lengths[index];
    if (traversed + segmentLength >= halfway) {
      const ratio = (halfway - traversed) / segmentLength;
      const first = line[index];
      const second = line[index + 1];
      return {
        coordinate: [
          first[0] + (second[0] - first[0]) * ratio,
          first[1] + (second[1] - first[1]) * ratio,
        ],
        length: totalLength,
      };
    }
    traversed += segmentLength;
  }

  return { coordinate: line[line.length - 1], length: totalLength };
}

function roadCoverageCenter(coordinates: unknown, isMultiLine: boolean): Coordinate | null {
  if (!isMultiLine) return lineMidpoint(coordinates)?.coordinate ?? null;
  if (!Array.isArray(coordinates)) return null;

  const carriageways = coordinates
    .map((line) => lineMidpoint(line))
    .filter((line): line is { coordinate: Coordinate; length: number } => line !== null);
  if (carriageways.length === 0) return null;

  const totalLength = carriageways.reduce((total, line) => total + line.length, 0);
  if (totalLength === 0) return carriageways[0].coordinate;

  return carriageways.reduce<Coordinate>(
    (center, line) => [
      center[0] + line.coordinate[0] * (line.length / totalLength),
      center[1] + line.coordinate[1] * (line.length / totalLength),
    ],
    [0, 0],
  );
}

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

  // 2. Follow road distance to the true segment midpoint. For a divided
  // road, average the length-weighted midpoint of each carriageway.
  if (rg && (rg.type === "LineString" || rg.type === "MultiLineString")) {
    const center = roadCoverageCenter(rg.coordinates, rg.type === "MultiLineString");
    if (center) return center;
  }

  // 3. If primary geometry is a Point
  if (g && g.type === "Point" && Array.isArray(g.coordinates)) {
    return [Number(g.coordinates[0]), Number(g.coordinates[1])];
  }

  // 4. Use the same road-aware midpoint for primary road geometry.
  if (g && (g.type === "LineString" || g.type === "MultiLineString")) {
    const center = roadCoverageCenter(g.coordinates, g.type === "MultiLineString");
    if (center) return center;
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
  padding?: { top?: number; bottom?: number; left?: number; right?: number };
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
    ...(options?.padding ? { padding: options.padding } : {}),
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
    ...(options?.padding ? { padding: options.padding } : {}),
  });
}
