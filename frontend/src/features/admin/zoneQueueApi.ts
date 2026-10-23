import type { HistoricalNewsMetadata } from "@/features/news/historicalNewsTypes";
import { apiClient } from "@/lib/apiClient";
import type { AvoidanceZone } from "./adminApi";
import { getReportForSpatialReview } from "./adminApi";
import { queryOptions } from "@tanstack/react-query";
import type { QueryClient } from "@tanstack/react-query";

export const invalidateSpatialBrowsing = (client: QueryClient) => Promise.all([
  client.invalidateQueries({ queryKey: ["adminZones"] }),
  client.invalidateQueries({ queryKey: ["flood-event-history"] }),
  client.invalidateQueries({ queryKey: ["flood-event-planning-analytics"] }),
]);

export const zoneDetailQuery = (id: number | null | undefined) => queryOptions({
  queryKey: ["adminZones", "details", id],
  queryFn: ({ signal }) => apiClient.get<AvoidanceZone>(`/admin/zones/${id}?summary=true`, { signal }),
  enabled: id != null, staleTime: 15_000, retry: false,
});
export const contributorDetailQuery = (id: number | null) => queryOptions({
  queryKey: ["adminZones", "contributor-details", id], queryFn: ({ signal }) => getReportForSpatialReview(id!, signal),
  enabled: id !== null, staleTime: 15_000, retry: false,
});

export type ZoneSource = "all" | "user_reports" | "news" | "official" | "other";
export interface ZoneQueueFilters { source: ZoneSource; q: string; city: string; barangay: string; severity: string }
export interface ZoneQueueItem {
  historical?: HistoricalNewsMetadata | null;
  zone_id: number; member_count: number; location: string; area_summary: string; sources: string[];
  severity_levels: string[]; depth_levels: string[]; evidence: string; queued_at: string; group_reason: string;
  bounds?: [number, number, number, number] | null;
}
export interface ZoneQueuePage {
  items: ZoneQueueItem[]; zones: AvoidanceZone[]; total: number; item_total: number;
  counts: Record<ZoneSource, number>; facets: { cities: string[]; barangays: string[] };
  page: number; pages: number; page_size: number; read_only: true;
}
export interface ZoneMembersPage {
  zone_total?: number;
  zone_id: number; zones: AvoidanceZone[]; total: number; page: number; pages: number; page_size: number;
  group_reason: string; read_only: true;
}
export function getZoneQueue(activeOnly: boolean, page = 1, filters?: ZoneQueueFilters, signal?: AbortSignal) {
  const params = new URLSearchParams({ active_only: String(activeOnly), page: String(page), page_size: "20", ...filters });
  params.set("summary", "true");
  return apiClient.get<ZoneQueuePage>(`/admin/zones/queue?${params}`, { signal }).then((data) => {
    if (!Array.isArray(data.items) || !Array.isArray(data.zones) || !data.counts || data.read_only !== true) throw new Error("Update the backend to load zones.");
    return data;
  });
}
export function getZoneMembers(zoneId: number, page: number | null, signal?: AbortSignal) {
  const params = new URLSearchParams({ page_size: "20" });
  params.set("summary", "true");
  if (page !== null) params.set("page", String(page));
  return apiClient.get<ZoneMembersPage>(`/admin/zones/groups/${zoneId}/members?${params}`, { signal });
}
