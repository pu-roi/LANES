"use client";

import React from "react";
import { AlertTriangle, Check, ShieldAlert } from "lucide-react";
import type { MergeConflict } from "../../adminApi";

interface ConflictResolutionNoticeProps {
  conflicts: MergeConflict[];
  onResolveConflict?: (field: string, value: any) => void;
}

export function ConflictResolutionNotice({
  conflicts,
  onResolveConflict,
}: ConflictResolutionNoticeProps) {
  if (!conflicts || conflicts.length === 0) return null;

  return (
    <div className="bg-amber-50/90 border border-amber-200 rounded-xl p-3 text-left">
      <div className="flex items-center gap-2 text-amber-800 text-xs font-semibold mb-2">
        <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0" />
        <span>Attribute Discrepancies Detected ({conflicts.length})</span>
      </div>

      <div className="space-y-1.5">
        {conflicts.map((conflict, i) => (
          <div 
            key={i} 
            className="flex items-center justify-between gap-2 text-[11px] bg-white/80 border border-amber-100/80 rounded-lg px-2.5 py-1.5"
          >
            <div className="min-w-0 flex-1">
              <span className="font-semibold text-slate-700 capitalize mr-1.5">
                {conflict.field.replace(/_/g, " ")}:
              </span>
              <span className="text-slate-600 truncate">{conflict.message}</span>
            </div>

            {conflict.suggested_value && onResolveConflict && (
              <button
                type="button"
                onClick={() => onResolveConflict(conflict.field, conflict.suggested_value)}
                className="shrink-0 bg-amber-100 text-amber-800 hover:bg-amber-200 font-semibold px-2 py-0.5 rounded text-[10px] transition-colors flex items-center gap-1"
              >
                <Check className="w-3 h-3" />
                Use {String(conflict.suggested_value)}
              </button>
            )}
          </div>
        ))}
      </div>
      <p className="text-[10px] text-amber-600/90 mt-2 font-medium">
        Safety-first protocol: Higher severity and deeper gauges are suggested by default.
      </p>
    </div>
  );
}
