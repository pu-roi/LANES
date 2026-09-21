"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import maplibregl, { type Map } from "maplibre-gl";
import BaseMap from "@/shared/ui/map/BaseMap";
import type { FloodEventRecord, HistoricalMapFocusTarget } from "./floodHistoryApi";

const SOURCE_ID = "historical-flood-events-source";
const FILL_LAYER_ID = "historical-flood-events-fill";
const OUTLINE_LAYER_ID = "historical-flood-events-outline";
const FOCUS_SOURCE_ID = "historical-flood-focus-source";
const FOCUS_FILL_LAYER_ID = "historical-flood-focus-fill";
const FOCUS_LINE_LAYER_ID = "historical-flood-focus-line";
const FOCUS_POINT_LAYER_ID = "historical-flood-focus-point";

function geometryForZone(value: unknown): GeoJSON.Geometry | null {
  if (!value) return null;
  try {
    const geometry = typeof value === "string" ? JSON.parse(value) : value;
    if (geometry && typeof geometry === "object" && "type" in geometry && "coordinates" in geometry) return geometry as GeoJSON.Geometry;
  } catch { return null; }
  return null;
}

function coordinatesOf(value: unknown): [number, number][] {
  if (!Array.isArray(value)) return [];
  if (value.length >= 2 && typeof value[0] === "number" && typeof value[1] === "number") return [[value[0], value[1]]];
  return value.flatMap(coordinatesOf);
}

function buildCollection(events: FloodEventRecord[]): GeoJSON.FeatureCollection {
  return { type: "FeatureCollection", features: events.flatMap((event) => event.zones.flatMap((zone) => {
    const geometry = geometryForZone(zone.geometry);
    return geometry ? [{ type: "Feature" as const, properties: { event_id: event.id, severity: event.peak_severity, is_selected: false }, geometry }] : [];
  })) };
}

interface HistoricalEventsMapProps { events: FloodEventRecord[]; selectedEventId: number | null; onSelectEvent: (eventId: number) => void; }

export function HistoricalEventsMap({ events, selectedEventId, onSelectEvent, focusTarget }: HistoricalEventsMapProps & { focusTarget: HistoricalMapFocusTarget | null }) {
  const mapRef = useRef<Map | null>(null);
  const [isReady, setIsReady] = useState(false);
  const renderEvents = useCallback(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;
    const collection = buildCollection(events);
    const data = { ...collection, features: collection.features.map((feature) => ({ ...feature, properties: { ...feature.properties, is_selected: Number(feature.properties?.event_id) === selectedEventId } })) };
    const source = map.getSource(SOURCE_ID) as maplibregl.GeoJSONSource | undefined;
    if (source) source.setData(data); else map.addSource(SOURCE_ID, { type: "geojson", data });
    if (!map.getLayer(FILL_LAYER_ID)) map.addLayer({ id: FILL_LAYER_ID, type: "fill", source: SOURCE_ID, paint: { "fill-color": ["match", ["get", "severity"], "extreme", "#dc2626", "high", "#f97316", "medium", "#eab308", "#84cc16"], "fill-opacity": ["case", ["get", "is_selected"], 0.46, 0.22] } });
    if (!map.getLayer(OUTLINE_LAYER_ID)) map.addLayer({ id: OUTLINE_LAYER_ID, type: "line", source: SOURCE_ID, paint: { "line-color": ["case", ["get", "is_selected"], "#0f172a", "#475569"], "line-width": ["case", ["get", "is_selected"], 3, 1.5], "line-opacity": 0.9 } });
  }, [events, selectedEventId]);

  const renderFocus = useCallback(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;
    const geometry = geometryForZone(focusTarget?.geometry);
    const data: GeoJSON.FeatureCollection = { type: "FeatureCollection", features: geometry ? [{ type: "Feature", properties: { label: focusTarget?.label ?? "Historical detail" }, geometry }] : [] };
    const source = map.getSource(FOCUS_SOURCE_ID) as maplibregl.GeoJSONSource | undefined;
    if (source) source.setData(data); else map.addSource(FOCUS_SOURCE_ID, { type: "geojson", data });
    if (!map.getLayer(FOCUS_FILL_LAYER_ID)) map.addLayer({ id: FOCUS_FILL_LAYER_ID, type: "fill", source: FOCUS_SOURCE_ID, filter: ["==", ["geometry-type"], "Polygon"], paint: { "fill-color": "#2563eb", "fill-opacity": 0.16 } });
    if (!map.getLayer(FOCUS_LINE_LAYER_ID)) map.addLayer({ id: FOCUS_LINE_LAYER_ID, type: "line", source: FOCUS_SOURCE_ID, paint: { "line-color": "#1d4ed8", "line-width": 4, "line-opacity": 0.95 } });
    if (!map.getLayer(FOCUS_POINT_LAYER_ID)) map.addLayer({ id: FOCUS_POINT_LAYER_ID, type: "circle", source: FOCUS_SOURCE_ID, filter: ["==", ["geometry-type"], "Point"], paint: { "circle-radius": 8, "circle-color": "#2563eb", "circle-stroke-width": 3, "circle-stroke-color": "#ffffff" } });
  }, [focusTarget]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !isReady) return;
    renderEvents();
    renderFocus();
    const onStyleLoad = () => { renderEvents(); renderFocus(); };
    const selectFeature = (event: maplibregl.MapLayerMouseEvent) => {
      const id = Number(event.features?.[0]?.properties?.event_id);
      if (id) onSelectEvent(id);
    };
    const showPointer = () => { map.getCanvas().style.cursor = "pointer"; };
    const clearPointer = () => { map.getCanvas().style.cursor = ""; };
    map.on("style.load", onStyleLoad);
    map.on("click", FILL_LAYER_ID, selectFeature);
    map.on("click", OUTLINE_LAYER_ID, selectFeature);
    map.on("mouseenter", FILL_LAYER_ID, showPointer);
    map.on("mouseleave", FILL_LAYER_ID, clearPointer);
    return () => {
      map.off("style.load", onStyleLoad);
      map.off("click", FILL_LAYER_ID, selectFeature);
      map.off("click", OUTLINE_LAYER_ID, selectFeature);
      map.off("mouseenter", FILL_LAYER_ID, showPointer);
      map.off("mouseleave", FILL_LAYER_ID, clearPointer);
    };
  }, [isReady, onSelectEvent, renderEvents, renderFocus]);
  useEffect(() => { const map = mapRef.current; const selected = events.find((event) => event.id === selectedEventId); if (!map || !selected || !isReady) return; const focusGeometry = geometryForZone(focusTarget?.geometry); const points = focusGeometry ? coordinatesOf((focusGeometry as GeoJSON.Geometry & { coordinates?: unknown }).coordinates) : selected.zones.flatMap((zone) => coordinatesOf((geometryForZone(zone.geometry) as GeoJSON.Geometry & { coordinates?: unknown } | null)?.coordinates)); if (!points.length) return; const bounds = points.slice(1).reduce((next, point) => next.extend(point), new maplibregl.LngLatBounds(points[0], points[0])); map.fitBounds(bounds, { padding: 56, maxZoom: 16, duration: 700 }); }, [events, focusTarget, isReady, selectedEventId]);

  const handleMapLoad = useCallback((map: Map) => { mapRef.current = map; setIsReady(true); }, []);

  return <div className="relative h-[22rem] overflow-hidden rounded-xl border border-slate-200 bg-slate-100 lg:h-full lg:min-h-[38rem]"><BaseMap onMapLoad={handleMapLoad} center={[121.085, 14.576]} zoom={12.7} className="h-full w-full" /><div className="pointer-events-none absolute left-3 top-3 rounded-lg bg-white/95 px-3 py-2 text-xs text-slate-600 shadow-sm"><p className="font-semibold text-slate-800">Verified event footprints</p><p>Historical only — never used for live routing.</p></div><div className="pointer-events-none absolute bottom-3 left-3 max-w-[calc(100%-1.5rem)] rounded-lg bg-white/95 p-2 text-[11px] text-slate-600 shadow-sm"><p className="font-medium text-slate-800">Peak verified severity — not exact depth or frequency</p><div className="mt-1 flex flex-wrap gap-x-2 gap-y-1"><span><i className="mr-1 inline-block h-2 w-2 rounded-full bg-lime-500" />Low</span><span><i className="mr-1 inline-block h-2 w-2 rounded-full bg-amber-500" />Medium</span><span><i className="mr-1 inline-block h-2 w-2 rounded-full bg-orange-500" />High</span><span><i className="mr-1 inline-block h-2 w-2 rounded-full bg-red-600" />Extreme</span><span className="border-l border-slate-300 pl-2">Dark outline: selected event</span></div></div></div>;
}
