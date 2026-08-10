"use client";

import { useState, useEffect } from "react";
import { Panel } from "@/shared/ui/Panel";
import { Input } from "@/shared/ui/Input";
import { Button } from "@/shared/ui/Button";
import { Select } from "@/shared/ui/Select";
import { MapPin, Home, Briefcase, GraduationCap, Building, Star, Coffee, Heart, Crosshair } from "lucide-react";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import { MapPickerMobileOverlay } from "@/features/map/MapPickerMobileOverlay";
import { useMapContext } from "@/features/map/MapContext";
import { LocationAutocomplete } from "@/shared/ui/LocationAutocomplete";
import { savedPlacesApi } from "@/features/profile/savedPlacesApi";
import { getCurrentLocation } from "@/features/geocoding/geocodingApi";

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
    setSavePlaceIcon: setIcon
  } = useMapContext();

  const [name, setName] = useState("");
  const [address, setAddress] = useState("");
  const [coords, setCoords] = useState<[number, number] | null>(null);
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const isMobile = useMediaQuery("(max-width: 640px), (pointer: coarse)");
  const [mapCenter, setMapCenter] = useState<[number, number] | null>(null);

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

  if (!isSavePlacePanelOpen && !isPickingOnMap) return null;

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
  if (isPickingOnMap) return null;

  const handleSave = async () => {
    if (!name.trim()) {
      setError("Please enter a name for this place.");
      return;
    }
    if (!coords) {
      setError("Please select a location.");
      return;
    }

    setIsSubmitting(true);
    setError(null);

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
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to save place");
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
            setIsSavePlacePanelOpen(false); // Hide panel while picking
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
      icon={<MapPin className="h-4 w-4 text-blue-600" />}
      iconBgClassName="bg-blue-100"
      isOpen={isSavePlacePanelOpen}
      onClose={() => setIsSavePlacePanelOpen(false)}
      isCollapsed={!isSavePlacePanelOpen}
      onCollapseToggle={() => setIsSavePlacePanelOpen(!isSavePlacePanelOpen)}
      isMobile={window.innerWidth < 640} // Simple check for TS
      bodyClassName="!max-h-[60vh] min-h-[45vh] pb-0 flex flex-col"
    >
      <div className="flex flex-col gap-4 p-1 flex-1">
        {error && (
          <div className="text-sm text-red-500 bg-red-50 p-2 rounded-md">
            {error}
          </div>
        )}

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
          <div className="flex gap-2 flex-wrap">
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
    </Panel>
  );
}
