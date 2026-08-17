"use client";

import { useState, useEffect, useRef } from "react";
import { Panel } from "@/shared/ui/Panel";
import { Input } from "@/shared/ui/Input";
import { Button } from "@/shared/ui/Button";
import { Select } from "@/shared/ui/Select";
import { MapPin, Home, Briefcase, GraduationCap, Building, Star, Coffee, Heart, Crosshair, User } from "lucide-react";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import { MapPickerMobileOverlay } from "@/features/map/MapPickerMobileOverlay";
import { useMapContext } from "@/features/map/MapContext";
import { LocationAutocomplete } from "@/shared/ui/LocationAutocomplete";
import { savedPlacesApi } from "@/features/profile/savedPlacesApi";
import { getCurrentLocation } from "@/features/geocoding/geocodingApi";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/shared/ui/Toast";
import Link from "next/link";

const ICON_OPTIONS = [
  { value: "🏠", label: "Home" },
  { value: "💼", label: "Work" },
  { value: "🎓", label: "School" },
  { value: "🏢", label: "Building" },
  { value: "💻", label: "Tech" },
  { value: "🛏️", label: "Hotel" },
  { value: "☕", label: "Cafe" },
  { value: "🍔", label: "Food" },
  { value: "🛒", label: "Shopping" },
  { value: "🏥", label: "Medical" },
  { value: "🌳", label: "Park" },
  { value: "🏋️", label: "Gym" },
  { value: "⛽", label: "Gas" },
  { value: "🚌", label: "Transit" },
  { value: "✈️", label: "Airport" },
  { value: "🏦", label: "Bank" },
  { value: "❤️", label: "Favorite" },
  { value: "⭐", label: "Star" },
  { value: "📍", label: "Pin" },
];

export function SavePlacePanel() {
  const {
    isSavePlacePanelOpen,
    setIsSavePlacePanelOpen,
    isPickingOnMap,
    setIsPickingOnMap,
    activePoint,
    setActivePoint,
    savedPlaces,
    setSavedPlaces,
    draftSavePlaceCoords,
    setDraftSavePlaceCoords,
    savePlaceIcon: icon,
    setSavePlaceIcon: setIcon,
    isAnalyticsOpen,
    lastOpenedLeftPanel,
  } = useMapContext();

  const { isAuthenticated } = useAuth();
  const { error: showError, success } = useToast();

  const [name, setName] = useState("");
  const [address, setAddress] = useState("");
  const [coords, setCoords] = useState<[number, number] | null>(null);
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isPanelCollapsed, setIsPanelCollapsed] = useState(false);

  // Reset to expanded when opened
  useEffect(() => {
    if (isSavePlacePanelOpen) {
      setIsPanelCollapsed(false);
    }
  }, [isSavePlacePanelOpen]);

  // When Analytics is open (and is the newer panel), dodge right (same pattern as RoutePanel dodges for Analytics/SavePlace)
  const isDesktop = !useMediaQuery("(max-width: 640px), (pointer: coarse)");
  const isMobile = !isDesktop;
  const isDodgingAnalytics = isSavePlacePanelOpen && isAnalyticsOpen && lastOpenedLeftPanel === "analytics" && isDesktop;
  const [mapCenter, setMapCenter] = useState<[number, number] | null>(null);

  const [actualDodging, setActualDodging] = useState(isDodgingAnalytics);

  // Auto-collapse when Analytics opens (fires once on transition, user can re-expand after)
  const prevIsDodging = useRef(isDodgingAnalytics);
  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (isDodgingAnalytics && !prevIsDodging.current) {
      // 1. Collapse first (takes 250ms)
      setIsPanelCollapsed(true);
      // 2. Move exactly after collapse finishes
      timer = setTimeout(() => setActualDodging(true), 250);
    } else if (!isDodgingAnalytics && prevIsDodging.current) {
      // 1. Move first (takes 300ms)
      setActualDodging(false);
      // 2. Expand exactly after move finishes
      timer = setTimeout(() => setIsPanelCollapsed(false), 300);
    }
    prevIsDodging.current = isDodgingAnalytics;
    return () => clearTimeout(timer);
  }, [isDodgingAnalytics]);

  // If Save Place just opened and is forcing Analytics to dodge, wait 250ms for Analytics to collapse before sliding in.
  const isForcingAnalyticsToDodge = isAnalyticsOpen && lastOpenedLeftPanel === "save_place" && isDesktop;
  const entranceDelay = isForcingAnalyticsToDodge ? 0.25 : 0;

  useEffect(() => {
    const handleCenterChange = (e: Event) => {
      const customEvent = e as CustomEvent<[number, number]>;
      setMapCenter(customEvent.detail);
    };
    window.addEventListener("map-center-changed", handleCenterChange);
    return () => window.removeEventListener("map-center-changed", handleCenterChange);
  }, []);

  // Sync draft coords into local state
  useEffect(() => {
    if (draftSavePlaceCoords) {
      setCoords(draftSavePlaceCoords.coords);
      setAddress(draftSavePlaceCoords.label);
      setDraftSavePlaceCoords(null);
      setIsSavePlacePanelOpen(true);
    }
  }, [draftSavePlaceCoords, setDraftSavePlaceCoords, setIsSavePlacePanelOpen]);

  if (!isSavePlacePanelOpen && !(isPickingOnMap && activePoint === "save_place_location")) return null;

  if (isMobile && isPickingOnMap && activePoint === "save_place_location") {
    return (
      <MapPickerMobileOverlay 
        onCancel={() => {
          setIsPickingOnMap(false);
          setActivePoint(null);
          setIsSavePlacePanelOpen(true);
        }}
        onConfirm={() => {
          if (mapCenter) {
            setCoords(mapCenter);
            setAddress(`${mapCenter[1].toFixed(5)}, ${mapCenter[0].toFixed(5)}`);
            setIsPickingOnMap(false);
            setActivePoint(null);
            setIsSavePlacePanelOpen(true);
          }
        }}
        confirmText="Set Location"
      />
    );
  }

  // We reuse picking logic for desktop. The user clicks "Choose on Map" and we hide this panel until they pick.
  if (isPickingOnMap && isMobile) return null;

  const handleSave = async () => {
    if (!name.trim()) {
      showError("Validation Error", "Please enter a name for this place.");
      return;
    }
    if (!coords) {
      showError("Validation Error", "Please select a location.");
      return;
    }

    setIsSubmitting(true);

    try {
      const newPlace = await savedPlacesApi.createSavedPlace({
        name,
        icon,
        address,
        latitude: coords[1],
        longitude: coords[0]
      });
      setSavedPlaces([newPlace, ...savedPlaces]);
      setIsSavePlacePanelOpen(false);
      // Reset
      setName("");
      setIcon("Home");
      setAddress("");
      setCoords(null);
      success("Success", "Place saved successfully");
    } catch (err: any) {
      showError("Failed to save", err.response?.data?.detail || "Failed to save place");
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderTopOptions = () => (
    <>
      <li>
        <button
          type="button"
          className="flex w-full items-start gap-2 px-3 py-3 text-left text-sm hover:bg-blue-50 transition-colors border-b border-gray-100"
          onMouseDown={(e) => e.preventDefault()}
          onClick={() => {
            setActivePoint("save_place_location");
            setIsPickingOnMap(true);
            if (isMobile) setIsSavePlacePanelOpen(false); // Hide panel while picking on mobile
          }}
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
          onClick={async () => {
            try {
              const currentCoords = await getCurrentLocation();
              setCoords(currentCoords);
              setAddress("Current Location");
            } catch (err: any) {
              alert(err.message || "Unable to retrieve your location");
            }
          }}
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
    <Panel
      title="Save Place"
      icon={<MapPin className="h-4 w-4 text-emerald-600" />}
      iconBgClassName="bg-emerald-100"
      isOpen={isSavePlacePanelOpen}
      onClose={() => setIsSavePlacePanelOpen(false)}
      isCollapsed={isPanelCollapsed}
      onCollapseToggle={() => setIsPanelCollapsed(!isPanelCollapsed)}
      isMobile={isMobile}
      bodyClassName="!max-h-[60vh] min-h-[45vh] pb-0 flex flex-col"
      anchor="left"
      initialPosition={{ x: actualDodging ? 360 : 16, y: 80 }}
      showDesktopClose={true}
      panelId="save_place"
      entranceDelay={entranceDelay}
    >
      {!isAuthenticated ? (
        <div className="flex flex-col items-center justify-center h-full p-6 text-center space-y-4">
          <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center text-blue-500 mb-2 mt-8">
            <User className="w-8 h-8" />
          </div>
          <h3 className="text-lg font-bold text-gray-900">Login Required</h3>
          <p className="text-sm text-gray-500">
            You need to be logged in to save places for quick navigation.
          </p>
          <Link href="/login?redirect=/map" className="w-full mt-4">
            <Button className="w-full">Sign In</Button>
          </Link>
        </div>
      ) : (
        <div className="flex flex-col gap-4 p-1 flex-1">
          <div>
            <label className="text-sm font-medium text-slate-700 block mb-1">Name</label>
            <Input 
              value={name} 
              onChange={(e) => setName(e.target.value)} 
              placeholder="e.g. Home, Work, Gym" 
            />
          </div>

          <div>
            <label className="text-sm font-medium text-slate-700 block mb-1">Icon</label>
            <div className="grid grid-cols-[repeat(auto-fill,minmax(2.5rem,1fr))] gap-2 place-items-center">
              {ICON_OPTIONS.map((opt) => {
                const isSelected = icon === opt.value;
                return (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => setIcon(opt.value)}
                    className={`p-2 rounded-xl transition-colors flex items-center justify-center text-xl ${
                      isSelected ? 'bg-blue-600 shadow-md ring-2 ring-blue-200' : 'bg-slate-100 hover:bg-slate-200'
                    }`}
                    title={opt.label}
                  >
                    <span className="w-5 h-5 flex items-center justify-center drop-shadow-sm">{opt.value}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-slate-700 block mb-1">Location</label>
            {coords ? (
              <div className="flex items-center justify-between bg-slate-50 p-3 rounded-xl border border-slate-200">
                <div className="flex items-center gap-2 overflow-hidden">
                  <MapPin className="w-4 h-4 text-slate-400 shrink-0" />
                  <span className="text-sm text-slate-700 truncate">{address || `${coords[1].toFixed(5)}, ${coords[0].toFixed(5)}`}</span>
                </div>
                <button onClick={() => { setCoords(null); setAddress(""); }} className="text-xs text-red-500 font-medium px-2 py-1 hover:bg-red-50 rounded">Clear</button>
              </div>
            ) : (
              <div className="w-full rounded-lg transition-all bg-gray-50 border border-gray-200 focus-within:border-blue-400 focus-within:ring-2 focus-within:ring-blue-100 focus-within:bg-white shadow-sm relative z-10">
                <LocationAutocomplete 
                  placeholder="Search address..."
                  value={address}
                  onChange={setAddress}
                  onSelect={(s) => {
                    setCoords([s.lng, s.lat]);
                    setAddress(s.label || "");
                  }}
                  className="[&_input]:border-none [&_input]:h-10 [&_input]:bg-transparent [&_input]:text-sm [&_input]:font-medium"
                  renderTopOptions={renderTopOptions()}
                />
              </div>
            )}
          </div>

          <div className="mt-auto sticky bottom-0 bg-white pt-2 pb-6 z-20 border-t border-transparent">
            <Button 
              className="w-full" 
              onClick={handleSave} 
              disabled={isSubmitting || !name || !coords}
            >
              {isSubmitting ? "Saving..." : "Save Place"}
            </Button>
          </div>
        </div>
      )}
    </Panel>
  );
}
