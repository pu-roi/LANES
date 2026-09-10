"use client";

import React from "react";
import { format } from "date-fns";
import type { FloodReport, MergeCandidateItem } from "../../adminApi";

type ComparableReport = FloodReport | MergeCandidateItem;

interface ReportComparisonMatrixProps {
  primaryReport: FloodReport;
  candidates: MergeCandidateItem[];
}

function reportId(report: ComparableReport): number {
  return "id" in report ? report.id : report.report_id;
}

function valueFor(report: ComparableReport, field: string): React.ReactNode {
  const survey = "survey" in report ? report.survey : null;
  const timestamp = "created_at" in report ? report.created_at : report.reported_at;

  switch (field) {
    case "reporter":
      return report.reporter_name || report.reporter_username || "Unknown reporter";
    case "role":
      return "reporter_role" in report && report.reporter_role ? report.reporter_role : "Citizen";
    case "trust":
      return report.reporter_trust_score == null ? "Not available" : `${Math.round(report.reporter_trust_score)}%`;
    case "submitted":
      return timestamp ? format(new Date(timestamp), "MMM d, yyyy · h:mm a") : "Not available";
    case "location":
      return report.road_name || report.human_readable_location || [report.barangay, report.city].filter(Boolean).join(", ") || "Not available";
    case "severity":
      return report.severity || "Not reported";
    case "depth":
      return report.depth?.replace(/-/g, " ") || "Not reported";
    case "vehicles": {
      const vehicles = "survey" in report ? survey?.passable_vehicles : report.passable_vehicles;
      return vehicles?.split(",").filter(Boolean).join(", ") || "Not specified";
    }
    case "hazards": {
      const hazards = "survey" in report ? survey?.hidden_hazards : report.hidden_hazards;
      return hazards || "Not specified";
    }
    case "description":
      return report.raw_text || "No description";
    case "evidence":
      return report.media_urls?.length ? `${report.media_urls.length} attachment${report.media_urls.length === 1 ? "" : "s"}` : "No attachments";
    default:
      return "—";
  }
}

const ROWS = [
  ["reporter", "Reporter"],
  ["role", "Role"],
  ["trust", "Trust score"],
  ["submitted", "Submitted"],
  ["location", "Road / location"],
  ["severity", "Severity"],
  ["depth", "Water depth"],
  ["vehicles", "Passable vehicles"],
  ["hazards", "Hidden hazards"],
  ["description", "Original description"],
  ["evidence", "Evidence"],
] as const;

export function ReportComparisonMatrix({ primaryReport, candidates }: ReportComparisonMatrixProps) {
  const reports: ComparableReport[] = [primaryReport, ...candidates];

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white" tabIndex={0} aria-label="Selected flood report comparison">
      <table className="min-w-full border-collapse text-left text-[11px]">
        <thead className="sticky top-0 z-10 bg-slate-50">
          <tr>
            <th className="w-32 min-w-32 border-b border-r border-slate-200 px-3 py-2 font-bold text-slate-600">Field</th>
            {reports.map((report, index) => (
              <th
                key={reportId(report)}
                className="min-w-44 border-b border-r border-slate-200 px-3 py-2 font-bold text-slate-800 last:border-r-0"
              >
                {index === 0 ? `Primary #${reportId(report)}` : `Included #${reportId(report)}`}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {ROWS.map(([field, label]) => {
            const normalizedValues = reports.map((report) => String(valueFor(report, field)).trim().toLowerCase());
            const differs = new Set(normalizedValues).size > 1;
            return (
              <tr key={field} className={differs ? "bg-amber-50/45" : "bg-white"}>
                <th className="border-b border-r border-slate-100 px-3 py-2 align-top font-semibold text-slate-500">
                  {label}
                  {differs && <span className="ml-1 text-amber-600" aria-label="Values differ">●</span>}
                </th>
                {reports.map((report) => (
                  <td
                    key={`${field}-${reportId(report)}`}
                    className="border-b border-r border-slate-100 px-3 py-2 align-top font-medium capitalize text-slate-700 last:border-r-0"
                  >
                    {valueFor(report, field)}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
