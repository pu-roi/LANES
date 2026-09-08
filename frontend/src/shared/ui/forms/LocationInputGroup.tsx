"use client";

import { CircleDot, MapPin, ArrowDownUp, Crosshair } from "lucide-react";
import { LocationAutocomplete } from "@/shared/ui";
import { cn } from "@/lib/utils";
import type { ActivePoint } from "@/features/map/MapContext";

interface LocationInputGroupProps {
  theme?: "blue" | "orange";
  
  startInput: string;
  setStartInput: (val: string) => void;
  startPlaceholder?: string;
  
  endInput: string;
  setEndInput: (val: string) => void;
  endPlaceholder?: string;
  
  activePoint: ActivePoint;
  setActivePoint: (val: ActivePoint) => void;
  startPointId: ActivePoint;
  endPointId: ActivePoint;
  
  onStartSelect: (s: { lng: number, lat: number, label: string }) => void;
  onEndSelect: (s: { lng: number, lat: number, label: string }) => void;
  onStartClear: () => void;
  onEndClear: () => void;
  onStartChange?: (val: string) => void; 
  onEndChange?: (val: string) => void;   

  onSwap?: () => void;
  canSwap?: boolean;

  onPickOnMap: (target: ActivePoint) => void;
  onUseCurrentLocation?: (target: ActivePoint) => void;
  
  inputClassName?: string;
}

export function LocationInputGroup({
  theme = "blue",
  startInput,
  setStartInput,
  startPlaceholder = "Your location",
  endInput,
  setEndInput,
  endPlaceholder = "Choose destination",
  activePoint,
  setActivePoint,
  startPointId,
  endPointId,
  onStartSelect,
  onEndSelect,
  onStartClear,
  onEndClear,
  onStartChange,
  onEndChange,
  onSwap,
  canSwap = false,
  onPickOnMap,
  onUseCurrentLocation,
  inputClassName = "[&_input]:border-none [&_input]:h-9 [&_input]:bg-transparent [&_input]:text-sm [&_input]:font-medium"
}: LocationInputGroupProps) {

  const isBlue = theme === "blue";
  
  const renderOptions = (target: ActivePoint) => (
    <>
      <li>
        <button
          type="button"
          className={cn(
            "flex w-full items-start gap-2 px-3 py-3 text-left text-sm transition-colors border-b border-gray-100",
            isBlue ? "hover:bg-blue-50" : "hover:bg-orange-50"
          )}
          onMouseDown={(e) => e.preventDefault()}
          onClick={(e) => {
            onPickOnMap(target);
          }}
        >
          <div className={cn("p-1.5 rounded-full shrink-0", isBlue ? "bg-blue-100" : "bg-orange-100")}>
            <Crosshair className={cn("h-4 w-4", isBlue ? "text-blue-700" : "text-orange-700")} />
          </div>
          <span className={cn("flex flex-col justify-center h-7 font-semibold", isBlue ? "text-blue-700" : "text-orange-700")}>
            Choose on Map
          </span>
        </button>
      </li>
      {onUseCurrentLocation && (
        <li>
          <button
            type="button"
            className={cn(
              "flex w-full items-start gap-2 px-3 py-3 text-left text-sm transition-colors border-b border-gray-100 mb-1",
              isBlue ? "hover:bg-blue-50" : "hover:bg-orange-50"
            )}
            onMouseDown={(e) => e.preventDefault()}
            onClick={() => onUseCurrentLocation(target)}
          >
            <div className="bg-gray-100 p-1.5 rounded-full shrink-0">
              <MapPin className="h-4 w-4 text-gray-700" />
            </div>
            <span className="flex flex-col justify-center h-7 font-semibold text-gray-800">
              Use Current Location
            </span>
          </button>
        </li>
      )}
    </>
  );

  return (
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
          className={cn(
            "w-full rounded-lg transition-all bg-gray-50 border",
            activePoint === startPointId
              ? "bg-white shadow-sm relative z-30 ring-2 border-gray-300 ring-gray-100"
              : "border-transparent relative z-10"
          )}
          onClick={() => setActivePoint(startPointId)}
        >
          <LocationAutocomplete
            value={startInput}
            onChange={(val) => {
              setStartInput(val);
              if (onStartChange) onStartChange(val);
            }}
            onSelect={onStartSelect}
            onClear={onStartClear}
            placeholder={startPlaceholder}
            className={inputClassName}
            renderTopOptions={renderOptions(startPointId)}
          />
        </div>
        <div
          className={cn(
            "w-full rounded-lg transition-all bg-gray-50 border",
            activePoint === endPointId
              ? "bg-white shadow-sm relative z-30 ring-2 border-gray-300 ring-gray-100"
              : "border-transparent relative z-10"
          )}
          onClick={() => setActivePoint(endPointId)}
        >
          <LocationAutocomplete
            value={endInput}
            onChange={(val) => {
              setEndInput(val);
              if (onEndChange) onEndChange(val);
            }}
            onSelect={onEndSelect}
            onClear={onEndClear}
            placeholder={endPlaceholder}
            className={inputClassName}
            renderTopOptions={renderOptions(endPointId)}
          />
        </div>
      </div>

      {/* Swap Button */}
      <div className="w-8 flex items-center justify-center self-center shrink-0 pl-1">
        {canSwap && onSwap && (
          <button
            onClick={onSwap}
            className={cn(
              "p-1.5 rounded-full text-gray-400 transition-colors",
              isBlue ? "hover:text-blue-500 hover:bg-blue-50" : "hover:text-orange-500 hover:bg-orange-50"
            )}
            title="Swap start and destination"
          >
            <ArrowDownUp className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
}
