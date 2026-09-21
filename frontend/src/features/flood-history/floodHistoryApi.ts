import { apiClient } from "@/lib/apiClient";
import type { FloodReport, PolygonGeometry } from "@/features/admin/adminApi";

export type FloodEventStatus = "active" | "ended";

export interface FloodEventLocation {
  id: number;
  location_type: "road" | "barangay" | "city";
  display_name: string;
  normalized_name: string;
  created_at: string;
}

export interface FloodEventZone {
  id: number;
  geometry: PolygonGeometry | string | null;
  created_at: string;
  is_active: boolean;
  severity: string;
  depth?: string | null;
}

export interface FloodEventTimelineEntry {
  id: number;
  entry_type: string;
  occurred_at: string;
  summary: string;
}

export interface FloodEventRecord {
  id: number;
  status: FloodEventStatus;
  first_reported_at: string | null;
  verified_at: string;
  ended_at: string | null;
  peak_severity: "low" | "medium" | "high" | "extreme";
  peak_depth: string | null;
  duration_minutes?: number | null;
  supporting_report_count?: number;
  reporter_count?: number;
  media_count?: number;
  locations: FloodEventLocation[];
  zones: FloodEventZone[];
}

export interface FloodEventDetail extends FloodEventRecord {
  reports: FloodReport[];
  timeline: FloodEventTimelineEntry[];
}

export interface FloodHistoryFilters {
  status: "all" | FloodEventStatus;
  severity: "" | FloodEventRecord["peak_severity"];
  dateFrom: string;
  dateTo: string;
  barangay: string;
  road: string;
  search: string;
}

export interface FloodEventPlanningAnalytics {
  total_events: number;
  ended_events: number;
  active_events: number;
  peak_severity_distribution: Array<{ severity: FloodEventRecord["peak_severity"]; event_count: number }>;
  duration: { ended_event_count: number; average_minutes: number | null; distribution: Array<{ bucket: string; event_count: number }> };
  events_over_time: Array<{ date: string; event_count: number }>;
  approved_reports_over_time: Array<{ date: string; report_count: number }>;
  verification_pattern: Array<{ weekday: number; hour: number; event_count: number }>;
  recurring_barangays: Array<{ name: string; event_count: number }>;
  frequently_affected_roads: Array<{ name: string; event_count: number }>;
  supporting_report_volume: { approved_report_count: number; average_per_event: number };
  definitions: Record<string, string>;
}

function historyParams(filters: FloodHistoryFilters, includeLimit = false): URLSearchParams {
  const params = new URLSearchParams({ status_filter: filters.status, limit: "250" });
  if (!includeLimit) params.delete("limit");
  if (filters.severity) params.set("severity", filters.severity);
  if (filters.dateFrom) params.set("date_from", `${filters.dateFrom}T00:00:00`);
  if (filters.dateTo) params.set("date_to", `${filters.dateTo}T23:59:59`);
  if (filters.barangay.trim()) params.set("barangay", filters.barangay.trim());
  if (filters.road.trim()) params.set("road", filters.road.trim());
  // `@multiple` is the Records-only recurrence filter. It is evaluated after
  // the server returns the authorized event set, not treated as place text.
  if (filters.search.trim() && !filters.search.startsWith("@")) params.set("search", filters.search.trim());
  return params;
}

export async function getFloodEventHistory(filters: FloodHistoryFilters): Promise<FloodEventRecord[]> {
  const params = historyParams(filters, true);
  return apiClient.get<FloodEventRecord[]>(`/admin/flood-events/history?${params.toString()}`);
}

export async function getFloodEventHistoryDetail(eventId: number): Promise<FloodEventDetail> {
  return apiClient.get<FloodEventDetail>(`/admin/flood-events/${eventId}/history-detail`);
}

export async function getFloodEventPlanningAnalytics(filters: FloodHistoryFilters): Promise<FloodEventPlanningAnalytics> {
  return apiClient.get<FloodEventPlanningAnalytics>(`/admin/flood-events/analytics?${historyParams(filters).toString()}`);
}

export async function downloadFloodEventPlanningData(
  filters: FloodHistoryFilters,
  exportType: "records" | "analytics",
  exportFormat: "csv" | "json",
): Promise<void> {
  const params = historyParams(filters);
  params.set("export_type", exportType);
  params.set("export_format", exportFormat);
  await apiClient.download(`/admin/flood-events/export?${params.toString()}`, `lanes_flood_event_${exportType}.${exportFormat}`);
}
