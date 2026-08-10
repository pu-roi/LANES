"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { MapPin, Loader2, X } from "lucide-react";
import { Input } from "./Input";
import { cn } from "@/lib/utils";
import { searchLocations } from "@/features/geocoding/geocodingApi";
import type { LocationSuggestion } from "@/features/geocoding/types";

interface LocationAutocompleteProps {
  value: string;
  onChange: (value: string) => void;
  onSelect: (suggestion: LocationSuggestion) => void;
  onClear?: () => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  renderTopOptions?: React.ReactNode;
}

function tryParseCoordinates(query: string): { lng: number; lat: number } | null {
  const parts = query.split(",").map((p) => p.trim());
  if (parts.length !== 2) return null;
  const val1 = Number(parts[0]);
  const val2 = Number(parts[1]);
  if (Number.isNaN(val1) || Number.isNaN(val2)) return null;

  // In the Philippines (specifically Pasig/Metro Manila), longitude is ~121.0, latitude is ~14.5
  const isLng = (v: number) => v >= 115 && v <= 126;
  const isLat = (v: number) => v >= 5 && v <= 22;

  if (isLng(val1) && isLat(val2)) {
    return { lng: val1, lat: val2 };
  }
  if (isLat(val1) && isLng(val2)) {
    return { lng: val2, lat: val1 };
  }

  // Fallback assuming [longitude, latitude] if first is larger than second
  if (Math.abs(val1) > Math.abs(val2)) {
    return { lng: val1, lat: val2 };
  }
  return { lng: val2, lat: val1 };
}

export function LocationAutocomplete({
  value,
  onChange,
  onSelect,
  onClear,
  placeholder = "Search for a street or place",
  disabled = false,
  className,
  renderTopOptions,
}: LocationAutocompleteProps) {
  const [suggestions, setSuggestions] = useState<LocationSuggestion[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [highlightIndex, setHighlightIndex] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [dropdownRect, setDropdownRect] = useState<DOMRect | null>(null);

  const updateRect = useCallback(() => {
    if (containerRef.current) {
      setDropdownRect(containerRef.current.getBoundingClientRect());
    }
  }, []);

  useEffect(() => {
    if (isOpen) {
      updateRect();
      window.addEventListener("scroll", updateRect, true); // capture phase to handle inner scrolls
      window.addEventListener("resize", updateRect);
      return () => {
        window.removeEventListener("scroll", updateRect, true);
        window.removeEventListener("resize", updateRect);
      };
    }
  }, [isOpen, updateRect]);

  const fetchSuggestions = useCallback(async (query: string) => {
    const parsedCoords = tryParseCoordinates(query);

    if (query.trim().length < 2) {
      if (parsedCoords) {
        // If coordinate is valid even if query is short, show it
      } else {
        setSuggestions([]);
        setIsOpen(false);
        return;
      }
    }

    setIsSearching(true);
    try {
      const results = await searchLocations(query);
      
      if (parsedCoords) {
        const coordSuggestion: LocationSuggestion = {
          id: `coords-${parsedCoords.lng}-${parsedCoords.lat}`,
          label: `${parsedCoords.lng.toFixed(5)}, ${parsedCoords.lat.toFixed(5)}`,
          displayName: `Coordinates: ${parsedCoords.lng.toFixed(5)}, ${parsedCoords.lat.toFixed(5)}`,
          lng: parsedCoords.lng,
          lat: parsedCoords.lat,
          relevanceScore: 1000,
        };
        // Prepend coordinate suggestion to Nominatim search results
        setSuggestions([coordSuggestion, ...results]);
        setIsOpen(true);
      } else {
        setSuggestions(results);
        setIsOpen(results.length > 0);
      }
      setHighlightIndex(-1);
    } catch {
      if (parsedCoords) {
        const coordSuggestion: LocationSuggestion = {
          id: `coords-${parsedCoords.lng}-${parsedCoords.lat}`,
          label: `${parsedCoords.lng.toFixed(5)}, ${parsedCoords.lat.toFixed(5)}`,
          displayName: `Coordinates: ${parsedCoords.lng.toFixed(5)}, ${parsedCoords.lat.toFixed(5)}`,
          lng: parsedCoords.lng,
          lat: parsedCoords.lat,
          relevanceScore: 1000,
        };
        setSuggestions([coordSuggestion]);
        setIsOpen(true);
      } else {
        setSuggestions([]);
        setIsOpen(false);
      }
    } finally {
      setIsSearching(false);
    }
  }, []);

  const handleInputChange = (newValue: string) => {
    onChange(newValue);
    
    if (debounceRef.current) clearTimeout(debounceRef.current);
    
    debounceRef.current = setTimeout(() => {
      void fetchSuggestions(newValue);
    }, 800);
  };

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current && 
        !containerRef.current.contains(event.target as Node) &&
        !(event.target as HTMLElement).closest('[data-portal="location-autocomplete"]')
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelect = (suggestion: LocationSuggestion) => {
    onChange(suggestion.label);
    onSelect(suggestion);
    setIsOpen(false);
    setSuggestions([]);
    if (debounceRef.current) clearTimeout(debounceRef.current);
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isOpen || suggestions.length === 0) return;

    if (event.key === "ArrowDown") {
      event.preventDefault();
      setHighlightIndex((prev) => (prev < suggestions.length - 1 ? prev + 1 : 0));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setHighlightIndex((prev) => (prev > 0 ? prev - 1 : suggestions.length - 1));
    } else if (event.key === "Enter" && highlightIndex >= 0) {
      event.preventDefault();
      handleSelect(suggestions[highlightIndex]);
    } else if (event.key === "Escape") {
      setIsOpen(false);
    }
  };

  return (
    <div ref={containerRef} className={cn("relative", className)}>
      <div className="relative">
        <Input
          value={value}
          onChange={(e) => handleInputChange(e.target.value)}
          onFocus={() => {
            if (suggestions.length > 0 || renderTopOptions) setIsOpen(true);
          }}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          autoComplete="off"
          className={value || isSearching ? "pr-8" : ""}
        />
        {isSearching ? (
          <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 animate-spin" />
        ) : value ? (
          <button
            type="button"
            onClick={() => {
              if (onClear) onClear();
              else onChange("");
              setSuggestions([]);
              setIsOpen(false);
              if (debounceRef.current) clearTimeout(debounceRef.current);
            }}
            className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        ) : null}
      </div>

      {isOpen && (suggestions.length > 0 || renderTopOptions) && typeof document !== "undefined" && createPortal(
        <ul 
          data-portal="location-autocomplete"
          className="fixed z-[9999] mt-1 overflow-auto rounded-md border border-gray-200 bg-white text-gray-900 shadow-lg"
          style={{
            top: dropdownRect ? dropdownRect.bottom : 0,
            left: dropdownRect ? dropdownRect.left : 0,
            width: dropdownRect ? dropdownRect.width : 0,
            maxHeight: "14rem"
          }}
          onClick={(e) => {
            if ((e.target as HTMLElement).closest("button")) {
              setIsOpen(false);
            }
          }}
        >
          {renderTopOptions}
          {suggestions.map((suggestion, index) => (
            <li key={suggestion.id}>
              <button
                type="button"
                className={cn(
                  "flex w-full items-start gap-2 px-3 py-2 text-left text-sm hover:bg-blue-50 transition-colors",
                  highlightIndex === index && "bg-blue-50"
                )}
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => handleSelect(suggestion)}
              >
                <MapPin className="h-4 w-4 mt-0.5 shrink-0 text-blue-600" />
                <span>
                  <span className="block font-medium text-gray-900">{suggestion.label}</span>
                  <span className="block text-xs text-gray-500 truncate">{suggestion.displayName}</span>
                </span>
              </button>
            </li>
          ))}
        </ul>,
        document.body
      )}
    </div>
  );
}
