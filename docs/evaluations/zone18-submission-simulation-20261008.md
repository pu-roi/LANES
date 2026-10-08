# Approved-citizen submission simulation and cross-barangay footprints

> **Last Updated:** October 08, 2026, 10:33 PM (Asia/Manila)

**Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

The developer requests a fix for Zone #18 showing unavailable in San Nicolas/Santo Tomas. The adapter required one barangay and supplied recording-proxy simulations only for manually registered official zones. This delivery fixes those two limits without new user inputs or imputed flood-onset clocks.

## Runtime policy

Validate the complete geometry against the same-source Pasig parent before resolving positive-area barangay memberships. Retain all intersected names and explicitly identify pooled multi-barangay scope. Preview validation checks every supplied footprint barangay; an out-of-cohort member requires pooled transfer even when another member is trained. The intercept-only model returns the same duration distribution, with no geographic/area weighting or new local effect. Outside-city, missing/invalid catalog and invalid geometry still abstain.

When qualified actual wet observations are absent, an approved citizen source can supply a separate `submission_simulation`. Require the original untimed citizen audit, matching owner and geometry digest, validated road, current zone/event correspondence and staff approval audit matching both report and zone. Submitted/approved/audit clocks must be chronological and nonfuture; changed report/zone versions, explicit malformed observation times, zone edits, follow-ups, later public evidence, expiry/inactivity and unsupported age stop the fallback. An invalid linked source cannot fall back to unrelated manual registration.

The immutable submission recording is the proxy reference; the approval audit is the fixed availability/issuance anchor. Neither is written into observed_at. Existing official-registration simulations remain supported. Both are research responses, not physical dryness, public passability, training outcomes or operational expiry decisions.

The existing Overview automatically labels report-submission versus official-registration simulations and keeps all detected names. Calculation details identify Citizen report submitted and show the same exact formula; source details retain the report/submission/approval audit IDs. No form, new page/tab, bubble prediction or Moderation section is introduced.

Different zones can produce different dates from their own source clocks and different remaining times from the conditional age. This does not mean the baseline has learned different durations for individual barangays/roads. Location/depth/weather effects still require independent matched outcomes and group-aware comparison through the developer-selected future LANES reporting/review path; previously worse candidates remain unselected.

## Real Zone #18 verification

The saved valid footprint is entirely inside Pasig, with approximate polygon-area shares San Nicolas 72.641% and Santo Tomas 27.359%. These shares are locality diagnostics, not model coefficients. The approved linked citizen report is #16 in event #18. Its source audit #164 records October 8, 9:15:04.352185 PM PHT and `observed_at=null`; staff approval audit #166 records 9:15:49.319456 PM PHT. Geometry and ownership match, and neither source nor zone has a later disqualifying change at this checkpoint.

A local ASGI GET using current staff capability checks and the real database in a repeatable-read/read-only transaction returns HTTP 200 with no-store, both barangay names and `citizen_submission_proxy_simulation`. The proxy age at the approval anchor is approximately 0.749455 minutes. Returned model quantiles are:

| Percentile | Simulated reported-subsidence time (PHT) |
| --- | --- |
| 10th | October 9, 7:01:17 AM |
| 50th | October 9, 2:52:59 PM |
| 90th | October 10, 5:04:13 AM |

The observed-evidence state remains unavailable/reference null; the separate simulation is usable and labeled in the UI. Repeating the calculation later preserves forecast timestamps. Geometry, status, expiry and the null original observation clock remain unchanged. No cloud API revision was deployed; this verifies the local code against actual records, not live browser rollout or prediction accuracy. The response-only snapshot remains ignored under frontend/test-results.

## Checks and limits

Seventy-seven backend/model/location checks pass across submission qualification, private read/permission/serialization behavior, all 30 locality fixtures, multi/outside-city geometry and original preview contracts. Negative cases include mismatched source/approval, missing actor, pending status, geometry/event/locality conflicts, edited versions, explicit/future clocks, follow-ups/public updates, unsupported age and closed/expired zones. The first run exposed incomplete transient-user fixtures and an outside-city empty-membership response; both are corrected without relaxing authentication.

Twelve targeted desktop/mobile workflows pass: citizen and official-registration proxies, formula walkthrough for recording/observed clocks, prediction retry and current-input retry. TypeScript/scoped ESLint pass. This run overlaps earlier walkthrough checks; do not add counts to claim a new complete platform suite. The new citizen case uses synthetic authenticated presentation fixtures; the database-backed verification above separately proves the real source selection. Responsive screenshots are inspected under ignored frontend/test-results/submission-proxy.

Docker remains stopped after the prior Windows socket/WSL issue, so disposable native database mutation/migration checks are not rerun. No SQLAlchemy/Alembic definition or package change is made. Both selected model artifact hashes and the mathematical kernel remain unchanged; no observed label backfill, source-data edit, zone status/expiry/routing write, commit, push or deployment occurs. Matching API/frontend publication is required before the cloud UI shows the new simulation.
