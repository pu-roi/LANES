# Pasig expiry v3: engineering acceptance — October 11, 2026

> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe).
> **Database acceptance:** October 11, 2026, 1:49:25 PM, Asia/Manila.
> **Scope:** local app, shared API and matching cloud workers; hosted forecast UI accepted in the October 11, 4:25 PM continuation below. Scientific accuracy remains unqualified.

## Hosted UI continuation — October 11, 4:25 PM PHT

The developer requested resuming all remaining work. Firebase App Hosting rollout **`build-2026-10-11-005`** is accepted from pushed commit `e150fea0a5cfafb55edea95df79c49e00a459f80`. Cloud Build **`60d53a00-4dcb-40da-8bd5-fe8fb79b5ab2`** succeeded at 4:20:50 PM PHT; Cloud Run revision **`lanes-frontend-build-2026-10-11-005` serves 100% traffic**. The [hosted Admin map](https://lanes-frontend--lanes-project-508809.asia-east1.hosted.app/admin/map) now includes the saved primary forecasts and calculations. Earlier local-only/rollout-004 checkpoints below are historical.

- Six actual hosted Info flows pass: zones #50/#37/#36 on desktop 1280×900 and mobile 390×844. Saved medians/deadlines, #50 Manggahan locality, secondary preview initially hidden and no primary overflow are verified against the real shared API.
- Six additional expanded-calculation checks pass on those same zones/screens. Cross-location values and the pooled walkthrough are visible with no overflow. Screenshots of desktop and mobile forecast/calculation flows were inspected; private screenshots remain ignored.
- Matching production API still serves revision `lanes-api-subsidence-v3-20261011-1350` at 100%. Health/database and protected expiry reads pass; historical #17/#18, pooled/cross-location forecasts and activation-retention fallbacks remain intact. Existing scheduled expiry execution `lanes-zone-expiry-qrtrj` completes successfully with one succeeded task. No API/worker/settings/schema/model change was made by this frontend release.
- Four actual public feed widths pass (1920/1280/1024/390): news HTTP 200, no horizontal overflow; desktop navigation/right panels measure 280/376 pixels, tablet navigation 256 pixels, mobile panels hidden. The capped feed measures 720 pixels at 1920 and 488 at 1280. This release also ships the previously pushed navigation spacing preview. [Feed acceptance](community-local-updates-20261011.md#navigation-spacing-hosted-release--october-11-425-pm-pht).

The developer confirms **no additional government flood-history files yet**. Public FOI leads expose a pending request, a referral or delivery to a requester's email rather than an acquired training dataset. Add a prepared [government-data acquisition specification](../guides/pasig-recession-observation-collection.md#government-data-acquisition-specification--october-11-continuation), including section identity, depth basis, successive observations, clearance definition, independent episodes, missing/censored outcomes and provenance. No external request was sent or unverified source admitted.

All eight core documents were audited for this continuation; README indexes the existing acceptance/guide. Database storage and dependency definitions remain unchanged. Previously verified 254 backend/model checks, migration upgrade, TypeScript/scoped lint and 66 responsive fixtures remain applicable because no application source changed. **The hosted UI gate is complete; improved field accuracy remains unproven and requires qualified real outcomes.**

The [initial investigation](pasig-subsidence-availability-audit-20261011.md) found seven unscheduled records among 22 active Pasig zones. Policy `pasig-experimental-ml-expiry-v3` repairs the cache/lifecycle defects and reconciles source locality using the reviewed Pasig geometry catalog. The post-release, repeatable-read, read-only database audit finds **17 active Pasig zones: eight pooled and nine cross-location forecasts, zero unscheduled active zones**. These are snapshot counts, not a guarantee that every future report qualifies for a scientific estimate. The [sanitized acceptance table](pasig-subsidence-v3-active-zones-20261011.csv) records the saved methods, depths and deadlines without reporter identity.

## Repairs and evidence boundaries

1. **Transient negative cache:** #36 was evaluated about 1.25 seconds before its official-registration source audit existed. An unchanged source signature then kept its null forecast cached. Negative results now retry after 60 seconds, while successful forecasts retain their original issuance/deadline. Identical failures do not generate duplicate audit records. A controlled source-clock regression proves later eligibility recovers without inventing a new observation time.
2. **Authoritative locality:** OSM/Nominatim/Photon address labels are suggestions. The final validated road/report geometry resolves city/barangay against the source-consistent 30-barangay COD/PSGC catalog. Existing reports #29 and #30 resolve to **Manggahan**, rather than their submitted Rosario labels. Correction audits #416/#418 preserve submitted labels, geometry fingerprint and source clocks. Their `updated_at` remains `2026-10-11T04:07:14.876428Z` / `2026-10-11T04:17:31.288382Z`. Multi-barangay footprints retain all identities rather than guessing one. Unsupported/outside geometry is not assigned a guessed Pasig locality.
3. **Snapshot compatibility:** an immutable locality correction can reconcile an older source snapshot only when all non-label identity fields and geometry still match. This does not excuse a changed episode, road, extent or observation, grant a pending clearance review, or change training admission.
4. **Evidence expiry after ML abstention:** when an eligible Pasig record has no usable ML result and no retained deadline, the existing configured evidence timer supplies a deadline from immutable **zone activation**, labelled `activation_retention`. It is not a predicted clearing time and does not fabricate wet evidence. Explicit staff deadlines and global pause remain respected. Repeated synchronization cannot extend the deadline or resurrect inactive records.
5. **One primary forecast:** local Active Zones → Info displays the operationally saved method, depth basis, locality, median, uncertainty dates and p90 expiry together. Its calculation disclosure reads the frozen selected calculation. Pooled estimates explicitly disclose that depth/rainfall effects are not learned. Secondary research previews load in their labelled disclosure and cannot replace the saved operational forecast. Historical v1/v2/v3 forecasts remain inspectable after expiry and policy changes.

Current retention settings were preserved, not replaced with a new recession formula:

| Gauge | Evidence retention, minutes |
| --- | ---: |
| Gutter | 30 |
| Half-knee | 40 |
| Half-tire | 60 |
| Knee | 80 |
| Tires | 100 |
| Waist / chest / neck / unknown | 120 |

These timers apply to fallback evidence ageing; they do not change the learned shallow/deep relationship. Expiry becomes **Unconfirmed**, never observed Cleared or an admitted training outcome.

## Record acceptance

| Record | Post-release result, Philippine time |
| --- | --- |
| #36 | Pooled ML recovered at original October 11, 10:40:27 AM registration issuance; p90 expiry October 12, **6:29:36 PM**. |
| #50 | Manggahan locality reconciled; cross-location ML saved at original issuance; p90 expiry October 13, **1:54:41 AM**. |
| #47 / #49 / #54 / #55 / #56 | Inactive with `evidence_expired` timelines and **Unconfirmed** condition. Their activation-based retention deadlines had elapsed. Pending subsided claims were not automatically accepted. Legacy missing wet clocks were not fabricated. |
| #17 / #18 | Original historical forecasts remain visible: October 9, **7:25:02 AM** / October 10, **5:04:13 AM**, despite policy-version changes. |

The five fallback expiries are evidence-lifecycle outcomes. The system did not observe these test floods becoming dry. The developer confirmed the groupmate created reports through the public manual report panel for application testing. Such reports exercise submission, approval, locality, forecasts and expiry; they cannot validate physical duration or become real clearance labels.

## Tests and live checks

- **166 native backend/database tests passed** in a fresh disposable PostGIS database, including expiry/cache recovery, original clocks, pause/fallback changes, historical forecasts, all 30 locality identities, final-road locality, correction identity guards, review and source qualification. Existing Alembic migrations ran through head **`d7e4b9a21c60`**. Three existing multipart/Pydantic warnings remain. No SQLAlchemy model, table, column or migration was added or changed.
- **62 distinct scientific/model tests passed across runs**: the initial run passed 61 and exposed a faulty new synthetic fixture; after repair, the new test passed. Contrary-data curvature abstention is tested explicitly. These tests establish numerical behavior, not field prediction accuracy.
- **66 responsive Playwright scenarios passed**: 33 desktop and 33 mobile in `flood-review-suggestions.spec.ts`, covering selected forecasts/calculations, fallback labels, existing review and request states. TypeScript and scoped lint passed.
- **Six actual, unmocked local Info workflows passed**: zones #50/#37/#36 at 1280×900 and 390×844, using the actual private API. Saved primary forecasts, Manggahan label and initially hidden secondary preview were verified; no horizontal overflow. Desktop/mobile screenshots were visually inspected. These checks are separate from mocked regression fixtures.
- Actual local, tagged-release and production API reads returned healthy database status, unauthenticated expiry-policy **401**, and authorized **200** with expected saved metadata for #17/#18/#34/#36/#37/#47/#49/#50/#54/#55/#56. GET checks made no moderation/training decisions.

No new Python/Node package is imported; declared requirements/package/lock files remain unchanged. Runtime duration coefficients/assets are unchanged. Secrets were supplied through the existing configuration and never included in the release bundle or documentation.

## Shared release and local runtime

| Target | Accepted state |
| --- | --- |
| Cloud Build base | `9140c361-6748-4fe8-800c-f58588e7d8f6`, success. |
| Cloud Build final | `75fdced0-f50a-44a4-98c2-aa49c322b288`, success; final app/scripts layer over the verified base. |
| Final image | `subsidence-v3-20261011-1350`, digest `sha256:aee6d0d95ce6521b9046081060ecfda37262af3a2319a79e4d535407313735a0`. |
| Cloud API | **`lanes-api-subsidence-v3-20261011-1350` serves 100% traffic**, verified after both worker updates. |
| Cloud workers | `lanes-zone-expiry` and `lanes-news-discovery` use the matching final digest; existing arguments, environment, permissions and schedules preserved. |
| Expiry execution | `lanes-zone-expiry-vvsk9` succeeded; scheduled executions `4c45c` and `9qbxb` also succeeded. News discovery was not triggered just for validation. |
| Local app | Matching API on port 8000, independent 60-second expiry worker and actual Next.js map on port 3000 verified. |
| Initial cloud frontend (1:49 PM) | App Hosting `build-2026-10-11-004`; the hosted forecast UI was subsequently accepted in rollout 005 above. |

The API was prepared with zero traffic, checked, then explicitly promoted only after matching workers. Existing rollback references remain available. Workspace changes are on `roi-branch`; this acceptance records direct runtime release, not a new Git commit/push.

## Scientific result and remaining gates

**Later October 11 continuation:** A local offline episode builder now makes the reviewed observation path reproducible, with 26 targeted tests and immutable source/code hashes. The complete live follow-up export contains three pending observations across two reports, no numeric depths and zero eligible real episodes. [Collection readiness](pasig-recession-collection-readiness-20261011/README.md). This adds no new runtime deployment and does not establish scientific improvement.

The pooled model still has no depth input. The cross-location artifact includes depth but changes the gutter-to-knee median by only about **1.5%**, based on 36 projections sharing **three** historical subsidence summaries. Green severity is not a separately learned predictor. Long p90 deadlines cannot be validated as accurate using simulated reports.

An optional nondecreasing central-depth candidate was implemented and evaluated offline with summary/episode purging, location and forward-time folds. Its constraint was inactive: the coefficient and 1.5% shallow/deep difference barely changed. Only three of ten candidate folds were supported and **none of its three forward-time folds were supported**. Across all candidates, 29 of 70 attempts were supported and 41 explicitly abstained. **No runtime model was replaced and no accuracy improvement is claimed.** [Full evaluation and checksums](pasig-depth-shape-candidate-20261011/README.md).

Next, collect safely observed, reviewed wet-to-clearance bounds for the same road section/episode; freeze depth/context available at issuance; retain censoring and independent episode identity. Test reports, administrative approval and automatic expiry cannot supply clearance ground truth. The [collection guide](../guides/pasig-recession-observation-collection.md) uses existing private source/review exports with `training_admitted=false`; no new schema is required for this initial evidence collection. Model promotion needs comparative benefit and calibration on qualified held-out outcomes. Pending historical follow-ups still need authorized human source review; no agent review was substituted.

## Eight-document audit

Task plan, progress, feature reference, Decision 27, system documentation, tech stack, database design plan and BUG-145 were audited and synchronized with this release. README indexes the supporting research, evaluation and collection guide. BUG-145 separates repaired availability/locality from open accuracy qualification. No new flagship feature or decision number was created. Existing dependency/runtime and schema definitions remain in place. The original investigation tables remain historical pre-fix evidence, linked to this post-release acceptance.

## Planner and pre-push audit — October 11, 4:08 PM PHT

**Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe); branch verified as `roi-branch`. The developer requested documentation synchronization and publication of all current changes. This checkpoint records verification before the commit/push; it does not assert a new hosted frontend release or completion of scientific validation.

| Core record | Verified current scope |
| --- | --- |
| `task_plan.md` | Delivered expiry/locality/local UI and offline qualification; real outcomes/calibration and hosted UI remain open. |
| `progress.md` | Newest-first delivered milestones and fresh pre-push checks; historical release evidence retained. |
| `feature-reference.md` | Existing Spatial Operations section updated; no new flagship number. |
| `decisions.md` | Decision 27 separates operational ML expiry from activation-based evidence retention; Decision 26 retains research qualification. No routine publication decision added. |
| `tech-stack.md` | Existing declared libraries reused; no requirements/package/lockfile changes. |
| `others/system-documentation.md` | Selected saved forecast and secondary previews; final-geometry locality and offline dataset entry point; hosted UI distinguished from local. |
| `others/database-design-plan.md` | Existing JSON audit storage; SQL models/migrations unchanged. |
| `others/bug-log.md` | BUG-145 operational defects repaired, accuracy qualification still In Progress. |

README catalogs all new research, evaluation and guide documents. The new offline builder uses complete private staff exports and explicit episode reviews, emits sanitized conditional research candidates, and performs no database write, model promotion or automatic training admission.

Fresh checks on the final source state:

- **166 native backend/PostGIS tests passed**, with three existing warnings. The test fixture calls Alembic `upgrade head` on a fresh disposable database; the database is removed afterward. Existing head is `d7e4b9a21c60`.
- **88 model/dataset tests passed in one clean run**: 62 duration/cross-location checks plus 26 recession-dataset checks, with the same three existing warnings. These are engineering/numerical checks, not field accuracy evidence.
- TypeScript `--noEmit` and scoped lint for all three changed forecast components passed.
- The earlier **66 responsive scenarios and six unmocked desktop/mobile Info workflows** remain applicable; no frontend source changed after that acceptance and those browser runs were not repeated for publication.
- Dependency manifests, SQLAlchemy models and Alembic migrations have no changes. Runtime learned artifacts are unchanged. Private raw exports, operational helpers and release staging remain ignored and excluded from publication.
- Staged audit covers **52 files**, parses all 17 changed/new Python files and ten JSON artifacts, and resolves **931 relative documentation links**. Staged whitespace checks pass; private-path and credential-pattern scans find no matches. The existing expiry endpoint retains authenticated staff/zone-reader checks and private no-store response handling; changed UI keeps visible error/retry states.

Operational acceptance remains the timestamped 1:49:25 PM snapshot above. Current scientific collection evidence is the [2:29 PM recheck](pasig-recession-collection-readiness-20261011/README.md#revalidation--october-11-229-pm-pht): three pending follow-ups, zero numeric depths and zero qualified episodes. Test reports and administrative expiry do not close this evidence gap. Git publication does not establish accurate depth-sensitive recession prediction or verify a new hosted frontend rollout.
