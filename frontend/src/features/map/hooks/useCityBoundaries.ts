import { useEffect } from "react";
import type { Map } from "maplibre-gl";

export function useCityBoundaries(map: Map | null, isLoaded: boolean) {
  useEffect(() => {
    if (!map || !isLoaded) return;

    // ── Helper: idempotently add all boundary sources + layers ───────────────
    // Called both on first load and on every subsequent style.load (MapLibre v5
    // re-triggers style.load when setTerrain() is called, wiping custom layers).
    function initBoundaries() {
      if (!map || !map.getStyle()) return;

      // 1. Philippines Border Line
      if (!map.getSource("philippines-boundary")) {
        map.addSource("philippines-boundary", {
          type: "geojson",
          data: "/philippines-boundary.geojson",
        });
      }
      if (!map.getLayer("philippines-boundary-line")) {
        map.addLayer({
          id: "philippines-boundary-line",
          type: "line",
          source: "philippines-boundary",
          paint: {
            "line-color": "#10b981",
            "line-width": 3,
            "line-opacity": 0.5,
          },
        });
      }

      // 2. Pasig City Dark Mask
      if (!map.getSource("pasig-mask")) {
        map.addSource("pasig-mask", {
          type: "geojson",
          data: "/pasig-mask.geojson",
        });
      }
      if (!map.getLayer("pasig-mask-fill")) {
        map.addLayer({
          id: "pasig-mask-fill",
          type: "fill",
          source: "pasig-mask",
          paint: {
            "fill-color": "#000000",
            "fill-opacity": 0.35,
          },
        });
      }

      // 3. Pasig City Boundary Line
      if (!map.getSource("pasig-boundary")) {
        map.addSource("pasig-boundary", {
          type: "geojson",
          data: "/pasig-boundary.geojson",
        });
      }
      if (!map.getLayer("pasig-boundary-line")) {
        map.addLayer({
          id: "pasig-boundary-line",
          type: "line",
          source: "pasig-boundary",
          paint: {
            "line-color": "#3b82f6",
            "line-width": 4,
            "line-opacity": 0.8,
            "line-dasharray": [2, 2],
          },
        });
      }
    }

    // ── Persistent style.load listener ───────────────────────────────────────
    // MapLibre v5 fires 'style.load' after every setTerrain() call as well as
    // on manual style hot-swaps. Re-applying boundaries here ensures they are
    // never lost when terrain is toggled.
    const handleStyleLoad = () => {
      initBoundaries();
    };
    map.on("style.load", handleStyleLoad);

    // ── Initial application ───────────────────────────────────────────────────
    initBoundaries();

    return () => {
      map.off("style.load", handleStyleLoad);
    };
  }, [map, isLoaded]);
}
