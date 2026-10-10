import React, { useEffect, useRef } from "react";
import maplibregl, { Map } from "maplibre-gl";
import { createRoot, type Root } from "react-dom/client";
import { FloodZonePopup, type FloodPlacementPopupDetails } from "../components/FloodZonePopup";
import type { ZoneCondition, ZoneUpdateContext } from "@/features/hazards/zoneUpdatesApi";
import {
  SEVERITY_COLORS,
  SEVERITY_BORDER_COLORS,
  ZOOM_THRESHOLDS,
  PIN_CIRCLE_PAINT,
  ACTIVE_ZONE_POLYGON_FILL_PAINT,
  ACTIVE_ZONE_ROAD_CORE_PAINT,
  PENDING_REPORT_ROAD_AURA_PAINT,
} from "../mapStyles";
import { computeCenterCoordinate, flyToCoordinates } from "../mapGeoUtils";
import { floodPopupAnchor } from "../mapPopupUtils";

export interface FloodZoneLayerOptions {
  namespace?: string;
  mode?: "active" | "review";
  onError?: (message: string | null) => void;
}

export function useFloodZonesLayer(
  map: Map | null,
  isLoaded: boolean,
  activeZonesData?: any[],
  isTouchDevice: boolean = false,
  activeTab: string = "zones",
  selectedZoneId?: number | null,
  setSelectedZoneId?: (id: number | null) => void,
  selectedContributorId?: number | null,
  setSelectedContributorId?: (id: number | null) => void,
  onZoneUpdate?: (zone: ZoneUpdateContext, condition: ZoneCondition) => void,
  options?: FloodZoneLayerOptions
) {
  const activePopupRef = useRef<{ popup: maplibregl.Popup | null; root: Root; zoneId?: number;
    container: HTMLElement; lngLat: { lng: number; lat: number }; color: string } | null>(null);
  const namespace = options?.namespace ?? "active-zones";
  const reviewMode = options?.mode === "review";
  const onError = options?.onError;
  const sourceId = `${namespace}-source`;
  const fillLayer = `${namespace}-layer`;
  const roadLayer = `${namespace}-road-core-layer`;
  const pinLayer = `${namespace}-circle-layer`;
  const interaction = useRef({ activeZonesData, selectedZoneId, setSelectedZoneId, onZoneUpdate });
  useEffect(() => {
    interaction.current = { activeZonesData, selectedZoneId, setSelectedZoneId, onZoneUpdate };
  }, [activeZonesData, selectedZoneId, setSelectedZoneId, onZoneUpdate]);

  useEffect(() => {
    if (!map || !isLoaded || namespace === "active-zones") return;
    return () => {
      if (!map.getStyle()) return;
      for (const layer of [pinLayer, roadLayer, fillLayer]) if (map.getLayer(layer)) map.removeLayer(layer);
      if (map.getSource(sourceId)) map.removeSource(sourceId);
    };
  }, [map, isLoaded, namespace, sourceId, fillLayer, roadLayer, pinLayer]);

  useEffect(() => {
    console.log("[useFloodZonesLayer] hook execution started", { mapExists: !!map, isLoaded, activeZonesLength: activeZonesData?.length });
    if (!map || !isLoaded) return;

    const setupLayers = () => {
      console.log("[useFloodZonesLayer] setupLayers triggered", { activeZonesDataLength: activeZonesData?.length, activeTab });
      if (!map.getStyle()) return;

      const existingSource = map.getSource(sourceId) as maplibregl.GeoJSONSource;

      if (!activeZonesData || activeZonesData.length === 0 || activeTab !== "zones") {
        console.log("[useFloodZonesLayer] Cleared active zones because activeZonesData is empty or activeTab is not 'zones'");
        if (existingSource) {
          existingSource.setData({ type: "FeatureCollection", features: [] });
        }
        return;
      }
      
      console.log("[useFloodZonesLayer] Proceeding to add map layers for active zones");

      const features: any[] = [];
      activeZonesData.forEach((zone: any) => {
        const severity = (zone.severity || "medium").toLowerCase();
        const color = SEVERITY_COLORS[severity] || (reviewMode ? "#94a3b8" : "#eab308");
        const borderColor = SEVERITY_BORDER_COLORS[severity] || (reviewMode ? "#64748b" : "#a16207");
        const isSelected = selectedZoneId === zone.id;

        // Check if a specific contributor in this zone is being inspected
        const contributors: any[] = zone.contributors || [];
        const activeContributor = selectedContributorId 
          ? contributors.find((c: any) => c.report_id === selectedContributorId) 
          : null;

        // If inspecting a specific contributor in this zone, render ONLY that contributor's original individual report geometry!
        if (activeContributor && activeContributor.geometry) {
          const contribSeverity = (activeContributor.severity || severity).toLowerCase();
          const contribColor = SEVERITY_COLORS[contribSeverity] || color;
          const contribBorder = SEVERITY_BORDER_COLORS[contribSeverity] || borderColor;

          let contribGeom = activeContributor.geometry;
          if (typeof contribGeom === "string") {
            try { contribGeom = JSON.parse(contribGeom); } catch (e) {}
          }
          const isLine = contribGeom && (contribGeom.type === "LineString" || contribGeom.type === "MultiLineString");

          const contribProps = {
            id: zone.id,
            contributor_report_id: activeContributor.report_id,
            reporter_name: activeContributor.reporter_name,
            reporter_role: activeContributor.reporter_role,
            is_road_based: isLine,
            severity: contribSeverity.toUpperCase(),
            color: contribColor,
            border_color: contribBorder,
            is_selected: isSelected,
          };

          if (isLine) {
            features.push({
              type: "Feature",
              properties: { ...contribProps, is_zoomed_out_point: false, is_road_line: true },
              geometry: contribGeom,
            });
          } else if (contribGeom && contribGeom.type === "Point") {
            features.push({
              type: "Feature",
              properties: { ...contribProps, is_zoomed_out_point: true, is_road_line: false },
              geometry: contribGeom,
            });
          }
          
          const centerCoord = computeCenterCoordinate(
            contribGeom && contribGeom.type === "Point" ? contribGeom : null, 
            isLine ? contribGeom : null
          );
          if (centerCoord) {
            features.push({
              type: "Feature",
              properties: { ...contribProps, is_zoomed_out_point: true, is_road_line: false },
              geometry: { type: "Point", coordinates: centerCoord },
            });
          }
          return; // Skip rendering the generic merged polygon / road line!
        }

        // Standard Avoidance Zone rendering
        let repGeom = zone.report_geometry;
        if (typeof repGeom === "string") {
          try { repGeom = JSON.parse(repGeom); } catch (e) {}
        }
        let zoneGeom = zone.geometry;
        if (typeof zoneGeom === "string") {
          try { zoneGeom = JSON.parse(zoneGeom); } catch (e) {}
        }

        // Defensive fallback: if zone.report_geometry is missing but zone.geometry is linear
        if (!repGeom && zoneGeom && (zoneGeom.type === "LineString" || zoneGeom.type === "MultiLineString")) {
          repGeom = zoneGeom;
        }

        const isRoadBased = !!(repGeom && (repGeom.type === "LineString" || repGeom.type === "MultiLineString"));
        const commonProps = {
          id: zone.id,
          report_id: zone.report_id,
          severity: severity.toUpperCase(),
          color: color,
          border_color: borderColor,
          is_road_based: isRoadBased,
          is_selected: isSelected,
          created_at: zone.created_at,
          expires_at: zone.expires_at,
          depth: zone.depth,
          depth_formatted: zone.depth_formatted,
          is_pending: zone.is_pending ?? reviewMode,
          placement_json: zone.placement_details ? JSON.stringify(zone.placement_details) : undefined,
          report_text: zone.report_text,
          reporter_name: zone.reporter_name,
          reporter_role: zone.reporter_role,
          passable_vehicles: zone.passable_vehicles,
          hidden_hazards: zone.hidden_hazards,
          contributors_json: JSON.stringify(zone.contributors || []),
          news_json: JSON.stringify(zone.news || []),
        };

        // 1. Zoomed-in Road Solid Core feature (Street Level: Zoom > 14)
        if (isRoadBased && repGeom) {
          features.push({
            type: "Feature",
            properties: { ...commonProps, is_zoomed_out_point: false, is_road_line: true },
            geometry: repGeom,
          });
        }

        // 2. Zoomed-in Avoidance Buffer Polygon (Street Level: Zoom > 14)
        if (zoneGeom) {
          features.push({
            type: "Feature",
            properties: { ...commonProps, is_zoomed_out_point: false, is_road_line: false },
            geometry: zoneGeom,
          });
        }

        // 3. Zoomed-out Center Coordinate Point (City Level: Zoom <= 14)
        const centerCoord = computeCenterCoordinate(zoneGeom, repGeom);
        if (centerCoord) {
          features.push({
            type: "Feature",
            properties: { ...commonProps, is_zoomed_out_point: true, is_road_line: false },
            geometry: { type: "Point", coordinates: centerCoord },
          });
        }
      });

      // Sort features so selected zone renders on top
      features.sort((a, b) => {
        if (a.properties.is_selected && !b.properties.is_selected) return 1;
        if (!a.properties.is_selected && b.properties.is_selected) return -1;
        return 0;
      });

      const featureCollection: GeoJSON.FeatureCollection = {
        type: "FeatureCollection",
        features: features,
      };

      if (existingSource) {
        existingSource.setData(featureCollection);
      } else {
        if (!map.getStyle()) return; // Failsafe
        map.addSource(sourceId, {
          type: "geojson",
          data: featureCollection,
        });
      }

      // Layer 1: Avoidance Buffer Polygon Aura (Street Level: Zoom > 14 - pure transparent buffer, no border)
      if (!map.getLayer(fillLayer)) {
        map.addLayer({
          id: fillLayer,
          type: "fill",
          source: sourceId,
          minzoom: ZOOM_THRESHOLDS.DETAILED_MIN_ZOOM,
          paint: ACTIVE_ZONE_POLYGON_FILL_PAINT,
          filter: ["in", ["geometry-type"], ["literal", ["Polygon", "MultiPolygon"]]],
        });
      }

      // Layer 2: Solid Inner Centerline for Road Segments (Street Level: Zoom > 14)
      if (!map.getLayer(roadLayer)) {
        map.addLayer({
          id: roadLayer,
          type: "line",
          source: sourceId,
          minzoom: ZOOM_THRESHOLDS.DETAILED_MIN_ZOOM,
          layout: {
            "line-join": "round",
            "line-cap": "round",
          },
          paint: reviewMode ? PENDING_REPORT_ROAD_AURA_PAINT : ACTIVE_ZONE_ROAD_CORE_PAINT,
          filter: [
            "all",
            ["!=", ["get", "is_zoomed_out_point"], true],
            ["in", ["geometry-type"], ["literal", ["LineString", "MultiLineString"]]],
          ],
        });
      } else {
        // The same source can switch presentation modes without retaining its
        // previous pending stroke. Painting still comes from canonical tokens.
        const paint = reviewMode ? PENDING_REPORT_ROAD_AURA_PAINT : ACTIVE_ZONE_ROAD_CORE_PAINT;
        for (const [property, value] of Object.entries(paint)) map.setPaintProperty(roadLayer, property, value);
      }

      // Layer 3: Standardized Map Pin Circles (City Overview: Zoom <= 14)
      if (!map.getLayer(pinLayer)) {
        map.addLayer({
          id: pinLayer,
          type: "circle",
          source: sourceId,
          maxzoom: ZOOM_THRESHOLDS.PIN_MAX_ZOOM,
          paint: PIN_CIRCLE_PAINT,
          filter: ["==", ["get", "is_zoomed_out_point"], true],
        });
      }
    };

    const draw = () => {
      try { setupLayers(); onError?.(null); }
      catch (error) {
        if (!onError) throw error;
        onError(`Flood zones could not be drawn. ${error instanceof Error ? error.message : "Reload the map to retry."}`);
      }
    };
    draw();

    // MapLibre GL JS v5 fires 'style.load' (not just 'styledata') after setTerrain()
    // wipes custom layers. Listening here ensures flood zones are always re-applied.
    const handleMapStyleData = () => {
      draw();
    };
    map.on("style.load", handleMapStyleData);

    return () => { map.off("style.load", handleMapStyleData); };
  }, [map, isLoaded, activeZonesData, activeTab, selectedZoneId, selectedContributorId,
    reviewMode, sourceId, fillLayer, roadLayer, pinLayer, onError]);

  useEffect(() => {
    if (!map || !isLoaded || activeTab !== "zones") return;

    // Popups and Interactivity
    const closeTimeoutRef = { current: null as any };
    const openTimeoutRef = { current: null as any };
    const pendingHoverIdRef = { current: null as number | null };
    let positionFrame: number | undefined;

    const clearCloseTimeout = () => {
      if (closeTimeoutRef.current) {
        clearTimeout(closeTimeoutRef.current);
        closeTimeoutRef.current = null;
      }
    };

    const clearOpenTimeout = () => {
      if (openTimeoutRef.current) {
        clearTimeout(openTimeoutRef.current);
        openTimeoutRef.current = null;
      }
      pendingHoverIdRef.current = null;
    };

    const removeActivePopup = () => {
      const activePopup = activePopupRef.current;
      if (!activePopup) return;
      activePopupRef.current = null;
      if (positionFrame !== undefined) cancelAnimationFrame(positionFrame);
      activePopup.popup?.remove();
      activePopup.root.unmount();
    };

    const attachPopup = (container: HTMLElement, lngLat: { lng: number; lat: number }, color: string, height: number) => {
      const anchor = floodPopupAnchor(map, lngLat, height);
      const point = map.project(lngLat);
      const centeredY = Math.max(height / 2 + 80,
        Math.min(point.y, map.getCanvas().clientHeight - height / 2 - 16));
      const popup = new maplibregl.Popup({ closeButton: false, closeOnClick: false, maxWidth: "360px",
        offset: anchor === "left" || anchor === "right" ? [anchor === "left" ? 14 : -14, centeredY - point.y] : 14,
        anchor, className: "flood-zone-popup" }).setLngLat(lngLat).setDOMContent(container).addTo(map);
      const tip = popup.getElement().querySelector<HTMLElement>(".maplibregl-popup-tip");
      if (tip && anchor.startsWith("top")) tip.style.borderBottomColor = color;
      return popup;
    };
    const reposition = () => {
      const active = activePopupRef.current;
      if (!active?.popup) return;
      const height = active.container.offsetHeight;
      if (!height) return;
      active.popup.remove();
      active.popup = attachPopup(active.container, active.lngLat, active.color, height);
    };

    const scheduleClose = () => {
      clearCloseTimeout();
      closeTimeoutRef.current = setTimeout(() => {
        if (!isTouchDevice && activePopupRef.current) {
          removeActivePopup();
        }
      }, 250); // 250ms grace period to allow cursor to bridge into the popup
    };

    const handlePopupOpen = (properties: any, lngLat: { lng: number; lat: number }) => {
      if (!properties) return;

      clearCloseTimeout();

      // If popup is already active for this exact zone, keep it without flickering
      if (activePopupRef.current && activePopupRef.current.zoneId === Number(properties.id)) {
        return;
      }

      if (activePopupRef.current) {
        removeActivePopup();
      }

      const popupContainer = document.createElement("div");
      popupContainer.className = "flood-zone-popup-root";
      
      // Keep popup open when hovering over the popup itself
      popupContainer.addEventListener("mouseenter", clearCloseTimeout);
      popupContainer.addEventListener("mouseleave", scheduleClose);

      const popupHeight = (properties.placement_json || (properties.news_json && properties.news_json !== "[]") ? 550 : 360) + (interaction.current.onZoneUpdate ? 132 : 0);

      const root = createRoot(popupContainer);

      const popup = isTouchDevice
        ? null
        : attachPopup(popupContainer, lngLat, properties.color || "#eab308", popupHeight);

      const record = interaction.current.activeZonesData?.find(zone => zone.id === Number(properties.id));
      const placementPreview: FloodPlacementPopupDetails | undefined = record?.placement_details;
      root.render(React.createElement(FloodZonePopup, {
        properties,
        compact: !isTouchDevice,
        modal: isTouchDevice,
        onClose: () => {
          removeActivePopup();
          interaction.current.setSelectedZoneId?.(null);
        },
        placementPreview,
        onUpdate: interaction.current.onZoneUpdate ? (condition: ZoneCondition) => {
          const zone = interaction.current.activeZonesData?.find(zone => zone.id === Number(properties.id));
          if (zone) interaction.current.onZoneUpdate?.(zone, condition);
          setTimeout(removeActivePopup, 0);
        } : undefined,
      }));

      activePopupRef.current = { popup, root, zoneId: Number(properties.id), container: popupContainer,
        lngLat, color: properties.color || "#eab308" };
      if (popup) positionFrame = requestAnimationFrame(() => { positionFrame = requestAnimationFrame(reposition); });
    };

    const handleMouseEnterOrMove = (e: any) => {
      map.getCanvas().style.cursor = "pointer";
      if (isTouchDevice) return;
      if (map.isMoving()) return;
      if (!e.features || e.features.length === 0) return;
      const feature = e.features[0];
      const properties = feature.properties;
      const id = Number(properties?.id);
      if (!id) return;

      clearCloseTimeout();

      // If popup is already active for this exact zone, keep it without flickering
      if (activePopupRef.current && activePopupRef.current.zoneId === id) {
        return;
      }

      // If already counting down for this exact zone, let the timer run (do not reset!)
      if (pendingHoverIdRef.current === id) {
        return;
      }

      // Start 400ms hover dwell countdown for this zone
      clearOpenTimeout();
      pendingHoverIdRef.current = id;
      const targetLngLat = { lng: e.lngLat.lng, lat: e.lngLat.lat };

      openTimeoutRef.current = setTimeout(() => {
        handlePopupOpen(properties, targetLngLat);
        pendingHoverIdRef.current = null;
      }, 400);
    };

    const handleMouseLeave = () => {
      map.getCanvas().style.cursor = "";
      if (!isTouchDevice) {
        clearOpenTimeout();
        scheduleClose();
      }
    };

    const handleZoneClick = (e: any) => {
      if (!e.features || e.features.length === 0) return;
      clearOpenTimeout();
      const id = e.features[0].properties.id;
      const isSelecting = interaction.current.selectedZoneId !== Number(id);
      if (interaction.current.setSelectedZoneId && id) {
        interaction.current.setSelectedZoneId(isSelecting ? Number(id) : null);
      }
      if (!isTouchDevice) removeActivePopup();

      // Center, angle, and zoom into the clicked active zone ONLY on select
      if (isSelecting && e.lngLat) {
        flyToCoordinates(map, [e.lngLat.lng, e.lngLat.lat], { zoom: 16, pitch: map.getPitch(),
          duration: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 1500 });
      }

      if (isTouchDevice && isSelecting) {
        handlePopupOpen(e.features[0].properties, { lng: e.lngLat.lng, lat: e.lngLat.lat });
      }
    };

    const activeLayers = [
      fillLayer,
      roadLayer,
      pinLayer,
    ];

    const handleMapClick = (e: maplibregl.MapMouseEvent) => {
      if (!isTouchDevice || !activePopupRef.current) return;

      const clickedZone = map.queryRenderedFeatures(e.point, { layers: activeLayers }).length > 0;
      if (clickedZone) return;

      clearOpenTimeout();
      removeActivePopup();
      interaction.current.setSelectedZoneId?.(null);
    };

    activeLayers.forEach((layer) => {
      map.on("mouseenter", layer, handleMouseEnterOrMove);
      map.on("mousemove", layer, handleMouseEnterOrMove);
      map.on("mouseleave", layer, handleMouseLeave);
      map.on("click", layer, handleZoneClick);
    });
    map.on("click", handleMapClick);
    map.on("moveend", reposition);

    return () => {
      map.off("click", handleMapClick);
      map.off("moveend", reposition);
      clearOpenTimeout();
      clearCloseTimeout();
      if (activePopupRef.current) {
        removeActivePopup();
      }
      activeLayers.forEach((layer) => {
        map.off("mouseenter", layer, handleMouseEnterOrMove);
        map.off("mousemove", layer, handleMouseEnterOrMove);
        map.off("mouseleave", layer, handleMouseLeave);
        map.off("click", layer, handleZoneClick);
      });
    };
  }, [map, isLoaded, activeZonesData, isTouchDevice, activeTab, fillLayer, roadLayer, pinLayer]);
}
