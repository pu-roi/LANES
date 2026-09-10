"use client";

import React, { useState } from "react";
import { LocationInputGroup } from "@/shared/ui";
import { getCurrentLocation } from "@/features/geocoding/geocodingApi";
import { useMapContext, type ActivePoint } from "@/features/map/MapContext";
import { useToast } from "@/shared/ui";

interface RoadSegmentPickerProps {
  isBidirectional: boolean;
  onBidirectionalChange: (val: boolean) => void;
  onStartChange?: (label: string) => void;
  onEndChange?: (label: string) => void;
}

export function RoadSegmentPicker({
  isBidirectional,
  onBidirectionalChange,
  onStartChange,
  onEndChange,
}: RoadSegmentPickerProps) {
  const { error } = useToast();
  const {
    floodStart,
    floodEnd,
    activePoint,
    setActivePoint,
    setIsPickingOnMap,
    setFloodStart,
    setFloodEnd,
    setFloodStartLabel,
    setFloodEndLabel,
  } = useMapContext();

  const [startDraft, setStartDraft] = useState("");
  const [endDraft, setEndDraft] = useState("");
  const startInput = floodStart?.label ?? startDraft;
  const endInput = floodEnd?.label ?? endDraft;

  const handleUseCurrent = async (target: ActivePoint) => {
    try {
      const coords = await getCurrentLocation();
      const label = "Current Location";
      if (target === "start" || target === "flood_start") {
        setFloodStart(coords, label);
        setStartDraft(label);
        setActivePoint("flood_end");
        setIsPickingOnMap(false);
        if (onStartChange) onStartChange(label);
      } else if (target === "end" || target === "flood_end") {
        setFloodEnd(coords, label);
        setEndDraft(label);
        setActivePoint(null);
        setIsPickingOnMap(false);
        if (onEndChange) onEndChange(label);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Unable to retrieve current location";
      error("Location Error", message);
    }
  };

  const handleSwap = () => {
    if (!floodStart || !floodEnd) return;

    const previousStart = floodStart;
    const previousEnd = floodEnd;
    setFloodStart(previousEnd.coords, previousEnd.label);
    setFloodEnd(previousStart.coords, previousStart.label);
    setStartDraft(previousEnd.label);
    setEndDraft(previousStart.label);
    setActivePoint(null);
    setIsPickingOnMap(false);
    onStartChange?.(previousEnd.label);
    onEndChange?.(previousStart.label);
  };

  return (
    <div className="space-y-4">
      <LocationInputGroup
        startInput={startInput}
        setStartInput={(val) => {
          setStartDraft(val);
          setFloodStartLabel(val);
          setIsPickingOnMap(false);
        }}
        endInput={endInput}
        setEndInput={(val) => {
          setEndDraft(val);
          setFloodEndLabel(val);
          setIsPickingOnMap(false);
        }}
        activePoint={activePoint}
        setActivePoint={setActivePoint}
        startPointId="flood_start"
        endPointId="flood_end"
        onStartSelect={(s) => {
          setFloodStart([s.lng, s.lat], s.label);
          setStartDraft(s.label);
          setActivePoint("flood_end");
          setIsPickingOnMap(false);
          if (onStartChange) onStartChange(s.label);
        }}
        onEndSelect={(s) => {
          setFloodEnd([s.lng, s.lat], s.label);
          setEndDraft(s.label);
          setActivePoint(null);
          setIsPickingOnMap(false);
          if (onEndChange) onEndChange(s.label);
        }}
        onStartClear={() => {
          setFloodStart(null);
          setStartDraft("");
          setFloodStartLabel("");
          setActivePoint("flood_start");
          setIsPickingOnMap(false);
        }}
        onEndClear={() => {
          setFloodEnd(null);
          setEndDraft("");
          setFloodEndLabel("");
          setActivePoint("flood_end");
          setIsPickingOnMap(false);
        }}
        onStartChange={(val) => {
          setFloodStartLabel(val);
          if (onStartChange) onStartChange(val);
        }}
        onEndChange={(val) => {
          setFloodEndLabel(val);
          if (onEndChange) onEndChange(val);
        }}
        onPickOnMap={(target) => {
          setActivePoint(target as ActivePoint);
          setIsPickingOnMap(true);
        }}
        canSwap={Boolean(floodStart && floodEnd)}
        onSwap={handleSwap}
        onUseCurrentLocation={handleUseCurrent}
        startPlaceholder="e.g. Ortigas Ave, Pasig (Start)"
        endPlaceholder="e.g. C. Raymundo Ave (End)"
      />

      {/* Bidirectional Toggle for Line Mode */}
      <div
        className="flex items-start gap-2.5 px-3 py-2.5 rounded-xl border border-slate-200 bg-slate-50/70 hover:bg-slate-50 transition-colors cursor-pointer group select-none"
        onClick={() => onBidirectionalChange(!isBidirectional)}
      >
        <div className="flex h-5 items-center mt-0.5">
          <input
            type="checkbox"
            id="isBidirectionalZone"
            checked={isBidirectional}
            onChange={(e) => onBidirectionalChange(e.target.checked)}
            className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
        <div className="flex flex-col">
          <label htmlFor="isBidirectionalZone" className="text-xs font-semibold text-slate-800 cursor-pointer">
            Both directions affected
          </label>
          <span className="text-[11px] text-slate-500">
            Automatically applies avoidance to opposite carriageways or 2-way traffic
          </span>
        </div>
      </div>
    </div>
  );
}
