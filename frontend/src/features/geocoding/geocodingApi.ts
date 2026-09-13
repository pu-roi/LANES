import { CONSTANTS } from "@/features/map/mapUtils";
import type { LocationSuggestion } from "./types";

const PHOTON_URL = "https://photon.komoot.io/api/";

// Fallback scoring for relevance if needed
function scorePhotonResult(feature: any, query: string): number {
  const normalizedQuery = query.toLowerCase().trim();
  const name = (feature.properties.name || "").toLowerCase();
  let score = 0;

  if (name.includes(normalizedQuery)) {
    score += 50;
  }

  const queryParts = normalizedQuery.split(/[\s,]+/).filter(Boolean);
  for (const part of queryParts) {
    if (part.length >= 2 && name.includes(part)) {
      score += 15;
    }
  }

  const locality = feature.properties.city || feature.properties.locality || feature.properties.state || "";
  if (locality.toLowerCase().includes("pasig")) {
    score += 40;
  } else if (name.includes("pasig")) {
    score += 30;
  }

  if (name.includes("metro manila") || name.includes("national capital region")) {
    score += 10;
  }

  const [centerLng, centerLat] = CONSTANTS.DEFAULT_CENTER;
  const lng = feature.geometry.coordinates[0];
  const lat = feature.geometry.coordinates[1];
  const distance = Math.sqrt((lng - centerLng) ** 2 + (lat - centerLat) ** 2) * 111; // approx km
  score += Math.max(0, 20 - distance);

  return score;
}

function featureToSuggestion(feature: any, query: string): LocationSuggestion {
  const props = feature.properties;
  
  // Construct a sensible display name
  const parts = [props.name, props.street, props.locality, props.city, props.state]
    .filter(Boolean)
    // Remove duplicates
    .filter((value, index, self) => self.indexOf(value) === index);
    
  const displayName = parts.join(", ");
  const label = parts.slice(0, 2).join(", ");

  return {
    id: String(props.osm_id || Math.random()),
    label: label || "Unknown Location",
    displayName: displayName || "Unknown Location",
    lng: feature.geometry.coordinates[0],
    lat: feature.geometry.coordinates[1],
    relevanceScore: scorePhotonResult(feature, query),
  };
}

export async function searchLocations(query: string): Promise<LocationSuggestion[]> {
  const trimmed = query.trim();
  if (trimmed.length < 2) return [];

  const params = new URLSearchParams({
    q: trimmed,
    limit: "8",
    // Bias results towards Pasig/Metro Manila
    lon: CONSTANTS.DEFAULT_CENTER[0].toString(),
    lat: CONSTANTS.DEFAULT_CENTER[1].toString()
  });

  const response = await fetch(`${PHOTON_URL}?${params.toString()}`, {
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    throw new Error("Location search failed");
  }

  const data = await response.json();
  const features = data.features || [];

  return features
    .map((feature: any) => featureToSuggestion(feature, trimmed))
    .sort((a: LocationSuggestion, b: LocationSuggestion) => b.relevanceScore - a.relevanceScore)
    .slice(0, 6);
}

export function formatCoords(lng: number, lat: number): string {
  return `${lng.toFixed(6)},${lat.toFixed(6)}`;
}

export function parseCoords(value: string): [number, number] | null {
  const parts = value.split(",").map((part) => part.trim());
  if (parts.length !== 2) return null;

  const lng = Number(parts[0]);
  const lat = Number(parts[1]);
  if (Number.isNaN(lng) || Number.isNaN(lat)) return null;

  return [lng, lat];
}

export async function getCurrentLocation(): Promise<[number, number]> {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error("Geolocation is not supported by your browser. Please use a modern browser."));
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => resolve([position.coords.longitude, position.coords.latitude]),
      (error) => {
        // Do NOT silently fall back to IP-based location — it is city/ISP-level and highly inaccurate.
        // Surface the actual error so the user knows to grant location permissions.
        let message: string;
        switch (error.code) {
          case error.PERMISSION_DENIED:
            message =
              "Location access was denied. Please enable location permissions in your browser settings and try again.";
            break;
          case error.POSITION_UNAVAILABLE:
            message =
              "Your location could not be determined. Please ensure your device's GPS or location services are enabled.";
            break;
          case error.TIMEOUT:
            message =
              "Location request timed out. Please check your connection and try again.";
            break;
          default:
            message = "Unable to retrieve your location. Please check your location permissions.";
        }
        reject(new Error(message));
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0,
      }
    );
  });
}
