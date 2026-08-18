import maplibregl from "maplibre-gl";
import { Protocol } from "pmtiles";

let isRegistered = false;

export function registerOfflineProtocol() {
  if (typeof window === "undefined" || isRegistered) return;

  try {
    const protocol = new Protocol();
    maplibregl.addProtocol("pmtiles", protocol.tile);
    isRegistered = true;
    console.log("Registered pmtiles:// protocol for MapLibre offline vector tiles");
  } catch (e) {
    console.warn("Failed to register pmtiles protocol:", e);
  }
}
