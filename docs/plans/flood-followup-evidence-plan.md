# Structured Pasig flood follow-up evidence

> **Last Updated:** October 08, 2026, 02:42 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Status:** Local backend/owner-flow acceptance complete; staff queue placement, physical PWA and deployment pending. [Recorded verification](../evaluations/structured-flood-followups-20261007.md).

**October 8 future LANES source collection:** Public zone updates and owner follow-ups freeze versioned model inputs/actual-or-null observation clocks and independent review provenance. Public metadata records claimed-point/proposed-road/official-context basis and spot-only scope; new review JSON includes reviewed_zone_version and training_admitted=false. Existing private follow-up exports retain numeric/unknown feature snapshots. Authenticated GET `/admin/zones/{zone_id}/model-evidence` requires both Reports and Zones read capability, uses bounded keyset pagination/no-store, omits personal/free-text/media/request fields and returns explicit qualification blockers without operational writes or automatic training. The data source is the developer-selected future LANES reporting/review workflow; no new input fields or historical backfill. [Acceptance](../evaluations/pasig-location-feature-models-20261008/README.md#developer-selected-future-lanes-evidence-collection). [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 8 continuation

**Placement correction:** The developer subsequently removed Flood condition follow-ups and ML review assistant from Moderation Center, including per-report ML controls. The two staff queue components are unmounted and replacement UI placement is unfinished; native API acceptance and owner follow-ups remain. Existing Active Zone Overview now uses automatic geometry/evidence prediction and a labeled official registration simulation; former case save/test inputs are withdrawn. Actual observation clocks and independently reviewed follow-up admission remain separate. Historical staff queue verification below does not establish acceptance of its location.

Local database/authenticated API and desktop/mobile follow-up acceptance is now complete, and the experimental case-linked staff review assistant is implemented. See [current acceptance](../evaluations/case-linked-ml-review-assistant-20261008.md). The historical checkpoint below preserves what was known on October 7. Physical PWA/deployment, the monitored pilot and qualified prospective model evaluation remain open. No automatic clearance, schema/dependency change or training admission is introduced. [@roicambe](https://github.com/roicambe) (Roi Cambe)

## October 8 model-input continuation

New citizen observations and official create/edit audits now freeze versioned location/gauge/source-clock inputs and cached-or-missing environmental context. This adds no observed time when absent, does not backfill older audits or admit a training label. Protected input inspection fetches current coarse Open-Meteo/Copernicus background; it cannot reconstruct historical availability. Complete 30-barangay prediction locality and failed feature-model comparisons are recorded in [the current evaluation](../evaluations/pasig-location-feature-models-20261008/README.md). More independent matched outcomes are still required; follow-up acceptance, operational clearance and model-label admission remain separate.

## Purpose

The [additional source review](../evaluations/pasig-clearance-followup-20261007/README.md) is complete but supplies zero new subsidence-duration pairs. Create a sustainable way to record same-location **still flooded** and **subsided** follow-ups. Preserve each actual observation, its availability and its subsequent review so future data preparation can evaluate whether it supports a duration label.

The existing DRRMO annual CSV begins with year/barangay/street/landmark/estimated water-level fields. These selected historical rows do not include per-incident observed wet and clearance clocks. An incident-monitoring log with those clocks would be a different export. No incident log was supplied or acquired in this implementation slice.

## Storage and workflow

Use the existing append-only `AuditLog.metadata_json` pattern already used for `CITIZEN_OBSERVATION`. Store versioned `FLOOD_FOLLOWUP_OBSERVATION` and `FLOOD_FOLLOWUP_REVIEW` records under dedicated action types. Do not change SQLAlchemy models, Alembic definitions or generic operational report status. An accepted follow-up may add a readable entry to an existing matching flood-event timeline; it does not end that event.

1. An authenticated owner opens a follow-up under their own nondeleted, unrejected direct-user Pasig report with a mapped location.
2. They explicitly enter when they observed the condition, whether water remained or had subsided, and the evidence/description. Optional measured centimeters and HTTPS source links stay separate. Attesting to the same road section is a user claim, not automated spatial verification.
3. The backend freezes original report/event/zone IDs, city/barangay/place and geometry fingerprint. Submission time is server-recorded and never substituted for observed time. Missing initial observation time stays missing.
4. Staff with report-read capability inspect the queue; staff with full report capability append an independent accept/reject decision, review evidence and location attestation. Self-review is disallowed. If report linkage or location has changed, acceptance must stop until correspondence is resolved.
5. Read-only JSON export preserves observation/submission/review clocks and provenance for later preparation. Accepted evidence is not automatically admitted for model training.

## Contracts and guards

Submission requires an idempotency UUID, explicit timezone-aware nonfuture `observed_at`, condition, supporting text and same-location attestation. Positive depth conflicts with `subsided`; zero conflicts with `still_flooded`. No time is defaulted to form opening, report creation, approval, event end or expiry. When a known original observation clock exists, follow-up cannot precede it.

Use report locks for concurrent submissions and original-follow-up locks for reviews. Repeated identical submission UUIDs return the same record; changed payloads under the same UUID conflict. Bound per-report storage and page size. Review entries never overwrite the original observation. Authentication, ownership, role capabilities, unchanged scope and visible API/UI errors are server-owned.

Source URLs are supporting links, not fetched by the server. No photo upload is added in this first slice; evidence text is mandatory. A source link does not certify its content or historical availability. Raw reporter evidence and staff notes stay in authenticated owner/staff reads, not public maps or feeds.

The profile report list and staff moderation screen expose the same flow on narrow and wide screens with visible loading/error/success states; actual viewport interaction remains unverified. The initial implementation supports follow-ups by the original reporter. Other observers can submit their own reports; automatic association to someone else's incident remains separate work. City/geometry checks are not Pasig polygon containment or physical road verification; preserve that limitation when reviewing claims.

## Dataset qualification after collection

Keep the following separately identifiable: original wet reference, follow-up observation, submission/availability time, staff review time, original spatial snapshot and linked case identities. Review field `accepted` means the source claim was reviewed. It does not establish exact physical dry time, uninterrupted episode, independent storm, absence of recurrence, final predictor availability or representative sampling.

Future preparation must select references without seeing outcomes, use evidence available before issuance, keep shared events/storms together, preserve missing outcomes, qualify scope/continuity and audit reporting bias. Subsidence observed at a later check generally gives an upper bound; it is not automatically the exact first moment water disappeared. The October 7 conditional research model remains separate and unchanged.

## Verification and release

Source-data review and artifact reconstruction are complete. Implementation checks and limitations will be recorded in the dated evaluation. Do not mark durable API, concurrent/idempotent database behavior, authenticated review, desktop/mobile browser interaction or deployment accepted merely because source code compiles. Automated tests were not requested in this task; actual database/browser acceptance remains a release requirement.

No automatic model retraining, zone expiry/clearance/routing/reputation update, public status change or notification to third parties is part of this collection workflow.
