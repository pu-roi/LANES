import { apiClient } from "@/lib/apiClient";
import type { AvoidanceZoneUpdatePayload, ReportGeometry } from "@/features/admin/adminApi";

export type ZoneCondition = "still_flooded" | "no_floodwater" | "other_change";
export const ZONE_CONDITIONS: { id: ZoneCondition; label: string }[] = [
  { id: "still_flooded", label: "Still flooded" }, { id: "no_floodwater", label: "No floodwater" },
  { id: "other_change", label: "Other change / Unsure" },
];
export interface ZoneUpdateContext { id: number; name?: string | null; depth?: string | null; severity?: string }
export interface ZoneObservation {
  id: number; zone_id: number; author_id: number; author_name: string; condition: ZoneCondition;
  observed_at: string | null; submitted_at: string; observed_location: string | null; description: string;
  road_start?: [number, number] | null; road_end?: [number, number] | null;
  start_label?: string | null; end_label?: string | null; is_bidirectional?: boolean;
  proposed_extent?: { geometry: ReportGeometry; validation_status: string; road_type: string; message: string } | null;
  depth: string | null; severity: string | null; latitude: number | null; longitude: number | null;
  passable_vehicles: string[] | null; hidden_hazards: string; media_urls: string[];
  review_state: "pending" | "reviewed" | "dismissed";
  review: { note: string; reviewed_at: string } | null;
  applications?: { id: number; fields: string[]; saved_at: string; reason: string; zone_version: string }[];
}
export type ZoneUpdateField = "depth" | "passable_vehicles" | "hidden_hazards" | "geometry";
export interface ZoneEditorProposal { patch: AvoidanceZoneUpdatePayload; expected_updated_at: string; community_update: { update_id: number; fields: ZoneUpdateField[]; reason: string } }
export const prepareZoneUpdateEditor = (zoneId: number, updateId: number, fields: ZoneUpdateField[], reason: string) => apiClient.post<ZoneEditorProposal>(`/admin/zones/${zoneId}/updates/${updateId}/editor`, { fields, reason });
export interface ZoneUpdatesPage { updates: ZoneObservation[]; next_before_id: number | null; is_active: boolean; can_review: boolean }
export const getZoneUpdateCounts = (ids: number[]) => apiClient.get<Record<string, number>>(`/admin/zone-updates/counts?${ids.map(id => `zone_ids=${id}`).join("&")}`);
export const getZoneUpdates = (id: number, before?: number) => apiClient.get<ZoneUpdatesPage>(`/admin/zones/${id}/updates${before ? `?before_id=${before}` : ""}`);
export const reviewZoneUpdate = (zoneId: number, id: number, decision: "reviewed" | "dismissed", note: string) => apiClient.post(`/admin/zones/${zoneId}/updates/${id}/review`, { decision, note });
