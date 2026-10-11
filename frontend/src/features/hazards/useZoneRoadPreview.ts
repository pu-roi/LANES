"use client";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/apiClient";
import type { MapPoint } from "@/features/map/MapContext";
import type { RouteGeometry } from "@/features/routing/routingApi";

export function useZoneRoadPreview(start: MapPoint | null, end: MapPoint | null, isBidirectional: boolean, enabled: boolean) {
  return useQuery({ queryKey: ["zone-update-road-preview", start?.coords, end?.coords, isBidirectional],
    enabled: enabled && !!start && !!end,
    queryFn: () => apiClient.post<{ original: RouteGeometry; opposite: RouteGeometry | null; coverage_geometry: RouteGeometry; message: string; validation_status: string }>("/reports/preview-bidirectional", { start: start!.coords, end: end!.coords, is_bidirectional: isBidirectional, road_name: null }),
    retry: false, staleTime: 30000,
  });
}
