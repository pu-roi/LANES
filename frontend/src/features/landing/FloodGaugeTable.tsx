"use client";

import { motion, AnimatePresence } from "framer-motion";
import { FLOOD_DEPTH_OPTIONS, type FloodDepthSpec } from "@/lib/floodDepth";

/* ─── Severity colour tokens ─────────────────────────── */
const SEVERITY_DOT: Record<string, string> = {
  low: "#d8ed34",
  medium: "#f59e0b",
  high: "#f97316",
  extreme: "#dc2626",
};

const SEVERITY_ACTIVE_BG: Record<string, string> = {
  low: "rgba(217,237,52,0.12)",
  medium: "rgba(245,158,11,0.10)",
  high: "rgba(249,115,22,0.10)",
  extreme: "rgba(220,38,38,0.08)",
};

/* ─── Vehicle accessibility badges ───────────────────── */
const ACCESS_BADGE: Record<
  string,
  { label: string; detail: string; className: string }
> = {
  PATV: {
    label: "All Vehicles",
    detail: "Passable to All Types",
    className: "text-green-700 bg-green-50 border-green-200",
  },
  NPLV: {
    label: "Heavy Only",
    detail: "Not Passable to Light Vehicles",
    className: "text-amber-700 bg-amber-50 border-amber-200",
  },
  NPATV: {
    label: "No Vehicles",
    detail: "Not Passable to All Types",
    className: "text-red-700 bg-red-50 border-red-200",
  },
};

/* ─── Component ──────────────────────────────────────── */
interface Props {
  hoveredDepth: string | null;
  onHoverDepth: (depth: string | null) => void;
  /** Called when a row is tapped (mobile scroll-to-silhouette) */
  onActivate?: () => void;
}

export function FloodGaugeTable({
  hoveredDepth,
  onHoverDepth,
  onActivate,
}: Props) {
  const handleClick = (id: string) => {
    onHoverDepth(hoveredDepth === id ? null : id);
    onActivate?.();
  };

  return (
    <div className="space-y-1" role="listbox" aria-label="MMDA Flood Depth Levels">
      {FLOOD_DEPTH_OPTIONS.map((spec: FloodDepthSpec) => {
        const isActive = hoveredDepth === spec.id;
        const access = ACCESS_BADGE[spec.accessibilityClass];

        return (
          <div
            key={spec.id}
            className={`rounded-lg cursor-pointer transition-all duration-200 border-l-[3px] px-3 py-2.5 ${
              isActive ? "shadow-sm" : "border-l-transparent hover:bg-slate-50"
            }`}
            style={
              isActive
                ? {
                    borderLeftColor: SEVERITY_DOT[spec.severity],
                    backgroundColor: SEVERITY_ACTIVE_BG[spec.severity],
                  }
                : undefined
            }
            onMouseEnter={() => onHoverDepth(spec.id)}
            onMouseLeave={() => onHoverDepth(null)}
            onClick={() => handleClick(spec.id)}
            tabIndex={0}
            role="option"
            aria-selected={isActive}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                handleClick(spec.id);
              }
            }}
          >
            {/* Main row: dot + label + depth */}
            <div className="flex items-center gap-2.5">
              <div
                className="w-2.5 h-2.5 rounded-full shrink-0 shadow-sm"
                style={{ backgroundColor: SEVERITY_DOT[spec.severity] }}
              />
              <span className="font-semibold text-sm text-gray-800">
                {spec.label}
              </span>
              <span className="text-xs text-gray-500 tabular-nums ml-auto whitespace-nowrap">
                {spec.formatted}
              </span>
            </div>

            {/* Expandable detail: vehicle access badge */}
            <AnimatePresence>
              {isActive && access && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.15 }}
                  className="overflow-hidden"
                >
                  <div className="flex items-center gap-2 pt-2 pl-5">
                    <span
                      className={`text-[10px] font-medium px-2 py-0.5 rounded-md border ${access.className}`}
                    >
                      {access.label}
                    </span>
                    <span className="text-[10px] text-gray-400">
                      {access.detail}
                    </span>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        );
      })}
    </div>
  );
}
