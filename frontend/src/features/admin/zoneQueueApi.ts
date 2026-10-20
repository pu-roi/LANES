import { apiClient } from "@/lib/apiClient";
import type { AvoidanceZone } from "./adminApi";

export type ZoneSource = "all" | "user_reports" | "news" | "official" | "other";
export interface ZoneQueueFilters { source: ZoneSource; q: string; city: string; barangay: string; severity: string }
export interface ZoneQueueItem {
  zone_id: number; member_count: number; location: string; area_summary: string; sources: string[];
  severity_levels: string[]; depth_levels: string[]; evidence: string; queued_at: string; group_reason: string;
}
export interface ZoneQueuePage {
  items: ZoneQueueItem[]; zones: AvoidanceZone[]; total: number; item_total: number;
  counts: Record<ZoneSource, number>; facets: { cities: string[]; barangays: string[] };
  page: number; pages: number; page_size: number; read_only: true;
}
export interface ZoneMembersPage {
  zone_id: number; zones: AvoidanceZone[]; total: number; page: number; pages: number; page_size: number;
  group_reason: string; read_only: true;
}
export function getZoneQueue(activeOnly: boolean, page = 1, filters?: ZoneQueueFilters, signal?: AbortSignal) {
  const params = new URLSearchParams({ active_only: String(activeOnly), page: String(page), page_size: "20", ...filters });
  return apiClient.get<ZoneQueuePage>(`/admin/zones/queue?${params}`, { signal }).then((data) => {
    if (!Array.isArray(data.items) || !Array.isArray(data.zones) || !data.counts || data.read_only !== true) throw new Error("Update the backend to load the zone queue.");
    return data;
  });
}
export function getZoneMembers(zoneId: number, page: number | null, signal?: AbortSignal) {
  const params = new URLSearchParams({ page_size: "20" });
  if (page !== null) params.set("page", String(page));
  return apiClient.get<ZoneMembersPage>(`/admin/zones/groups/${zoneId}/members?${params}`, { signal });
}
