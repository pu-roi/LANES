import { apiClient } from "@/lib/apiClient";

export type ProcessingStatus = "not_recorded" | "pending" | "processing" | "completed" | "retry_wait" | "failed";
export type BodyStatus = "available" | "missing" | "error";

export interface NewsArticleItem {
  id: number;
  title: string;
  excerpt: string;
  canonical_url: string;
  publisher_source_id: string;
  publisher: string;
  published_at: string | null;
  last_seen_at: string;
  body_status: BodyStatus;
  article_error: string | null;
  review_state: string;
  processing_status: ProcessingStatus;
  latest_run_id: number | null;
}

export interface NewsArticlePage {
  items: NewsArticleItem[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
  publishers: { id: string; label: string }[];
}

export interface NewsArticleFilters {
  page: number;
  search: string;
  publisher: string;
  body: string;
  processing: string;
  order: string;
}

export interface CapturedInput {
  title: string;
  canonical_url: string;
  publisher: string;
  excerpt: string;
  article_text: string | null;
  published_at: string | null;
}

export interface NewsClaim {
  raw_place_name: string;
  canonical_city: string | null;
  canonical_barangay: string | null;
  canonical_road: string | null;
  road_segment_raw?: string | null;
  local_area_raw?: string | null;
  event_time_raw?: string | null;
  depth_raw: string | null;
  depth_formatted: string | null;
  condition: string;
  event_time_resolved: string | null;
  event_time_kind: string;
  evidence_sentence: string;
  uncertainty_reasons: string[];
  is_historical: boolean;
  is_forecast: boolean;
  is_negated: boolean;
  road_passability: string;
  action_type: string | null;
  action_rationale?: string | null;
  road_placement: { status: string; reason: string } | null;
}

export interface NewsExtraction {
  article_id: number;
  claims: NewsClaim[];
  extracted_at: string;
  extractor_version: string;
  is_metadata_only: boolean;
  errors: string[];
}

export interface NewsRun {
  id: number;
  article_version_id: number;
  pipeline_version: string;
  mode: "rules_only";
  status: Exclude<ProcessingStatus, "not_recorded">;
  attempt_count: number;
  next_attempt_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  error_code: string | null;
  result: NewsExtraction | null;
  created_at: string;
  updated_at: string;
}

export interface NewsArticleDetail {
  article: Omit<CapturedInput, "publisher"> & {
    id: number;
    publisher_source_id: string;
    fetched_at: string | null;
    first_seen_at: string;
    last_seen_at: string;
    article_error: string | null;
    review_state: string;
    feed_entries: { source_id: string; feed_url: string; feed_guid: string; first_seen_at: string; last_seen_at: string }[];
  };
  publisher: string;
  body_status: BodyStatus;
  runs: NewsRun[];
  versions: { id: number; input_fingerprint: string; input_snapshot: CapturedInput; created_at: string }[];
  history_total: number;
  history_limit: number;
  read_only: true;
  flood_summaries: Record<number, NewsFloodSummary[]>;
}

export interface NewsFloodSummary {
  location: string;
  area: string | null;
  location_qualifier: string | null;
  water_level: string;
  condition: string;
  passability?: string;
  flood_time: string | null;
  flood_time_label: string;
  map_status: string;
  reading_status: "reported_location" | "needs_checking";
  reading_reason: string | null;
}

export function getNewsArticles(filters: NewsArticleFilters, signal?: AbortSignal) {
  const params = new URLSearchParams({ page: String(filters.page), page_size: "12", order: filters.order });
  for (const name of ["search", "publisher", "body", "processing"] as const) {
    if (filters[name]) params.set(name, filters[name]);
  }
  return apiClient.get<NewsArticlePage>(`/admin/news/articles?${params}`, { signal });
}

export function getNewsArticle(id: number, signal?: AbortSignal) {
  return apiClient.get<NewsArticleDetail>(`/admin/news/articles/${id}`, { signal });
}

export interface NewsResultItem {
  key: string;
  run_id: number;
  claim_index: number;
  article_id: number;
  article_version_id: number;
  title: string;
  publisher_source_id: string;
  publisher: string;
  published_at: string | null;
  extracted_at: string | null;
  captured_at: string;
  saved_at: string;
  claim: NewsClaim;
  summary: NewsFloodSummary;
}

export interface NewsResultPage {
  items: NewsResultItem[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
  publishers: { id: string; label: string }[];
  scope: "latest_reported_locations";
  read_only: true;
}

export interface NewsResultFilters {
  page: number;
  search: string;
  publisher: string;
  condition: string;
  placement: string;
  order: string;
}

export interface NewsResultDetail {
  item: NewsResultItem;
  claim: NewsClaim;
  captured_input: CapturedInput;
  input_fingerprint: string;
  pipeline_version: string;
  extraction_errors: string[];
  is_metadata_only: boolean;
  lifecycle_status: "not_available";
  read_only: true;
}

export function getNewsResults(filters: NewsResultFilters, signal?: AbortSignal) {
  const params = new URLSearchParams({ page: String(filters.page), page_size: "12", order: filters.order });
  for (const name of ["search", "publisher", "condition", "placement"] as const) {
    if (filters[name]) params.set(name, filters[name]);
  }
  return apiClient.get<NewsResultPage>(`/admin/news/results?${params}`, { signal }).then((data) => {
    if (data.scope !== "latest_reported_locations" || !data.items.every((item) => item.summary)) throw new Error("Update the backend to load the current flood locations.");
    return data;
  });
}

export function getNewsResult(runId: number, claimIndex: number, signal?: AbortSignal) {
  return apiClient.get<NewsResultDetail>(`/admin/news/results/${runId}/${claimIndex}`, { signal }).then((data) => {
    if (!data.item.summary) throw new Error("Update the backend to load flood details.");
    return data;
  });
}

export type CollectionStatus = "ready" | "needs_checking" | "excluded" | "no_locations" | "waiting" | "processing" | "processing_failed" | "retrieval_failed" | "missing_text";

export interface NewsCollectionItem extends NewsArticleItem {
  collection_status: CollectionStatus;
  collection_label: string;
  collection_reason: string;
  location_count: number;
  questionable_count: number;
}

export interface NewsCollectionPage {
  items: NewsCollectionItem[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
  counts: Record<CollectionStatus, number>;
  publishers: { id: string; label: string }[];
}

export interface NewsCollectionFilters {
  page: number;
  search: string;
  publisher: string;
  status: "attention" | "all" | CollectionStatus;
}

export function getNewsCollection(filters: NewsCollectionFilters, signal?: AbortSignal) {
  const params = new URLSearchParams({ page: String(filters.page), page_size: "12", status: filters.status });
  if (filters.search) params.set("search", filters.search);
  if (filters.publisher) params.set("publisher", filters.publisher);
  return apiClient.get<NewsCollectionPage>(`/admin/news/collection?${params}`, { signal });
}

export interface NewsSource {
  id: string;
  publisher: string;
  article_domains: string[];
  feed_urls: string[];
  verified_at: string | null;
  enabled: boolean;
}

export interface NewsFeedCheckpoint {
  source_id: string;
  feed_url: string;
  last_checked_at: string | null;
  last_success_at: string | null;
  last_error: string | null;
}

export function getNewsSources(signal?: AbortSignal) {
  return apiClient.get<NewsSource[]>("/admin/news/sources", { signal }).then((data) => {
    if (!Array.isArray(data)) throw new Error("Publisher configuration is unavailable.");
    return data;
  });
}

export interface NewsMonitoringSummary {
  read_only: true;
  articles_total: number;
  body_counts: Record<BodyStatus, number>;
  latest_processing_counts: Record<ProcessingStatus, number>;
  recent_retrieval_issues: { article_id: number; title: string; publisher: string; body_status: BodyStatus; article_error: string | null; last_seen_at: string }[];
  issue_limit: number;
  discovery_history: "recorded";
  fallback_history: "recorded";
  collection_to_alert_delay: "unavailable";
}

export function getNewsMonitoring(signal?: AbortSignal) {
  return apiClient.get<NewsMonitoringSummary>("/admin/news/monitoring", { signal });
}

export type TelemetryKind = "discovery" | "fallback";
export interface NewsTelemetryPage {
  read_only: true;
  items: {
    id: number;
    status: "running" | "completed" | "failed" | "interrupted";
    started_at: string;
    finished_at: string | null;
    error_code: string | null;
    trigger: string | null;
    article_id: number | null;
    retrieve_articles: boolean | null;
    retry_after_seconds: number | null;
    feeds: { source_id: string; feed_url: string; status: string; checked_at: string; error_code: string | null; entries_seen: number; candidates_saved: number; body_errors: number; scope_unresolved: number }[];
    leads: { ordinal: number; article_url: string; source_id: string | null; retrieved_at: string | null; retrieval_status: string; error_code: string | null; assessment: string | null }[];
  }[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export function getNewsTelemetry(kind: TelemetryKind, page: number, signal?: AbortSignal) {
  return apiClient.get<NewsTelemetryPage>(`/admin/news/monitoring/${kind}?page=${page}&page_size=5`, { signal });
}

export function getNewsFeedCheckpoints(signal?: AbortSignal) {
  return apiClient.get<NewsFeedCheckpoint[]>("/admin/news/feeds", { signal }).then((data) => {
    if (!Array.isArray(data)) throw new Error("Saved feed checks are unavailable.");
    return data;
  });
}
