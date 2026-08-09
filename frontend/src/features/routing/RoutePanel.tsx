"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  CircleDot,
  Crosshair,
  Flag,
  Loader2,
  MapPin,
  Navigation,
  ArrowLeftRight,
  ArrowDownUp,
  Check,
  AlertTriangle,
  CheckCircle,
  X,
  Car,
  Bike,
  PersonStanding
} from "lucide-react";
import { Panel } from "@/shared/ui/Panel";
import { CardContent } from "@/shared/ui/Card";
import { LocationAutocomplete } from "@/shared/ui/LocationAutocomplete";
import { LoadingOverlay } from "@/shared/ui";
import { cn } from "@/lib/utils";
import { useMapContext, type ActivePoint } from "@/features/map/MapContext";
import type { LocationSuggestion } from "@/features/geocoding/types";
import { getCurrentLocation } from "@/features/geocoding/geocodingApi";
import { useMediaQuery } from "@/hooks/useMediaQuery";

const POINT_COLORS = {
  start: {
    accent: "border-green-200",
    stripe: "from-green-500 to-emerald-400",
    bg: "bg-green-50",
    text: "text-green-700",
    icon: "text-green-600",
    marker: "#16a34a",
    label: "Start",
  },
  end: {
    accent: "border-red-200",
    stripe: "from-red-500 to-rose-400",
    bg: "bg-red-50",
    text: "text-red-700",
    icon: "text-red-600",
    marker: "#dc2626",
    label: "Destination",
  },
} as const;

function DesktopPointSelector({
  point,
  label,
  placeholder,
  isActive,
  isSet,
  onActivate,
  onLabelChange,
  onSelect,
  onUseCurrent,
  onClear,
}: {
  point: "start" | "end";
  label: string;
  placeholder: string;
  isActive: boolean;
  isSet: boolean;
  onActivate: () => void;
  onLabelChange: (value: string) => void;
  onSelect: (suggestion: LocationSuggestion) => void;
  onUseCurrent: () => void;
  onClear: () => void;
}) {
  const colors = POINT_COLORS[point];
  const Icon = point === "start" ? CircleDot : Flag;

  const renderTopOptions = () => (
    <>
      <li>
        <button
          type="button"
          className="flex w-full items-start gap-2 px-3 py-3 text-left text-sm hover:bg-blue-50 transition-colors border-b border-gray-100"
          onMouseDown={(e) => e.preventDefault()}
          onClick={onActivate}
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
          onClick={onUseCurrent}
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
    <div
      className={cn(
        "rounded-xl border bg-white transition-all",
        isActive
          ? "shadow-md border-blue-200 ring-1 ring-blue-100"
          : colors.accent
      )}
    >
      {/* Top accent stripe */}
      <div
        className={cn(
          "h-[3px] w-full bg-gradient-to-r rounded-t-xl",
          isActive ? "from-blue-500 to-indigo-400" : colors.stripe
        )}
      />

      <div className="flex items-center justify-between px-3 pt-2 pb-1">
        <div className="flex items-center gap-1.5">
          <Icon className={cn("h-4 w-4", colors.icon)} />
          <span className={cn("text-xs font-semibold uppercase tracking-wide", colors.text)}>
            {colors.label}
          </span>
          {isSet && (
            <span className="flex items-center gap-0.5 text-[10px] font-medium text-green-600 bg-green-100 px-1.5 py-0.5 rounded-full">
              <Check className="h-3 w-3" />
              Set
            </span>
          )}
        </div>
      </div>

      <div className="px-3 pb-2.5 mt-1">
        <LocationAutocomplete
          value={label}
          onChange={onLabelChange}
          onSelect={onSelect}
          onClear={onClear}
          placeholder={placeholder}
          className="[&_input]:h-9"
          renderTopOptions={renderTopOptions()}
        />
      </div>
    </div>
  );
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
    routeInfo,
    isRouting,
    routeError,
    setActivePoint,
    setStart,
    setEnd,
    setStartLabel,
    setEndLabel,
    setPointFromMap,
    clearRoute,
    resetAll,
    isPickingOnMap,
    setIsPickingOnMap,
    vehicleProfile,
    setVehicleProfile,
    isAnalyticsOpen,
    isReportPanelOpen,
  } = useMapContext();

  const isMobile = useMediaQuery("(max-width: 640px), (pointer: coarse)");
  const isDesktop = !isMobile;
  const isRight = isAnalyticsOpen && isDesktop;
  const isCollapsed = activePanel !== "route";
  const [startInput, setStartInput] = useState("");
  const [endInput, setEndInput] = useState("");
  const [mapCenter, setMapCenter] = useState<[number, number] | null>(null);

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
        setActivePoint(null); // Deselect after setting end
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

  const PROFILE_OPTIONS: Array<{ id: "light" | "heavy" | "motorcycle" | "walk", icon: any, label: string }> = [
    { id: "heavy", icon: Car, label: "High Clearance" },
    { id: "light", icon: Car, label: "Low Clearance" },
    { id: "motorcycle", icon: Bike, label: "Motorcycle" },
    { id: "walk", icon: PersonStanding, label: "Walk" },
  ];

  if (isMobile) {
    if (isPickingOnMap && (activePoint === "start" || activePoint === "end")) {
      return (
        <div className="absolute inset-0 pointer-events-none z-40 flex flex-col justify-between">
          <div className="p-4 pointer-events-auto">
            <button
              onClick={() => {
                setIsPickingOnMap(false);
                if (!start && !end) setActivePoint(null);
              }}
              className="flex items-center justify-center w-12 h-12 bg-white rounded-full shadow-md text-gray-900 hover:bg-gray-100 border border-gray-300"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
          
          <div className="p-4 pointer-events-auto flex justify-center pb-24">
            <button
              onClick={confirmMapLocation}
              className="flex items-center justify-center gap-2 bg-blue-600 text-white rounded-full px-6 py-3 shadow-lg font-bold text-base border border-blue-500 hover:bg-blue-700 transition-all min-w-[200px]"
            >
              <Check className="w-5 h-5" />
              Set {activePoint === "start" ? "Start" : "Destination"}
            </button>
          </div>
        </div>
      );
    }
    
    if (isPickingOnMap && (activePoint === "flood_start" || activePoint === "flood_end")) {
      return null;
    }

    if (isMobile && (isReportPanelOpen || isAnalyticsOpen) && activePoint !== "start" && activePoint !== "end") {
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
        <LoadingOverlay isVisible={isRouting} message="Calculating safe route..." />
        
        {/* Google Maps Style Mobile Top Search Bar */}
        <div className="absolute top-4 left-4 right-4 z-40 bg-white rounded-2xl shadow-lg border border-gray-100 overflow-visible transition-all">
          <div className="flex p-3 pr-2">
            {/* Left Icons */}
            <div className="flex flex-col items-center justify-start gap-1 w-6 mt-3 relative z-10">
              <CircleDot className="w-4 h-4 text-green-600 shrink-0 bg-white" />
              <div className="w-[3px] h-6 bg-gray-200 border-l border-dashed border-gray-300" />
              <MapPin className="w-5 h-5 text-red-500 shrink-0 bg-white" />
            </div>
            
            {/* Inputs */}
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

            {/* Right Swap Button */}
            <div className="w-10 flex flex-col items-center justify-center relative z-10 pl-1">
              {(start || end) ? (
                <button 
                  onClick={handleSwap}
                  className="p-2 rounded-full text-gray-400 hover:text-blue-500 hover:bg-blue-50 transition-colors"
                >
                  <ArrowDownUp className="w-5 h-5" />
                </button>
              ) : null}
            </div>
          </div>
          
          {/* Mobile Vehicle Profile Selector */}
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

              <div className="px-4 pb-5">
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
                    onClick={() => {
                      resetAll();
                      setStartInput("");
                      setEndInput("");
                    }}
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
                        {route.is_truncated && (
                          <span className="text-[10px] text-amber-600 mt-0.5">⚠ Limited</span>
                        )}
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

  // Desktop view — uses shared Panel shell
  const clearButton =
    start || end ? (
      <button
        onClick={() => {
          resetAll();
          setStartInput("");
          setEndInput("");
        }}
        className="text-[11px] font-medium text-gray-500 hover:text-red-600 transition-colors px-2 py-1 mr-1"
        title="Clear route and inputs"
      >
        Clear
      </button>
    ) : undefined;

  const collapsedSummary =
    isCollapsed && routeInfo ? (
      <div className="flex items-center justify-between text-sm bg-gray-50 p-2 rounded-lg border border-gray-100">
        <div className="flex items-center gap-2">
          <span className="font-bold text-gray-900">
            {(routeInfo.distance / 1000).toFixed(1)} km
          </span>
          <span className="text-gray-400">•</span>
          <span className="font-medium text-gray-700">
            {formatDuration(routeInfo.duration)}
          </span>
        </div>
        {routeInfo.blocked ? (
          <AlertTriangle className="h-4 w-4 text-red-600" />
        ) : routeInfo.avoided_floods ? (
          <CheckCircle className="h-4 w-4 text-amber-500" />
        ) : (
          <CheckCircle className="h-4 w-4 text-green-600" />
        )}
      </div>
    ) : undefined;

  return (
    <>
      <LoadingOverlay isVisible={isRouting} message="Calculating safe route..." />
      <Panel
        key={isAnalyticsOpen ? "analytics-mode" : "default-mode"}
        title="Route Planner"
        icon={<Navigation className="h-4 w-4 text-blue-600" />}
        iconBgClassName="bg-blue-100"
        isCollapsed={isCollapsed}
        onCollapseToggle={() => setActivePanel(isCollapsed ? "route" : null)}
        isMobile={false}
        anchor={isAnalyticsOpen ? "right" : "left"}
        initialPosition={{ x: isAnalyticsOpen ? 372 : 16, y: 80 }}
        headerActions={clearButton}
        collapsedSummary={collapsedSummary}
      >
        <DesktopPointSelector
          point="start"
          label={startInput}
          placeholder="e.g. C. Santos, Taft Ave"
          isActive={activePoint === "start"}
          isSet={!!start}
          onActivate={() => handlePickOnMapToggle("start")}
          onLabelChange={(val) => { setStartInput(val); setStartLabel(val); }}
          onSelect={(s) => { setStart([s.lng, s.lat], s.label); setStartInput(s.label); setActivePoint("end"); }}
          onUseCurrent={() => handleUseCurrentLocation("start")}
          onClear={() => { setStart(null, ""); setStartInput(""); setStartLabel(""); }}
        />

        {start && end && (
          <div className="flex justify-center -my-3 z-10 relative">
            <button
              type="button"
              onClick={handleSwap}
              title="Swap start and destination"
              className="flex items-center justify-center w-8 h-8 rounded-full border border-gray-300 bg-white text-gray-500 hover:bg-gray-100 hover:text-blue-600 hover:border-blue-300 transition-all shadow-md"
            >
              <ArrowLeftRight className="h-4 w-4" />
            </button>
          </div>
        )}

        <DesktopPointSelector
          point="end"
          label={endInput}
          placeholder="e.g. Pasig City Hall"
          isActive={activePoint === "end"}
          isSet={!!end}
          onActivate={() => handlePickOnMapToggle("end")}
          onLabelChange={(val) => { setEndInput(val); setEndLabel(val); }}
          onSelect={(s) => { setEnd([s.lng, s.lat], s.label); setEndInput(s.label); }}
          onUseCurrent={() => handleUseCurrentLocation("end")}
          onClear={() => { setEnd(null, ""); setEndInput(""); setEndLabel(""); }}
        />

        {/* Desktop Vehicle Profile Selector */}
        <div className="flex bg-gray-50 rounded-lg p-1 border border-gray-200">
          {PROFILE_OPTIONS.map((opt) => (
            <button
              key={opt.id}
              onClick={() => setVehicleProfile(opt.id)}
              className={cn(
                "flex-1 flex flex-col items-center gap-1 py-1.5 px-2 rounded-md transition-all",
                vehicleProfile === opt.id
                  ? "bg-white text-blue-600 shadow-sm border border-gray-200"
                  : "text-gray-500 hover:bg-gray-100"
              )}
            >
              <opt.icon className="w-4 h-4" />
              <span className="text-[10px] font-medium">{opt.label}</span>
            </button>
          ))}
        </div>

        {routeError && (
          <div className="flex items-center gap-2 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2.5">
            <AlertTriangle className="h-5 w-5 shrink-0" />
            <span>{routeError}</span>
          </div>
        )}

        {/* Selectable route cards */}
        {allRoutes && allRoutes.length > 0 && !isRouting && (
          <div className="flex flex-col gap-2">
            {allRoutes.map((route) => (
              <button
                key={route.index}
                id={`desktop-route-option-${route.index}`}
                onClick={() => setSelectedRouteIndex(route.index)}
                className={cn(
                  "w-full text-left rounded-xl border p-3 transition-all duration-150",
                  route.index === selectedRouteIndex
                    ? "border-blue-400 bg-blue-50 ring-1 ring-blue-200 shadow-sm"
                    : "border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50"
                )}
              >
                {/* Header row */}
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[10px] font-semibold uppercase tracking-wide text-gray-400">
                    {route.label}
                  </span>
                  {route.index === selectedRouteIndex && (
                    <CheckCircle className="h-4 w-4 text-blue-500 shrink-0" />
                  )}
                </div>

                {/* ETA + distance */}
                <div className="flex items-baseline gap-2 mb-1.5">
                  <span className="text-lg font-black text-gray-900">
                    {formatDuration(route.duration)}
                  </span>
                  <span className="text-sm text-gray-500">
                    {(route.distance / 1000).toFixed(1)} km
                  </span>
                </div>

                {/* Flood status badge */}
                <div
                  className={cn(
                    "inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full",
                    route.blocked
                      ? "bg-red-100 text-red-700"
                      : route.avoided_floods
                        ? "bg-amber-100 text-amber-700"
                        : "bg-green-100 text-green-700"
                  )}
                >
                  {route.blocked || route.avoided_floods ? (
                    <AlertTriangle className="h-3 w-3" />
                  ) : (
                    <CheckCircle className="h-3 w-3" />
                  )}
                  {route.blocked
                    ? `Passes flooded area (${route.safety_score}% safe)`
                    : route.avoided_floods
                      ? `Detours around flood (${route.safety_score}% safe)`
                      : `Clear path (${route.safety_score}% safe)`}
                </div>

                {/* Truncation warning */}
                {route.is_truncated && (
                  <p className="flex items-center gap-1 text-[11px] text-amber-600 mt-1.5 font-medium">
                    <AlertTriangle className="h-3 w-3" />
                    Limited by one-way roads
                  </p>
                )}
              </button>
            ))}
          </div>
        )}
      </Panel>
    </>
  );
}
