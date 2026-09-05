import React, { useState } from "react";
import { format } from "date-fns";
import { Clock, Ruler, Car, EyeOff, ShieldCheck, User, Users, ChevronDown, ChevronUp, Shield } from "lucide-react";

interface FloodZonePopupProps {
  properties: any;
  onToggleExpand?: () => void;
}

const SEVERITY_COLORS: Record<string, string> = {
  low: "#84cc16",
  medium: "#eab308",
  high: "#f97316",
  extreme: "#ef4444",
};

export const FloodZonePopup: React.FC<FloodZonePopupProps> = ({ properties, onToggleExpand }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const {
    severity = "medium",
    color = SEVERITY_COLORS["medium"],
    created_at,
    expires_at,
    report_text,
    reporter_name,
    reporter_role,
    depth,
    passable_vehicles,
    hidden_hazards,
    contributors_json,
  } = properties;

  let contributors: any[] = [];
  try {
    if (contributors_json) {
      contributors = JSON.parse(contributors_json);
    }
  } catch (e) {
    contributors = [];
  }

  const hasMultipleContributors = contributors.length > 1;

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
  if (created_at) {
    try {
      reportedText = format(new Date(created_at), "MMM d, h:mm a");
    } catch (e) {}
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

  return (
    <div className="flex flex-col w-full font-sans bg-white rounded-2xl overflow-hidden pointer-events-auto border-x border-b border-slate-200/80">
      {/* Header */}
      <div 
        className="px-4 py-3 select-none flex flex-col gap-1.5 rounded-t-2xl"
        style={{ backgroundColor: color, color: "#ffffff" }}
      >
        {/* Top Row: Severity + Status Badge */}
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-white shadow-xs shrink-0 animate-pulse" />
            <h3 className="text-base font-extrabold uppercase tracking-tight text-white leading-none">
              {severity} Risk
            </h3>
          </div>
          {properties.is_pending ? (
            <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full bg-black/20 text-white tracking-wider backdrop-blur-xs shrink-0">
              Pending
            </span>
          ) : (
            <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full bg-white/25 text-white tracking-wider backdrop-blur-xs shrink-0">
              Active Zone
            </span>
          )}
        </div>

        {/* Bottom Row: Timestamp */}
        <div className="flex items-center gap-1.5 text-xs text-white/95 font-medium tracking-wide">
          <Clock className="w-3.5 h-3.5 opacity-85 shrink-0" />
          <span>Reported {reportedText}</span>
        </div>
      </div>

      <div className="p-4">
        {/* Description */}
        {report_text && report_text !== "null" && (
          <div className="text-sm text-gray-700 mb-4 leading-relaxed bg-slate-50 p-2.5 rounded-lg border border-slate-100 italic">
            "{report_text}"
          </div>
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
              {depth && depth !== "null" ? depth.replace(/_/g, ' ') : "Not specified"}
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
              Safe to pass for
            </div>
            {vehicleList.length > 0 ? (
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
      <div className="border-t border-gray-100 bg-gray-50/90 px-4 py-3 flex flex-col gap-2">
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
                {hasMultipleContributors ? "Community Reports (Click to expand)" : "Reporter"}
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
          <div className="mt-1 pt-2 border-t border-slate-200/70 flex flex-col gap-2 max-h-40 overflow-y-auto">
            <div className="text-[10px] font-bold text-slate-500 flex items-center gap-1">
              <Shield className="w-3 h-3 text-blue-500" />
              {contributors.length} Contributing Reports
            </div>
            <div className="flex flex-col gap-1.5">
              {contributors.map((c: any) => (
                <div key={c.report_id} className="bg-white p-2 rounded-md border border-slate-200 text-[11px] flex flex-col gap-0.5">
                  <div className="flex items-center justify-between font-semibold text-slate-800 text-[10px]">
                    <span className="truncate max-w-[150px]">{c.reporter_name}</span>
                    <span className="text-[9px] text-slate-400">
                      {new Date(c.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  <p className="text-slate-600 text-[10px] italic line-clamp-2">
                    "{c.raw_text}"
                  </p>
                  <div className="flex items-center gap-2 text-[9px] text-slate-400">
                    <span>Trust: <strong>{c.reporter_trust_score}%</strong></span>
                    {c.depth && <span>• Depth: <strong>{c.depth}</strong></span>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
