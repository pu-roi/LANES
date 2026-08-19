"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  CircleDot,
  Crosshair,
  MapPin,
  ArrowDownUp,
  AlertTriangle,
  CheckCircle,
  Car,
  Bike,
  PersonStanding,
  Home, Briefcase, GraduationCap, Building, Coffee, Heart, Star,
  ArrowLeft,
  ArrowRight,
  ArrowUp,
  ArrowUpLeft,
  ArrowUpRight,
  CornerDownLeft,
  CornerDownRight,
  Navigation,
  Flag,
} from "lucide-react";
import { MapPickerMobileOverlay } from "@/features/map/MapPickerMobileOverlay";
import { LocationAutocomplete } from "@/shared/ui/LocationAutocomplete";
import { LoadingOverlay } from "@/shared/ui";
import { cn } from "@/lib/utils";
import { useMapContext, type ActivePoint } from "@/features/map/MapContext";
import { getCurrentLocation } from "@/features/geocoding/geocodingApi";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import { OfflineManager } from "@/components/Map/OfflineManager";

// ORS maneuver type → Lucide icon mapping
// https://openrouteservice.org/dev/#/api-docs (type codes)
function getStepIcon(type: number) {
  switch (type) {
    case 0: return ArrowLeft;        // Turn left
    case 1: return ArrowRight;       // Turn right
    case 2: return CornerDownLeft;   // Sharp left
    case 3: return CornerDownRight;  // Sharp right
    case 4: return ArrowUpLeft;      // Slight left
    case 5: return ArrowUpRight;     // Slight right
    case 6: return ArrowUp;          // Straight
    case 7: return ArrowLeft;        // Enter roundabout
    case 10: return Flag;            // Arrive
    case 11: return Navigation;      // Depart
    default: return ArrowUp;
  }
}

export default function RoutePanel() {
  const {
    start,
    end,
    allRoutes,
    selectedRouteIndex,
    selectedRoute,
    setSelectedRouteIndex,
    activePoint,
    activePanel,
    setActivePanel,
    isRouting,
    routeError,
    setActivePoint,
    setStart,
    setEnd,
    setStartLabel,
    setEndLabel,
    resetAll,
    isPickingOnMap,
    setIsPickingOnMap,
    vehicleProfile,
    setVehicleProfile,
    isAnalyticsOpen,
    isReportPanelOpen,
    isSavePlacePanelOpen,
    savedPlaces,
    routingEngine,
    setRoutingEngine
  } = useMapContext();

  const isMobile = useMediaQuery("(max-width: 640px), (pointer: coarse)");
  const isCollapsed = activePanel !== "route";
  const [startInput, setStartInput] = useState("");
  const [endInput, setEndInput] = useState("");
  const [mapCenter, setMapCenter] = useState<[number, number] | null>(null);
  const [hoveredStepIdx, setHoveredStepIdx] = useState<number | null>(null);

  useEffect(() => {
    const handleCenterChange = (e: Event) => {
      const customEvent = e as CustomEvent<[number, number]>;
      setMapCenter(customEvent.detail);
    };
    window.addEventListener("map-center-changed", handleCenterChange);
    return () => window.removeEventListener("map-center-changed", handleCenterChange);
  }, []);

  const handlePickOnMapToggle = (target: ActivePoint) => {
    setActivePoint(target);
    setIsPickingOnMap(true);
  };

  const confirmMapLocation = () => {
    if (activePoint && mapCenter) {
      const label = `${mapCenter[0].toFixed(5)}, ${mapCenter[1].toFixed(5)}`;
      if (activePoint === "start") {
        setStart(mapCenter, label);
        setStartInput(label);
        setActivePoint("end");
      } else {
        setEnd(mapCenter, label);
        setEndInput(label);
        setActivePoint(null);
      }
      setIsPickingOnMap(false);
    }
  };

  useEffect(() => {
    if (start?.label) setStartInput(start.label);
  }, [start?.label]);

  useEffect(() => {
    if (end?.label) setEndInput(end.label);
  }, [end?.label]);

  useEffect(() => {
    if (isMobile && selectedRoute) {
      setActivePanel(null);
      setActivePoint(null);
    }
  }, [selectedRoute, isMobile, setActivePoint, setActivePanel]);

  const handleUseCurrentLocation = async (target: ActivePoint) => {
    try {
      const coords = await getCurrentLocation();
      const label = "Current Location";
      if (target === "start") {
        setStart(coords, label);
        setStartInput(label);
      } else {
        setEnd(coords, label);
        setEndInput(label);
      }
    } catch (err: any) {
      alert(err.message || "Unable to retrieve your location");
    }
  };

  const handleSwap = () => {
    if (!start || !end) return;
    const startCoords = start.coords;
    const startLabel = start.label;
    setStart(end.coords, end.label);
    setStartInput(end.label);
    setEnd(startCoords, startLabel);
    setEndInput(startLabel);
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.round(seconds / 60);
    return mins < 60 ? `${mins} min` : `${Math.floor(mins / 60)}h ${mins % 60}m`;
  };

  const formatStepDistance = (meters: number) => {
    return meters < 1000 ? `${Math.round(meters)} m` : `${(meters / 1000).toFixed(1)} km`;
  };

  const PROFILE_OPTIONS: Array<{ id: "light" | "heavy" | "motorcycle" | "walk", icon: any, label: string }> = [
    { id: "heavy", icon: Car, label: "High Cl." },
    { id: "light", icon: Car, label: "Low Cl." },
    { id: "motorcycle", icon: Bike, label: "Moto" },
    { id: "walk", icon: PersonStanding, label: "Walk" },
  ];

  const iconMap: Record<string, any> = { Home, Briefcase, GraduationCap, Building, Coffee, Heart, Star, MapPin };

  const handleSelectSavedPlace = (place: any) => {
    const coords: [number, number] = [place.longitude, place.latitude];
    const label = place.name;
    if (activePoint === "start" || (!activePoint && !start)) {
      setStart(coords, label);
      setStartInput(label);
      setActivePoint("end");
    } else {
      setEnd(coords, label);
      setEndInput(label);
      setActivePoint(null);
    }
  };

  // Step hover/click: fire DOM events so MapCanvas can draw the highlight segment
  const fireStepHover = useCallback((stepIdx: number | null) => {
    if (!selectedRoute?.geometry || !selectedRoute?.instructions) return;
    if (stepIdx === null) {
      window.dispatchEvent(new CustomEvent("route-step-clear"));
      return;
    }
    const step = selectedRoute.instructions[stepIdx];
    if (!step) return;
    const coords = selectedRoute.geometry.coordinates;
    // ORS uses way_points: [start_idx, end_idx], Valhalla uses begin_shape_index/end_shape_index
    const startIdx: number = step.way_points?.[0] ?? step.begin_shape_index ?? 0;
    const endIdx: number = step.way_points?.[1] ?? step.end_shape_index ?? coords.length - 1;
    const segment = coords.slice(startIdx, endIdx + 1);
    if (segment.length < 2) return;
    window.dispatchEvent(new CustomEvent("route-step-hover", { detail: { segment } }));
  }, [selectedRoute]);

  const fireStepClick = useCallback((stepIdx: number) => {
    if (!selectedRoute?.geometry || !selectedRoute?.instructions) return;
    const step = selectedRoute.instructions[stepIdx];
    if (!step) return;
    const coords = selectedRoute.geometry.coordinates;
    const startIdx: number = step.way_points?.[0] ?? step.begin_shape_index ?? 0;
    const endIdx: number = step.way_points?.[1] ?? step.end_shape_index ?? coords.length - 1;
    const segment = coords.slice(startIdx, endIdx + 1);
    if (segment.length < 1) return;
    window.dispatchEvent(new CustomEvent("route-step-click", { detail: { segment } }));
  }, [selectedRoute]);

  // ── MOBILE PATHS ────────────────────────────────────────────────────────────
  if (isMobile) {
    if (isPickingOnMap && (activePoint === "start" || activePoint === "end")) {
      return (
        <MapPickerMobileOverlay
          onCancel={() => {
            setIsPickingOnMap(false);
            if (!start && !end) setActivePoint(null);
          }}
          onConfirm={confirmMapLocation}
          confirmText={`Set ${activePoint === "start" ? "Start" : "Destination"}`}
        />
      );
    }

    if (isPickingOnMap && (activePoint === "flood_start" || activePoint === "flood_end")) {
      return null;
    }

    if (isMobile && (isReportPanelOpen || isAnalyticsOpen || isSavePlacePanelOpen || (isPickingOnMap && activePoint !== "start" && activePoint !== "end")) && activePoint !== "start" && activePoint !== "end") {
      return null;
    }

    const renderTopOptions = (target: ActivePoint) => (
      <>
        <li>
          <button
            type="button"
            className="flex w-full items-start gap-2 px-3 py-3 text-left text-sm hover:bg-blue-50 transition-colors border-b border-gray-100"
            onMouseDown={(e) => e.preventDefault()}
            onClick={() => handlePickOnMapToggle(target)}
          >
            <div className="bg-blue-100 p-1.5 rounded-full shrink-0">
              <Crosshair className="h-4 w-4 text-blue-700" />
            </div>
            <span className="flex flex-col justify-center h-7 font-semibold text-blue-700">Choose on Map</span>
          </button>
        </li>
        <li>
          <button
            type="button"
            className="flex w-full items-start gap-2 px-3 py-3 text-left text-sm hover:bg-blue-50 transition-colors border-b border-gray-100 mb-1"
            onMouseDown={(e) => e.preventDefault()}
            onClick={() => handleUseCurrentLocation(target)}
          >
            <div className="bg-gray-100 p-1.5 rounded-full shrink-0">
              <MapPin className="h-4 w-4 text-gray-700" />
            </div>
            <span className="flex flex-col justify-center h-7 font-semibold text-gray-800">Use Current Location</span>
          </button>
        </li>
      </>
    );

    return (
      <>
        {/* Mobile Top Search Bar */}
        <div className="absolute top-4 left-4 right-4 z-40 bg-white rounded-2xl shadow-lg border border-gray-100 overflow-visible transition-all">
          <div className="flex items-center p-3 pr-2">
            <div className="flex flex-col items-center justify-center gap-1 w-6 relative z-10">
              <CircleDot className="w-4 h-4 text-green-600 shrink-0 bg-white" />
              <div className="w-[3px] h-6 bg-gray-200 border-l border-dashed border-gray-300" />
              <MapPin className="w-5 h-5 text-red-500 shrink-0 bg-white" />
            </div>

            <div className="flex-1 flex flex-col gap-2 relative z-20">
              <div
                className={cn("w-full rounded-lg transition-all bg-gray-50 border", activePoint === "start" ? "border-blue-400 ring-2 ring-blue-100 bg-white shadow-sm relative z-30" : "border-transparent relative z-10")}
                onClick={() => setActivePoint("start")}
              >
                <LocationAutocomplete
                  value={startInput}
                  onChange={(val) => { setStartInput(val); setStartLabel(val); }}
                  onSelect={(s) => { setStart([s.lng, s.lat], s.label); setStartInput(s.label); setActivePoint("end"); }}
                  onClear={() => { setStart(null, ""); setStartInput(""); setStartLabel(""); }}
                  placeholder="Your location"
                  className="[&_input]:border-none [&_input]:h-10 [&_input]:bg-transparent [&_input]:text-sm [&_input]:font-medium"
                  renderTopOptions={renderTopOptions("start")}
                />
              </div>
              <div
                className={cn("w-full rounded-lg transition-all bg-gray-50 border", activePoint === "end" ? "border-blue-400 ring-2 ring-blue-100 bg-white shadow-sm relative z-30" : "border-transparent relative z-10")}
                onClick={() => setActivePoint("end")}
              >
                <LocationAutocomplete
                  value={endInput}
                  onChange={(val) => { setEndInput(val); setEndLabel(val); }}
                  onSelect={(s) => { setEnd([s.lng, s.lat], s.label); setEndInput(s.label); }}
                  onClear={() => { setEnd(null, ""); setEndInput(""); setEndLabel(""); }}
                  placeholder="Choose destination"
                  className="[&_input]:border-none [&_input]:h-10 [&_input]:bg-transparent [&_input]:text-sm [&_input]:font-medium"
                  renderTopOptions={renderTopOptions("end")}
                />
              </div>
            </div>

            <div className="w-10 flex items-center justify-center relative z-10 pl-1">
              {(start || end) ? (
                <button onClick={handleSwap} className="p-2 rounded-full text-gray-400 hover:text-blue-500 hover:bg-blue-50 transition-colors" title="Swap start and destination">
                  <ArrowDownUp className="w-5 h-5" />
                </button>
              ) : null}
            </div>
          </div>

          {/* Inline loading */}
          {isRouting && (
            <div className="px-4 pb-3">
              <LoadingOverlay isVisible={isRouting} message="Calculating safe route..." variant="inline" />
            </div>
          )}

          {/* Saved Places */}
          {savedPlaces && savedPlaces.length > 0 && (
            <div className="flex gap-2 overflow-x-auto px-4 pb-3 no-scrollbar border-b border-gray-100">
              {savedPlaces.map(place => {
                const Icon = iconMap[place.icon] || MapPin;
                return (
                  <button
                    key={place.id}
                    onClick={() => handleSelectSavedPlace(place)}
                    className="flex items-center gap-1.5 bg-blue-50 border border-blue-100 text-blue-700 px-3 py-1.5 rounded-full whitespace-nowrap text-xs font-semibold hover:bg-blue-100 active:scale-95 transition-all"
                  >
                    <Icon className="w-3.5 h-3.5" />
                    {place.name}
                  </button>
                );
              })}
            </div>
          )}

          {/* Mobile Vehicle Profile */}
          <div className="flex border-t border-gray-100 overflow-x-auto">
            {PROFILE_OPTIONS.map((opt) => (
              <button
                key={opt.id}
                onClick={() => setVehicleProfile(opt.id)}
                className={cn(
                  "flex-1 flex items-center justify-center gap-1.5 py-2.5 px-4 text-[11px] font-semibold transition-colors",
                  vehicleProfile === opt.id
                    ? "bg-blue-50 text-blue-700"
                    : "text-gray-500 hover:bg-gray-50 hover:text-gray-900"
                )}
              >
                <opt.icon className="w-4 h-4" />
                <span className="whitespace-nowrap">{opt.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Mobile Bottom Sheet for Route Summary */}
        <AnimatePresence>
          {selectedRoute && (
            <motion.div
              drag="y"
              dragConstraints={{ top: 0, bottom: 300 }}
              dragElastic={0.2}
              onDragEnd={(e, { offset, velocity }) => {
                if (offset.y > 50 || velocity.y > 200) setActivePanel(null);
                else if (offset.y < -50 || velocity.y < -200) setActivePanel("route");
              }}
              initial={{ y: "100%" }}
              animate={{ y: isCollapsed ? "calc(100% - 64px)" : "0%" }}
              exit={{ y: "100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="fixed bottom-[calc(64px+env(safe-area-inset-bottom))] left-0 right-0 z-40 rounded-t-3xl bg-white shadow-[0_-8px_30px_rgba(0,0,0,0.12)] overflow-hidden overscroll-y-none"
            >
              <div
                className="w-full flex justify-center pt-3 pb-2 cursor-grab active:cursor-grabbing touch-none select-none"
                onClick={() => setActivePanel(isCollapsed ? "route" : null)}
              >
                <div className="w-12 h-1.5 bg-gray-300 rounded-full" />
              </div>

              <div className="px-4 pb-5 overflow-y-auto max-h-[60vh]">
                {/* Selected route summary */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex flex-col">
                    <span className="text-2xl font-black text-blue-600">
                      {formatDuration(selectedRoute.duration)}
                    </span>
                    <span className="text-sm font-medium text-gray-500">
                      {(selectedRoute.distance / 1000).toFixed(1)} km · {selectedRoute.label}
                    </span>
                  </div>
                  <button
                    onClick={() => { resetAll(); setStartInput(""); setEndInput(""); }}
                    className="text-xs font-semibold text-gray-400 bg-gray-100 hover:bg-red-50 hover:text-red-600 px-3 py-1.5 rounded-full transition-colors"
                  >
                    Clear
                  </button>
                </div>

                {/* Route option strip */}
                {allRoutes && allRoutes.length > 1 && (
                  <div className="flex gap-2 overflow-x-auto pb-1 -mx-1 px-1">
                    {allRoutes.map((route) => (
                      <button
                        key={route.index}
                        id={`mobile-route-option-${route.index}`}
                        onClick={() => setSelectedRouteIndex(route.index)}
                        className={cn(
                          "flex-shrink-0 flex flex-col items-center rounded-xl border px-3 py-2 text-left transition-all min-w-[100px]",
                          route.index === selectedRouteIndex
                            ? "border-blue-400 bg-blue-50 ring-1 ring-blue-200"
                            : "border-gray-200 bg-white"
                        )}
                      >
                        <span className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide">
                          {route.label}
                        </span>
                        <span className="text-base font-black text-gray-900">
                          {formatDuration(route.duration)}
                        </span>
                        <span className="text-[11px] text-gray-500">
                          {(route.distance / 1000).toFixed(1)} km
                        </span>
                      </button>
                    ))}
                  </div>
                )}

                {/* Flood status badge */}
                <div
                  className={cn(
                    "flex items-center gap-2 px-4 py-2.5 text-sm font-semibold rounded-xl border mt-3",
                    selectedRoute.blocked
                      ? "bg-red-50 text-red-700 border-red-100"
                      : selectedRoute.avoided_floods
                        ? "bg-amber-50 text-amber-700 border-amber-100"
                        : "bg-green-50 text-green-700 border-green-100"
                  )}
                >
                  {selectedRoute.blocked || selectedRoute.avoided_floods ? (
                    <AlertTriangle className="h-5 w-5" />
                  ) : (
                    <CheckCircle className="h-5 w-5" />
                  )}
                  <span>
                    {selectedRoute.blocked
                      ? "Route contains flooded areas"
                      : selectedRoute.avoided_floods
                        ? "Safe detour applied"
                        : "Clear path — no floods detected"}
                  </span>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </>
    );
  }

  // ── DESKTOP VIEW ─────────────────────────────────────────────────────────────
  const renderTopOptions = (target: ActivePoint) => (
    <>
      <li>
        <button
          type="button"
          className="flex w-full items-start gap-2 px-3 py-3 text-left text-sm hover:bg-blue-50 transition-colors border-b border-gray-100"
          onMouseDown={(e) => e.preventDefault()}
          onClick={() => handlePickOnMapToggle(target)}
        >
          <div className="bg-blue-100 p-1.5 rounded-full shrink-0">
            <Crosshair className="h-4 w-4 text-blue-700" />
          </div>
          <span className="flex flex-col justify-center h-7 font-semibold text-blue-700">Choose on Map</span>
        </button>
      </li>
      <li>
        <button
          type="button"
          className="flex w-full items-start gap-2 px-3 py-3 text-left text-sm hover:bg-blue-50 transition-colors border-b border-gray-100 mb-1"
          onMouseDown={(e) => e.preventDefault()}
          onClick={() => handleUseCurrentLocation(target)}
        >
          <div className="bg-gray-100 p-1.5 rounded-full shrink-0">
            <MapPin className="h-4 w-4 text-gray-700" />
          </div>
          <span className="flex flex-col justify-center h-7 font-semibold text-gray-800">Use Current Location</span>
        </button>
      </li>
    </>
  );

  return (
    <>
      <div className="fixed top-0 left-0 bottom-0 z-40 bg-white shadow-xl border-r border-gray-200 flex flex-col w-[340px]">
        {/* ── FIXED HEADER: Engine + Profile + Inputs ── */}
        <div className="p-3 border-b border-gray-100 flex flex-col gap-3 flex-shrink-0">

          {/* Engine Switcher */}
          <div className="flex bg-gray-100 p-0.5 rounded-lg">
            <button
              onClick={() => setRoutingEngine("valhalla")}
              className={cn("flex-1 text-xs font-semibold py-1.5 rounded-md transition-colors", routingEngine === "valhalla" ? "bg-white shadow-sm text-blue-600" : "text-gray-500 hover:text-gray-700")}
            >
              Valhalla
            </button>
            <button
              onClick={() => setRoutingEngine("ors")}
              className={cn("flex-1 text-xs font-semibold py-1.5 rounded-md transition-colors", routingEngine === "ors" ? "bg-white shadow-sm text-blue-600" : "text-gray-500 hover:text-gray-700")}
            >
              OpenRouteService
            </button>
          </div>

          {/* Vehicle Profile Selector */}
          <div className="flex bg-gray-50 rounded-lg p-0.5 border border-gray-200">
            {PROFILE_OPTIONS.map((opt) => (
              <button
                key={opt.id}
                onClick={() => setVehicleProfile(opt.id)}
                className={cn(
                  "flex-1 flex flex-col items-center gap-0.5 py-1.5 px-1 rounded-md transition-all",
                  vehicleProfile === opt.id
                    ? "bg-white text-blue-600 shadow-sm border border-gray-200"
                    : "text-gray-500 hover:bg-gray-100"
                )}
              >
                <opt.icon className="w-3.5 h-3.5" />
                <span className="text-[9px] font-medium leading-none">{opt.label}</span>
              </button>
            ))}
          </div>

          {/* Location Inputs (Timeline Style) */}
          <div className="flex items-center">
            {/* Left Icons */}
            <div className="flex flex-col items-center justify-center gap-1 w-5 mr-2 relative z-10 shrink-0">
              <CircleDot className="w-3.5 h-3.5 text-green-600 shrink-0 bg-white" />
              <div className="w-[2px] h-5 bg-gray-200 border-l border-dashed border-gray-300" />
              <MapPin className="w-4 h-4 text-red-500 shrink-0 bg-white" />
            </div>

            {/* Inputs */}
            <div className="flex-1 flex flex-col gap-1.5 relative z-20 min-w-0">
              <div
                className={cn("w-full rounded-lg transition-all bg-gray-50 border", activePoint === "start" ? "border-blue-400 ring-2 ring-blue-100 bg-white shadow-sm relative z-30" : "border-transparent relative z-10")}
                onClick={() => setActivePoint("start")}
              >
                <LocationAutocomplete
                  value={startInput}
                  onChange={(val) => { setStartInput(val); setStartLabel(val); }}
                  onSelect={(s) => { setStart([s.lng, s.lat], s.label); setStartInput(s.label); setActivePoint("end"); }}
                  onClear={() => { setStart(null, ""); setStartInput(""); setStartLabel(""); }}
                  placeholder="Your location"
                  className="[&_input]:border-none [&_input]:h-9 [&_input]:bg-transparent [&_input]:text-sm [&_input]:font-medium"
                  renderTopOptions={renderTopOptions("start")}
                />
              </div>
              <div
                className={cn("w-full rounded-lg transition-all bg-gray-50 border", activePoint === "end" ? "border-blue-400 ring-2 ring-blue-100 bg-white shadow-sm relative z-30" : "border-transparent relative z-10")}
                onClick={() => setActivePoint("end")}
              >
                <LocationAutocomplete
                  value={endInput}
                  onChange={(val) => { setEndInput(val); setEndLabel(val); }}
                  onSelect={(s) => { setEnd([s.lng, s.lat], s.label); setEndInput(s.label); }}
                  onClear={() => { setEnd(null, ""); setEndInput(""); setEndLabel(""); }}
                  placeholder="Choose destination"
                  className="[&_input]:border-none [&_input]:h-9 [&_input]:bg-transparent [&_input]:text-sm [&_input]:font-medium"
                  renderTopOptions={renderTopOptions("end")}
                />
              </div>
            </div>

            {/* Swap Button */}
            <div className="w-8 flex items-center justify-center self-center shrink-0 pl-1">
              {(start || end) ? (
                <button onClick={handleSwap} className="p-1.5 rounded-full text-gray-400 hover:text-blue-500 hover:bg-blue-50 transition-colors" title="Swap start and destination">
                  <ArrowDownUp className="w-4 h-4" />
                </button>
              ) : null}
            </div>
          </div>

          {/* Saved Places Chips */}
          {savedPlaces && savedPlaces.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {savedPlaces.map(place => {
                const Icon = iconMap[place.icon] || MapPin;
                return (
                  <button
                    key={place.id}
                    onClick={() => handleSelectSavedPlace(place)}
                    className="flex items-center gap-1 bg-blue-50 border border-blue-100 text-blue-700 px-2 py-1 rounded-full whitespace-nowrap text-xs font-semibold hover:bg-blue-100 active:scale-95 transition-all"
                  >
                    <Icon className="w-3 h-3" />
                    {place.name}
                  </button>
                );
              })}
            </div>
          )}

          {/* Inline Loading */}
          <LoadingOverlay isVisible={isRouting} message="Calculating safe route..." variant="inline" />

          {/* Route Error */}
          {routeError && !isRouting && (
            <div className="flex items-center gap-2 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              <span className="text-xs">{routeError}</span>
            </div>
          )}
        </div>

        {/* ── SCROLLABLE RESULTS AREA ── */}
        <div className="flex-1 overflow-y-auto min-h-0">

          {/* Compact Route Option Strips */}
          {allRoutes && allRoutes.length > 0 && !isRouting && (
            <div className="px-3 pt-3 flex flex-col gap-1.5">
              {allRoutes.map((route) => (
                <button
                  key={route.index}
                  id={`desktop-route-option-${route.index}`}
                  onClick={() => setSelectedRouteIndex(route.index)}
                  className={cn(
                    "w-full text-left rounded-lg border flex items-center gap-2 px-3 py-2 transition-all duration-150 relative overflow-hidden",
                    route.index === selectedRouteIndex
                      ? "border-blue-300 bg-blue-50/60"
                      : "border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50"
                  )}
                >
                  {/* Active accent bar */}
                  {route.index === selectedRouteIndex && (
                    <div className="absolute left-0 top-0 bottom-0 w-[3px] bg-blue-500 rounded-r" />
                  )}

                  {/* Flood icon */}
                  <div className="shrink-0 ml-1">
                    {route.blocked ? (
                      <AlertTriangle className="h-3.5 w-3.5 text-red-500" />
                    ) : route.avoided_floods ? (
                      <AlertTriangle className="h-3.5 w-3.5 text-amber-500" />
                    ) : (
                      <CheckCircle className="h-3.5 w-3.5 text-green-500" />
                    )}
                  </div>

                  {/* Label */}
                  <span className={cn("text-[10px] font-semibold uppercase tracking-wide truncate flex-1", route.index === selectedRouteIndex ? "text-blue-600" : "text-gray-400")}>
                    {route.label}
                  </span>

                  {/* ETA + distance */}
                  <div className="flex items-baseline gap-1.5 shrink-0">
                    <span className="text-sm font-black text-gray-900">{formatDuration(route.duration)}</span>
                    <span className="text-xs text-gray-400">{(route.distance / 1000).toFixed(1)} km</span>
                  </div>

                  {route.index === selectedRouteIndex && (
                    <CheckCircle className="h-3.5 w-3.5 text-blue-500 shrink-0" />
                  )}
                </button>
              ))}
            </div>
          )}

          {/* ── TURN-BY-TURN DIRECTIONS ── */}
          {selectedRoute?.instructions && selectedRoute.instructions.length > 0 && !isRouting && (
            <div className="px-3 pt-4 pb-3">
              {/* Section header */}
              <div className="flex items-center gap-2 mb-2">
                <Navigation className="w-3.5 h-3.5 text-gray-400" />
                <span className="text-[11px] font-bold uppercase tracking-widest text-gray-400">Turn-by-Turn</span>
              </div>

              <div className="flex flex-col divide-y divide-gray-100 rounded-xl overflow-hidden border border-gray-100">
                {selectedRoute.instructions.map((step: any, idx: number) => {
                  const StepIcon = getStepIcon(step.type ?? 6);
                  const isHovered = hoveredStepIdx === idx;
                  return (
                    <button
                      key={idx}
                      className={cn(
                        "flex items-center gap-2.5 px-3 py-2.5 text-left transition-colors w-full",
                        isHovered ? "bg-blue-50" : "bg-white hover:bg-gray-50"
                      )}
                      onMouseEnter={() => {
                        setHoveredStepIdx(idx);
                        fireStepHover(idx);
                      }}
                      onMouseLeave={() => {
                        setHoveredStepIdx(null);
                        fireStepHover(null);
                      }}
                      onClick={() => fireStepClick(idx)}
                    >
                      {/* Direction icon */}
                      <div className={cn(
                        "w-7 h-7 rounded-full flex items-center justify-center shrink-0 transition-colors",
                        isHovered ? "bg-blue-500 text-white" : "bg-gray-100 text-gray-600"
                      )}>
                        <StepIcon className="w-3.5 h-3.5" />
                      </div>

                      {/* Instruction text */}
                      <div className="flex-1 min-w-0">
                        <p className={cn("text-xs font-medium leading-snug truncate", isHovered ? "text-blue-700" : "text-gray-800")}>
                          {step.instruction || step.name || "Continue"}
                        </p>
                        {step.name && step.name !== "-" && step.instruction && step.name !== step.instruction && (
                          <p className="text-[10px] text-gray-400 truncate">{step.name}</p>
                        )}
                      </div>

                      {/* Step distance */}
                      {(step.distance ?? 0) > 0 && (
                        <span className="text-[10px] font-semibold text-gray-400 shrink-0">
                          {formatStepDistance(step.distance)}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* ── FOOTER: Offline Manager ── */}
        <div className="p-3 border-t border-gray-100 flex-shrink-0">
          <OfflineManager />
        </div>
      </div>
    </>
  );
}
