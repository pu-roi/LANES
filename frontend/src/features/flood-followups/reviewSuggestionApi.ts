import { apiClient } from "@/lib/apiClient";

export type ReviewSuggestionState = "no_suggestion" | "scheduled" | "due" | "evidence_changed" | "followup_received" | "evidence_stale" | "case_closed";
export interface WetEvidence {
  audit_id: number;
  review_id: number | null;
  observed_at: string;
  available_at: string;
  provenance: "original_citizen_observation" | "accepted_owner_followup";
}
export interface CaseReviewSuggestion {
  report_id: number;
  location: string | null;
  zone_id: number | null;
  can_issue: boolean;
  ineligibility_reason: string | null;
  reference: WetEvidence | null;
  latest_wet: WetEvidence | null;
  state: ReviewSuggestionState;
  state_reason: string | null;
  evaluated_at: string;
  suggestion: {
    id: number;
    issued_at: string;
    issued_by: number;
    suggested_review_at: string;
    reference: WetEvidence;
    latest_wet: WetEvidence;
    model: { model_sha256: string; algorithm: string; target_version: string };
    quantiles: { quantile: number; remaining_minutes: number; estimated_reported_subsidence_at: string }[];
  } | null;
}
export interface SuggestionRequest {
  request_id: string;
  acknowledge_research_limitations: true;
  assume_continuous_wet: true;
}
export const suggestionKey = (userId: number) => ["flood-review-suggestions", userId] as const;
export const getCaseSuggestion = (reportId: number) => apiClient.get<CaseReviewSuggestion>(`/admin/reports/${reportId}/review-suggestion`);
export const saveCaseSuggestion = (reportId: number, payload: SuggestionRequest) => apiClient.post<CaseReviewSuggestion>(`/admin/reports/${reportId}/review-suggestion`, payload);
export interface DurationModelStatus {
  status: "research_model_available" | "model_unavailable";
  supported_barangays: string[];
  model_sha256: string | null;
  prediction_barangays?: string[];
  geographic_policy?: string;
}
export interface DurationPreviewRequest {
  city: "Pasig";
  barangay: string;
  reference_at: string;
  prediction_as_of_at: string;
  reference_policy: "first_recorded_wet_in_episode";
  acknowledge_research_limitations: true;
  assume_continuous_wet: true;
}
export interface DurationPreview {
  status: "research_estimate" | "abstained";
  abstention_reason: string | null;
  reference_at: string;
  prediction_as_of_at: string;
  input_provenance?: "staff_supplied_hypothetical_not_verified_case_evidence" | "admin_registration_proxy_simulation" | "citizen_submission_proxy_simulation";
  model: DurationModelStatus;
  quantiles: { quantile: number; remaining_minutes: number; estimated_reported_subsidence_at: string }[];
  pooled_geographic_transfer?: boolean;
  calculation?: DurationCalculation | null;
}
export interface DurationCalculation {
  schema_version: "lognormal_aft_calculation_v1";
  reference_at: string;
  prediction_as_of_at: string;
  elapsed_minutes: number;
  log_duration_location: number;
  log_duration_scale: number;
  probability_before_anchor: number;
  quantiles: (DurationPreview["quantiles"][number] & {
    total_minutes: number;
    adjusted_probability: number;
    normal_score: number;
    remaining_duration_display: string;
  })[];
}
export const getDurationModel = () => apiClient.get<DurationModelStatus>("/admin/news/duration-model");
export const previewDuration = (payload: DurationPreviewRequest) => apiClient.post<DurationPreview>("/admin/news/duration-preview", payload);
export interface ZonePrediction {
  zone_id: number;
  state: "estimated" | "unavailable" | "needs_review" | "expired" | "inactive";
  reasons: string[];
  city: string | null;
  barangays: string[];
  coordinates: [number, number] | null;
  boundary_revision: string | null;
  nearby_report_count: number;
  evaluated_at: string;
  prediction_as_of_at?: string | null;
  reference: { source_kind: string; source_id: number; report_id: number | null; observed_at: string; available_at: string } | null;
  latest_wet: ZonePrediction["reference"];
  evidence: NonNullable<ZonePrediction["reference"]>[];
  model: DurationModelStatus | null;
  quantiles: DurationPreview["quantiles"];
  continuity_assumed: boolean;
  research_only: boolean;
  changes_status_expiry_or_routing: false;
  pooled_geographic_transfer?: boolean;
  warnings?: string[];
  registration_simulation?: DurationPreview | null;
  registration_audit_id?: number | null;
  submission_simulation?: DurationPreview | null;
  submission_report_id?: number | null;
  submission_audit_id?: number | null;
  submission_approval_audit_id?: number | null;
  calculation?: DurationCalculation | null;
}
export const getZonePrediction = (zoneId: number) => apiClient.get<ZonePrediction>(`/admin/zones/${zoneId}/subsidence-prediction`);
export interface PredictionFeatures {
  schema_version: string;
  recorded_at: string;
  observed_at: string | null;
  depth_cm: number | null;
  depth_basis: string;
  errors: string[];
  environment: { elevation_m?: number | null; rainfall_previous_3h_mm?: number | null; errors?: string[] } | null;
}
export const getPredictionFeatures = (zoneId: number) => apiClient.get<PredictionFeatures>(`/admin/zones/${zoneId}/prediction-features`);
export interface CrossLocationPrediction {
  zone_id: number;
  status: "research_comparison" | "abstained" | "model_unavailable";
  reason: string | null;
  selected_for_primary: false;
  changes_status_expiry_or_routing: false;
  validation_summary: string | null;
  selection_blockers: string[];
  model_sha256: string | null;
  qualified_rows: number;
  shared_outcomes: number;
  trained_locations: string[];
  target_location: string | null;
  depth_cm: number | null;
  depth_basis: string | null;
  reference_basis: "observed_reference" | "registration_proxy" | "submission_proxy" | null;
  source_audit_id: number | null;
  reference_at: string | null;
  source_observed_at: string | null;
  prediction_as_of_at: string | null;
  quantiles: DurationPreview["quantiles"];
  warnings: string[];
  calculation: {
    log_duration_location: number;
    predictive_log_scale: number;
    shared_depth_effect: number;
    local_effect: number;
    coefficient_variance: number;
    unseen_location_variance: number;
    location_outcomes: number;
    transfer_basis: "partial_pooling" | "shared_depth_with_unseen_location_prior";
    uncertainty_method: string;
  } | null;
}
export const getCrossLocationPrediction = (zoneId: number) => apiClient.get<CrossLocationPrediction>(`/admin/zones/${zoneId}/cross-location-prediction`);
export function getSuggestionQueue(beforeId: number | null, actionableOnly: boolean) {
  const params = new URLSearchParams({ limit: "25", actionable_only: String(actionableOnly) });
  if (beforeId !== null) params.set("before_id", String(beforeId));
  return apiClient.get<{ cases: CaseReviewSuggestion[]; next_before_id: number | null; evaluated_at: string; page_scanned: number }>(`/admin/flood-review-suggestions?${params}`);
}
