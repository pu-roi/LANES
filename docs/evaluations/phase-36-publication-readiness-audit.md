# Phase 36: Backend publication readiness assessment

> **Last Updated:** October 05, 2026, 7:02 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Later October 5 continuation:** source-alert publication/lifecycle, F6 decisions and F7 desktop/mobile alert views are now implemented locally. This earlier assessment/placement record remains historical; operational zone activation and deployment are still gated. [Current lifecycle evaluation](phase-36-news-publication-lifecycle.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

> **Scope:** Source inspection, isolated mocked auditor probe and existing hybrid regressions. No application/model/migration changes, database writes, live model requests, cloud inspection/deployment or new browser acceptance.

**Subsequent approved implementation:** after the review below, the developer approved the five additive publication tables. Models and migration `d7e4b9a21c60` are implemented and verified in disposable local PostGIS with 60 focused checks. The [storage evaluation](phase-36-news-publication-storage.md) records current delivery; pending-schema statements below describe the review before that approval. Auditor, decision/publication services and operational geometry remain unfinished. No production verification or cloud migration occurred. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

**Subsequent independent evaluation delivery:** BUG-098 provider/context/structured-evidence defects are repaired locally and the approved storage now has immutable claim binding/leased evaluation services. External requests are explicitly configured and remain separate from extraction; no public decisions/zones are created. C5/Pasig route coverage and twenty Pasig OSM community preview polygons including Ugong are delivered locally, while omitted barangays/regions and operational footprints remain unsupported. The probes below retain their original assessment context. [Current verification](phase-36-independent-evaluation-and-spatial-coverage.md).

## October 5 conversation and source reconciliation

Read the three explicitly referenced chats through `read_thread`: **Plan flood zone expiry** (`01a1072a-88d1-7541-ba75-da9e96795b59`), **Review article pipeline progress** (`01a0faf3-a146-74b0-a96f-f6b3c9167d45`), and **Review flood plotting conversation** (`01a105dd-b43a-70b2-aa2b-4fa054aa144b`). Reviewed their relevant recent decisions; also read the older page of the article-pipeline chat for the original priority order and frontend pause. Conversation outputs were treated as historical context and compared with current files. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

| Area | Current evidence and consequence |
| --- | --- |
| Delivery order | The latest expiry-chat correction and lifecycle plan agree: finish AI/automatic plotting, include basic freshness before release, then evaluate expiry/duration primarily in Pasig. No additional broad data collection or model training is prerequisite to publication work. |
| Runtime connection | `news_processing_service.py` calls saved-body extraction and persists immutable results. It does not perform external auditing or public ingestion. `models/news.py` still contains feed/article/version/extraction storage, without the five proposed publication tables. F6 durable decisions and F7 public reads remain implementation work. |
| Auditor | `hybrid_extraction_service.py` still uses `openrouter_api_key or gemini_api_key` for an OpenRouter request, supplies a single user prompt without complete `context_text`, and lacks explicit place/time confirmation in `LLMAuditResult`. BUG-098 remains unresolved; no live provider probe was run in this continuation. |
| Prototype writes | `news_auto_ingestion_service.py` still uses manual-seeder provenance and builds a zone without an expiry. It is not a substitute for the proposed identity, transaction and support lifecycle. |
| Duration evidence | The current follow-up bundle records 819 wet observations and three shared summaries; 37 conditional projections remain training-ineligible. Source review supports reported-subsidence research, not verified physical clearance or a deployed predictor. Data/capture hashes were not re-audited here. |
| Interface | Preserve current local F5 inspection and the current parent plan. Older card/tab proposals in the referenced chat do not override later repository decisions. No frontend edit is included in this continuation. |
| Authorization | Exact five-table schema approval remains pending in the current plan/database reference. Earlier approval for extraction or monitoring migrations is separate. No models/migrations, database state, cloud settings or public zones were changed. |

The [continuation checkpoint](../plans/news-publication-readiness-plan.md#october-5-continuation-checkpoint) makes the next work reviewable: approve the exact additive schema, verify it locally, repair audit/evaluation, implement alert/decision/freshness transactions, then connect zones only with supported geometry. Public status projection, finite Unconfirmed retention and routing uncertainty remain release-policy work. This review used source inspection and documentation consistency checks; no new application tests or deployment acceptance are claimed.

## October 4 result and next task (historical assessment)

F5 inspection is locally implemented. F6 durable decisions and F7 public alerts/zones still need backend work. Existing domain storage can represent verified multi-section incidents, but cannot safely represent unresolved news alerts or durable per-claim publication/correction/expiry. The [concrete readiness contract](../plans/news-publication-readiness-plan.md) proposes five additive tables, transaction ownership, staff/public API contracts and staged acceptance. Exact schema approval and expiry policy are pending; automatic operational geometry remains independently blocked.

## Verified runtime and storage

- `backend/app/services/news_processing_service.py` persists rules-only results under a lease and never calls external audit or public ingestion. `backend/scripts/run_news_discovery.py --process` invokes this worker. Root `cloudbuild.yaml` configures collector arguments `--discover,--process,--limit,50`, not publication/evaluation.
- `backend/app/models/news.py` stores article summaries, immutable article versions and extraction runs. There is no claim decision, alert expiry or operational link table. `NewsArticle.review_state` cannot separate roads with different outcomes.
- `backend/app/models/report.py` already supplies event locations, zone ownership by event, Polygon zones, generic source geometry, zone expiry and event timeline/history. It does not provide pending news claim identity. Event peak severity/verification fields preclude pretending an unknown-depth unresolved alert is a verified event. Report sources contain no news value.
- `backend/app/services/news_auto_ingestion_service.py` is a separate prototype. It labels a report `manual_seeder`, defaults automatic actor to user ID 1, handles only a LineString source core and omits zone expiry. The runtime collector does not invoke it. Current geometry gates fail closed; no current live publication is established by source inspection.
- `create_verified_event_with_zone` in `backend/app/services/flood_event_service.py` commits internally. The prototype later commits article summary separately. `deactivate_zone_and_end_event_if_final` also commits internally. A durable publication service needs backward-compatible transaction participation before recording claim decision, domain writes, links and audit atomically.
- `backend/app/crud/report.py` and routing readers filter active zones by expiry. Reuse those safeguards for news-owned zones; delayed maintenance must not restore routing eligibility. Existing SSE manager in `backend/app/core/sse.py` holds process-local queues. A separate collector process cannot reach API listeners through that manager; durable polling remains necessary.

## Auditor defects reproduced without external calls

`backend/app/services/hybrid_extraction_service.py` chooses `OPENROUTER_API_KEY or GEMINI_API_KEY` and always sends to OpenRouter. Its prompt includes only the extracted evidence sentence and candidate fields; it omits supplied `context_text`. `LLMAuditResult` lacks explicit place/time confirmation fields. An old hard-coded model identifier is source evidence, not proof of present provider availability.

A Python probe used `httpx.MockTransport`, replaced both credential attributes with an empty OpenRouter value and a synthetic Google value, and supplied article context saying the reported road had cleared. The mock returned positive JSON; no network or database request occurred. Observed results:

```json
{
  "provider": "openrouter.ai",
  "google_key_sent_to_openrouter": true,
  "full_article_context_sent": false,
  "structured_place_confirmation_requested": false,
  "mock_positive_audit_accepted": true
}
```

This proves the transport/context defects and permissive audit parsing. It does not prove a live provider approves an incorrect claim or that the publication gates currently activate a road. [BUG-098](../others/bug-log.md#bug-098-dormant-news-auditor-uses-the-wrong-credential-provider-and-omits-article-context) tracks the fixes.

## Geometry and deployment gaps

`backend/app/services/news_road_placement_service.py` explicitly rejects named-barangay claims with `missing_valid_barangay_boundary`. Bundled `pasig_barangay_reference.csv` has names/codes, not authoritative polygons. Frontend Pasig outline/mask and national outline provide different boundaries. Road ranking and current NOAH/DRRMO previews remain read-only and do not supply supported flooded width or operational polygons. Existing reviewed cross-boundary growth is a separate citizen/staff workflow, not proof of automatic multi-barangay news placement.

OSM manifest identifies 17 cities, 66,129 named ways and its immutable source/checksum identity. Pasig history is bundled locally. NOAH analytical tiles are under local root `data/noah-placement`; `.gcloudignore` excludes `data`, Docker builds only the backend context, and `backend/.dockerignore` excludes its own data directory. Docker copies only `runtime_data` into `/data`. Current build instructions therefore do not provision these local NOAH vectors. Public raster tiles are unrelated analytical inputs. Both API and future evaluator need a verified identical vector bundle and boundary/source versions; live production asset/config state was not inspected.

## DRRMO duration follow-up

The developer asked whether existing DRRMO history can set flood duration for monitoring without purchased sensors. Inspected `data/Flooded_Areas_Pasig_City_2020_2025_EDITED.xlsx` using standard-library ZIP/XML reading, the raw CSV headings and every cleaned CSV row. Main sheet headings are `No.`, `Barangay`, `Street`, `Landmark`, `Water Level (Estimated)` under annual headings. The second sheet contains source-text extracts, with no duration/onset/clearance/time/date labels. The cleaned file has 15 fields for source year/record, locality, road/landmark and depth parsing; none represents duration or observation/clearance time.

Therefore current files cannot estimate time until recession. Recommend a provisional two-hour evidence freshness window, then unknown/stale status and new-evidence review, never timer-derived clearance. Exact duration policy remains unapproved. Separate dated DRRMO incident records could support later calibration, with explicit uncertainty and no extrapolation from yearly rows. [PAGASA](https://www.pagasa.dost.gov.ph/learning-tools/floods) describes repeated rainfall/water-level observations for monitoring; report-driven updates cannot establish continuous street-level conditions. No additional data source or scheduled collection was enabled by this follow-up.

## Verification and limits

Executed from `backend`:

```powershell
& .\venv\Scripts\python.exe -m pytest tests/test_hybrid_extraction_service.py -q
```

**7 passed**, with the existing multipart deprecation warning. These tests verify current fail-closed prototype behavior, not durable publication, provider context correctness or release readiness. The mocked diagnostic is separate from those seven regressions. Earlier [automatic plotting investigation](phase-36-needs-review-inspection.md#october-4-automatic-plotting-readiness-audit) recorded 70 distinct focused checks; those were not rerun here. No migration test is claimed for the new proposal because no migration exists.

## Authoritative documentation audit

| Record | Outcome |
| --- | --- |
| Task plan / progress | Record this assessment complete; keep implementation, schema approval, geometry gates and F6/F7/F8 pending. |
| Database design plan | Link exact additive proposal without describing it as current schema. |
| Bug log | Record reproduced auditor defects as investigating, not resolved. |
| Tech stack | No dependency or provider release change; existing manifest unchanged. |
| Feature reference | Update current-stage assessment summary; no newly delivered feature or F6/F7 completion. |
| System documentation | Update current-stage summary; no route/screen implementation, proposed contracts live in the plan. |
| Decisions | No accepted architectural pivot; no new permanent decision. |

The master index and parent publication plan link this assessment. Existing frontend edits and dependency manifests remain unchanged during this task. Next required authorization concerns the exact proposed schema; production rollout is not implied by that authorization.
