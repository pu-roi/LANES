# GMA shared-depth historical archives — cloud acceptance

> **Source review, October 23:** The processed input was the older indexed capture, despite a clean publisher capture already existing. This report retains its original execution/consistency evidence; it does not establish original-publisher capture provenance. The five observations/events require reprocessing/review. [Source investigation and deployed reader repair](../news-source-review-20261023.md).

> **Last Updated:** October 23, 2026, 1:31 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Result and review boundary

**Five ended events and five inactive estimated road polygons are saved in Cloud SQL and visible on navlanes.live.** The same five GMA observations remain in News Intelligence. Hosted and local desktop/mobile checks pass. Stop here for user review: Tribune 25, Philstar 274 and active presentation instances remain pending.

The input is unchanged GMA article **47**, original source **137**, native version **574**, immutable NER **375** and completed correction **380**. Failed corrections 376/378/379 are unchanged. No new extraction run, inference, provider request, token count, retraining or source retrieval occurred.

| Group | Reported road | Event | Inactive zone |
|---|---|---:|---:|
| resolved-n13 | NS Amoranto cor Don Jose St. | 71 | 71 |
| resolved-n14 | NS Amoranto cor Palali St. | 72 | 72 |
| resolved-n16 | Banawe St. | 73 | 73 |
| resolved-n17 | Tabayoc St. | 74 | 74 |
| resolved-n18 | Ubay St. | 75 | 75 |

All observations retain **September 9, 2026, 8:55 AM Asia/Manila**. No supported clearance was available for these groups; the approved administrative closure is **10:55 AM**, with `assumed_two_hours` provenance. The assumed interval is excluded from observed-duration statistics in SQL, Python analytics, APIs and exports. Administrative creation/verification time remains October 23; it does not become the occurrence date.

## Historical-only repair

The former archive writer reused `_operational_zone_attributes`, requiring a confirmed individual canonical depth. Correctly retained shared measurements had no individual scalar, so all five previous archive evaluations were unresolved. That earlier evidence remains unchanged in [the GMA population checkpoint](gma-population.md).

The opt-in `gma-shared-depth-history-v1` policy accepts only the five frozen groups. It revalidates the saved full-article correction, exact passage references, target ownership and membership under the governing depth heading. The shared 37-inch waist heading and 26-inch tire heading both map to **high** using the existing gauge policy. Event `peak_depth`, zone `depth_override`, numeric road-depth projections and inferred passability remain null/absent. Raw text, shared members, quote offsets/IDs, gauge identity and policy/source/resolution hashes are retained in existing evaluation JSON.

The original OSM/NOAH geometry builder runs independently and unchanged. All five bounded estimates pass; they are **estimated road corridors, not measured wet widths or field-verified flood extents**. Shared severity cannot authorize operational publication, activation, missing evidence, approximate/ranged measurements, cross-road facts or model-default severity.

New preview/apply authorities bind the exact database, release/application, assets, article/version/run, retained evidence, five groups, stable session and preview. Previous grants are preserved for their original frozen releases. Only the new manual CLI modes can select this policy; there is no public processing endpoint.

Preview and application recheck source eligibility, closures and matching. The apply transaction takes existing pilot/incident advisory locks and a short event/zone table write lock so operational writers cannot enter the match/insert window. SELECT readers continue. Exact ended matches can receive evidence without changed lifecycle/geometry; ambiguous matches, unequal geometry and active overlap stay unresolved. Existing cases/sources are reused. A new evaluation policy fingerprint appends results without overwriting the five old finalized unresolved evaluations. Repeated execution reuses complete results, including any unresolved outcomes.

Implementation: `backend/app/services/news_gma_shared_history.py`, the optional archive-attributes hook in `news_historical_outputs.py`, `backend/scripts/run_news_gma_shared_history.py` and two new dispatch modes in `run_news_verified_cloud.py`. Normal historical/operational commands retain their defaults. No frontend, public response contract, model, schema, migration or dependency was changed.

## Release and immutable execution evidence

- Serving API is unchanged: **`lanes-api-gma-scoped-20261023-v17`**, existing traffic/specification retained.
- Manual worker image: **`asia-east1-docker.pkg.dev/lanes-project-508809/lanes/lanes-news-verified@sha256:d7dbb92026cbc7db75dfd44cf4ca631b2446ca8b715fbfc989f8480f929f6277`**.
- Release SHA-256: **`b45ada62992ad22ca8716c8cdd9c949ad7a9c82c64f1ca77aeb51d6b6f4cb680`**; 452 application/script files frozen. Raw and corrected pipeline identities remain unchanged.
- Policy SHA-256: `cbaa40f275f8c82c25a7f81e449baa9d54c2c16bc4bf18196bc794c5c92f5cb9`; shared-evidence SHA-256: `9538ab4d16691e3a8e11141fa0fe0e6165904baed98d06e56f5c5dce583a9848`.
- Saved run-380 result SHA-256: `955c983f1c6220407f309356b4dc294afc14a6de46b969ea01997f9c18ad67b0`; full saved resolution SHA-256: `c90ecf16ff8ac280fec30646774402b27336f76101da30836d302985d9d7a437`.
- Preview output SHA-256: **`058244b2bfcd199700b182d1d19baa9cab02a7f9f9f3814ca068d0c5d3a48b3c`**. Preview authority: `be8c4a42380c89de50d9a0c923446e3f25e4a1fff809c8f547b8d0cbc792686f`; apply authority: `6cdb8d6af328e5bd6195d7a601d7b14e1977f64337fb9456446a4aaec1ecca19`.
- Cloud executions: **r2ccc** preflight, **zxtnn** seven software contracts, **z6kw8** read-only preview, **krxqp** atomic apply, **wwls2** repeat; each prefixed `lanes-news-verified-`. All completed successfully without retries. Apply saved five; repeat reported zero writes and no further inference/provider calls.
- Worker retains Linux amd64, **1 CPU / 3 GiB / 600 seconds / zero retries**, supervised entrypoint, default `preflight`, general execution disabled and LANES secret version **2**. Private receipt access adds only conditional create/read grants for the dedicated prefix.

Private GCS receipts/authorities are under `private/news-pilot/20261022-5512bbaa/diagnostics/gma-shared-history-20261023-v1/`. Ignored local evidence is in `data/gma-shared-history-20261023/`: freezes, previous worker/rollback specification, recovery references, immutable dispatch/output receipts, disposable checks, snapshots, API results and screenshots. Credentials and authorization headers are excluded from worker receipts and public logs; private inspection/token/configuration files must never be committed.

The ledger remains **stopped at 36 attempts / US$0.7314696 effective commitment**, with identical object generation/content. The US$1 cap is unchanged. No budget resumption, settlement reset or attempt extension occurred. Hosting/storage and unrelated weather costs remain outside this news allowance.

## Verification and preservation

- **217 regression tests passed** with four settings-database cases initially skipped; those four passed in a separate **six-test reader/authorization run** using a freshly migrated disposable database. The final historical-policy suite has **42 passing tests**, including two additional ended-event restore/editor rejection checks. These figures overlap and are not an additive unique-test total.
- Two runs against disposable PostGIS with actual retained GMA data produced five ended incidents/five inactive polygons, null individual depths and unchanged original runs/evaluations. Changed preview rejection, forced post-flush rollback, concurrent application, repeated reuse, read-only preview, source evidence and duration exclusion pass. Runtime/provider sends are forbidden in these checks.
- The frozen Linux image and deployed cloud worker each pass all seven existing contracts. Network-disabled Linux qualification reproduces the five shared proofs and unchanged corridor checksums without inference or provider calls.
- **58 hosted API checks** and **61 local direct/proxied checks** pass: News Intelligence counts/pagination/details; all historical cards, evidence, polygons and map focus; road/status/severity/source-date filters; SQL analytics; JSON/CSV exports; protected unauthenticated 401; inactive routing exclusions and existing account/report/moderation reads. Local full API checks use the backend directly, with separate Next.js proxy checks for flood readers, matching the actual test setup.
- Hosted and local **1440×1000 desktop / 390×844 mobile** browser checks pass: news/source scrolling, five history cards, filtering, linked captured article, event detail scrolling, map focus, analytics/downloads and unchanged empty active/moderation views. Visual inspection confirms the plotted corridors and source dates. Early harness attempts are retained: one measured desktop overflow before asynchronous evidence loaded, and one local desktop hit cold compilation; waiting for the actual evidence/readiness resolves these without application/UI changes.
- Exactly five evaluations, five events, five zones, fifteen locations and five timeline entries were added. Cases/sources stay **5/5**; evaluations become **10**, preserving the original five. All **175 articles / 226 versions / five extraction runs / eight accounts / 37 community posts** remain exact. Citizen reports, surveys, moderation, active zones and public news decisions remain unchanged. Existing foreign keys, triggers and migration head `f1a9c7e2b604` are unchanged.
- The live site remained available: final snapshots additionally show **three normal `LOGIN_SUCCESS` inserts** and visitor-statistics drift. Every pre-existing audit row matches its original fingerprint. Neither verification browser nor worker called a login endpoint; the existing authentication handler emits those login records. Concurrent records are retained, not erased to force a fingerprint match. No archive code writes either table.

Normal news collection/processing/publication remains paused, both expiry settings stay OFF, and the old seed specification/scheduler states are unchanged. The personal key is unused. No Tribune/Philstar correction, active instance or normal routing exclusion was created.

## Recovery and next step

Review [Flood History](https://navlanes.live/admin/flood-history) and [News Intelligence](https://navlanes.live/admin/news). Remaining source/locality issues in GMA's other row outcomes are retained. Plan Tribune/Philstar and presentation activation separately; this acceptance does not authorize either.

Recovery restores the retained previous manual-worker specification/image and keeps further execution disabled. API v17 already remains unchanged. Retain all archived data, evaluations, receipts and spending evidence; do not reset the database or delete normal concurrent audit/visitor activity.
