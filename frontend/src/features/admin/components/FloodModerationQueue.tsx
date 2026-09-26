"use client";

import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useRef, useState } from "react";
import { AlertTriangle, CheckCircle2, Flag, Info, MapPin } from "lucide-react";
import type { FloodReport } from "../adminApi";
import { apiClient } from "@/lib/apiClient";
import { formatFloodDepth } from "@/lib/floodDepth";
import { AutocompleteInput, Button, Card, CardContent, DatePicker, FloodReportDetailsModal, LocationAutocomplete, Select, Skeleton } from "@/shared/ui";

type FloodModerationCase = {
  report_id: number;
  status: "pending" | "approved" | "rejected";
  source: string;
  raw_text: string;
  severity: string;
  depth?: string | null;
  submitted_at: string;
  location?: string | null;
  reporter: string;
  event_id?: number | null;
  zone_id?: number | null;
  resolution?: "approved" | "linked" | "rejected" | null;
  rejection_reason?: string | null;
  internal_note?: string | null;
  resolved_at?: string | null;
  acting_admin?: string | null;
  latitude?: number | null;
  longitude?: number | null;
};

const rejectionLabels: Record<string, string> = {
  insufficient_evidence: "Insufficient evidence",
  incorrect_location_or_details: "Incorrect location or details",
  false_spam_or_malicious: "False, spam, or malicious",
  outside_coverage_area: "Outside coverage area",
  withdrawn: "Withdrawn",
  other: "Other",
};

const depthLabels: Record<string, string> = {
  gutter: "Gutter", "half-knee": "Half-Knee", "half-tire": "Half-Tire",
  knee: "Knee", tires: "Tires", waist: "Waist", chest: "Chest", neck: "Neck & Above",
};

const severityStyles: Record<string, string> = {
  low: "bg-lime-100 text-lime-800", medium: "bg-amber-100 text-amber-800",
  high: "bg-orange-100 text-orange-800", extreme: "bg-red-100 text-red-800",
};

export function FloodModerationQueue({ initialStatus = "all" }: { initialStatus?: "all" | FloodModerationCase["status"] }) {
  const router = useRouter();
  const reviewToken = useRef(0);
  const [status, setStatus] = useState<"all" | FloodModerationCase["status"]>(initialStatus);
  const [location, setLocation] = useState("");
  const [reporter, setReporter] = useState("");
  const [reason, setReason] = useState("");
  const [source, setSource] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [detailCase, setDetailCase] = useState<FloodModerationCase | null>(null);
  const cases = useQuery({
    queryKey: ["flood-moderation-cases", status, location, reporter, reason, source, dateFrom, dateTo],
    queryFn: () => {
      const params = new URLSearchParams({ status_filter: status });
      if (location.trim()) params.set("location", location.trim());
      if (reporter.trim()) params.set("reporter", reporter.trim());
      if (reason) params.set("rejection_reason", reason);
      if (source) params.set("source", source);
      if (dateFrom) params.set("date_from", `${dateFrom}T00:00:00`);
      if (dateTo) params.set("date_to", `${dateTo}T23:59:59`);
      return apiClient.get<FloodModerationCase[]>(`/admin/moderation/flood-reports?${params.toString()}`);
    },
  });
  const reporterSuggestions = [...new Set((cases.data || []).map((caseItem) => caseItem.reporter).filter((name) => name && name !== "System"))];
  const nextReviewToken = () => String(++reviewToken.current);

  const reviewOnMap = (caseItem: FloodModerationCase) => {
    const params = new URLSearchParams({ focus_report_id: String(caseItem.report_id), tab: "pending", review_token: nextReviewToken() });
    if (caseItem.latitude != null && caseItem.longitude != null) {
      params.set("lat", String(caseItem.latitude));
      params.set("lng", String(caseItem.longitude));
      params.set("zoom", "16");
    }
    router.push(`/admin/map?${params.toString()}`);
  };

  return <div className="space-y-4">
    <Card className="shadow-sm"><CardContent className="grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      <Select label="Status" value={status} onChange={(event) => setStatus(String(event.target.value) as typeof status)} options={[{ label: "All cases", value: "all" }, { label: "Pending", value: "pending" }, { label: "Approved / linked", value: "approved" }, { label: "Rejected", value: "rejected" }]} />
      <Select label="Source" value={source} onChange={(event) => setSource(String(event.target.value))} options={[{ label: "Any source", value: "" }, { label: "Direct user report", value: "direct_user" }, { label: "X / Twitter", value: "twitter" }, { label: "Facebook", value: "facebook" }, { label: "Manual import", value: "manual_seeder" }]} />
      <div className="flex flex-col gap-1"><label className="text-sm font-medium text-gray-700">Location</label><LocationAutocomplete value={location} onChange={setLocation} onSelect={(suggestion) => setLocation(suggestion.label)} onClear={() => setLocation("")} placeholder="Search a road or place" /></div>
      <AutocompleteInput label="Reporter" value={reporter} onChange={setReporter} options={reporterSuggestions} placeholder="Search username" />
      <Select label="Rejection reason" value={reason} onChange={(event) => setReason(String(event.target.value))} options={[{ label: "Any reason", value: "" }, ...Object.entries(rejectionLabels).map(([value, label]) => ({ value, label }))]} />
      <DatePicker label="Submitted from" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} />
      <DatePicker label="Submitted to" value={dateTo} onChange={(event) => setDateTo(event.target.value)} />
    </CardContent></Card>

    {cases.isLoading && <Card><CardContent className="space-y-3 py-5"><Skeleton className="h-5 w-1/4" /><Skeleton className="h-4 w-full" /><Skeleton className="h-4 w-3/4" /></CardContent></Card>}
    {cases.isError && <Card className="border-red-200 bg-red-50"><CardContent className="flex gap-3 text-sm text-red-800"><AlertTriangle className="h-5 w-5 shrink-0" />Could not load Flood Report moderation cases. Please refresh and try again.</CardContent></Card>}
    {cases.data?.length === 0 && <Card><CardContent className="py-16 text-center text-sm text-gray-500"><Flag className="mx-auto mb-2 h-6 w-6 text-slate-400" />No Flood Report moderation cases match these filters.</CardContent></Card>}
    {cases.data?.map((caseItem) => <Card key={caseItem.report_id} className="shadow-sm"><CardContent className="p-5">
      <div className="flex flex-col justify-between gap-3 sm:flex-row"><div><div className="flex flex-wrap items-center gap-2"><p className="font-semibold text-gray-900">Flood report #{caseItem.report_id}</p><span className={`rounded-full px-2 py-0.5 text-xs font-semibold capitalize ${caseItem.status === "pending" ? "bg-amber-100 text-amber-800" : caseItem.status === "approved" ? "bg-emerald-100 text-emerald-800" : "bg-rose-100 text-rose-800"}`}>{caseItem.resolution || caseItem.status}</span></div><p className="mt-1 text-xs text-slate-500">{caseItem.source.replaceAll("_", " ")} · Submitted {new Date(caseItem.submitted_at).toLocaleString()} · Reporter: {caseItem.reporter}</p></div><div className="flex gap-2"><Button size="sm" variant="outline" onClick={() => setDetailCase(caseItem)}><Info className="mr-1 h-4 w-4" />Info</Button><Button size="sm" variant="outline" onClick={() => reviewOnMap(caseItem)}><MapPin className="mr-1 h-4 w-4" />Review on Map</Button></div></div>
      <p className="mt-4 whitespace-pre-wrap text-sm text-slate-700">{caseItem.raw_text}</p>
      <div className="mt-4 grid gap-2 text-sm text-slate-600 sm:grid-cols-2"><p><span className="font-medium text-slate-800">Flood level:</span> <span className={`ml-1 inline-flex rounded-full px-2 py-0.5 text-xs font-semibold capitalize ${severityStyles[caseItem.severity] || "bg-slate-100 text-slate-700"}`}>{caseItem.severity}</span>{caseItem.depth && <span className="ml-2 text-slate-600 font-medium">{formatFloodDepth(caseItem.depth, { compact: true })}</span>}</p><p><span className="font-medium text-slate-800">Location:</span> {caseItem.location || "Not supplied"}</p></div>
      {caseItem.event_id && <p className="mt-3 text-xs text-slate-500">Verified Flood Event #{caseItem.event_id}{caseItem.zone_id ? ` · Zone #${caseItem.zone_id}` : ""}</p>}
      {caseItem.status === "rejected" && <div className="mt-4 rounded-lg border border-rose-100 bg-rose-50 p-3 text-sm text-rose-900"><p><span className="font-semibold">Reason:</span> {caseItem.rejection_reason ? rejectionLabels[caseItem.rejection_reason] : "Not recorded"}</p>{caseItem.internal_note && <p className="mt-1"><span className="font-semibold">Internal note:</span> {caseItem.internal_note}</p>}</div>}
      {caseItem.resolved_at && <p className="mt-4 flex items-center gap-1.5 text-xs text-slate-500"><CheckCircle2 className="h-4 w-4 text-emerald-600" />{caseItem.resolution === "linked" ? "Linked" : "Resolved"} {new Date(caseItem.resolved_at).toLocaleString()}{caseItem.acting_admin ? ` by ${caseItem.acting_admin}` : ""}</p>}
    </CardContent></Card>)}
    <FloodReportDetailsModal report={detailCase ? ({ id: detailCase.report_id, status: detailCase.status, source: detailCase.source, raw_text: detailCase.raw_text, severity: detailCase.severity, depth: detailCase.depth, created_at: detailCase.submitted_at, updated_at: detailCase.submitted_at, human_readable_location: detailCase.location, reporter_username: detailCase.reporter } as FloodReport) : null} isOpen={detailCase !== null} onClose={() => setDetailCase(null)} onViewOnMap={(report) => router.push(`/admin/map?focus_report_id=${report.id}&tab=pending&review_token=${nextReviewToken()}`)} />
  </div>;
}
