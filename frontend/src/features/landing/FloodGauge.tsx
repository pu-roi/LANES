"use client";

import { useState, useRef } from "react";
import { Info } from "lucide-react";
import { FloodGaugeTable } from "./FloodGaugeTable";
import { FloodGaugeSilhouette } from "./FloodGaugeSilhouette";

export function FloodGauge() {
  const [hoveredDepth, setHoveredDepth] = useState<string | null>(null);
  const silhouetteContainerRef = useRef<HTMLDivElement>(null);

  const handleActivate = () => {
    if (typeof window !== "undefined" && window.innerWidth < 1024 && silhouetteContainerRef.current) {
      silhouetteContainerRef.current.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
      });
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 sm:p-7 w-full flex flex-col">
      {/* Header Info */}
      <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-gray-100 pb-4">
        <div>
          <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
            MMDA Flood Depth & Vehicle Clearance
          </h3>
          <p className="text-xs text-gray-500 mt-1 leading-relaxed">
            <span className="hidden sm:inline">Hover over</span>
            <span className="sm:hidden">Tap</span> any flood depth level to visualize water height on the reference figure and check passability.
          </p>
        </div>
        <div className="flex items-center gap-1.5 text-[11px] text-gray-400 self-start sm:self-auto bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-100">
          <Info className="w-3.5 h-3.5 text-blue-500 shrink-0" />
          <span>Interactive Visual Gauge</span>
        </div>
      </div>

      {/* Split View: Table on Left, Silhouette on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-8 items-start">
        {/* Left: Interactive Table (7 cols on desktop) */}
        <div className="lg:col-span-7 w-full">
          <div className="mb-2 flex items-center justify-between text-[11px] font-semibold text-gray-400 uppercase tracking-wider px-3">
            <span>Flood Level</span>
            <span>Depth (Inches / Metric)</span>
          </div>
          <FloodGaugeTable
            hoveredDepth={hoveredDepth}
            onHoverDepth={setHoveredDepth}
            onActivate={handleActivate}
          />
        </div>

        {/* Right: Silhouette Gauge (5 cols on desktop) */}
        <div
          ref={silhouetteContainerRef}
          className="lg:col-span-5 w-full flex flex-col items-center justify-center bg-slate-50/60 rounded-xl p-4 sm:p-5 border border-slate-100"
        >
          <FloodGaugeSilhouette hoveredDepth={hoveredDepth} />
        </div>
      </div>
    </div>
  );
}
