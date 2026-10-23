# Saved News Intelligence reader releases

The production API reads immutable saved extraction results. Reading them does not require the inference-worker image, an LLM request or a full model bundle.

## Packaged contract

The nonsecret manifest is tracked at `backend/runtime_data/news-reader/read-context.json`, with its canonical SHA-256 pinned in `news_reader_release.py`. It selects the existing primary/fallback processing identities and authenticates the database binding. Changes require explicit review of the selected processing history; do not regenerate it from whichever run happens to be newest.

The normal Docker build verifies the packaged manifest offline. API deployment explicitly configures:

- `LANES_NEWS_NATIVE_READ_CONTEXT=/data/news-reader/read-context.json`
- `LANES_NEWS_NATIVE_READ_CONTEXT_SHA256` from the reviewed package
- `LANES_NEWS_NATIVE_READ_REQUIRED=1`

Startup rejects missing/invalid configuration and mismatched databases before readiness. A required native reader must never silently become a legacy-only reader. Do not remove these settings to hide a 503.

## Checked deployment

`cloudbuild.yaml` runs `backend/scripts/deploy_api_checked.py` after image tests and the existing migration gate. The deployer creates a zero-traffic tagged revision and a release-specific Cloud Run read-check job using the API's existing runtime identity, Cloud SQL binding and database/signing credentials. Only those credentials are copied; provider secrets are excluded. The private temporary descriptor is deleted, and credentials never enter command arguments or logged receipts.

The job performs read-only database validation and authenticated GETs for results, counts, pagination, filters, details, article history and Collection Status. It compares the candidate against both the selected database projection and the serving revision, and checks that unauthenticated requests remain rejected. Valid metadata-only legacy records are supported. Failure leaves serving traffic unchanged. A concurrent serving-traffic change also blocks promotion.

API release readiness must not execute RSS processing or overwrite news/expiry/manual-worker specifications. Deploy those workers separately under their existing controls. The reader-check job runs with zero automatic retries and no provider credentials. It does not execute the application's startup seeding or retention worker.

## October 24 recovery and integration gate

The repaired API is `lanes-api-reader-recovery-20261024-v1`; v30 remains the retained traffic-recovery revision. The automatic backend trigger was disabled during recovery. **Keep it disabled until the repaired Docker/package/deployer/tests and `cloudbuild.yaml` are present on its configured deployment branch, `main`.** A push to another branch alone is insufficient. Review/merge through the normal protected-branch process, inspect that branch's actual files, then restore the trigger's previous enabled state. Do not merge unrelated local frontend edits as part of this repair.

For recovery, restore traffic to the retained working revision and keep the trigger disabled while investigating the candidate/check-job receipts. Do not reset the database, replay articles or call Gemini to repair a reader outage. See the [recovery evaluation](../evaluations/news-reader-recovery-20261024.md).

## Required history-detail gate

Before publishing or changing cloud resources, Cloud Build runs `check_history_media_ci.sh` against the built image. It creates an owned `postgis/postgis:15-3.4` container and an empty template0 database, requires explicit disposable test configuration, runs 18 media/auth checks and fresh/repeated migrations, and removes only its owned container. Missing configuration fails rather than skips. It never uses Cloud SQL credentials.

The protected read-check also selects up to three existing genuine history events (76 in this release), compares overview media/count fields and first pages of all five evidence collections against read-only database expectations. It must not compare repaired details to a broken baseline. Desktop/mobile acceptance opens the actual modal, changes evidence tabs, scrolls and focuses the map.

Manual history repair `lanes-api-history-details-20261024-v1` has passed. Keep the trigger disabled during integration. After scoped PR merge, verify exact `main` source, re-enable the existing `^main$` trigger and run it once pinned to the merge SHA. Check build, candidate, serving traffic and protected fingerprints. If integration permissions/checks block merge or build fails, retain the reviewed serving revision and record the blocker; never force-push or bypass protection.
