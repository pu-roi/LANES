import { apiClient } from "@/shared/api";

let valhallaWorker: Worker | null = null;

function getValhallaWorker(): Worker {
  if (!valhallaWorker && typeof window !== "undefined") {
    valhallaWorker = new Worker(new URL("../../workers/valhalla-worker.ts", import.meta.url));
  }
  return valhallaWorker!;
}

// Eagerly instantiate and cache worker in memory while online!
export function preloadOfflineEngine() {
  if (typeof window !== "undefined") {
    // Fire and forget: this fetches the worker chunk, valhalla.js, and valhalla.wasm while online.
    const worker = getValhallaWorker();
    worker.postMessage({ type: 'init' });
  }
}

// Valhalla polyline decoder (precision 6)
function decodeValhallaPolyline(str: string, precision: number = 6): [number, number][] {
  let index = 0, lat = 0, lng = 0, coordinates: [number, number][] = [];
  const factor = Math.pow(10, precision);

  while (index < str.length) {
    let b, shift = 0, result = 0;
    do {
      b = str.charCodeAt(index++) - 63;
      result |= (b & 0x1f) << shift;
      shift += 5;
    } while (b >= 0x20);
    const dlat = ((result & 1) ? ~(result >> 1) : (result >> 1));
    lat += dlat;

    shift = 0;
    result = 0;
    do {
      b = str.charCodeAt(index++) - 63;
      result |= (b & 0x1f) << shift;
      shift += 5;
    } while (b >= 0x20);
    const dlng = ((result & 1) ? ~(result >> 1) : (result >> 1));
    lng += dlng;

    // GeoJSON format is [lon, lat]
    coordinates.push([lng / factor, lat / factor]);
  }
  return coordinates;
}

export interface RouteGeometry {
  type: "LineString";
  coordinates: [number, number][];
}

export interface RouteOption {
  index: number;
  label: string; // "Recommended" | "Alternative 1" | "Alternative 2"
  geometry: RouteGeometry;
  distance: number;  // meters
  duration: number;  // seconds
  avoided_floods: boolean;
  blocked: boolean;
  is_truncated: boolean;
  safety_score: number;
  flood_risk: string;
}

export interface MultiRouteResponse {
  routes: RouteOption[];
  recommended_index: number;
  avoided_floods?: boolean;
  blocked?: boolean;
  weather_condition?: string;
  weather_advisory?: string;
  hazard_summary?: string;
  has_critical_floods?: boolean;
}

export interface RouteInfo {
  distance: number;
  duration: number;
  avoided_floods: boolean;
  blocked: boolean;
}

import { getFloodsOffline } from '@/lib/offline/storage';

export async function getRoute(
  start: [number, number],
  end: [number, number],
  ignoreFloods: boolean = false,
  vehicleProfile: "light" | "heavy" | "motorcycle" | "walk" = "light"
): Promise<MultiRouteResponse> {
  // If we are completely offline, fall back to the Valhalla WASM Web Worker
  if (typeof window !== "undefined" && !navigator.onLine) {
    let excludePolygons: [number, number][][] = [];
    
    if (!ignoreFloods) {
      try {
        const cachedFloods = await getFloodsOffline();
        if (cachedFloods && cachedFloods.length > 0) {
          // Convert cached GeoJSON polygons to Valhalla format
          excludePolygons = cachedFloods.map((flood: any) => {
             // The backend SSE sends the GeoJSON under the 'polygon' key
             if (flood.polygon && flood.polygon.type === "Polygon") {
                return flood.polygon.coordinates[0];
             }
             return null;
          }).filter(Boolean);
          console.log("[Offline Routing] Fetched cached floods. excludePolygons =", excludePolygons);
        }
      } catch (err) {
        console.warn("Failed to load cached floods for offline routing", err);
      }
    }

    return new Promise((resolve, reject) => {
      try {
        const worker = getValhallaWorker();
        const payload: any = {
          start: [start[0], start[1]], // [lng, lat]
          end: [end[0], end[1]],       // [lng, lat]
          regions: ["philippines"]     // matches philippines_routing.tar
        };
        
        if (excludePolygons.length > 0) {
           payload.exclude_polygons = excludePolygons;
        }

        // 30-second timeout for first-time WASM compilation & tile reading
        const timeoutId = setTimeout(() => {
          worker.removeEventListener("message", handleMessage);
          worker.removeEventListener("error", handleError);
          reject(new Error("Offline routing timed out while initializing WASM engine. Please check console."));
        }, 30000);

        const handleError = (errEvent: ErrorEvent) => {
          clearTimeout(timeoutId);
          worker.removeEventListener("message", handleMessage);
          worker.removeEventListener("error", handleError);
          console.error("[Valhalla-Worker ErrorEvent]:", errEvent);
          reject(new Error(errEvent.message || "Failed to execute offline routing worker."));
        };

        const handleMessage = (e: MessageEvent) => {
          if (e.data.type === "progress") {
            console.log("[Valhalla-WASM Progress]:", e.data.message);
            return;
          }

          if (e.data.type === "success") {
            clearTimeout(timeoutId);
            worker.removeEventListener("message", handleMessage);
            worker.removeEventListener("error", handleError);
            const result = e.data.result;
            
            if (!result || !result.success || !result.geometry) {
              return reject(new Error(result?.error || "No route found by offline engine."));
            }

            // Snap exact start/end pins to the route geometry to prevent visual gaps
            if (result.geometry?.coordinates?.length > 0) {
              const coords = result.geometry.coordinates;
              const first = coords[0];
              const last = coords[coords.length - 1];
              
              if (Math.abs(first[0] - start[0]) > 0.00001 || Math.abs(first[1] - start[1]) > 0.00001) {
                coords.unshift([start[0], start[1]]);
              }
              if (Math.abs(last[0] - end[0]) > 0.00001 || Math.abs(last[1] - end[1]) > 0.00001) {
                coords.push([end[0], end[1]]);
              }
            }

            const routeOption: RouteOption = {
              index: 0,
              label: result.avoided_floods ? "Recommended (Offline)" : "Offline Route",
              geometry: result.geometry,
              distance: (result.summary?.distance || 0) * 1609.34, // valhalla summary distance is miles, convert to meters
              duration: result.summary?.time || 0, // seconds
              avoided_floods: result.avoided_floods,
              blocked: false,
              is_truncated: false,
              safety_score: 1.0,
              flood_risk: "None"
            };

            resolve({
              routes: [routeOption],
              recommended_index: 0
            });
          } else if (e.data.type === "error") {
            clearTimeout(timeoutId);
            worker.removeEventListener("message", handleMessage);
            worker.removeEventListener("error", handleError);
            reject(new Error(e.data.error));
          }
        };

        worker.addEventListener("error", handleError);
        worker.addEventListener("message", handleMessage);
        worker.postMessage(payload);
      } catch (err) {
        reject(err);
      }
    });
  }

  // Standard Online Mode using FastAPI & GraphHopper
  return apiClient.post<MultiRouteResponse>("/reports/route", {
    start,
    end,
    ignore_floods: ignoreFloods,
    vehicle_profile: vehicleProfile
  });
}
