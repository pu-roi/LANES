import { apiClient } from "@/lib/apiClient";

export interface PublicNewsAlert {
  case_id: number;
  decision_id: number;
  revision: number;
  status: "Active" | "Unconfirmed" | "Cleared";
  location_label: string;
  location_qualifier: string | null;
  depth_label: string | null;
  condition_label: string | null;
  passability_label: string | null;
  observed_at: string | null;
  expires_at: string | null;
  cleared_at: string | null;
  updated_at: string;
  source_title: string;
  source_publisher: string | null;
  source_url: string;
  source_published_at: string | null;
  correction_note: string | null;
  evidence_excerpt?: string | null;
  geometry_precision: "text_only" | "display_suggestion" | "operational_polygon";
  display_geojson: GeoJSON.Polygon | GeoJSON.MultiPolygon | null;
  current_status_unknown: boolean;
  affects_routing: boolean;
  geometry_basis?: "verified_current_footprint" | "estimated_road_corridor" | null;
}

export interface PublicNewsAlertPage {
  items: PublicNewsAlert[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
  as_of: string;
}

export const publicNewsApi = {
  list: (page: number, signal?: AbortSignal) => apiClient.get<PublicNewsAlertPage>(`/news/alerts?page=${page}&page_size=10`, { signal, cache: "no-store" }),
  detail: (caseId: number, signal?: AbortSignal) => apiClient.get<PublicNewsAlert>(`/news/alerts/${encodeURIComponent(caseId)}`, { signal, cache: "no-store" }),
};
