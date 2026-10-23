"use client";

import React from "react";
import { Check, ShieldAlert, TrendingDown, Info } from "lucide-react";
import type { MergeConflict } from "../../adminApi";

interface ConflictResolutionNoticeProps {
  conflicts: MergeConflict[];
  onResolveConflict?: (field: string, value: unknown) => void;
}

export function ConflictResolutionNotice({
  conflicts,
  onResolveConflict,
}: ConflictResolutionNoticeProps) {
  if (!conflicts || conflicts.length === 0) return null;

  const hasRecedingTrend = conflicts.some((c) => c.conflict_type === "receding_trend");

  return (
    <div className="space-y-2 text-left">
      {hasRecedingTrend && (
        <div className="rounded-xl border border-blue-200 bg-blue-50/90 p-3">
          <div className="mb-1.5 flex items-center gap-2 text-xs font-semibold text-blue-900">
            <TrendingDown className="h-4 w-4 shrink-0 text-blue-600" />
            <span>Receding Flood Trend Detected</span>
          </div>
          <p className="text-[11px] leading-relaxed text-blue-700">
            A later corroborating report indicates lower floodwaters than the earlier peak. Review whether floodwaters are actively subsiding before publishing.
          </p>
        </div>
      )}

      <div className="rounded-xl border border-amber-200 bg-amber-50/90 p-3">
        <div className="mb-2 flex items-center gap-2 text-xs font-semibold text-amber-800">
          <ShieldAlert className="h-4 w-4 shrink-0 text-amber-600" />
          <span>Attribute Discrepancies Detected ({conflicts.length})</span>
        </div>

        <div className="space-y-1.5">
          {conflicts.map((conflict, i) => {
            const isReceding = conflict.conflict_type === "receding_trend";
            return (
              <div
                key={i}
                className={`flex items-center justify-between gap-2 rounded-lg border px-2.5 py-1.5 text-[11px] ${
                  isReceding
                    ? "border-blue-200 bg-blue-50/60"
                    : "border-amber-100/80 bg-white/80"
                }`}
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-1.5">
                    <span className="mr-1 font-semibold capitalize text-slate-700">
                      {conflict.field.replace(/_/g, " ")}:
                    </span>
                    {isReceding && (
                      <span className="inline-flex items-center rounded-full bg-blue-100 px-1.5 py-0.2 text-[9px] font-bold text-blue-700">
                        Receding
                      </span>
                    )}
                  </div>
                  <span className="truncate text-slate-600">{conflict.message}</span>
                </div>

                {conflict.suggested_value != null && onResolveConflict && (
                  <button
                    type="button"
                    onClick={() => onResolveConflict(conflict.field, conflict.suggested_value)}
                    className={`flex shrink-0 items-center gap-1 rounded px-2 py-0.5 text-[10px] font-semibold transition-colors ${
                      isReceding
                        ? "bg-blue-100 text-blue-800 hover:bg-blue-200"
                        : "bg-amber-100 text-amber-800 hover:bg-amber-200"
                    }`}
                  >
                    <Check className="h-3 w-3" />
                    Use {String(conflict.suggested_value)}
                  </button>
                )}
              </div>
            );
          })}
        </div>
        <p className="mt-2 text-[10px] font-medium text-amber-600/90">
          Safety-first protocol: Peak severity and deeper gauges are suggested by default, unless a receding trend is verified.
        </p>
      </div>
    </div>
  );
}
