# Phase C1 — processing methods and saved-history compatibility

> **Last Updated:** October 20, 2026, 7:56 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Delivered: the first Phase C compatibility boundary, with 93 passing checks. Phase C remains open.** Default collection/processing still writes and claims `rules_only`. Native automatic extraction, qualified projection/source checking and native flood cards are not enabled. This follows the approved contract's consumer-before-writer ordering. [Aggregate](summary.json) · [Roadmap](../../task_plan.md#phase-c--connect-automatic-article-processing) · [Contract](../../plans/rss-ner-integration-contract.md).

## Queue compatibility

Enqueue accepts an explicit supported method. Native callers must provide a `ner-v1:` identity with a 64-character SHA-256 digest; there is no implicit native default. The pure identity builder includes model, tokenizer, runtime, location rules, context rules, projection, source checking and geography families in canonical JSON. It is an identity builder, not deployment-asset authentication; binding an actual approved manifest remains open.

Claims select both pipeline identity and persisted mode, including pending, retry-wait and expired processing work. Legacy workers cannot consume native rows even if stored pipeline strings collide, and native claims cannot consume legacy rows. Default restart capture remains legacy-only. Claims carry method, pipeline and immutable version ID; completion checks these identities alongside the existing lease token/deadline. Native completion rejects mismatched article/version/URL/input fingerprint/body hash/length. These checks do not establish full graph/projection or source consistency. The legacy evaluator continues to reject native runs.

## Saved result shape and errors

Saved-run responses dispatch by persisted method and discriminator. `NewsNerResult` preserves original/effective mentions, ordered proposals and abstentions, full graph including unassigned facts, groups, all seven time roles, source identity, provenance, projection metadata, measurements and limitations. Native projected claims accept unknown confidence as `null`; legacy scores/result shapes remain unchanged. Strict JSON validation refuses string-coerced offsets/lengths and bounds native payloads to 8 MiB. Ordinary JSON dumps retain the graph's `schema` key even when callers omit `by_alias=True`. Unknown root native fields or discriminator/mode/version mismatches are rejected rather than silently discarded.

Provenance/projection JSON is retained for inspection. It is **not a qualified operational projection or authenticated inference receipt**. Current saved readers do not run inference. Full source-bound graph/projection verification remains a later Phase C gate.

| Existing endpoint / consumer | Compatibility behavior |
|---|---|
| `GET /api/v1/admin/news/articles/{article_id}` | Preserves native history alongside legacy runs without inference/writes |
| `GET /api/v1/admin/news/candidates/{article_id}/processing` | Returns the same method-aware saved-run union |
| Invalid/unsupported saved run in either history endpoint | Bounded HTTP 409 `news_saved_result_unsupported_or_invalid`; raw validation/source details stay private |
| Legacy `/results` list | Excludes native rows and native-tagged payloads from this scalar reader |
| Legacy result detail / placement preview | HTTP 409 `news_native_result_consumer_not_ready` for native payloads |
| Collection attention | A readable completed native run stays Needs checking until native projection/cards qualify, rather than being called an empty extraction |
| Evaluation/publication | Existing evaluator rejects native runs; no source/geometry/time/freshness gate is bypassed |

Existing active-admin dependencies remain on every affected route. API tests verify unsigned requests return 401, commuter requests return 403 and authorized history reads perform no writes/inference. No route or frontend change is added. Native group cards/detail routes, frontend method types/inspection and intended-method selection across all current readers remain pending. Do not activate neural writes with those consumers incomplete.

## Verification

| Suite | Passed |
|---|---:|
| New constructed method/schema/API boundary checks | 36 |
| Existing saved processing checks | 18 |
| Existing article browsing checks | 8 |
| Existing result/collection checks | 19 |
| New PostgreSQL method boundary checks | 8 |
| Existing PostgreSQL extraction queue checks | 4 |
| **Unique final checks** | **93** |

The final software batch passes **81 cases in 25.24 s**; final PostgreSQL passes **12 in 16.16 s**. Cases cover deterministic identity changes, both-direction queue isolation, duplicate delivery, one input/two run identities, concurrent enqueue, actual `SKIP LOCKED`, retry/reclaimed ownership, input/method substitution refusal, null confidence, Unicode offsets, all seven native roles without invented absolute times, exact graph serialization, protected read-only history, visible version errors and SQL rejection of native keys even when their JSON values are null. Fictional source-authored mentions use unchanged pure rules and are labeled non-neural fixtures. These are compatibility tests, not accuracy measurements or the full 23-scenario acceptance suite.

Both owned PostgreSQL 15 / PostGIS 3.4 containers used pinned image `sha256:3f4a5d48e0be9580ed70ed618cd039ce57bbb2dd113053d3836e28513f1f87cd`, generated private credentials, ephemeral loopback ports and temporary storage. Fresh disposable databases were migrated to unchanged head `e8a6f1c2d903`. Independent inspection confirms both stopped with PID zero and matching owner labels. No configured development/shared database was used.

Earlier receipts remain: a SQLite import URL failed against PostgreSQL pool options; an intermediate batch had 69 passes/two UTC timestamp-format comparisons fail; another invocation referenced a nonexistent test filename and ran no cases. The harness/fictional fixture and target list were corrected. A subsequent 79-case software/nine-case PostgreSQL pass preceded review-driven alias/strictness/SQL-null checks. Final batches above cover final source; earlier passes are not added to the unique count. No attempt launched neural inference.

## Preservation and limits

Independent hashing verifies all files in the two failed runtime packages, passing three-GiB runtime package and completed schema verification package remain unchanged. Of the original 1,040 frozen runtime source/asset bindings, **1,032 still match**. Eight current-source differences are recorded separately: the already approved model check plus seven C1 consumer/queue files. New C1 modules/tests are additional files outside that set. Historical snapshots/manifests/receipts and trained model/tokenizer/v40/v44/v42/runtime code are not rewritten. The current whole application is not claimed to match its older runtime snapshot, and no inference requalification occurred.

Current differing paths are `backend/app/models/news.py`, `crud/news_processing.py`, `crud/news_results.py`, `crud/news_collection.py`, `schemas/news_candidate.py`, `services/news_browsing_service.py`, `services/news_results_service.py` and `api/v1/endpoints/admin_news.py` (the latter paths relative to `backend/app/`). New modules are `schemas/news_ner_result.py`, `services/news_processing_identity.py` and `services/news_saved_run_service.py`. Tests are `backend/tests/test_news_ner_method_boundary.py` and `test_news_ner_method_postgres.py`.

No new migration, dependency, dataset, training, inference, live fetch, cloud setting, shared/cloud mutation, UI or deployment change occurs. The 60/15/30 policy and inspected cloud resources remain untouched; there is no new live-cloud health claim. Mobile/desktop UI acceptance remains in the interface milestone.

## Reproduction and next ordered work

Run the four software suites named above with the repository virtualenv and `python -B -m pytest --noconftest -p no:cacheprovider -q`, retaining JUnit/stdout/stderr in a new ignored artifact directory. Set a sanitized process environment and backend `PYTHONPATH` before imports, use an empty working directory to avoid dotenv loading, and supply a non-shared PostgreSQL-format import URL. SQLite fixtures create their own in-memory databases. Set the existing valid process-only auditor batch size to 8; do not edit environment files.

For PostgreSQL, start a newly owned loopback-only container pinned above with generated credentials; create a fresh `lanes_p3_verify_*` database. Set `DATABASE_URL` and `LANES_NEWS_TEST_DATABASE_URL` to that database before imports, apply the existing chain to head, then run the new method PostgreSQL and existing queue PostgreSQL suites. Stop only the verified owned server in `finally`, including on failure. Do not use shared storage, remove history or overwrite completed packages. Old frozen runtime/schema controllers describe earlier source states; do not rerun them against this changed checkout to manufacture parity.

Next is the conservative native projection and deterministic proof/source-checking adapter: retain joint/collective/LOCAL_AREA outcomes natively, account for every fact, resolve only supported observation dates/timezones, preserve unknown confidence and qualify downstream consumers. Then connect runtime/session budgets, mode-aware admission/capture/evaluation/corrections and intended-method/native-group readers; prove controlled RSS-to-saved-result acceptance. Automatic NER processing remains open until these requirements pass. Shared/cloud migration and release retain separate gates.
