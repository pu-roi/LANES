"use client";

import { useEffect, useRef } from "react";
import type { Map, MapMouseEvent } from "maplibre-gl";
import { useMapContext } from "@/features/map/MapContext";
import { useFloodMapPreview } from "@/features/map/hooks/useFloodMapPreview";

interface AdminFloodMapInteractionProps {
  map: Map | null;
  isLoaded: boolean;
  isPreviewEnabled: boolean;
  isCreateZoneDrawerOpen: boolean;
}

/**
 * Keeps the admin Create Zone line interaction aligned with the public map.
 * The map owns one click listener; MapContext owns the Start/End state machine.
 */
export function AdminFloodMapInteraction({
  map,
  isLoaded,
  isPreviewEnabled,
  isCreateZoneDrawerOpen,
}: AdminFloodMapInteractionProps) {
  const {
    activePoint,
    isPickingOnMap,
    setPointFromMap,
    setActivePoint,
    setIsPickingOnMap,
    floodStart,
    floodEnd,
    floodPreviewGeometry,
    floodOppositeGeometry,
    floodIsBidirectional,
  } = useMapContext();

  const isPickingRef = useRef(isPickingOnMap);
  const setPointFromMapRef = useRef(setPointFromMap);
  const wasCreateZoneDrawerOpenRef = useRef(isCreateZoneDrawerOpen);

  useEffect(() => {
    isPickingRef.current = isPickingOnMap;
  }, [isPickingOnMap]);

  useEffect(() => {
    setPointFromMapRef.current = setPointFromMap;
  }, [setPointFromMap]);

  useEffect(() => {
    const wasOpen = wasCreateZoneDrawerOpenRef.current;
    wasCreateZoneDrawerOpenRef.current = isCreateZoneDrawerOpen;

    if (wasOpen && !isCreateZoneDrawerOpen && (activePoint === "flood_start" || activePoint === "flood_end")) {
      setIsPickingOnMap(false);
      setActivePoint(null);
    }
  }, [activePoint, isCreateZoneDrawerOpen, setActivePoint, setIsPickingOnMap]);

  useEffect(() => {
    if (!map || !isLoaded) return;

    const handleMapClick = (event: MapMouseEvent) => {
      if (!isPickingRef.current) return;
      setPointFromMapRef.current([event.lngLat.lng, event.lngLat.lat]);
    };

    map.on("click", handleMapClick);
    return () => {
      map.off("click", handleMapClick);
    };
  }, [map, isLoaded]);

  useEffect(() => {
    if (!map || !isLoaded) return;

    const canvas = map.getCanvas();
    const container = map.getCanvasContainer();
    const cursor = isPickingOnMap ? "crosshair" : "";
    canvas.style.cursor = cursor;
    container.style.cursor = cursor;

    return () => {
      canvas.style.cursor = "";
      container.style.cursor = "";
    };
  }, [map, isLoaded, isPickingOnMap, activePoint]);

  useFloodMapPreview(
    map,
    floodStart,
    floodEnd,
    floodPreviewGeometry,
    floodOppositeGeometry,
    floodIsBidirectional,
    isLoaded && isPreviewEnabled,
  );

  return null;
}
