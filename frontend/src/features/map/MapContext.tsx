"use client";
// Forced cache refresh

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { parseCoords } from "@/features/geocoding/geocodingApi";
import {
  getRoute,
  type RouteGeometry,
  type RouteOption,
  type MultiRouteResponse,
} from "@/features/routing/routingApi";
import { getBearing } from "@/lib/utils";
import { apiClient } from "@/lib/apiClient";
import toast from "react-hot-toast";

export type ActivePoint = "start" | "end" | "flood_start" | "flood_end" | "post_location" | "save_place_location" | null;
export type ActivePanel = "route" | "flood" | "save_place" | null;

export interface MapPoint {
  coords: [number, number];
  label: string;
}

export interface DraftReport {
  id: string;
  geometry: RouteGeometry;
  oppositeGeometry: RouteGeometry | null;
  isBidirectional: boolean;
  severity: string;
  depth: string;
  description: string;
  mediaFiles: File[];
  startLabel: string;
  endLabel: string;
  roadName: string | null;
}

interface MapContextValue {
  start: MapPoint | null;
  end: MapPoint | null;
  activePoint: ActivePoint;
  activePanel: ActivePanel;
  isAnalyticsOpen: boolean;
  isAnalyticsCollapsed: boolean;
  lastOpenedLeftPanel: "analytics" | "save_place" | null;

  // --- Multi-route state ---
  allRoutes: RouteOption[] | null;
  selectedRouteIndex: number;
  selectedRoute: RouteOption | null;
  setSelectedRouteIndex: (index: number) => void;

  // Derived convenience accessors (backward-compat with RoutePanel / MapCanvas)
  routeGeometry: RouteGeometry | null;
  routeInfo: {
    distance: number;
    duration: number;
    avoided_floods: boolean;
    blocked: boolean;
  } | null;

  isRouting: boolean;
  routeError: string | null;
  isPickingOnMap: boolean;
  isReportPanelOpen: boolean;
  isSavePlacePanelOpen: boolean;
  hasBottomOffset: boolean;
  setIsPickingOnMap: (value: boolean) => void;
  setIsReportPanelOpen: (value: boolean) => void;
  setIsSavePlacePanelOpen: (value: boolean) => void;
  setActivePoint: (point: ActivePoint) => void;
  setActivePanel: (panel: ActivePanel) => void;
  setIsAnalyticsOpen: (open: boolean) => void;
  setIsAnalyticsCollapsed: (collapsed: boolean) => void;
  setStart: (coords: [number, number] | null, label?: string) => void;
  setEnd: (coords: [number, number] | null, label?: string) => void;
  setStartLabel: (label: string) => void;
  setEndLabel: (label: string) => void;
  setPointFromMap: (coords: [number, number]) => void;
  floodStart: MapPoint | null;
  floodEnd: MapPoint | null;
  floodPreviewGeometry: RouteGeometry | null;
  floodOppositeGeometry: RouteGeometry | null;
  setFloodStart: (coords: [number, number] | null, label?: string) => void;
  setFloodEnd: (coords: [number, number] | null, label?: string) => void;
  setFloodStartLabel: (label: string) => void;
  setFloodEndLabel: (label: string) => void;
  floodIsBidirectional: boolean;
  setFloodIsBidirectional: (isBi: boolean) => void;
  clearRoute: () => void;
  resetAll: () => void;
  vehicleProfile: "light" | "heavy" | "motorcycle" | "walk";
  setVehicleProfile: (profile: "light" | "heavy" | "motorcycle" | "walk") => void;

  draftReports: DraftReport[];
  setDraftReports: React.Dispatch<React.SetStateAction<DraftReport[]>>;

  routingEngine: "valhalla" | "ors";
  setRoutingEngine: (engine: "valhalla" | "ors") => void;

  savedPlaces: any[];
  setSavedPlaces: (places: any[]) => void;
  draftSavePlaceCoords: {coords: [number, number], label: string} | null;
  setDraftSavePlaceCoords: (data: {coords: [number, number], label: string} | null) => void;
  savePlaceIcon: string;
  setSavePlaceIcon: (icon: string) => void;

  panelZIndices: Record<string, number>;
  bringPanelToFront: (panelId: string) => void;
}

const MapContext = createContext<MapContextValue | null>(null);

function coordsLabel(coords: [number, number]): string {
  return `${coords[0].toFixed(5)}, ${coords[1].toFixed(5)}`;
}

export function MapProvider({ children }: { children: ReactNode }) {
  const searchParams = useSearchParams();
  const router = useRouter();
  const locationParam = searchParams.get("location");
  const typeParam = searchParams.get("type") as ActivePoint | null;
  const labelParam = searchParams.get("label");
  const panelParam = searchParams.get("panel");

  const [start, setStartState] = useState<MapPoint | null>(null);
  const [end, setEndState] = useState<MapPoint | null>(null);
  const [activePoint, setActivePoint] = useState<ActivePoint>(null);
  const [activePanel, setActivePanelState] = useState<ActivePanel>("route");
  const [isAnalyticsOpen, setIsAnalyticsOpenState] = useState(false);
  const [isAnalyticsCollapsed, setIsAnalyticsCollapsedState] = useState(false);
  const [lastOpenedLeftPanel, setLastOpenedLeftPanel] = useState<"analytics" | "save_place" | null>(null);

  // Multi-route state
  const [allRoutes, setAllRoutes] = useState<RouteOption[] | null>(null);
  const [selectedRouteIndex, setSelectedRouteIndexState] = useState<number>(0);

  const [isRouting, setIsRouting] = useState(false);
  const [routeError, setRouteError] = useState<string | null>(null);
  const [isPickingOnMap, setIsPickingOnMap] = useState(false);
  const [isReportPanelOpen, setIsReportPanelOpen] = useState(false);
  const [isSavePlacePanelOpen, setIsSavePlacePanelOpenState] = useState(false);

  const setIsSavePlacePanelOpen = useCallback((open: boolean) => {
    setIsSavePlacePanelOpenState(open);
    if (open) {
      setLastOpenedLeftPanel("save_place");
    }
  }, []);
  
  const [savedPlaces, setSavedPlaces] = useState<any[]>([]);
  const [draftSavePlaceCoords, setDraftSavePlaceCoords] = useState<{coords: [number, number], label: string} | null>(null);
  const [savePlaceIcon, setSavePlaceIcon] = useState<string>("🏠");

  const hasBottomOffset = false;

  const [floodStart, setFloodStartState] = useState<MapPoint | null>(null);
  const [floodEnd, setFloodEndState] = useState<MapPoint | null>(null);
  const [floodPreviewGeometry, setFloodPreviewGeometry] = useState<RouteGeometry | null>(null);
  const [floodOppositeGeometry, setFloodOppositeGeometry] = useState<RouteGeometry | null>(null);
  const [floodIsBidirectional, setFloodIsBidirectional] = useState(false);
  const [draftReports, setDraftReports] = useState<DraftReport[]>([]);

  const [vehicleProfile, setVehicleProfile] = useState<"light" | "heavy" | "motorcycle" | "walk">("light");
  const [routingEngine, setRoutingEngine] = useState<"valhalla" | "ors">("ors");

  const [panelZIndices, setPanelZIndices] = useState<Record<string, number>>({});
  const [highestZIndex, setHighestZIndex] = useState(40);
  const bringPanelToFront = useCallback((panelId: string) => {
    setHighestZIndex((prev) => {
      const next = prev + 1;
      setPanelZIndices((zMap) => ({ ...zMap, [panelId]: next }));
      return next;
    });
  }, []);

  // Derived: currently active route option
  const selectedRoute: RouteOption | null = allRoutes?.[selectedRouteIndex] ?? null;

  // Backward-compat derived accessors
  const routeGeometry: RouteGeometry | null = selectedRoute?.geometry ?? null;
  const routeInfo = selectedRoute
    ? {
        distance: selectedRoute.distance,
        duration: selectedRoute.duration,
        avoided_floods: selectedRoute.avoided_floods,
        blocked: selectedRoute.blocked,
      }
    : null;

  const setSelectedRouteIndex = useCallback((index: number) => {
    setSelectedRouteIndexState(index);
  }, []);

  useEffect(() => {
    if (!locationParam) return;
    const coords = parseCoords(locationParam);
    if (!coords) return;
    const label = labelParam ?? coordsLabel(coords);
    const pointType = typeParam === "end" ? "end" : "start";
    if (pointType === "end") {
      setEndState({ coords, label });
      setActivePoint("start");
    } else {
      setStartState({ coords, label });
      setActivePoint("end");
    }
  }, [locationParam, typeParam, labelParam]);

  useEffect(() => {
    if (panelParam === "saveplace") {
      setIsSavePlacePanelOpen(true);
    }
  }, [panelParam]);

  const setActivePanel = useCallback((panel: ActivePanel) => {
    setActivePanelState(panel);
  }, []);

  const setIsAnalyticsOpen = useCallback((open: boolean) => {
    setIsAnalyticsOpenState(open);
    if (open) {
      setLastOpenedLeftPanel("analytics");
      setIsAnalyticsCollapsedState(false);
    } else {
      setIsAnalyticsCollapsedState(false);
    }
  }, []);

  // When a panel closes, shift focus to the other one if it's open
  useEffect(() => {
    if (!isAnalyticsOpen && isSavePlacePanelOpen) {
      setLastOpenedLeftPanel("save_place");
    }
  }, [isAnalyticsOpen, isSavePlacePanelOpen]);

  useEffect(() => {
    if (!isSavePlacePanelOpen && isAnalyticsOpen) {
      setLastOpenedLeftPanel("analytics");
    }
  }, [isAnalyticsOpen, isSavePlacePanelOpen]);

  // When both left panels are closed, expand Route Planner
  useEffect(() => {
    if (!isAnalyticsOpen && !isSavePlacePanelOpen) {
      setActivePanelState("route");
    }
  }, [isAnalyticsOpen, isSavePlacePanelOpen]);
  const setIsAnalyticsCollapsed = useCallback((collapsed: boolean) => {
    setIsAnalyticsCollapsedState(collapsed);
  }, []);

  const clearRoute = useCallback(() => {
    setAllRoutes(null);
    setSelectedRouteIndexState(0);
    setRouteError(null);
    setIsRouting(false);
  }, []);

  const setStart = useCallback((coords: [number, number] | null, label?: string) => {
    if (coords === null) {
      setStartState(null);
    } else {
      setStartState({ coords, label: label ?? coordsLabel(coords) });
    }
    clearRoute();
  }, [clearRoute]);

  const setEnd = useCallback((coords: [number, number] | null, label?: string) => {
    if (coords === null) {
      setEndState(null);
    } else {
      setEndState({ coords, label: label ?? coordsLabel(coords) });
    }
    clearRoute();
  }, [clearRoute]);

  const setStartLabel = useCallback((label: string) => {
    setStartState((prev) => (prev ? { ...prev, label } : null));
  }, []);

  const setEndLabel = useCallback((label: string) => {
    setEndState((prev) => (prev ? { ...prev, label } : null));
  }, []);

  const setFloodStart = useCallback((coords: [number, number] | null, label?: string) => {
    if (coords === null) {
      setFloodStartState(null);
    } else {
      setFloodStartState({ coords, label: label ?? coordsLabel(coords) });
    }
  }, []);

  const setFloodEnd = useCallback((coords: [number, number] | null, label?: string) => {
    if (coords === null) {
      setFloodEndState(null);
    } else {
      setFloodEndState({ coords, label: label ?? coordsLabel(coords) });
    }
  }, []);

  const setFloodStartLabel = useCallback((label: string) => {
    setFloodStartState((prev) => (prev ? { ...prev, label } : null));
  }, []);

  const setFloodEndLabel = useCallback((label: string) => {
    setFloodEndState((prev) => (prev ? { ...prev, label } : null));
  }, []);

  const setPointFromMap = useCallback(
    (coords: [number, number]) => {
      if (!activePoint) return;
      const label = coordsLabel(coords);
      if (activePoint === "start") {
        setStart(coords, label);
        setActivePoint("end");
      } else if (activePoint === "end") {
        setEnd(coords, label);
        setActivePoint(null);
        setIsPickingOnMap(false);
      } else if (activePoint === "flood_start") {
        setFloodStart(coords, label);
        setActivePoint("flood_end");
      } else if (activePoint === "flood_end") {
        setFloodEnd(coords, label);
        setActivePoint(null);
        setIsPickingOnMap(false);
      } else if (activePoint === "post_location") {
        setActivePoint(null);
        setIsPickingOnMap(false);
        fetch(`https://photon.komoot.io/reverse?lon=${coords[0]}&lat=${coords[1]}`)
          .then(res => res.json())
          .then(data => {
            let labelVal = coordsLabel(coords);
            if (data.features && data.features.length > 0) {
              const props = data.features[0].properties;
              const parts = [props.name, props.street, props.locality, props.city, props.state]
                .filter(Boolean)
                .filter((value, index, self) => self.indexOf(value) === index);
              labelVal = parts.slice(0, 2).join(", ") || labelVal;
            }
            router.push(`/feed?openPostModal=true&location_tag=${encodeURIComponent(labelVal)}`);
          })
          .catch(() => {
            router.push(`/feed?openPostModal=true&location_tag=${encodeURIComponent(coordsLabel(coords))}`);
          });
      } else if (activePoint === "save_place_location") {
        setDraftSavePlaceCoords({ coords, label: coordsLabel(coords) });
        setActivePoint(null);
        setIsPickingOnMap(false);
      }
    },
    [activePoint, setStart, setEnd, setFloodStart, setFloodEnd, router]
  );

  const resetAll = useCallback(() => {
    setStartState(null);
    setEndState(null);
    setFloodStartState(null);
    setFloodEndState(null);
    setFloodPreviewGeometry(null);
    setActivePoint("start");
    clearRoute();
  }, [clearRoute]);

  // Fetch routes whenever start + end are both set
  useEffect(() => {
    if (!start || !end) {
      clearRoute();
      return;
    }

    let cancelled = false;

    const fetchRoutes = async () => {
      setIsRouting(true);
      setRouteError(null);

      try {
        const result: MultiRouteResponse = await getRoute(start.coords, end.coords, false, vehicleProfile, routingEngine);
        if (cancelled) return;

        setAllRoutes(result.routes);
        setSelectedRouteIndexState(result.recommended_index);
        
        if (result.routes.length === 0) {
          setRouteError("No safe route available. The destination is completely blocked by severe floods for your vehicle profile.");
        }
      } catch (err: any) {
        if (!cancelled) {
          const message = err?.message || err?.response?.data?.detail || "Could not calculate route. Check that the backend is running.";
          setRouteError(message);
          setAllRoutes(null);
          setSelectedRouteIndexState(0);
        }
      } finally {
        if (!cancelled) setIsRouting(false);
      }
    };

    void fetchRoutes();

    return () => {
      cancelled = true;
    };
  }, [start, end, clearRoute, vehicleProfile]);

  // Flood segment preview (uses ignore_floods=true for a straight reference line)
  useEffect(() => {
    if (!floodStart || !floodEnd) {
      setFloodPreviewGeometry(null);
      setFloodOppositeGeometry(null);
      return;
    }

    let cancelled = false;

    const fetchFloodPreview = async () => {
      try {
        const routeAB = await getRoute(floodStart.coords, floodEnd.coords, true);
        if (cancelled) return;
        
        const originalGeometry = routeAB.routes[0]?.geometry ?? null;

        if (!cancelled) {
          setFloodPreviewGeometry(originalGeometry);
        }

        // If bidirectional is enabled, call the backend to find the real opposite carriageway
        if (floodIsBidirectional && originalGeometry?.coordinates?.length >= 2) {
          try {
            const preview = await apiClient.post<{
              original: RouteGeometry;
              opposite: RouteGeometry | null;
              is_divided: boolean;
              road_type: string;
            }>("/reports/preview-bidirectional", {
              coordinates: originalGeometry.coordinates,
              road_name: null,
            });

            if (!cancelled) {
              setFloodOppositeGeometry(preview.opposite ?? null);
              
              if (preview.road_type === "NARROW_TWO_WAY") {
                toast.info("This is a standard two-way road. A single boundary is sufficient.");
              } else if (preview.road_type === "TRUE_ONE_WAY") {
                toast.error("This is a one-way street. Two-way mapping cannot be applied.");
              }
            }
          } catch {
            if (!cancelled) setFloodOppositeGeometry(null);
          }
        } else {
          if (!cancelled) setFloodOppositeGeometry(null);
        }
      } catch {
        if (!cancelled) {
          setFloodPreviewGeometry(null);
          setFloodOppositeGeometry(null);
        }
      }
    };

    void fetchFloodPreview();

    return () => {
      cancelled = true;
    };
  }, [floodStart, floodEnd, floodIsBidirectional]);


  const value = useMemo<MapContextValue>(
    () => ({
      start,
      end,
      activePoint,
      activePanel,
      isAnalyticsOpen,
      isAnalyticsCollapsed,
      lastOpenedLeftPanel,
      allRoutes,
      selectedRouteIndex,
      selectedRoute,
      setSelectedRouteIndex,
      routeGeometry,
      routeInfo,
      isRouting,
      routeError,
      isPickingOnMap,
      isReportPanelOpen,
      isSavePlacePanelOpen,
      hasBottomOffset,
      floodStart,
      floodEnd,
      floodPreviewGeometry,
      floodOppositeGeometry,
      floodIsBidirectional,
      setFloodIsBidirectional,
      savedPlaces,
      draftSavePlaceCoords,
      savePlaceIcon,
      setSavePlaceIcon,
      setIsPickingOnMap,
      setIsReportPanelOpen,
      setIsSavePlacePanelOpen,
      setSavedPlaces,
      setDraftSavePlaceCoords,
      setActivePoint,
      setActivePanel,
      setIsAnalyticsOpen,
      setIsAnalyticsCollapsed,
      setStart,
      setEnd,
      setStartLabel,
      setEndLabel,
      setFloodStart,
      setFloodEnd,
      setFloodStartLabel,
      setFloodEndLabel,
      setPointFromMap,
      clearRoute,
      resetAll,
      vehicleProfile,
      setVehicleProfile,
      routingEngine,
      setRoutingEngine,
      panelZIndices,
      bringPanelToFront,
    }),
    [
      start,
      end,
      activePoint,
      activePanel,
      isAnalyticsOpen,
      isAnalyticsCollapsed,
      lastOpenedLeftPanel,
      allRoutes,
      selectedRouteIndex,
      selectedRoute,
      setSelectedRouteIndex,
      routeGeometry,
      routeInfo,
      isRouting,
      routeError,
      isPickingOnMap,
      isReportPanelOpen,
      isSavePlacePanelOpen,
      hasBottomOffset,
      floodStart,
      floodEnd,
      floodPreviewGeometry,
      floodOppositeGeometry,
      floodIsBidirectional,
      setFloodIsBidirectional,
      savedPlaces,
      draftSavePlaceCoords,
      savePlaceIcon,
      setSavePlaceIcon,
      setIsPickingOnMap,
      setIsReportPanelOpen,
      setIsSavePlacePanelOpen,
      setSavedPlaces,
      setDraftSavePlaceCoords,
      setActivePoint,
      setActivePanel,
      setIsAnalyticsOpen,
      setIsAnalyticsCollapsed,
      setStart,
      setEnd,
      setStartLabel,
      setEndLabel,
      setFloodStart,
      setFloodEnd,
      floodIsBidirectional,
      setFloodStartLabel,
      setFloodEndLabel,
      setPointFromMap,
      clearRoute,
      resetAll,
      vehicleProfile,
      setVehicleProfile,
      routingEngine,
      setRoutingEngine,
      panelZIndices,
      bringPanelToFront,
    ]
  );

  return <MapContext.Provider value={value}>{children}</MapContext.Provider>;
}

export function useMapContext(): MapContextValue {
  const context = useContext(MapContext);
  if (!context) {
    throw new Error("useMapContext must be used within a MapProvider");
  }
  return context;
}

export function useOptionalMapContext(): MapContextValue | null {
  return useContext(MapContext);
}
