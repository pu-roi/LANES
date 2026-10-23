# E1.2 — frozen historical processing command

> **Last Updated:** October 22, 2026, 12:58 AM Asia/Manila

Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe). **Implemented and tested locally; cloud processing and real September inference remain blocked/unrun.** [Task plan](../../task_plan.md#e1--connect-controlled-historical-processing) · [Operator guide](../../guides/historical-news-preparation.md#e12--manifest-bound-preflight-and-disposable-processing) · [Aggregate verification](summary.json).

## Delivered behavior

`scripts.run_news_historical_processing` exposes explicit `preflight` and `process` modes with required E0 manifest/hash, database-name confirmation, bundle/worker/current-assets hashes and private receipt directory. The package loader authenticates all five documents and reconstructs E0's source/native/session bindings using its original inventory and original assets. It preserves exact text, original IDs, publication uncertainty and dispositions. It does not recapture mutable article text or reset article review state.

Execution manifests separately bind the frozen parent, stable session, configured source/target identity, current assets/pipeline and operator code. Current projection/source-check families may differ from E0 because of the approved E1.1/E1.2 application changes; other model/tokenizer/runtime/rule/geography changes are blocked. The caller must pin the complete current asset manifest. Existing E0 files are never rewritten to match current code.

Preflight runs in a database-enforced repeatable-read/read-only transaction, verifies the connected database and applies five-second SQL/lock timeouts. It checks immutable source rows and article identity, processing/source settings, the approved native migration and actual named/validated PostgreSQL mode constraint. Existing selected native captures/results are authenticated too. Blockers are returned individually. No run is claimed or inserted and no model is started.

Processing rejects non-disposable targets before connecting. In this step, only test-environment PostgreSQL databases with the existing `lanes_p3_verify_*` naming guard, a loopback host and no URL query overrides qualify. The frozen source database identity remains distinct from an explicit disposable mirror. The configured cloud origin can be recognized during inspection; it does not acquire processing permission.

The shared enqueue helper inserts native input/run evidence with existing conflict-safe identities. Exact run selection skips general capture and cannot consume other queue entries, including another version of the same article. Only pending, non-exhausted selected runs are claimable. Completed runs are authenticated/reused; failed, retry-wait and foreign processing leases remain intact, including expired leases. The existing worker still owns supervision, result validation, transaction/lease deadlines, cancellation and cleanup. No discovery, evaluation/publication, placement enrichment or event/zone write is called.

Readiness checks require Linux amd64, Python 3.12, spaCy 3.7.5, the qualified one-CPU/3-GiB cgroup envelope, an available main-thread timer and the authenticated `/assets` bundle mount. Actual seccomp/socket denial remains enforced at worker startup; preflight does not claim it started or qualified a worker. JSON attempts and separately identified execution manifests are stored privately without replacing prior attempts. Stdout contains bounded status/hashes/counts, not article bodies or credentials. Exit codes are 0 for ready/completed, 1 for blocked/failure/attention and 130 for interruption.

## Verification

**227 checks pass, zero failures or skips**, with three existing multipart/Pydantic warnings. The final run covers the new package/CLI and disposable PostGIS suites plus existing E0, native processing/CLI, durable queue/projection, pipeline and E1.1 maintenance checks.

- Reject tampered manifest/inventory/native captures/receipt, duplicate JSON keys, changed session/request bindings, unexpected package members, wrong target confirmation, asset-pin mismatches and protected asset changes.
- Prove read-only preflight emits only SET/SELECT/SHOW, leaves rows untouched, starts no model and separately reports migration, configuration, runtime and source blockers.
- Process exactly two fictional immutable captures despite different current article bodies and approved review states; preserve an unrelated pending version of the same article.
- Repeat completed processing without another runtime start or row/result change; concurrent enqueue produces one native version/run per capture.
- Preserve failed, retry-wait and expired foreign processing leases. Lost completion ownership cannot overwrite the replacement owner. Empty exact selection never falls back to the general queue.
- Persist timeout, worker failure and cancellation once; report interrupted/attention outcomes and cleanup failure without erasing completed results. Existing worker target, budget, normalization, isolation-contract and CLI checks remain passing.
- Confirm event, zone, claim/evaluation/publication tables remain empty throughout the new processing tests. All runtime responses are explicitly constructed fictional fixtures; real neural session startup and publisher requests are forbidden.

The first integration run exposed a new preflight check using the model's short constraint name rather than the migrated PostgreSQL name. It was corrected to inspect the approved named, validated canonical expression. Earlier failed XML receipts and the corrected targeted run remain private; no test was deleted or weakened. The final 227-check run passes.

Fresh owned PostGIS storage reached existing head `e8a6f1c2d903`; no migration file was added or edited. Per-case clones, the owned template and queue database were removed after verification. No cloud database was accessed. Private runner, XML, exit and cleanup receipts are under ignored `data/news-historical-command-e12-20261022/`.

## Actual E0 authentication and preserved boundaries

Separately authenticated the real frozen E0 package **without database access, model startup or inference**: article/version 25/66 and 47/137, five history references and session `ee30c69d-32cd-555f-bb90-26899cb74810` remain bound. This validates preparation compatibility, not neural/source/geometry eligibility.

- Parent manifest SHA-256: `0beb452c80dd0a805bada20dffd6c92dfdee3cd99e1951bf5eaf0862ce9f8439`.
- Current execution asset manifest SHA-256: `76abbcb518f0ca16cf6fbab05ba425599e4f0c31942f59d37cb213644fc9c745`.
- Changed families: `projection`, `source_check` only; original model/tokenizer/worker/location/context/geography identities remain fixed.
- All five E0 package files and the three E1.1 application service files retain their exact preceding file hashes.

No new public endpoint, UI control, frontend/schema/dependency change, cloud access/deployment, real September inference, plotting, activation, history overwrite, commit or push occurred. E1.2 completes the command and software verification only. The next task is the explicit historical cloud execution-target policy; date/source qualification, real-corpus inference and geometry, active demonstration/history persistence, UI and release remain open. **No new zones should appear on either map yet.**
