"use client";

import React from "react";
import { createPortal } from "react-dom";
import { Route, Hexagon, Pencil, Square, Circle, Crosshair, X } from "lucide-react";
import { Tabs } from "@/shared/ui";
import type { GeometryMode } from "../types";

interface GeometryModeSelectorProps {
  geometryMode: GeometryMode;
  onChange: (mode: GeometryMode) => void;
  isDrawingMode: boolean;
  onCancelDrawing: () => void;
}

export function GeometryModeSelector({
  geometryMode,
  onChange,
  isDrawingMode,
  onCancelDrawing,
}: GeometryModeSelectorProps) {
  const mapInstructionRoot = typeof document === "undefined"
    ? null
    : document.getElementById("admin-map-drawing-instruction-root");

  const drawingInstruction = (
    <div className="absolute bottom-6 left-1/2 z-50 -translate-x-1/2 pointer-events-auto animate-in fade-in slide-in-from-bottom-3 duration-200">
      <div className="flex items-center gap-3 rounded-full border border-gray-200/90 bg-white/95 px-4 py-2.5 text-gray-800 shadow-2xl ring-1 ring-black/5 backdrop-blur-md">
        <div className="flex items-center justify-center rounded-full bg-blue-50 p-1.5 text-blue-600">
          <Crosshair className="w-4 h-4 animate-pulse" />
        </div>
        <div className="flex flex-col">
          <span className="text-xs font-bold text-gray-900 capitalize">
            Drawing {geometryMode}
          </span>
          <span className="text-[11px] text-gray-500 font-medium">
            {geometryMode === "freehand"
              ? "Click & drag on the map to draw"
              : geometryMode === "circle"
              ? "Click center & drag radius to draw"
              : "Click on map to place points. Double-click to finish."}
          </span>
        </div>
        <button
          type="button"
          onClick={onCancelDrawing}
          className="ml-2 rounded-full p-1.5 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-700"
          title="Cancel drawing"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );

  return (
    <>
      <Tabs<GeometryMode>
        tabs={[
          { id: "line", label: "Line", icon: Route },
          { id: "polygon", label: "Polygon", icon: Hexagon },
          { id: "freehand", label: "Freehand", icon: Pencil },
          { id: "rectangle", label: "Rect", icon: Square },
          { id: "circle", label: "Circle", icon: Circle },
        ]}
        activeTab={geometryMode}
        onChange={onChange}
        variant="segmented"
        fullWidth
        layoutId="official-zone-geometry-mode-tab"
        className="mb-4 bg-slate-100 p-1"
        tabClassName="py-2 px-1 gap-1 text-[10px] font-semibold min-w-0"
      />

      {isDrawingMode && mapInstructionRoot && createPortal(drawingInstruction, mapInstructionRoot)}
    </>
  );
}
