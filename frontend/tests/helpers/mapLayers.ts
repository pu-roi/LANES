import type { Page } from "@playwright/test";
import type { Map } from "maplibre-gl";

/** Inspect the real MapLibre instance held by React; no production test globals. */
export async function mapLayers(page: Page, action?: { zoom?: number; center?: [number, number]; reloadStyle?: boolean; pan?: boolean; failHeatmap?: boolean; restore?: boolean; countsOnly?: boolean }) {
  return page.evaluate(params => {
    type Hook = { memoizedState?: unknown; next?: Hook };
    type Fiber = { memoizedState?: Hook; return?: Fiber; alternate?: Fiber };
    const canvas = document.querySelector('[aria-label="Historical flood map"] .maplibregl-canvas') ?? document.querySelector(".maplibregl-canvas");
    let map: Map | undefined;
    for (let element = canvas; element && !map; element = element.parentElement) {
      const key = Object.keys(element).find(value => value.startsWith("__reactFiber$"));
      if (!key) continue;
      let fiber = (element as unknown as Record<string, Fiber>)[key];
      while (fiber && !map) {
        for (const current of [fiber, fiber.alternate]) for (let hook = current?.memoizedState; hook; hook = hook.next) {
          const state = hook.memoizedState as { current?: unknown } | undefined;
          const candidate = (state?.current ?? state) as Map | undefined;
          if (candidate && typeof candidate.getStyle === "function" && typeof candidate.getCanvas === "function") { map = candidate; break; }
        }
        fiber = fiber.return!;
      }
    }
    if (!map) return null;
    const controlled = map as Map & { originalHeatmapAddLayer?: Map["addLayer"] };
    if (params?.failHeatmap && !controlled.originalHeatmapAddLayer) {
      controlled.originalHeatmapAddLayer = map.addLayer;
      map.addLayer = function(layer, before) {
        if (layer.type === "heatmap") throw new Error("Fictional heatmap rendering failure");
        return controlled.originalHeatmapAddLayer!.call(this, layer, before);
      };
    }
    if (params?.restore && controlled.originalHeatmapAddLayer) { map.addLayer = controlled.originalHeatmapAddLayer; delete controlled.originalHeatmapAddLayer; }
    if (params?.zoom !== undefined) map.jumpTo({ zoom: params.zoom });
    if (params?.center) map.jumpTo({ center: params.center });
    if (params?.pan) map.jumpTo({ center: [121.1, 14.6] });
    if (params?.reloadStyle) map.setStyle({ version: 8, sources: {}, layers: [{ id: "fixture-background", type: "background", paint: { "background-color": "#f1f5f9" } }] });
    const style = map.getStyle();
    const sourceCounts = Object.fromEntries(Object.entries(style?.sources ?? {}).map(([id, source]) => [id,
      source.type === "geojson" && typeof source.data === "object" && "features" in source.data ? source.data.features.length : 0]));
    return { zoom: map.getZoom(), center: map.getCenter().toArray(), layers: style?.layers ?? [], sourceCounts,
      sources: params?.countsOnly ? {} : style?.sources ?? {},
      rendered: params?.countsOnly ? [] : map.queryRenderedFeatures().map(feature => ({ layer: feature.layer.id, properties: feature.properties })) };
  }, action);
}
