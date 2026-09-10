"use client";

import React from "react";
import { cn } from "@/lib/utils";
import type { ReportGeometry } from "../adminApi";

// ── Shared types ─────────────────────────────────────────────────────────────

export interface ZoneDataEditorValues {
  name?: string;
  severity: "low" | "medium" | "high" | "extreme";
  depth: string;
  passable_vehicles: string[];
  hidden_hazards: string;
  is_bidirectional: boolean;
  geometry: ReportGeometry;
  admin_notes: string;
  merge_rationale?: string;
  buffer_radius?: number;
}

interface ZoneDataEditorFormProps {
  initialValues: Partial<ZoneDataEditorValues>;
  onChange: (values: ZoneDataEditorValues) => void;
  readOnlyGeometry?: boolean;
  /** When true, hides the bidirectional toggle (RoadSegmentPicker handles it in line mode) */
  hideBidirectional?: boolean;
  /** When true, hides survey fields (passable vehicles + hidden hazards) — rendered as own section in parent */
  hideSurvey?: boolean;
  /** When true, hides the Description textarea — rendered as own section in parent */
  hideDescription?: boolean;
}

// ── Shared constants (exported so OfficialZoneDrawer can reuse them) ──────────

type DepthOption = {
  id: string;
  severity: "low" | "medium" | "high" | "extreme";
  label: string;
  description: string;
};

const VISUAL_OPTIONS: DepthOption[] = [
  { id: "gutter",    severity: "low",     label: "Gutter",       description: "8 inches" },
  { id: "half-knee", severity: "low",     label: "Half-Knee",    description: "10 inches" },
  { id: "half-tire", severity: "medium",  label: "Half-Tire",    description: "13 inches" },
  { id: "knee",      severity: "medium",  label: "Knee",         description: "19 inches" },
  { id: "tires",     severity: "high",    label: "Tires",        description: "26 inches" },
  { id: "waist",     severity: "high",    label: "Waist",        description: "37 inches" },
  { id: "chest",     severity: "high",    label: "Chest",        description: "45 inches" },
  { id: "neck",      severity: "extreme", label: "Neck & Above", description: "Danger" },
];

const SEVERITY_COLORS: Record<string, { pill: string; active: string }> = {
  low:     { pill: "border-lime-300 text-lime-700 bg-lime-50 hover:bg-lime-100",         active: "border-lime-400 bg-lime-100 text-lime-800 ring-2 ring-lime-300/50" },
  medium:  { pill: "border-amber-300 text-amber-700 bg-amber-50 hover:bg-amber-100",     active: "border-amber-400 bg-amber-100 text-amber-800 ring-2 ring-amber-300/50" },
  high:    { pill: "border-orange-300 text-orange-700 bg-orange-50 hover:bg-orange-100", active: "border-orange-400 bg-orange-100 text-orange-800 ring-2 ring-orange-300/50" },
  extreme: { pill: "border-red-300 text-red-700 bg-red-50 hover:bg-red-100",             active: "border-red-400 bg-red-100 text-red-800 ring-2 ring-red-300/50" },
};

const SEVERITY_DOT_COLORS: Record<string, string> = {
  low:     "bg-[#d8ed34]",
  medium:  "bg-amber-400",
  high:    "bg-orange-500",
  extreme: "bg-red-600",
};

export const VEHICLE_OPTIONS = [
  { id: "walk",        label: "Pedestrians" },
  { id: "bicycle",    label: "Bicycles / E-Bikes" },
  { id: "motorcycle", label: "Motorcycles" },
  { id: "light",      label: "Sedans / Hatchbacks" },
  { id: "suv",        label: "SUVs / Pickups" },
  { id: "heavy",      label: "Large Trucks / Buses" },
];

export const HAZARD_OPTIONS = [
  { value: "yes",    label: "Yes",    activeClass: "bg-red-50 border-red-300 text-red-700" },
  { value: "no",     label: "No",     activeClass: "bg-green-50 border-green-300 text-green-700" },
  { value: "unsure", label: "Unsure", activeClass: "bg-gray-100 border-gray-300 text-gray-700" },
];

// ── Component ────────────────────────────────────────────────────────────────

export function ZoneDataEditorForm({
  initialValues,
  onChange,
  hideBidirectional = false,
  hideSurvey = false,
  hideDescription = false,
}: ZoneDataEditorFormProps) {
  const selectedOption = VISUAL_OPTIONS.find(o => o.id === initialValues.depth) ?? VISUAL_OPTIONS[3];
  const values: ZoneDataEditorValues = {
    name: initialValues.name || "Official Flood Avoidance Zone",
    severity: selectedOption.severity,
    depth: selectedOption.id,
    passable_vehicles: initialValues.passable_vehicles || [],
    hidden_hazards: initialValues.hidden_hazards || "unsure",
    is_bidirectional: initialValues.is_bidirectional || false,
    geometry: initialValues.geometry || { type: "LineString", coordinates: [] },
    admin_notes: initialValues.admin_notes || "",
    merge_rationale: initialValues.merge_rationale,
    buffer_radius: initialValues.buffer_radius,
  };

  const updateValues = (updates: Partial<ZoneDataEditorValues>) => {
    onChange({ ...values, ...updates });
  };

  return (
    <div className="space-y-4 text-left">

      {/* ── Flood Depth Visual Picker (auto-derives severity) ── */}
      <div>
        <label className="text-xs font-semibold text-slate-700 block mb-1.5">
          Flood Depth & Severity <span className="text-red-500">*</span>
        </label>
        <div className="grid grid-cols-4 gap-1.5">
          {VISUAL_OPTIONS.map((opt) => {
            const colors = SEVERITY_COLORS[opt.severity];
            return (
              <button
                key={opt.id}
                type="button"
                onClick={() => updateValues({ depth: opt.id, severity: opt.severity })}
                className={cn(
                  "flex flex-col items-center gap-0.5 rounded-lg border px-1.5 py-2 text-xs font-semibold transition-all",
                  selectedOption.id === opt.id ? colors.active : colors.pill
                )}
              >
                <div className={cn("w-3.5 h-3.5 rounded-sm mb-0.5 shadow-sm shadow-black/10", SEVERITY_DOT_COLORS[opt.severity])} />
                <span>{opt.label}</span>
                <span className="font-normal text-[10px] opacity-75">{opt.description}</span>
              </button>
            );
          })}
        </div>
        <p className="text-[10px] text-slate-400 mt-1">
          Severity is automatically set based on depth:{" "}
          <span className="font-semibold capitalize text-slate-500">{selectedOption.severity}</span>
        </p>
      </div>

      {/* ── Bidirectional Toggle ── */}
      {!hideBidirectional && (
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 flex items-center justify-between gap-3">
          <div>
            <span className="text-xs font-semibold text-slate-800 block">
              Affects Both Road Directions (2-Way)
            </span>
            <span className="text-[11px] text-slate-500 block leading-snug">
              Applies hazard avoidance to opposing carriageway lane.
            </span>
          </div>
          <button
            type="button"
            onClick={() => updateValues({ is_bidirectional: !values.is_bidirectional })}
            className={cn(
              "w-11 h-6 rounded-full transition-colors relative shrink-0 p-0.5 border",
              values.is_bidirectional ? "bg-blue-600 border-blue-700" : "bg-slate-200 border-slate-300"
            )}
          >
            <div className={cn(
              "w-5 h-5 rounded-full bg-white transition-transform shadow-xs",
              values.is_bidirectional ? "translate-x-5" : "translate-x-0"
            )} />
          </button>
        </div>
      )}



      {/* ── Survey: vehicles + hidden hazards (shown when hideSurvey is false, e.g. in MergeWorkspacePanel) ── */}
      {!hideSurvey && (
        <>
          <div>
            <label className="text-xs font-semibold text-slate-700 block mb-1">
              Which vehicles can safely pass? <span className="text-red-500">*</span>
            </label>
            <p className="text-[11px] text-slate-400 mb-2">Select all that apply.</p>
            <div className="grid grid-cols-2 gap-2">
              {VEHICLE_OPTIONS.map((v) => {
                const isChecked = values.passable_vehicles.includes(v.id);
                return (
                  <label
                    key={v.id}
                    className={cn(
                      "flex items-center gap-2 rounded-lg border p-2 cursor-pointer transition-colors",
                      isChecked ? "border-blue-400 bg-blue-50" : "border-slate-200 hover:bg-slate-50"
                    )}
                  >
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={(e) => {
                        if (e.target.checked) {
                          updateValues({ passable_vehicles: [...values.passable_vehicles, v.id] });
                        } else {
                          updateValues({ passable_vehicles: values.passable_vehicles.filter(x => x !== v.id) });
                        }
                      }}
                      className="w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500 focus:ring-2"
                    />
                    <span className={cn("text-xs font-medium", isChecked ? "text-blue-900" : "text-slate-700")}>
                      {v.label}
                    </span>
                  </label>
                );
              })}
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-700 block mb-1">
              Are there hidden hazards? <span className="text-red-500">*</span>
            </label>
            <p className="text-[11px] text-slate-400 mb-2">E.g., open manholes, large debris underwater.</p>
            <div className="grid grid-cols-3 gap-2">
              {HAZARD_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => updateValues({ hidden_hazards: opt.value })}
                  className={cn(
                    "rounded-lg border py-2 text-xs font-semibold transition-colors",
                    values.hidden_hazards === opt.value
                      ? opt.activeClass
                      : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
                  )}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        </>
      )}

      {/* ── Description (shown when hideDescription is false, e.g. in MergeWorkspacePanel) ── */}
      {!hideDescription && (
        <div>
          <label className="text-xs font-semibold text-slate-700 block mb-1">
            Description
          </label>
          <textarea
            value={values.admin_notes}
            onChange={(e) => updateValues({ admin_notes: e.target.value })}
            placeholder="e.g., Pumping truck stationed on westbound lane. Detour all light vehicles via Shaw Blvd."
            rows={2}
            className="w-full text-xs p-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 resize-none font-medium text-slate-800"
          />
        </div>
      )}

    </div>
  );
}
