"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import maplibregl, { type Map } from "maplibre-gl";
import BaseMap from "@/shared/ui/map/BaseMap";
import { PENDING_REPORT_POLYGON_AURA_PAINT, SEVERITY_COLORS, ZOOM_THRESHOLDS } from "@/features/map/mapStyles";
import { useFloodHeatmapLayer } from "@/features/map/hooks/useFloodHeatmapLayer";
import { useStaffMapData, type StaffMapPage } from "@/features/map/hooks/useStaffMapData";
import { historyParams, type FloodHistoryFilters, type HistoricalMapFocusTarget } from "./floodHistoryApi";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/apiClient";
import { Button } from "@/shared/ui";
import { syncGeoJSONSource } from "@/features/map/syncGeoJSONSource";

const SOURCE_ID = "historical-flood-events-source";
const FILL_LAYER_ID = "historical-flood-events-fill";
const FOCUS_SOURCE_ID = "historical-flood-focus-source";
const FOCUS_LAYERS = ["historical-flood-focus-fill", "historical-flood-focus-line", "historical-flood-focus-point"];

function coordinatesOf(value: unknown): [number, number][] {
  if (!Array.isArray(value)) return [];
  if (value.length >= 2 && typeof value[0] === "number" && typeof value[1] === "number") {
    return Number.isFinite(value[0]) && Number.isFinite(value[1]) && Math.abs(value[0]) <= 180 && Math.abs(value[1]) <= 90 ? [[value[0], value[1]]] : [];
  }
  return value.flatMap(coordinatesOf);
}

function geometryForZone(value: unknown): GeoJSON.Geometry | null {
  if (!value) return null;
  try {
    const geometry = typeof value === "string" ? JSON.parse(value) : value;
    if (geometry && typeof geometry === "object" && "type" in geometry && "coordinates" in geometry
      && coordinatesOf(geometry.coordinates).length) return geometry as GeoJSON.Geometry;
  } catch { return null; }
  return null;
}

interface HistoricalEventsMapProps {
  filters: FloodHistoryFilters;
  selectedEventId: number | null;
  onSelectEvent: (eventId: number) => void;
  focusTarget: HistoricalMapFocusTarget | null;
  visible: boolean;
  filterKey: string;
}

export function HistoricalEventsMap({ filters, selectedEventId, onSelectEvent, focusTarget, visible, filterKey }: HistoricalEventsMapProps) {
  const [map, setMap] = useState<Map | null>(null);
  const [layerError, setLayerError] = useState<string | null>(null);
  const [heatmapError, setHeatmapError] = useState<string | null>(null);
  const [zoom, setZoom] = useState(12.7);
  const framed = useRef<string | null>(null);
  const parameters = historyParams(filters, true); parameters.delete("limit");
  const data = useStaffMapData(map, "history", parameters.toString(), visible);
  const cameraEventId = focusTarget?.eventId ?? selectedEventId;
  const focusBounds = useQuery({ queryKey: ["flood-event-history", "focus", cameraEventId, parameters.toString()],
    queryFn: ({ signal }) => apiClient.get<StaffMapPage>(`/admin/flood-events/map?${parameters}&summary_only=true&event_id=${cameraEventId}`, { signal }),
    enabled: visible && cameraEventId !== null && !focusTarget?.geometry, staleTime: 30_000, retry: false });
  const collection = useMemo<GeoJSON.FeatureCollection>(() => ({ type: "FeatureCollection", features: data.features.map(feature => ({
    ...feature, id: feature.properties?.zone_id, properties: { ...feature.properties, color: SEVERITY_COLORS[feature.properties?.severity] || SEVERITY_COLORS.medium,
      is_selected: feature.properties?.event_id === selectedEventId },
  })) }), [data.features, selectedEventId]);
  const heatmap = useMemo<GeoJSON.FeatureCollection>(() => ({ type: "FeatureCollection", features: data.heatmap }), [data.heatmap]);
  useFloodHeatmapLayer(map, !!map, heatmap, true, {
    sourceId: "historical-flood-heatmap-source", layerId: "historical-flood-heatmap-layer", beforeId: FILL_LAYER_ID, onError: setHeatmapError,
  });

  useEffect(() => {
    if (!map) return;
    const draw = () => {
      if (!map.getStyle()) return;
      try {
        syncGeoJSONSource(map, SOURCE_ID, collection);
        if (!map.getLayer(FILL_LAYER_ID)) map.addLayer({ id: FILL_LAYER_ID, type: "fill", source: SOURCE_ID,
          minzoom: ZOOM_THRESHOLDS.DETAILED_MIN_ZOOM, paint: PENDING_REPORT_POLYGON_AURA_PAINT });
        const geometry = focusTarget?.cameraOnly ? null : geometryForZone(focusTarget?.geometry);
        const data: GeoJSON.FeatureCollection = { type: "FeatureCollection", features: geometry ? [{ type: "Feature", geometry,
          properties: { label: focusTarget?.label ?? "Historical detail" } }] : [] };
        const focusSource = map.getSource(FOCUS_SOURCE_ID) as maplibregl.GeoJSONSource | undefined;
        if (focusSource) focusSource.setData(data); else map.addSource(FOCUS_SOURCE_ID, { type: "geojson", data });
        if (!map.getLayer(FOCUS_LAYERS[0])) map.addLayer({ id: FOCUS_LAYERS[0], type: "fill", source: FOCUS_SOURCE_ID,
          filter: ["==", ["geometry-type"], "Polygon"], paint: { "fill-color": "#2563eb", "fill-opacity": 0.16 } });
        if (!map.getLayer(FOCUS_LAYERS[1])) map.addLayer({ id: FOCUS_LAYERS[1], type: "line", source: FOCUS_SOURCE_ID,
          filter: ["!=", ["geometry-type"], "Point"], paint: { "line-color": "#1d4ed8", "line-width": 4, "line-opacity": 0.95 } });
        if (!map.getLayer(FOCUS_LAYERS[2])) map.addLayer({ id: FOCUS_LAYERS[2], type: "circle", source: FOCUS_SOURCE_ID,
          filter: ["==", ["geometry-type"], "Point"], paint: { "circle-radius": 8, "circle-color": "#2563eb", "circle-stroke-width": 3, "circle-stroke-color": "#ffffff" } });
        setLayerError(null);
      } catch { setLayerError("Historical flood shapes could not be drawn. Reload the map to retry."); }
    };
    draw();
    map.on("style.load", draw);
    return () => { map.off("style.load", draw); };
  }, [map, collection, focusTarget]);

  useEffect(() => {
    if (!map) return;
    const select = (event: maplibregl.MapLayerMouseEvent) => {
      const id = Number(event.features?.[0]?.properties?.event_id);
      if (id) onSelectEvent(id);
    };
    const showPointer = () => { map.getCanvas().style.cursor = "pointer"; };
    const clearPointer = () => { map.getCanvas().style.cursor = ""; };
    const updateZoom = () => setZoom(map.getZoom());
    map.on("click", FILL_LAYER_ID, select);
    map.on("mouseenter", FILL_LAYER_ID, showPointer);
    map.on("mouseleave", FILL_LAYER_ID, clearPointer);
    map.on("zoomend", updateZoom);
    return () => {
      map.off("click", FILL_LAYER_ID, select);
      map.off("mouseenter", FILL_LAYER_ID, showPointer);
      map.off("mouseleave", FILL_LAYER_ID, clearPointer);
      map.off("zoomend", updateZoom);
    };
  }, [map, onSelectEvent]);

  // Geometry identity, rather than query object identity, prevents background reads
  // or selecting the already-selected card from resetting a manual camera position.
  const focusGeometry = geometryForZone(focusTarget?.geometry);
  const bounds = cameraEventId !== null ? focusBounds.data?.bounds : data.summary?.bounds;
  const frameKey = JSON.stringify({ filterKey, selection: cameraEventId, geometry: focusGeometry });
  const framing = JSON.stringify({ frameKey, selection: cameraEventId, bounds, geometry: focusGeometry });
  // Each explicit detail action can frame again after a manual pan. Background
  // query updates keep the same target and must preserve the user's camera.
  useEffect(() => { framed.current = null; }, [focusTarget]);
  useEffect(() => {
    if (!map) return;
    let frame: number;
    const fit = () => {
      frame = requestAnimationFrame(() => {
        const rect = map.getContainer().getBoundingClientRect();
        if (rect.width <= 0 || rect.height <= 0) return;
        map.resize();
        const target = JSON.parse(framing) as { frameKey: string; selection: number | null; bounds: [number,number,number,number] | null; geometry: GeoJSON.Geometry | null };
        if (framed.current === target.frameKey) return;
        const geometries = target.geometry ? [target.geometry] : [];
        const points = geometries.flatMap(geometry => coordinatesOf((geometry as GeoJSON.Geometry & { coordinates?: unknown }).coordinates));
        if (!points.length && target.bounds) points.push([target.bounds[0],target.bounds[1]], [target.bounds[2],target.bounds[3]]);
        if (!points.length) return;
        try {
          const bounds = points.slice(1).reduce((next, point) => next.extend(point), new maplibregl.LngLatBounds(points[0], points[0]));
          map.fitBounds(bounds, { padding: { top: 76, bottom: 106, left: 36, right: 36 }, maxZoom: 16,
            duration: target.selection && !window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 700 : 0 });
          framed.current = target.frameKey;
        } catch { setLayerError("Historical flood shapes could not be framed. Reload the map to retry."); }
      });
    };
    const observer = new ResizeObserver(fit);
    observer.observe(map.getContainer());
    fit();
    return () => { observer.disconnect(); cancelAnimationFrame(frame); };
  }, [map, framing, visible, focusTarget]);

  useEffect(() => {
    if (!map) return;
    return () => {
      if (!map.getStyle()) return;
      for (const id of [...FOCUS_LAYERS, FILL_LAYER_ID]) if (map.getLayer(id)) map.removeLayer(id);
      for (const id of [FOCUS_SOURCE_ID, SOURCE_ID]) if (map.getSource(id)) map.removeSource(id);
    };
  }, [map]);
  const handleMapLoad = useCallback((loaded: Map) => setMap(loaded), []);
  const error = layerError || heatmapError || data.error?.message || focusBounds.error?.message;
  const isLoading = data.isLoading;
  return <div aria-label="Historical flood map" className="relative h-[22rem] min-w-0 overflow-hidden rounded-xl border border-slate-200 bg-slate-100 lg:h-full lg:min-h-[38rem]">
    <BaseMap preloadRouting={false} onMapLoad={handleMapLoad} center={[121.085, 14.576]} zoom={12.7} className="h-full w-full" />
    <div className="pointer-events-none absolute left-3 top-3 max-w-[calc(100%-5rem)] rounded-lg bg-white/95 px-3 py-2 text-xs text-slate-600 shadow-sm"><p className="font-semibold text-slate-800">Verified event footprints</p><p>Historical only — never used for live routing.</p></div>
    {(error || isLoading || !data.summary?.mapped_count) && <p role={error ? "alert" : "status"} className="absolute left-3 right-16 top-24 rounded-lg bg-white/95 p-3 text-xs text-slate-700 shadow-sm">{error || (isLoading ? "Loading historical flood shapes…" : data.summary?.total ? "These records have no valid mapped footprints. Their details remain available in the list." : "No historical flood shapes match these filters.")}</p>}
    {error && <Button size="sm" variant="outline" className="absolute left-3 top-40" onClick={() => { data.refetch(); if (cameraEventId !== null) void focusBounds.refetch(); }}>Retry map</Button>}
    <div className="pointer-events-none absolute bottom-3 left-3 max-w-[calc(100%-5rem)] rounded-lg bg-white/95 p-2 text-[11px] text-slate-600 shadow-sm">
      {zoom < 15 ? <><p className="font-medium text-slate-800">Severity-weighted historical zone concentration</p><p>Blue → red: increasing concentration; not distinct-event frequency.</p><p>{data.summary?.mapped_count ?? 0} matching mapped historical zones</p>{zoom >= 14 && <p>Heatmap fades into footprints by zoom 15.</p>}</> : <><p className="font-medium text-slate-800">Peak verified severity — not exact depth or frequency</p><div className="mt-1 flex flex-wrap gap-x-2 gap-y-1"><span><i className="mr-1 inline-block h-2 w-2 rounded-full bg-lime-500" />Low</span><span><i className="mr-1 inline-block h-2 w-2 rounded-full bg-yellow-500" />Medium</span><span><i className="mr-1 inline-block h-2 w-2 rounded-full bg-orange-500" />High</span><span><i className="mr-1 inline-block h-2 w-2 rounded-full bg-red-500" />Extreme</span><span>Stronger fill: selected event</span></div></>}
    </div>
  </div>;
}
