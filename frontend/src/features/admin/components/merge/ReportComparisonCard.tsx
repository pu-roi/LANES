"use client";

import React from "react";
import { formatDistanceToNow } from "date-fns";
import { MapPin, Clock, UserCheck } from "lucide-react";
import { cn } from "@/lib/utils";
import type { FloodReport, MergeCandidateItem } from "../../adminApi";
import { MergeExplanationBanner } from "./MergeExplanationBanner";

interface ReportComparisonCardProps {
  report: FloodReport | MergeCandidateItem;
  isPrimary?: boolean;
  isSelected?: boolean;
  onToggleSelect?: () => void;
  badgeLabel?: string;
  matchScore?: number;
  matchReasons?: string[];
  isCrowdConsensus?: boolean;
}

const SEVERITY_BADGES: Record<string, string> = {
  low: "bg-lime-50 text-lime-700 border-lime-200",
  medium: "bg-amber-50 text-amber-700 border-amber-200",
  high: "bg-orange-50 text-orange-700 border-orange-200",
  extreme: "bg-red-50 text-red-700 border-red-200",
};

export function ReportComparisonCard({
  report,
  isPrimary = false,
  isSelected = false,
  onToggleSelect,
  badgeLabel,
  matchScore,
  matchReasons = [],
  isCrowdConsensus = false,
}: ReportComparisonCardProps) {
  const reportId = "id" in report ? report.id : report.report_id;
  const rawText = report.raw_text;
  const severity = (report.severity || "medium").toLowerCase();
  const depth = report.depth;
  const mediaUrls = report.media_urls || [];
  
  // Extract surveyor details
  const passableVehicles = "survey" in report 
    ? report.survey?.passable_vehicles 
    : report.passable_vehicles;
  const hiddenHazards = "survey" in report 
    ? report.survey?.hidden_hazards 
    : report.hidden_hazards;
  const reporterName = report.reporter_name || report.reporter_username || "Citizen";
  const trustScore = report.reporter_trust_score;
  const createdAt = "created_at" in report ? report.created_at : report.reported_at;

  const timeAgo = createdAt 
    ? formatDistanceToNow(new Date(createdAt), { addSuffix: true }) 
    : "Recently";

  return (
    <article
      className={cn(
        "relative rounded-xl border p-3.5 text-left transition-all duration-150",
        isPrimary 
          ? "border-blue-200 bg-blue-50/40"
          : isSelected 
            ? "border-violet-400 bg-violet-50/50 ring-2 ring-violet-200/70"
            : "border-slate-200 bg-white hover:border-slate-300 hover:shadow-sm"
      )}
    >
      {/* Header Bar */}
      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-1.5 min-w-0">
          <span className={cn(
            "text-[10px] font-bold px-2 py-0.5 rounded-full border uppercase tracking-wider shrink-0",
            isPrimary 
              ? "bg-blue-600 text-white border-blue-700"
              : "bg-slate-100 text-slate-700 border-slate-200"
          )}>
            {isPrimary ? "Primary Base Report" : badgeLabel || `Report #${reportId}`}
          </span>

          <span className={cn(
            "text-[10px] font-bold px-2 py-0.5 rounded-full border capitalize shrink-0",
            SEVERITY_BADGES[severity] || SEVERITY_BADGES.medium
          )}>
            {severity}
          </span>
        </div>

        {!isPrimary && onToggleSelect && (
          <label
            className={cn(
              "flex shrink-0 cursor-pointer items-center gap-2 text-xs font-bold transition-colors",
              isSelected
                ? "text-violet-800"
                : "text-slate-700 hover:text-violet-700"
            )}
          >
            <input
              type="checkbox"
              checked={isSelected}
              onChange={onToggleSelect}
              className="h-5 w-5 shrink-0 cursor-pointer rounded border-2 border-slate-400 text-violet-600 accent-violet-600 focus:ring-2 focus:ring-violet-500 focus:ring-offset-2"
              aria-label={`Include report #${reportId} in merge`}
            />
            <span>{isSelected ? "Included in merge" : "Include in merge"}</span>
          </label>
        )}
      </div>

      {/* Description & Location */}
      <div className="mb-2.5">
        <p className="text-xs font-medium text-slate-800 line-clamp-2 leading-relaxed">
          {rawText || "No incident remarks provided."}
        </p>
        <div className="flex items-center gap-1.5 mt-1.5 text-[11px] text-slate-500">
          <MapPin className="w-3 h-3 text-slate-400 shrink-0" />
          <span className="truncate">
            {report.road_name || report.human_readable_location || report.barangay || "Pasig City"}
          </span>
        </div>
      </div>

      {/* Metrics Strip */}
      <div className="mb-3 mt-3 grid grid-cols-2 gap-x-4 gap-y-2 text-[11px] sm:grid-cols-3">
        <div className="min-w-0">
          <span className="text-slate-400 block text-[10px] uppercase font-semibold">Water Depth</span>
          <span className="font-semibold text-slate-700 capitalize">
            {depth ? depth.replace(/-/g, " ") : "Not reported"}
          </span>
        </div>

        <div className="min-w-0">
          <span className="text-slate-400 block text-[10px] uppercase font-semibold">Hidden Hazards</span>
          <span className="font-semibold text-slate-700 capitalize">
            {hiddenHazards || "Not specified"}
          </span>
        </div>

        <div className="min-w-0">
          <span className="text-slate-400 block text-[10px] uppercase font-semibold">Passable Vehicles</span>
          <span className="font-semibold text-slate-700 truncate block">
            {passableVehicles ? passableVehicles.split(",").join(", ") : "Not specified"}
          </span>
        </div>
      </div>

      {/* Footer Details: Reporter & Timestamp */}
      <div className="mt-1 flex items-center justify-between text-[11px] text-slate-500">
        <div className="flex items-center gap-1.5 min-w-0">
          <UserCheck className="w-3.5 h-3.5 text-blue-500 shrink-0" />
          <span className="font-medium text-slate-700 truncate">{reporterName}</span>
          {trustScore != null && (
            <span className="text-[10px] bg-slate-100 text-slate-600 px-1.5 py-0.2 rounded font-mono font-semibold">
              {trustScore.toFixed(0)}% trust
            </span>
          )}
        </div>

        <div className="flex items-center gap-1 text-slate-400 text-[10px] shrink-0">
          <Clock className="w-3 h-3" />
          <span>{timeAgo}</span>
        </div>
      </div>

      {/* Media Thumbnails */}
      {mediaUrls.length > 0 && (
        <div className="flex items-center gap-1.5 mt-2 overflow-x-auto pb-0.5">
          {mediaUrls.map((url, i) => (
            <a
              key={i}
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="block w-11 h-11 rounded-lg overflow-hidden border border-slate-200 shrink-0 relative hover:opacity-80 transition-opacity"
            >
              <img src={url} alt={`Report #${reportId} photo ${i + 1}`} className="w-full h-full object-cover" />
            </a>
          ))}
        </div>
      )}

      {matchScore != null && (
        <section aria-label={`Match evidence for report #${reportId}`} className="mt-3 pt-1">
          <p className="mb-1 text-[10px] font-bold uppercase tracking-wider text-slate-500">Why this report was suggested</p>
          <MergeExplanationBanner
            matchScore={matchScore}
            matchReasons={matchReasons}
            isCrowdConsensus={isCrowdConsensus}
          />
        </section>
      )}
    </article>
  );
}
