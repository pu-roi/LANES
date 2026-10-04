import { apiClient } from "@/lib/apiClient";
import type { LineString, MultiLineString } from "geojson";
import type { FloodReport } from "../adminApi";
import type { NewsClaim, NewsResultDetail } from "@/features/news/newsApi";

export type ReviewSource = "all" | "user_reports" | "news_claims";
export interface ReviewItem {
  key: string; source: "user_report" | "news_claim";
  report_id: number | null; run_id: number | null; claim_index: number | null;
  title: string; location: string; evidence: string; review_reason: string; queued_at: string;
  severity?: string | null; depth?: string | null;
  city?: string | null; barangay?: string | null;
  location_summary?: string; area_summary?: string;
  severity_levels?: string[]; depth_levels?: string[];
  member_count?: number; members?: ReviewItem[]; group_reason?: string | null;
}
export interface ReviewPage {
  items: ReviewItem[]; total: number; page: number; page_size: number; pages: number;
  counts: Record<ReviewSource, number>; read_only: true;
  item_total?: number;
  facets?: { cities: string[]; barangays: string[] };
}
export interface ReviewMembersPage {
  group_reason?: string | null;
  key: string; items: ReviewItem[]; total: number; page: number; page_size: number; pages: number; read_only: true;
}
export interface ReviewDetail {
  key: string; source: "user_report" | "news_claim"; is_current_review: boolean;
  report: FloodReport | null; news: NewsResultDetail | null; news_actions_available: false;
}
export interface HistoryMatch {
  source_year: string; source_record_no: string; barangay: string; street: string; landmark: string;
}
export interface PlacementSection {
  candidate_id: string; kind: "reported_span" | "road_section";
  centerline_geojson: LineString | MultiLineString; osm_way_ids: number[];
  cross_streets: string[][]; ambiguous_carriageway: boolean; article_place_level: number;
  approximate_length_m: number; modeled_overlap_m: Record<string, Record<string, number>>;
  modeled_overlap_fraction: Record<string, number>; matching_history: HistoryMatch[];
  modeled_fragments?: { fragment_id: string; centerline_geojson: LineString;
    approximate_length_m: number; return_period: 5 | 25 | 100; hazard_class: 1 | 2 | 3;
    noah_source_id: string; noah_archive_sha256: string }[];
  preview_geometry?: LineString | MultiLineString | null;
  fragment_status?: "available" | "no_modeled_overlap" | "source_unavailable";
}
export interface PlacementPreview {
  status: "predicted_candidate" | "ambiguous" | "unresolved" | "source_unavailable";
  reason: string; selected_candidate_id: string | null; placement_kind: "reported" | "predicted" | null;
  candidates: PlacementSection[]; total_candidate_count: number; candidates_truncated: boolean;
  osm_source_id: string | null; osm_catalog_sha256: string | null; osm_snapshot_at: string | null;
  noah_catalog_sha256: string | null; noah_source_ids: Record<string, string>; noah_attribution: string | null;
  history_status: "not_applicable" | "available" | "source_unavailable";
  history_sha256: string | null; unmatched_history: HistoryMatch[]; uncertainty_reasons: string[];
  reported_severity?: "low" | "medium" | "high" | "extreme" | null;
  barangay_catalog_sha256?: string | null; barangay_source_id?: string | null;
  barangay_psgc_code?: string | null;
  barangay_boundary_status?: "not_required" | "available" | "unavailable";
  proves_current_flood: false; may_affect_routing: false; read_only: true;
}
export interface PlacementEnvelope {
  run_id: number; claim_index: number; input_fingerprint: string;
  evidence_pipeline_version: string; placement_revision: string; claim: NewsClaim; preview: PlacementPreview;
  read_only: true;
}
export interface ReviewFilters { q: string; city: string; barangay: string; severity: string }
export function getReviewPage(source: ReviewSource, page: number, signal?: AbortSignal, filters?: ReviewFilters) {
  const params = new URLSearchParams({ source, page: String(page), page_size: "20", ...filters });
  return apiClient.get<ReviewPage>(`/admin/review/items?${params}`, { signal }).then((data) => {
    if (!Array.isArray(data.items) || !data.counts || data.read_only !== true) throw new Error("Update the backend to load the combined review queue.");
    return data;
  });
}
export function getReviewDetail(key: string, signal?: AbortSignal) {
  return apiClient.get<ReviewDetail>(`/admin/review/items/${encodeURIComponent(key)}`, { signal });
}
export function getReviewMembers(key: string, page: number, signal?: AbortSignal) {
  return apiClient.get<ReviewMembersPage>(`/admin/review/groups/${encodeURIComponent(key)}/members?page=${page}&page_size=20`, { signal });
}
export function getPlacementPreview(runId: number, claimIndex: number, signal?: AbortSignal) {
  return apiClient.get<PlacementEnvelope>(`/admin/news/results/${runId}/${claimIndex}/placement`, { signal });
}
