import { apiClient } from "@/lib/apiClient";
import type { FloodReport } from "@/features/admin/adminApi";

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
  geometry: GeoJSON.Polygon | GeoJSON.MultiPolygon | string | null;
  created_at: string;
  updated_at?: string;
  is_active: boolean;
  severity: string;
  depth?: string | null;
  passable_vehicles?: string | null;
  hidden_hazards?: string | null;
}

/** A display-only request to focus historic geometry; it never reaches live routing. */
export interface HistoricalMapFocusTarget {
  eventId: number;
  geometry?: unknown;
  label: string;
  /** Navigate to an existing footprint without changing its presentation or selection. */
  cameraOnly?: boolean;
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
  duration_seconds?: number;
  duration_minutes?: number | null;
  supporting_report_count?: number;
  reporter_count?: number;
  zone_count?: number;
  location_count?: number;
  media_count?: number;
  locations: FloodEventLocation[];
  zones: FloodEventZone[];
  heatmap_features: GeoJSON.Feature<GeoJSON.Point, { event_id: number; zone_id: number; weight: number }>[];
}

export interface FloodEventDetail extends Omit<FloodEventRecord, "heatmap_features"> {
  reports: FloodReport[];
  timeline: FloodEventTimelineEntry[];
}

export interface FloodEventHistoryPage {
  items: FloodEventRecord[];
  total: number;
  page: number;
  pages: number;
  page_size: number;
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

export function historyParams(filters: FloodHistoryFilters, includeLimit = false): URLSearchParams {
  const params = new URLSearchParams({ status_filter: filters.status, limit: "250" });
  if (!includeLimit) params.delete("limit");
  if (filters.severity) params.set("severity", filters.severity);
  if (filters.dateFrom) params.set("date_from", `${filters.dateFrom}T00:00:00`);
  if (filters.dateTo) params.set("date_to", `${filters.dateTo}T23:59:59`);
  if (filters.barangay.trim()) params.set("barangay", filters.barangay.trim());
  if (filters.road.trim()) params.set("road", filters.road.trim());
  // Records-only recurrence is evaluated before backend pagination.
  if (includeLimit && filters.search.startsWith("@multiple")) params.set("multiple_places", "true");
  if (filters.search.trim() && !filters.search.startsWith("@")) params.set("search", filters.search.trim());
  return params;
}

export async function getFloodEventHistory(filters: FloodHistoryFilters, signal?: AbortSignal): Promise<FloodEventRecord[]> {
  const params = historyParams(filters, true);
  params.set("summary", "true");
  return apiClient.get<FloodEventRecord[]>(`/admin/flood-events/history?${params.toString()}`, { signal });
}

export async function getFloodEventHistoryPage(filters: FloodHistoryFilters, page: number,
  focusEventId: number | null, signal?: AbortSignal): Promise<FloodEventHistoryPage> {
  const params = historyParams(filters, true);
  params.delete("limit");
  params.set("page", String(page));
  params.set("page_size", "20");
  params.set("summary", "true");
  if (focusEventId !== null) params.set("focus_event_id", String(focusEventId));
  const result = await apiClient.get<FloodEventHistoryPage>(`/admin/flood-events/records?${params}`, { signal });
  if (!Array.isArray(result.items)) throw new Error("Restart the backend to load paginated Flood Events.");
  return result;
}

export async function getFloodEventHistoryDetail(eventId: number): Promise<FloodEventDetail> {
  return apiClient.get<FloodEventDetail>(`/admin/flood-events/${eventId}/inspection`);
}

export interface InspectionPage<T> { items: T[]; total: number; page: number; pages: number; page_size: number }
export async function getHistoryCollection<T>(eventId: number, collection: "zones" | "reports" | "timeline" | "locations", page: number, signal?: AbortSignal) {
  const result = await apiClient.get<InspectionPage<T>>(`/admin/flood-events/${eventId}/inspection/${collection}?page=${page}`, { signal });
  if (!Array.isArray(result.items)) throw new Error("Event evidence could not be loaded. Update the backend and retry.");
  return result;
}

export async function getFloodEventPlanningAnalytics(filters: FloodHistoryFilters, signal?: AbortSignal): Promise<FloodEventPlanningAnalytics> {
  return apiClient.get<FloodEventPlanningAnalytics>(`/admin/flood-events/analytics?${historyParams(filters).toString()}`, { signal });
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
