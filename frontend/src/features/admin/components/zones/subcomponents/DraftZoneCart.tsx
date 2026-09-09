"use client";

import React from "react";
import { Layers, Trash2, MapPin, Route, Hexagon } from "lucide-react";
import { Button } from "@/shared/ui";
import type { ZoneDraftItem } from "../types";
import { SEVERITY_COLORS } from "../types";

interface DraftZoneCartProps {
  drafts: ZoneDraftItem[];
  onRemoveDraft: (id: string) => void;
  onClearDrafts: () => void;
}

export function DraftZoneCart({
  drafts,
  onRemoveDraft,
  onClearDrafts,
}: DraftZoneCartProps) {
  if (drafts.length === 0) return null;

  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50/50 p-3 space-y-2.5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-blue-600" />
          <span className="text-xs font-bold text-slate-800">
            Draft Queue ({drafts.length})
          </span>
        </div>
        <button
          type="button"
          onClick={onClearDrafts}
          className="text-[11px] font-medium text-slate-400 hover:text-red-600 transition-colors"
        >
          Clear all
        </button>
      </div>

      <div className="space-y-2 max-h-48 overflow-y-auto pr-1 divide-y divide-slate-100">
        {drafts.map((draft, idx) => {
          const isPolygon = draft.geometry?.type === "Polygon" || draft.geometry?.type === "MultiPolygon";
          const severityTheme = SEVERITY_COLORS[draft.severity] || SEVERITY_COLORS.low;

          return (
            <div key={draft.id} className="pt-2 first:pt-0 flex items-center justify-between gap-2">
              <div className="flex items-center gap-2 min-w-0">
                <div className="w-6 h-6 rounded-lg bg-white border border-slate-200 flex items-center justify-center shrink-0">
                  {isPolygon ? (
                    <Hexagon className="w-3.5 h-3.5 text-blue-600" />
                  ) : (
                    <Route className="w-3.5 h-3.5 text-blue-600" />
                  )}
                </div>
                <div className="min-w-0">
                  <div className="text-xs font-semibold text-slate-800 truncate">
                    {draft.name || (isPolygon ? `Drawn Hazard #${idx + 1}` : draft.startLabel || `Zone #${idx + 1}`)}
                  </div>
                  <div className="flex items-center gap-1.5 mt-0.5">
                    <span className={`text-[10px] font-bold px-1.5 py-0.2 rounded-full border ${severityTheme.pill}`}>
                      {draft.severity.toUpperCase()}
                    </span>
                    {draft.depth && (
                      <span className="text-[10px] text-slate-500 font-medium">
                        {draft.depth}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              <Button
                variant="ghost"
                size="sm"
                onClick={() => onRemoveDraft(draft.id)}
                className="h-7 w-7 p-0 text-slate-400 hover:text-red-600 rounded-lg shrink-0"
                title="Remove draft"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </Button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
