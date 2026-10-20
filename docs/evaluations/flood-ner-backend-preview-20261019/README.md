# Extraction-only backend preview — implemented and locally verified

> **Last Updated:** October 19, 2026, 11:03 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Later source review:** the response now includes the saved article link. One real read-only database call succeeds, but [field-by-field review](../flood-ner-saved-article-review-20261019/README.md) finds full-article extraction gaps. That later repair recommendation supersedes the interface-next suggestion below; this original bounded receipt and its results remain historical.

The default-disabled local backend now offers an active-admin saved-article NER preview. It returns grouped location/depth/time/status/access evidence with original neural mentions, separately labeled rule proposals, unresolved fields and model/runtime provenance. [Operator guide](../../guides/ner-backend-preview.md) · [Specification](../../plans/ner-extraction-only-backend-preview.md) · [Aggregate verification](verification.json).

No frontend screen, database history, automatic processing replacement, map plotting, publication or routing was added. The configured running application remains disabled. Verification used a small API app with fake read-only article storage and the real isolated model worker; a live database-backed preview session was not run.

## Verification result

- **798 software checks pass:** 379 new preview checks plus the 419 preserved v40/v41 checks. These cover frozen-copy behavior, all 310 context/temporal regressions, 36 location cases, projection accounting, time roles, unknown publication timezone, subsided evidence, auth, rate limits, explicit errors, bundle tampering and lifecycle/output bounds.
- **Nine real-worker API responses pass:** six previously qualified training articles plus three fictional inputs. All six original neural span lists match their saved spans exactly. These are adapter-parity checks, not new independent accuracy measurements. No new articles, validation/holdout content or training were used.
- **120 cached context-view comparisons match:** 24 unchanged contextual inputs across original and all four saved proposal views. Runtime copies preserve the frozen context graph; original research files, expectations and references are unchanged.
- A live Docker inspection verifies the pinned Linux image, no networking, two CPUs, 4 GiB memory/swap, PID/capability restrictions, read-only root and exactly two read-only bind mounts. No database credentials, repository root, reference or expected-answer directory is mounted. Zero preview-owned containers remain and the local owner lock is clear.
- Across the nine adapter receipts, maximum worker startup is **4.314 seconds**, maximum extraction stage is **1.466 seconds**, and maximum worker RSS is **386,506,752 bytes (368.6 MiB)**. These measurements cover the fixed workload, not a guarantee for every permitted 100,000-character article.

## Preservation reconciliation

The initial frozen checker stopped after all nine successful API responses because the historical metadata list includes `backend/app/core/config.py`. This task intentionally adds four preview settings there. The failed receipt and original frozen checker remain intact. No inference was retried and no extractor was tuned after the results.

A separate saved-receipt verifier confirms the input/model/code bindings, neural parity, complete graph/projection evidence, actual isolation and stopped state. Structural comparison with the clean pre-task Git version confirms that `config.py` changes only by the four declared settings. All **208 protected evidence hashes** and **55 frozen v41 source/test hashes** match. **1,538 historical metadata entries remain unchanged**, with the one declared application-config change recorded separately; all **82 excluded metadata entries** match. Historical/excluded sets overlap and use size/mtime, not content hashing. No validation/holdout content was opened.

Private evidence is retained under `backend/training/flood_ner/artifacts/ner-preview-authoring-20261019-v1`, `ner-preview-adapter-check-20261019-v1` and `ner-preview-saved-verification-20261019-v1`. The inference-only bundle is separate and ignored. Individual article text, identifiers, spans and responses are not published here.

## Limits and next work

Docker lifecycle faults are covered through deterministic controller tests; subprocess output/deadline bounds are exercised with actual child processes. The successful Docker worker and its live restrictions were checked directly. This task does not claim fresh real Docker OOM/timeout/crash experiments or cloud qualification.

Depth/time extraction and association remain rules; trained v19 still recognizes six location classes. Three contextual reference holds, the separate non-flood access omission, exposed silver-reference limits, real pure-Tagalog measurement and learned DEPTH/TIME remain unfinished. Observation/report/publication clocks never imply onset. Subsided status/time stay in extraction evidence; history retention without current plotting remains downstream work.

The next product task is separately scoped admin-interface design if desired. Durable neural run storage requires an approved schema/migration task because the existing run table accepts only `rules_only`. Normal pipeline replacement, plotting, cloud deployment and publication/routing remain later gates. No uploads, commits or pushes occurred. [@roicambe](https://github.com/roicambe) (Roi Cambe)
