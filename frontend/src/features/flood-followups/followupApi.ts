import { apiClient } from "@/lib/apiClient";

export type FollowupCondition = "still_flooded" | "subsided";
export type FollowupReviewState = "pending" | "accepted" | "rejected";

export interface FollowupSubmissionPayload {
  request_id: string;
  condition: FollowupCondition;
  observed_at: string;
  evidence_text: string;
  depth_cm: number | null;
  source_url: string | null;
  same_location_confirmed: true;
}

export interface FollowupReviewPayload {
  decision: "accepted" | "rejected";
  evidence_text: string;
  same_location_verified: boolean;
}

export interface FloodFollowup {
  id: number;
  request_id: string;
  report_id: number;
  user_id: number;
  condition: FollowupCondition;
  observed_at: string;
  submitted_at: string;
  evidence_text: string;
  depth_cm: number | null;
  source_url: string | null;
  same_location_confirmed: boolean;
  original_observed_at: string | null;
  original_available_at: string | null;
  original_observation_audit_id: number | null;
  location_snapshot: {
    city: string | null;
    barangay: string | null;
    human_readable_location: string | null;
    geometry_sha256: string | null;
    zone_id: number | null;
    event_id: number | null;
    report_id: number;
  };
  review_state: FollowupReviewState;
  review: ({ id: number; reviewer_id: number; reviewed_at: string } & FollowupReviewPayload) | null;
  source_claim_only: true;
  model_admitted: false;
}

export interface OwnerFollowups {
  follow_ups: FloodFollowup[];
  can_submit: boolean;
  ineligibility_reason: string | null;
}

export interface FollowupReviewPage {
  follow_ups: FloodFollowup[];
  next_before_id: number | null;
}

export const ownerFollowupKey = (userId: number, reportId: number) => ["flood-follow-ups", "owner", userId, reportId] as const;
export const adminFollowupKey = (userId: number) => ["flood-follow-ups", "admin", userId] as const;

export function getOwnerFollowups(reportId: number) {
  return apiClient.get<OwnerFollowups>(`/reports/${reportId}/follow-ups`);
}

export function submitFollowup(reportId: number, payload: FollowupSubmissionPayload) {
  return apiClient.post<FloodFollowup>(`/reports/${reportId}/follow-ups`, payload);
}

export function getFollowupReviewPage(reviewState: FollowupReviewState | "all", beforeId: number | null) {
  const params = new URLSearchParams({ review_state: reviewState, limit: "100" });
  if (beforeId !== null) params.set("before_id", String(beforeId));
  return apiClient.get<FollowupReviewPage>(`/admin/flood-follow-ups?${params.toString()}`);
}

export function reviewFollowup(followupId: number, payload: FollowupReviewPayload) {
  return apiClient.post<FloodFollowup>(`/admin/flood-follow-ups/${followupId}/review`, payload);
}

export function exportFollowupReviewPage(reviewState: FollowupReviewState | "all", beforeId: number | null) {
  const params = new URLSearchParams({ review_state: reviewState, limit: "100" });
  if (beforeId !== null) params.set("before_id", String(beforeId));
  return apiClient.download(`/admin/flood-follow-ups/export?${params.toString()}`, `flood-follow-ups-${reviewState}-${beforeId ?? "latest"}.json`);
}
