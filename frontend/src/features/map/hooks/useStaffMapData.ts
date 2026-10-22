"use client";

import { useEffect, useMemo, useState } from "react";
import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import type { Map } from "maplibre-gl";
import { apiClient } from "@/lib/apiClient";

export interface StaffMapPage {
  features: GeoJSON.Feature<GeoJSON.Geometry>[];
  heatmap_features: GeoJSON.Feature<GeoJSON.Point>[];
  bounds: [number, number, number, number] | null;
  total: number;
  mapped_count: number;
  unmapped_count: number;
  viewport_count: number;
  next_cursor: number | null;
}

export const staffKeys = {
  zones: ["adminZones"] as const,
  history: ["flood-event-history"] as const,
};

async function readMap(url: string, signal: AbortSignal): Promise<StaffMapPage> {
  const value = await apiClient.get<StaffMapPage>(url, { signal });
  if (!Array.isArray(value.features) || !Array.isArray(value.heatmap_features)) throw new Error("Map data could not be loaded. Update the backend and retry.");
  return value;
}

export function useStaffMapData(map: Map | null, domain: "zones" | "history", params: string, active: boolean) {
  const [viewport, setViewport] = useState<{ bbox: string; zoom: number } | null>(null);
  const prefix = domain === "zones" ? staffKeys.zones : staffKeys.history;
  const endpoint = domain === "zones" ? "/admin/zones/map" : "/admin/flood-events/map";
  const staleTime = domain === "zones" ? 15_000 : 30_000;
  useEffect(() => {
    if (!map || !active) return;
    let timer: ReturnType<typeof setTimeout>;
    const update = () => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        const bounds = map.getBounds();
        const west = Math.max(-180, bounds.getWest()), east = Math.min(180, bounds.getEast());
        const south = Math.max(-85.051128, bounds.getSouth()), north = Math.min(85.051128, bounds.getNorth());
        if (west < east && south < north) setViewport({ bbox: [west,south,east,north].map(value => value.toFixed(6)).join(","), zoom: map.getZoom() });
      }, 200);
    };
    update(); map.on("moveend", update); map.on("resize", update);
    return () => { clearTimeout(timer); map.off("moveend", update); map.off("resize", update); };
  }, [map, active]);
  const summary = useQuery({ queryKey: [...prefix, "map-summary", params],
    queryFn: ({ signal }) => readMap(`${endpoint}?${params}&summary_only=true`, signal),
    enabled: active && !!map, staleTime, retry: false,
    refetchInterval: active && domain === "zones" ? 15_000 : false });
  const pages = useInfiniteQuery({ queryKey: [...prefix, "map-viewport", params, viewport], initialPageParam: 0,
    queryFn: ({ pageParam, signal }) => readMap(`${endpoint}?${params}&bbox=${viewport!.bbox}&zoom=${viewport!.zoom}&cursor=${pageParam}`, signal),
    getNextPageParam: page => page.next_cursor ?? undefined, enabled: active && !!map && viewport !== null,
    staleTime, gcTime: 30_000, retry: false, refetchInterval: active && domain === "zones" ? 15_000 : false });
  const { hasNextPage, isFetching, isError, fetchNextPage } = pages;
  useEffect(() => { if (active && hasNextPage && !isFetching && !isError) void fetchNextPage(); },
    [active, hasNextPage, isFetching, isError, fetchNextPage]);
  const features = useMemo(() => pages.data?.pages.flatMap(page => page.features) ?? [], [pages.data]);
  const heatmap = useMemo(() => pages.data?.pages[0]?.heatmap_features ?? [], [pages.data]);
  return { features, heatmap, summary: summary.data, error: summary.error || pages.error,
    isLoading: summary.isLoading || pages.isLoading || pages.hasNextPage, isFetching: summary.isFetching || pages.isFetching,
    refetch: () => { void summary.refetch(); void pages.refetch(); } };
}
