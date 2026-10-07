# Functional LANES System Settings — implemented contract

> **Date:** October 7, 2026, Asia/Manila
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **State:** Local implementation; production activation is a separate release gate.

## Operational policy

| Group | Behavior and defaults |
|---|---|
| Flood zones | Future staff road operations use 25 metres, configurable 1–100. Saving settings never resizes zones. Automatic news corridors retain their fixed 25-metre policy. |
| Evidence expiry | Each canonical depth plus unknown defaults to 120 minutes, configurable 30–120. Deadlines use supported observation time and are saved with decisions. Expiry means Unconfirmed; accepted matched clearance is required for Cleared. News retention defaults to 24 hours, configurable 1–72. Explicit staff deadlines remain authoritative. |
| Citizen approval | Staged disabled until release acceptance. Defaults: trust 75/100, documented human accuracy 90%, five human-reviewed reports. Thresholds are configurable; minimum human reviews is 1–100. Automatic approvals never credit reputation or count as human reviews. |
| News automation | Separate automatic collection, extraction/evaluation and publication/plotting switches. Database interval is 15/30/60 minutes, default 30. Publishers are selected only from the verified server-owned registry. |

Citizen approval additionally requires authenticated active accounts, explicit observations no more than 30 minutes old, known consistent depth/severity/access/hazards and server-reconstructed road geometry in supported coverage. Points, fallback geometry, uncertainty and contradictions remain in review. Existing support must match one unexpired zone and its road core/conditions. New zones require two distinct eligible reporters with continuous shared road coverage; duplicate text or copied media cannot supply corroboration. Partial support retains only its own contained extent, while fresh full-section evidence can refresh an automatic zone. Staff-managed deadlines are preserved.

Observation evidence, road/media digests, policy, supporting reports, deadlines and decision reasons use existing audit JSONB and event timelines. Staff see automatic outcomes and retain correction/deactivation tools. This policy does not adopt or invoke the separate duration research model.

## API and worker

`GET/PUT /api/v1/admin/settings/configuration` expose typed settings, revision, update metadata, supported options and recorded runtime health. Reads require `settings=view/full`; writes require `full`. Unknown keys and invalid ranges fail validation. Advisory serialization and expected revisions prevent lost updates; settings, revision and audit commit together. Response construction occurs before commit. Legacy rows are retained, legacy GET remains compatible, and legacy PUT returns actionable HTTP 410.

`--scheduled` uses a session advisory lock and database due checks on a fixed 15-minute Scheduler tick. Duplicate delivery cannot repeat due collection or already committed decisions. Paused stages preserve evidence. Expiry and already qualified clearance maintenance remain independent, including clearance across expiry-only policy changes. Publication rechecks current policy and its switch inside the commit transaction. Disabled publishers retain queued work for later resumption.

Health shows recorded stage attempts, successes, counts, outcomes and safe errors. Enabled controls are not evidence that the deployed worker is running. A healthy collection with zero eligible reports is not a plotting acceptance result.

## Verification and release

See [controlled verification](../evaluations/functional-system-settings-20261007.md) and the [concrete rollout sequence](../guides/system-settings-rollout.md). Release matching API, worker and frontend before changing the cloud tick, then enable citizen approval after acceptance. Current production cadence and live plotting results remain distinct from local fixtures.
