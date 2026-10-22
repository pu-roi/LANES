# Local saved-article NER preview

> **Last Updated:** October 20, 2026, 12:58 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

The backend provides `POST /api/v1/admin/news/articles/{article_id}/ner-preview`. It requires existing active-admin authorization and is **disabled by default**. There is no new frontend screen. [Implementation and verification](../evaluations/flood-ner-backend-preview-20261019/README.md) · [Connection specification](../plans/ner-extraction-only-backend-preview.md).

**Current pipeline:** v19 neural locations → unchanged v40 proposals → qualified v44 combined repairs → unchanged v42 grouping. The shared adapter is used by worker and host; the host recomputes the complete proposal chain and graph. [V46 integration and verification](../evaluations/flood-ner-backend-location-v46-20261020/README.md). The backend task is complete; there is no admin interface yet. The reviewed article retains eight corrected location occurrences / 40 restored facts, with 11 unresolved rows. Earlier v42/research results remain preserved history.

## Prerequisites and local use

Use the local FastAPI backend with its existing dependencies, Docker Desktop's Linux engine and the previously qualified image. Do not run the feature in production; production-like environments reject it even if enabled. The API host launches the local Docker CLI; running this API inside another container or in Cloud Run is not supported by this task.

The private inference bundle is not included in Git. Its source checkpoint and base vocabulary must already be available and authenticated. To prepare a new bundle, run `backend/scripts/prepare_ner_preview_bundle.py --help` from the repository root and supply the retained scoped-model manifest/hash, pinned base-resource manifest/hash, base directory and an absent private destination. The command copies the eleven selected model files and five required base-vocabulary files, preserving originals, then prints the bundle manifest hash. It does not download or train anything. Keep the destination inside the ignored training artifacts directory. A failed preparation is retained; choose a new destination after investigating it.

On this verified checkout the prepared bundle is `backend/training/flood_ner/artifacts/ner-preview-bundle-20261019-v1`, with manifest SHA-256 `13137f64b216d2a9f2978f0eb3d278950754dc56731688495b8348f2ad43a8cd`. These private files must be supplied separately on another computer.

For a manual local session, set these process environment variables before starting the backend. This task did not edit `.env` or turn the feature on in the running application.

| Setting | Value |
|---|---|
| `ENVIRONMENT` | `development`, `local` or `test` |
| `NEWS_NER_PREVIEW_ENABLED` | `true` for the intentional local session |
| `NEWS_NER_PREVIEW_BUNDLE` | Absolute path to the authenticated private bundle directory |
| `NEWS_NER_PREVIEW_BUNDLE_SHA256` | SHA-256 of that bundle's `manifest.json` |
| `NEWS_NER_PREVIEW_DOCKER` | Docker executable path, or `docker` when available on PATH |

Start the existing backend from `backend/` with `uvicorn app.main:app --host 127.0.0.1 --port 8000`. Use the existing authentication flow and backend API documentation to authorize an administrator, then POST the ID of an already saved article. No request body is needed. The endpoint reads `article_text`; it does not fetch a missing body, concatenate the title/excerpt, run placement or save an extraction. Limit requests to three per minute. Only one worker runs across local API processes.

Return `NEWS_NER_PREVIEW_ENABLED` to false and restart the backend when the local session is finished. No feature flag is persisted by the preview itself.

## Reading the response

- `source.canonical_url` provides the saved article link. The other `source` fields identify the exact saved body and request snapshot with hashes. Offsets refer to unchanged Unicode body characters. A later article capture may have a different hash; there is no newly created article-version row.
- `neural_mentions` contains only original v19 predictions. `effective_mentions`, `proposals` and `abstentions` expose the final v40 → v44 combined rule view. Proposals are ordered by stage and retain their implementation identities/hashes; abstentions identify their stage. Additions, retags and boundary replacements are labeled rule proposals, with original IDs and exact evidence. Original neural spans are unchanged.
- `groups` contains locations/target IDs and arrays of `depth`, `time`, `status` and `access` facts, with evidence and graph IDs. Groups keep exact target occurrences, evidence and local/shared/collective scope separate. Empty arrays mean nothing was attached. A collective depth is not an exact measurement for each member.
- `graph` retains all extracted facts, relations and expressions; `unassigned` explains facts without a supported location link. Mention-only locations remain visible even when they have no facts. The preview does not invent a parent city or merge repeated events.
- Times retain their roles: observation, onset, report, publication, recession, clearance or unspecified. Publication metadata is separate; unknown timezones/dates are not supplied. A report saying flooding was observed at 6 PM does not establish when it started.
- Subsided/cleared reports remain in the response with their evidence and supporting times. Saving them in history while withholding current map plotting is a later integration requirement.
- `measurements` reports worker startup, extraction elapsed time and peak worker RSS. `provenance` binds the model, tokenizer/resources, code and image. Location provenance is `location_rules: lanes-location-repair-v40+v44`, `location_method: combined`; `context_rules` remains v42. These measurements are runtime evidence, not extraction confidence or independent accuracy.

The preview remains limited by missing/incomplete/mistyped location mentions, three held contextual references, an unresolved non-flood access omission and unmeasured real pure-Tagalog performance. Learned DEPTH/TIME recognition remains unfinished; these fields and their matching use rules. The response carries the general limitations and exposes unresolved fields, including the type family's lack of standalone real correction evidence. The combined view was explicitly selected and qualified as a whole. No verified/current-flood, geometry, publication or route eligibility is implied.

## Failures and cleanup

All successful and handled error responses use `Cache-Control: no-store`. Read the `detail.code` on preview errors: missing article 404; unavailable body 409; oversized body 413; busy/rate limit 429; disabled/environment/storage/assets/runtime/cleanup unavailable 503; deadline 504; invalid/crashed worker 502. Authentication and invalid-ID responses retain the existing API conventions. Failures never substitute a rules-only result or a successful empty extraction.

The limit is 100,000 characters; text is never truncated. Worker limits are two CPUs, 4 GiB RAM/swap, no network, read-only code/assets/root, 128 PIDs and 64 MiB temporary storage. Startup and extraction have 60/30-second worker deadlines; the host bounds execution and cleanup. Each request uses an owned container, removed on every exit. Raw worker stderr and private source text are not returned as diagnostic errors.

If cleanup cannot be verified, the owner file at `backend/runtime_data/ner_preview/owner.lock` remains marked and later previews fail closed. Do not delete it while an owner is active. First obtain its exact container name, acquire/check the OS lock, inspect the matching container's owner label and reconcile that container's termination/removal. Only after no matching owner remains may the stopped API's owner file be reset to a single NUL byte. Never prune unrelated Docker containers. Restart/reconcile Docker if it is unavailable; there is no automatic inference retry.

## Reproducing checks

From the repository root, run the three `test_news_ner_preview*.py` modules together with `test_context_association_v41.py` and `test_location_repair_v40.py` using the backend Python, `PYTHONPATH=backend`, `pytest --noconftest -p no:cacheprovider`. This avoids shared database fixtures and application startup jobs. The recorded run passes 798 tests.

For the current successor, also include `test_context_association_v42.py`, `test_news_ner_context_v42_wiring.py` and `test_news_ner_location_v46.py`; the complete eight-module run passes **1,281 tests**. The earlier v42-only post-promotion run passed 1,195 tests. The v42 guide describes saved-output verification without neural inference. The historical adapter checkers below refer to their frozen predecessor snapshots, not fresh qualification of v42.

`backend/scripts/check_ner_preview_adapter.py --help` describes the private frozen adapter check. It runs a small FastAPI test app with fake read-only article storage and real isolated inference, reusing six previously qualified training articles plus three fictional inputs. It does not connect to the configured database. Expected spans stay outside the worker. Raw receipts go to a new ignored directory, never a public report.

The first check's nine extraction receipts all succeeded, but its legacy metadata audit correctly detected the planned `config.py` edit. Its failure receipt is retained. `backend/scripts/verify_saved_ner_preview.py` independently verifies those saved receipts and explicitly reconciles only the four new settings against the pre-task Git version; it does not rerun neural inference. Run this reconciliation against the same pre-task Git baseline (recorded in the public verification summary), before changing that baseline, or audit that original revision explicitly. See the outcome for exact preservation counts and limits.


## V46 location integration receipts

Private evidence is under the ignored training artifacts directory: `backend-location-authoring-20261020-v46` (20 predecessor snapshots, boundary bindings and bound tests), `backend-location-cached-20261020-v46` (788-input parity, 418 applicable cases, three repaired checks and article dispositions), and `backend-location-live-20261020-v46` (one API/worker result, actual container inspections, cleanup receipts, promotion bindings and independent verification).

`backend/scripts/verify_ner_location_v46.py` verifies saved receipts and cached pure-adapter parity without neural inference. Supply the cached/live packages and a fresh output receipt path. `check_ner_location_v46.py` records the original cached/live checks; its live claim permits only one request. Preserve existing receipts and never retry inference automatically. The real check uses fake read-only article storage, no database connection, the original private bundle and a process-scoped enabled test configuration. It restores the default disabled flag and limiter/settings afterward.

Five application/test changes are explicitly reconciled against predecessor snapshots rather than describing their old promotion hashes as current. Research v44/v45 artifacts and historical reports remain unchanged. No source article, model weights or individual evidence is included in the public report. The admin-panel interface is the next task; normal processing, database history and plotting are separate.
