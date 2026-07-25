"use client";

import { Info } from "lucide-react";

export function FloodLegend() {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 w-full h-full flex flex-col">
      <div className="mb-6">
        <h3 className="text-sm font-semibold text-gray-800 mb-2">Flood Severity Zones</h3>
        <p className="text-xs text-gray-500 leading-relaxed">
          These colors represent flood zones on the map. The severity determines which vehicles can safely pass.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 flex-1">
        {/* Low Severity */}
        <div className="bg-[#fbfcdd]/50 border border-[#d8ed34]/50 rounded-xl p-4 flex flex-col justify-center">
          <div className="flex items-center gap-2 mb-1.5">
            <div className="w-3.5 h-3.5 rounded-full bg-[#d8ed34] shrink-0 shadow-sm border border-[#c2d62f]"></div>
            <span className="font-semibold text-lime-900 text-sm">Low (Yellow-Green)</span>
            <span className="text-[10px] text-lime-900 font-bold ml-auto px-2 py-0.5 bg-[#d8ed34]/30 rounded-md">Gutter to Half-Knee</span>
          </div>
          <p className="text-xs text-lime-900/90 leading-snug">
            8 - 10 inches. Passable by all vehicles, motorcycles, and pedestrians.
          </p>
        </div>

        {/* Medium Severity */}
        <div className="bg-amber-50/50 border border-amber-300/60 rounded-xl p-4 flex flex-col justify-center">
          <div className="flex items-center gap-2 mb-1.5">
            <div className="w-3.5 h-3.5 rounded-full bg-amber-400 shrink-0 shadow-sm border border-amber-500"></div>
            <span className="font-semibold text-amber-900 text-sm">Medium (Amber)</span>
            <span className="text-[10px] text-amber-900 font-bold ml-auto px-2 py-0.5 bg-amber-200/60 rounded-md">Half-Tire to Knee</span>
          </div>
          <p className="text-xs text-amber-900/90 leading-snug">
            13 - 19 inches. Passable by 4-Wheel High Clearance (SUVs) & Low Clearance (Sedans).
          </p>
        </div>

        {/* High Severity */}
        <div className="bg-orange-50/50 border border-orange-300/60 rounded-xl p-4 flex flex-col justify-center">
          <div className="flex items-center gap-2 mb-1.5">
            <div className="w-3.5 h-3.5 rounded-full bg-orange-500 shrink-0 shadow-sm border border-orange-600"></div>
            <span className="font-semibold text-orange-900 text-sm">High (Orange)</span>
            <span className="text-[10px] text-orange-900 font-bold ml-auto px-2 py-0.5 bg-orange-200/60 rounded-md">Tires to Chest</span>
          </div>
          <p className="text-xs text-orange-900/90 leading-snug">
            26 - 45 inches. Only passable by 4-Wheel High Clearance (SUVs, Pickups).
          </p>
        </div>

        {/* Extreme Severity */}
        <div className="bg-red-50/50 border border-red-300/60 rounded-xl p-4 flex flex-col justify-center">
          <div className="flex items-center gap-2 mb-1.5">
            <div className="w-3.5 h-3.5 rounded-full bg-red-600 shrink-0 shadow-sm border border-red-700"></div>
            <span className="font-semibold text-red-900 text-sm">Extreme (Red)</span>
            <span className="text-[10px] text-red-900 font-bold ml-auto px-2 py-0.5 bg-red-200/60 rounded-md">Neck & Above</span>
          </div>
          <p className="text-xs text-red-900/90 leading-snug">
            Danger. Impassable for all standard vehicles. Seek alternative routes.
          </p>
        </div>
      </div>
    </div>
  );
}
