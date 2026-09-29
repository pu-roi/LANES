import { useEffect, useRef } from "react";
import type { Map } from "maplibre-gl";
import manifest from "../../../../public/noah-hazard/manifest.json";
import type { NoahHazardScenario } from "../MapContext";

const SOURCE_ID = "noah-modeled-hazard-source";
const LAYER_ID = "noah-modeled-hazard-layer";
const [west, south, east, north] = manifest.bounds;
const coordinates: [[number, number], [number, number], [number, number], [number, number]] = [
  [west, north], [east, north], [east, south], [west, south],
];

export function useNoahHazardLayer(
  map: Map | null,
  isLoaded: boolean,
  scenario: NoahHazardScenario | null,
  onError: (message: string) => void,
) {
  const errorCallback = useRef(onError);
  useEffect(() => {
    errorCallback.current = onError;
  }, [onError]);

  useEffect(() => {
    if (!map || !isLoaded) return;
    let cancelled = false;
    let image: HTMLImageElement | null = null;
    const removeLayer = () => {
      if (!map.getStyle()) return;
      if (map.getLayer(LAYER_ID)) map.removeLayer(LAYER_ID);
      if (map.getSource(SOURCE_ID)) map.removeSource(SOURCE_ID);
    };

    removeLayer();
    if (scenario === null) return;

    const url = `/noah-hazard/metro-manila-${scenario}yr.png`;
    const setupLayer = () => {
      if (cancelled || !map.getStyle()) return;
      if (!map.getSource(SOURCE_ID)) {
        map.addSource(SOURCE_ID, { type: "image", url, coordinates });
      }
      if (!map.getLayer(LAYER_ID)) {
        // Place the model beneath labels and above the basemap. Active Flood
        // Zones and route lines use separate layers and remain above it.
        const firstLabel = map.getStyle().layers.find((layer) => layer.type === "symbol")?.id;
        map.addLayer({
          id: LAYER_ID,
          type: "raster",
          source: SOURCE_ID,
          paint: { "raster-opacity": 0.68, "raster-fade-duration": 0 },
        }, firstLabel);
      }
    };

    const handleError = (event: { sourceId?: string; error?: { message?: string } }) => {
      if (event.sourceId === SOURCE_ID || event.error?.message?.includes(url)) {
        errorCallback.current("Could not display the selected NOAH hazard map. Please try another scenario.");
      }
    };
    map.on("style.load", setupLayer);
    map.on("error", handleError);

    // Check the image before adding it as a MapLibre source so missing or
    // unreadable presentation assets produce a clear user-facing error.
    image = new Image();
    image.onload = setupLayer;
    image.onerror = () => {
      if (!cancelled) errorCallback.current("Could not load the selected NOAH hazard map. Please try another scenario.");
    };
    image.src = url;

    return () => {
      cancelled = true;
      if (image) {
        image.onload = null;
        image.onerror = null;
      }
      map.off("style.load", setupLayer);
      map.off("error", handleError);
      removeLayer();
    };
  }, [map, isLoaded, scenario]);
}
