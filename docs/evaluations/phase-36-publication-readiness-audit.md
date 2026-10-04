# Phase 36: Backend publication readiness assessment

> **Last Updated:** October 04, 2026, 3:24 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)
> **Scope:** Source inspection, isolated mocked auditor probe and existing hybrid regressions. No application/model/migration changes, database writes, live model requests, cloud inspection/deployment or new browser acceptance.

## Result and next task

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
