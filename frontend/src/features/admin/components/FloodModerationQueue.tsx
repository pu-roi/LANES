"use client";

import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { AlertTriangle, CheckCircle2, Flag, MapPin } from "lucide-react";
import { apiClient } from "@/lib/apiClient";
import { Button, Card, CardContent, Skeleton } from "@/shared/ui";

type FloodModerationCase = {
  report_id: number;
  status: "pending" | "approved" | "rejected";
  source: string;
  raw_text: string;
  severity: string;
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

export function FloodModerationQueue() {
  const router = useRouter();
  const [status, setStatus] = useState<"all" | FloodModerationCase["status"]>("all");
  const [location, setLocation] = useState("");
  const [reporter, setReporter] = useState("");
  const [reason, setReason] = useState("");
  const [source, setSource] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
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

  const reviewOnMap = (caseItem: FloodModerationCase) => {
    const params = new URLSearchParams({ focus_report_id: String(caseItem.report_id), tab: "pending" });
    if (caseItem.latitude != null && caseItem.longitude != null) {
      params.set("lat", String(caseItem.latitude));
      params.set("lng", String(caseItem.longitude));
      params.set("zoom", "16");
    }
    router.push(`/admin/map?${params.toString()}`);
  };

  return <div className="space-y-4">
    <Card className="shadow-sm"><CardContent className="grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      <label className="text-sm font-medium text-slate-700">Status<select value={status} onChange={(event) => setStatus(event.target.value as typeof status)} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"><option value="all">All cases</option><option value="pending">Pending</option><option value="approved">Approved / linked</option><option value="rejected">Rejected</option></select></label>
      <label className="text-sm font-medium text-slate-700">Source<select value={source} onChange={(event) => setSource(event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"><option value="">Any source</option><option value="direct_user">Direct user report</option><option value="twitter">X / Twitter</option><option value="facebook">Facebook</option><option value="manual_seeder">Manual import</option></select></label>
      <label className="text-sm font-medium text-slate-700">Location<input value={location} onChange={(event) => setLocation(event.target.value)} placeholder="Road, barangay, or city" className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" /></label>
      <label className="text-sm font-medium text-slate-700">Reporter<input value={reporter} onChange={(event) => setReporter(event.target.value)} placeholder="Username" className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" /></label>
      <label className="text-sm font-medium text-slate-700">Rejection reason<select value={reason} onChange={(event) => setReason(event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"><option value="">Any reason</option>{Object.entries(rejectionLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
      <label className="text-sm font-medium text-slate-700">Submitted from<input type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" /></label>
      <label className="text-sm font-medium text-slate-700">Submitted to<input type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" /></label>
    </CardContent></Card>

    {cases.isLoading && <Card><CardContent className="space-y-3 py-5"><Skeleton className="h-5 w-1/4" /><Skeleton className="h-4 w-full" /><Skeleton className="h-4 w-3/4" /></CardContent></Card>}
    {cases.isError && <Card className="border-red-200 bg-red-50"><CardContent className="flex gap-3 text-sm text-red-800"><AlertTriangle className="h-5 w-5 shrink-0" />Could not load Flood Report moderation cases. Please refresh and try again.</CardContent></Card>}
    {cases.data?.length === 0 && <Card><CardContent className="py-16 text-center text-sm text-gray-500"><Flag className="mx-auto mb-2 h-6 w-6 text-slate-400" />No Flood Report moderation cases match these filters.</CardContent></Card>}
    {cases.data?.map((caseItem) => <Card key={caseItem.report_id} className="shadow-sm"><CardContent className="p-5">
      <div className="flex flex-col justify-between gap-3 sm:flex-row"><div><div className="flex flex-wrap items-center gap-2"><p className="font-semibold text-gray-900">Flood report #{caseItem.report_id}</p><span className={`rounded-full px-2 py-0.5 text-xs font-semibold capitalize ${caseItem.status === "pending" ? "bg-amber-100 text-amber-800" : caseItem.status === "approved" ? "bg-emerald-100 text-emerald-800" : "bg-rose-100 text-rose-800"}`}>{caseItem.resolution || caseItem.status}</span></div><p className="mt-1 text-xs text-slate-500">{caseItem.source.replaceAll("_", " ")} · Submitted {new Date(caseItem.submitted_at).toLocaleString()} · Reporter: {caseItem.reporter}</p></div><Button size="sm" variant="outline" onClick={() => reviewOnMap(caseItem)}><MapPin className="mr-1 h-4 w-4" />Review on Map</Button></div>
      <p className="mt-4 whitespace-pre-wrap text-sm text-slate-700">{caseItem.raw_text}</p>
      <div className="mt-4 grid gap-2 text-sm text-slate-600 sm:grid-cols-2 lg:grid-cols-4"><p><span className="font-medium text-slate-800">Severity:</span> {caseItem.severity}</p><p><span className="font-medium text-slate-800">Location:</span> {caseItem.location || "Not supplied"}</p><p><span className="font-medium text-slate-800">Event:</span> {caseItem.event_id ? `#${caseItem.event_id}` : "Not linked"}</p><p><span className="font-medium text-slate-800">Zone:</span> {caseItem.zone_id ? `#${caseItem.zone_id}` : "Not linked"}</p></div>
      {caseItem.status === "rejected" && <div className="mt-4 rounded-lg border border-rose-100 bg-rose-50 p-3 text-sm text-rose-900"><p><span className="font-semibold">Reason:</span> {caseItem.rejection_reason ? rejectionLabels[caseItem.rejection_reason] : "Not recorded"}</p>{caseItem.internal_note && <p className="mt-1"><span className="font-semibold">Internal note:</span> {caseItem.internal_note}</p>}</div>}
      {caseItem.resolved_at && <p className="mt-4 flex items-center gap-1.5 text-xs text-slate-500"><CheckCircle2 className="h-4 w-4 text-emerald-600" />{caseItem.resolution === "linked" ? "Linked" : "Resolved"} {new Date(caseItem.resolved_at).toLocaleString()}{caseItem.acting_admin ? ` by ${caseItem.acting_admin}` : ""}</p>}
    </CardContent></Card>)}
  </div>;
}
