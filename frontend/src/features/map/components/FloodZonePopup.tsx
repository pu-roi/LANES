import React, { useEffect, useId, useRef, useState } from "react";
import { format } from "date-fns";
import { parseUtcDate } from "@/lib/utils";
import { Clock, Ruler, Car, EyeOff, ShieldCheck, User, Users, ChevronDown, ChevronUp, Shield, X } from "lucide-react";
import { Modal, Button } from "@/shared/ui";
import type { ZoneCondition } from "@/features/hazards/zoneUpdatesApi";
import { formatFloodDepth } from "@/lib/floodDepth";
import type { PublicNewsAlert } from "@/features/news/publicNewsApi";
import { newsDate, publisherLink } from "@/features/news/newsPresentation";
import { SEVERITY_COLORS } from "../mapStyles";

export interface FloodPlacementPopupDetails {
  location: string;
  section: string;
  depth: string | null;
  passability: string;
  observedAt: string | null;
  publishedAt?: string | null;
  sourceTitle?: string;
  sourceUrl?: string;
  publisher?: string;
  ambiguousCarriageway: boolean;
}

interface FloodZoneProperties {
  severity?: string;
  color?: string;
  created_at?: string;
  report_text?: string;
  reporter_name?: string;
  reporter_role?: string;
  depth?: string;
  depth_formatted?: string;
  passable_vehicles?: string;
  hidden_hazards?: string;
  contributors_json?: string;
  news_json?: string;
  is_pending?: boolean;
}

interface FloodZoneContributor {
  report_id: number;
  reporter_name: string;
  created_at: string;
  raw_text: string;
  reporter_trust_score: number;
  depth?: string;
}

interface FloodZonePopupProps {
  properties: FloodZoneProperties;
  onToggleExpand?: () => void;
  compact?: boolean;
  drawer?: boolean;
  modal?: boolean;
  onClose?: () => void;
  onUpdate?: (condition: ZoneCondition) => void;
  placementPreview?: FloodPlacementPopupDetails;
}

function ReportDescription({ text }: { text: string }) {
  const [expanded, setExpanded] = useState(false);
  const [canExpand, setCanExpand] = useState(false);
  const descriptionRef = useRef<HTMLParagraphElement>(null);
  const descriptionId = useId();

  useEffect(() => {
    const description = descriptionRef.current;
    if (!description || expanded) return;

    const measure = () => setCanExpand(description.scrollHeight > description.clientHeight + 1);
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(description);
    return () => observer.disconnect();
  }, [text, expanded]);

  return (
    <div className="mb-4">
      <p className="mb-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400">Report details</p>
      <p
        id={descriptionId}
        ref={descriptionRef}
        className={`break-words text-sm italic leading-relaxed text-slate-600 ${expanded ? "" : "line-clamp-3"}`}
      >
        &ldquo;{text}&rdquo;
      </p>
      {canExpand && (
        <Button
          type="button"
          variant="ghost"
          size="sm"
          aria-expanded={expanded}
          aria-controls={descriptionId}
          className="mt-1 min-h-11 gap-1 px-0 text-blue-700 hover:bg-transparent hover:underline"
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? "See less" : "See more"}
          {expanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
        </Button>
      )}
    </div>
  );
}

export const FloodZonePopup: React.FC<FloodZonePopupProps> = ({ properties, onToggleExpand, compact = false, drawer = false, modal = false, onClose, onUpdate, placementPreview }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const {
    severity = "medium",
    color = SEVERITY_COLORS["medium"],
    created_at,
    report_text,
    reporter_name,
    reporter_role,
    depth,
    depth_formatted,
    passable_vehicles,
    hidden_hazards,
    contributors_json,
  } = properties;

  let news: PublicNewsAlert[] = [];
  try {
    news = JSON.parse(properties.news_json || "[]");
  } catch {
    news = [];
  }

  let contributors: FloodZoneContributor[] = [];
  try {
    if (contributors_json) {
      contributors = JSON.parse(contributors_json);
    }
  } catch {
    contributors = [];
  }

  const hasMultipleContributors = contributors.length > 1;
  const previewSourceLink = publisherLink(placementPreview?.sourceUrl || "");

  // Determine if the primary reporter is an official authority (DRRM Officer / Admin / Moderator)
  const isOfficialReporter =
    reporter_role &&
    (reporter_role.includes("Admin") ||
      reporter_role.includes("DRRM") ||
      reporter_role.includes("Moderator") ||
      reporter_role.includes("Officer"));

  // Display label logic:
  // - If single reporter: Show reporter's name
  // - If multiple reporters and primary is Official: Show "[Officer Name] (+X others)"
  // - If multiple reporters and regular commuters: Show "Multiple Users (X Reports)"
  let displayReporterTitle = reporter_name && reporter_name !== "null" ? reporter_name : "System";
  if (hasMultipleContributors) {
    if (isOfficialReporter) {
      displayReporterTitle = `${reporter_name} (+${contributors.length - 1} other${contributors.length - 1 > 1 ? "s" : ""})`;
    } else {
      displayReporterTitle = `Multiple Users (${contributors.length} Reports)`;
    }
  }

  let reportedText = "Unknown";
  if (placementPreview) {
    reportedText = newsDate(placementPreview.observedAt, "Time not specified");
  } else if (news[0]?.observed_at) {
    reportedText = newsDate(news[0].observed_at);
  } else if (created_at) {
    try {
      reportedText = format(parseUtcDate(created_at) || new Date(created_at), "MMM d, h:mm a");
    } catch {
      reportedText = "Unknown";
    }
  }

  // Determine badge styling based on role
  let badgeColor = "bg-gray-100 text-gray-700 border-gray-200";
  if (reporter_role === "Admin" || reporter_role === "Super Admin") {
    badgeColor = "bg-red-100 text-red-700 border-red-200";
  } else if (reporter_role === "Moderator") {
    badgeColor = "bg-purple-100 text-purple-700 border-purple-200";
  } else if (reporter_role === "DRRM Officer") {
    badgeColor = "bg-blue-100 text-blue-700 border-blue-200";
  } else if (reporter_role === "Commuter") {
    badgeColor = "bg-green-100 text-green-700 border-green-200";
  }

  const vehicleList =
    passable_vehicles && passable_vehicles !== "null"
      ? passable_vehicles.split(",").map((v: string) => v.trim()).filter(Boolean)
      : [];

  const popupHeightClass = drawer
    ? "max-h-[min(560px,calc(100dvh-var(--bottom-nav-height)-1rem-env(safe-area-inset-bottom,0px)))]"
    : modal
      ? "max-h-[min(560px,calc(100dvh-var(--bottom-nav-height)-2rem-env(safe-area-inset-bottom,0px)))]"
      : "max-h-[min(560px,calc(100dvh-var(--bottom-nav-height)-8rem-env(safe-area-inset-bottom,0px)))]";

  const popupContent = (
    <>
      {drawer && (
        <div
          className="fixed inset-0 z-[99] bg-slate-950/35 backdrop-blur-[2px]"
          onClick={onClose}
          aria-hidden="true"
        />
      )}
      <div
        className={`flex min-h-0 flex-col w-full font-sans bg-white overflow-hidden pointer-events-auto border-slate-200/80 ${popupHeightClass} ${compact ? "flood-zone-popup-compact" : ""} ${drawer ? "fixed inset-x-0 bottom-[calc(var(--bottom-nav-height)+env(safe-area-inset-bottom,0px))] z-[100] rounded-t-2xl border-t shadow-[0_-8px_30px_rgba(0,0,0,0.16)]" : "rounded-2xl border-x border-b"}`}
        onClick={drawer ? (e) => e.stopPropagation() : undefined}
      >
        {drawer && (
          <>
            <div className="flex shrink-0 justify-center py-2.5">
              <div className="h-1.5 w-12 rounded-full bg-slate-300" />
            </div>
            <div className="flex shrink-0 items-center justify-between border-b border-slate-100 px-4 pb-3">
              <h2 className="text-base font-bold text-slate-900">Flood Zone</h2>
              <button
                type="button"
                onClick={onClose}
                className="flex h-9 w-9 items-center justify-center rounded-full text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-900"
                aria-label="Close flood details"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          </>
        )}
      {/* Header */}
      <div 
        className={`shrink-0 px-4 py-3 select-none flex flex-col gap-1.5 ${compact ? "popup-header-compact" : ""}`}
        style={{ backgroundColor: color, color: "#ffffff" }}
      >
        {/* Top Row: Severity + Status Badge */}
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-white shadow-xs shrink-0 animate-pulse" />
            <h3 className="text-base font-extrabold uppercase tracking-tight text-white leading-none">
              {severity === "unknown" ? "Severity unknown" : `${severity} Risk`}
            </h3>
          </div>
          {placementPreview ? (
            <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full bg-black/20 text-white tracking-wider shrink-0">Needs Review</span>
          ) : properties.is_pending ? (
            <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full bg-black/20 text-white tracking-wider backdrop-blur-xs shrink-0">
              Pending
            </span>
          ) : (
            <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full bg-white/25 text-white tracking-wider backdrop-blur-xs shrink-0">
              {news[0]?.status ?? "Active"}
            </span>
          )}
          {modal && <button type="button" onClick={onClose} aria-label="Close flood details" className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-white hover:bg-white/20"><X className="h-5 w-5" /></button>}
        </div>

        {/* Bottom Row: Timestamp */}
        <div className="flex items-center gap-1.5 text-xs text-white/95 font-medium tracking-wide">
          <Clock className="w-3.5 h-3.5 opacity-85 shrink-0" />
          <span>Reported {reportedText}</span>
        </div>
      </div>

      {/* Only the details scroll; risk and update actions remain visible. */}
      <div
        role="region"
        aria-label="Flood zone details"
        tabIndex={0}
        className="min-h-0 overflow-y-auto overscroll-contain [scrollbar-gutter:stable] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-blue-500"
      >
      <div className={`p-4 ${compact ? "popup-body-compact" : ""}`}>
        {placementPreview && <div className="mb-3 text-sm text-slate-700">
          <p className="font-semibold">{placementPreview.location}</p>
          {placementPreview.section && <p className="mt-1 text-xs">{placementPreview.section}</p>}
        </div>}
        {/* Description */}
        {report_text && report_text !== "null" && (
          <ReportDescription text={report_text} />
        )}

        {/* Details Grid */}
        <div className="grid grid-cols-2 gap-y-3 gap-x-3 mb-1">
          {/* Depth */}
          <div className="flex flex-col gap-0.5">
            <div className="flex items-center text-[10px] font-bold text-gray-400 uppercase tracking-wider">
              <Ruler className="w-3 h-3 mr-1" />
              Height
            </div>
            <div className="text-xs font-semibold text-gray-900">
              {depth_formatted || formatFloodDepth(depth)}
            </div>
          </div>

          {/* Hidden Hazards */}
          <div className="flex flex-col gap-0.5">
            <div className="flex items-center text-[10px] font-bold text-gray-400 uppercase tracking-wider">
              <EyeOff className="w-3 h-3 mr-1" />
              Hazards
            </div>
            <div className="text-xs font-semibold text-gray-900 capitalize">
              {hidden_hazards && hidden_hazards !== "null" ? hidden_hazards : "Unsure"}
            </div>
          </div>

          {/* Passable Vehicles */}
          <div className="col-span-2 flex flex-col gap-1 mt-0.5">
            <div className="flex items-center text-[10px] font-bold text-gray-400 uppercase tracking-wider">
              <Car className="w-3 h-3 mr-1" />
              {placementPreview ? "Reported passability" : "Safe to pass for"}
            </div>
            {placementPreview ? <div className="text-xs font-semibold text-gray-900">{placementPreview.passability === "passable all" ? "All vehicle types (reported)" : placementPreview.passability}</div> : vehicleList.length > 0 ? (
              <div className="flex flex-wrap gap-1.5 mt-0.5">
                {vehicleList.map((v: string, idx: number) => (
                  <span 
                    key={idx} 
                    className="inline-flex items-center text-[11px] font-semibold bg-slate-100 text-slate-700 px-2 py-0.5 rounded-md border border-slate-200/60"
                  >
                    {v.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            ) : (
              <div className="text-xs font-semibold text-gray-900">
                Not specified
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Footer (Reporter & Contributors) */}
      <div className={`border-t border-gray-100 bg-gray-50/90 px-4 py-3 flex flex-col gap-2 ${compact ? "popup-footer-compact" : ""}`}>
        {placementPreview && <div className="flex flex-col gap-1 text-xs text-slate-600">
          <span className="font-semibold text-slate-900">{placementPreview.publisher || "News report"}</span>
          {previewSourceLink ? <a href={previewSourceLink} target="_blank" rel="noopener noreferrer" className="break-words text-blue-700 underline underline-offset-2">{placementPreview.sourceTitle || "Source article"}<span className="sr-only"> (opens in a new tab)</span></a> : placementPreview.sourceTitle && <span>{placementPreview.sourceTitle}</span>}
          {placementPreview.publishedAt && <span>Published {newsDate(placementPreview.publishedAt)}</span>}
          <span>Modeled placement suggestion; current flooding and its extent are unconfirmed. Does not affect routing.</span>
          {placementPreview.ambiguousCarriageway && <span>Competing carriageways remain unresolved.</span>}
        </div>}
        {news.map((alert) => {
          const link = publisherLink(alert.source_url);
          return <div key={alert.case_id} className="flex flex-col gap-1 text-xs text-slate-600">
            <span className="font-semibold text-slate-900">{alert.source_publisher} · {alert.status}</span>
            {link ? <a href={link} target="_blank" rel="noopener noreferrer" className="break-words text-blue-700 underline underline-offset-2">{alert.source_title}<span className="sr-only"> (opens in a new tab)</span></a> : <span>{alert.source_title}</span>}
            <span>{alert.geometry_basis === "estimated_road_corridor" ? "Estimated road corridor; flood extent is unmeasured." : "Verified current flood footprint."}</span>
            <span>Observed {newsDate(alert.observed_at)} · Evidence expires {newsDate(alert.expires_at)}</span>
          </div>;
        })}
        <div
          onClick={() => {
            if (hasMultipleContributors) {
              setIsExpanded(!isExpanded);
              if (onToggleExpand) onToggleExpand();
            }
          }}
          className={`flex items-center justify-between ${hasMultipleContributors ? "cursor-pointer hover:opacity-80 select-none" : ""}`}
        >
          <div className="flex items-center gap-2">
            <div className={`w-7 h-7 rounded-full flex items-center justify-center ${
              hasMultipleContributors 
                ? "bg-blue-600 text-white" 
                : isOfficialReporter 
                  ? "bg-blue-100 text-blue-600" 
                  : "bg-slate-200 text-slate-700"
            }`}>
              {hasMultipleContributors ? (
                <Users className="w-4 h-4" />
              ) : isOfficialReporter ? (
                <ShieldCheck className="w-4 h-4" />
              ) : (
                <User className="w-4 h-4" />
              )}
            </div>
            <div className="flex flex-col">
              <span className="text-xs font-bold text-gray-900 leading-tight">
                {displayReporterTitle}
              </span>
              <span className="text-[10px] text-gray-500 font-medium leading-tight">
                {hasMultipleContributors ? "Community Reports (Click to expand)" : news.length || placementPreview ? "News source" : "Reporter"}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-1.5">
            {hasMultipleContributors ? (
              isExpanded ? (
                <ChevronUp className="w-4 h-4 text-blue-600" />
              ) : (
                <ChevronDown className="w-4 h-4 text-gray-400" />
              )
            ) : (
              reporter_role && reporter_role !== "null" && (
                <div className={`px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider border rounded-full ${badgeColor}`}>
                  {reporter_role}
                </div>
              )
            )}
          </div>
        </div>

        {/* Expanded Contributors List in Popup */}
        {isExpanded && hasMultipleContributors && (
          <div className="mt-1 pt-2 border-t border-slate-200/70 flex flex-col gap-2">
            <div className="text-[10px] font-bold text-slate-500 flex items-center gap-1">
              <Shield className="w-3 h-3 text-blue-500" />
              {contributors.length} Contributing Reports
            </div>
            <div className="flex flex-col gap-1.5">
              {contributors.map((c) => (
                <div key={c.report_id} className="bg-white p-2 rounded-md border border-slate-200 text-[11px] flex flex-col gap-0.5">
                  <div className="flex items-center justify-between font-semibold text-slate-800 text-[10px]">
                    <span className="truncate max-w-[150px]">{c.reporter_name}</span>
                    <span className="text-[9px] text-slate-400">
                      {parseUtcDate(c.created_at)?.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  <p className="text-slate-600 text-[10px] italic line-clamp-2">
                    &ldquo;{c.raw_text}&rdquo;
                  </p>
                  <div className="flex items-center gap-2 text-[9px] text-slate-400">
                    <span>Trust: <strong>{c.reporter_trust_score}%</strong></span>
                    {c.depth && <span>• Depth: <strong>{formatFloodDepth(c.depth, { compact: true })}</strong></span>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
      </div>
      {onUpdate && (
        <div className="shrink-0 border-t border-slate-200 bg-white px-4 py-3 shadow-[0_-4px_12px_rgba(15,23,42,0.04)]">
          <div className="grid grid-cols-2 gap-2">
            <Button type="button" variant="outline" size="sm" className="min-h-11 whitespace-normal px-2 text-xs" onClick={() => onUpdate("still_flooded")}>Still flooded</Button>
            <Button type="button" variant="outline" size="sm" className="min-h-11 whitespace-normal px-2 text-xs" onClick={() => onUpdate("no_floodwater")}>No floodwater</Button>
          </div>
          <Button type="button" variant="ghost" size="sm" className="mt-1 min-h-11 w-full text-blue-700" onClick={() => onUpdate("other_change")}>Update</Button>
        </div>
      )}
      </div>
    </>
  );

  if (modal) {
    return (
      <Modal isOpen={true} onClose={onClose || (() => undefined)} title="Flood Zone" bare>
        {popupContent}
      </Modal>
    );
  }

  return popupContent;
};
