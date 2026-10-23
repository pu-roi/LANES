# NER → Gemini — guarded cloud release

> **Last Updated:** October 22, 2026, 7:54 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

The matching backend/readers now serve navlanes.live through `lanes-api-gemini-20261022-v4` at 100% traffic. The separate unscheduled `lanes-news-verified` job uses the same unchanged Gemini secret binding. **Actual provider acceptance is blocked: the single authorized real request returned HTTP 402.** No accepted real-model correction or three-article seed is claimed. No billing setting/key was changed. The provider's error body was deliberately not retained, so its exact account-level payment restriction is not established.

## Release and checks

- Worker: Linux amd64, 1 CPU/3 GiB, 600-second timeout, one task, zero automatic retries. Default `preflight` is read-only; general provider execution remains disabled. `resolve` requires explicit enablement and an exact target/input/assets/model authority; at most two articles/invocation. It creates no event/report/zone/publication. Ordinary RSS method/job spec and disabled historical seed spec remain unchanged.
- `news_verified_cloud.py` verifies frozen application files, authenticated unchanged original NER/runtime assets, exact Cloud SQL target/schema, selected derived/raw reader versions, paused news settings and configured credential binding. Database credentials remain in the processing parent; existing isolated neural execution is unchanged.
- `news_verified_contract.py` checks source-clock assignment, publication-time fallback, saved recomputation, unsupported-clock rejection and HTTP 401/429/503/302 handling without retries/redirects. Contract-only execution blocks outbound sockets. The local network-disabled image and actual Cloud Run contract both pass seven cases, with zero external requests/database writes/neural inference.
- `news_verified_provider_check.py` uses a short fictional complete article and source-authored neural mentions, not model predictions. Real transport is limited to one request, 30 seconds, one candidate batch and bounded structured output. Execution `lanes-news-verified-7wz4v` received HTTP 402 and stopped without retrying or writing to the database. This proves provider reachability, not NER accuracy or model correction quality.
- **60 local checks pass**, including real migrated disposable PostGIS handoff/readers/evaluation, source suppression, concurrency, completed reuse, guarded failures, read-only cloud preflight and mocked provider failures. Initial development-environment runs rejected disposable writes; rerunning with explicit `ENVIRONMENT=test` passes. Earlier failed attempts remain privately retained.
- Canary and promoted authenticated API reads pass existing response shapes, empty flood/history/report/moderation/zone results, analytics/export, all 174 collection records across pagination, preserved community content/accounts, and unauthenticated admin rejection. No frontend artifact was deployed or UI source edited for this release.
- Cloud contract peak memory: 898,883,584 bytes; provider attempt: 900,227,072 bytes, below approved headroom. Both pass the approved Cloud Run resource profile. Host-no-swap evidence is retained without claiming an enforced cgroup swap limit.

Hosted desktop/mobile acceptance passes across the combined main and focused spatial runs, retained in private `hosted-ui-acceptance.json`, `hosted-ui-v2/summary.json` and `hosted-spatial-v3/spatial-summary.json`. Initial spatial selectors ran before hydration or used a misencoded middle dot; corrected focused selectors pass, with no browser errors or failing API reads. Earlier selector failures remain retained. Empty cards/maps/exports are verified; populated article evidence, corrected times, map focus and archived/active demonstration admission require the later three selected articles. The exact screenshot's 4:34 PM source has not been replayed.

## Preservation and operating state

Full before/after row fingerprints match, with unchanged constraints/triggers/sequences. Accounts: 8; community posts: 37; original articles: 174; versions: 224. Extraction runs, flood events/reports/zones and all targeted flood outputs remain empty. Existing news scheduler is paused; collection/processing/publication flags are false. Zone-expiry scheduling remains enabled. Existing API resource limits, other environment bindings and ingress are preserved.

`Verified.Dockerfile` packages current application/scripts and separately frozen release/reader manifests with authenticated NER/reference assets. It does not carry old Part 2A execution authorities. Exact image/platform/release/reader/pipeline hashes and execution IDs are in [summary.json](summary.json). Deployment descriptions, safe provider receipts, logs, failed attempts, screenshots and preservation snapshots are private under `data/ner-gemini-cloud-20261022/`; secrets/source bodies are not copied into this report.

## Remaining acceptance and rollback

Resolve provider payment/model access, then make a separately controlled successful real request before choosing and processing the three articles. Funding alone cannot prove key restrictions, structured-output compatibility or extraction quality. Fresh raw NER runs are required because the reset removed all previous live run IDs. Re-freeze exact input/authority manifests; do not reactivate old batches. This release does not execute new seeding, Part 2B activation or automation restart.

Rollback restores API traffic to retained revision `lanes-api-history2a-20261022-v3` and disables manual seed/provider execution. Keep existing news pauses and all database/receipt evidence. No database restore/reset is required for this release, which performed no database writes. Do not overwrite earlier manifests or delete failure receipts.

[Implementation plan](../../plans/ner-gemini-verification.md) · [Operator guide](../../guides/ner-gemini-verification.md).
