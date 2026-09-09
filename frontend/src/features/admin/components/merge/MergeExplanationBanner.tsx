"use client";

import React from "react";
import { Sparkles, Users, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface MergeExplanationBannerProps {
  matchScore: number;
  matchReasons: string[];
  isCrowdConsensus?: boolean;
}

export function MergeExplanationBanner({
  matchScore,
  matchReasons,
  isCrowdConsensus = false,
}: MergeExplanationBannerProps) {
  const getScoreColor = (score: number) => {
    if (score >= 85) return "text-emerald-700 bg-emerald-50 border-emerald-200";
    if (score >= 65) return "text-blue-700 bg-blue-50 border-blue-200";
    return "text-amber-700 bg-amber-50 border-amber-200";
  };

  return (
    <div className="flex flex-wrap items-center gap-1.5 py-1">
      {/* Match Score Badge */}
      <span className={cn(
        "text-[11px] font-bold px-2.5 py-0.5 rounded-full border flex items-center gap-1 shrink-0",
        getScoreColor(matchScore)
      )}>
        <Sparkles className="w-3 h-3" />
        {matchScore}% Match
      </span>

      {/* Crowd Consensus Tag */}
      {isCrowdConsensus && (
        <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full border bg-purple-50 text-purple-700 border-purple-200 flex items-center gap-1 shrink-0">
          <Users className="w-3 h-3" />
          Crowd Consensus
        </span>
      )}

      {/* Match Reason Pills */}
      {matchReasons.map((reason, i) => (
        <span 
          key={i} 
          className="text-[10px] text-slate-600 bg-slate-100/90 border border-slate-200/80 px-2 py-0.5 rounded-md font-medium"
        >
          {reason}
        </span>
      ))}
    </div>
  );
}
