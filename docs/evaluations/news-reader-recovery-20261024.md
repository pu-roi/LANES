# News Intelligence reader recovery — October 24, 2026

Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe).

## Cause and recovery

The automatic `main` build `b49a73e8-be63-4166-b85b-fc74ae1dee56` promoted commit `326bc083bf603587a02c70d6195cfcddcf449905` at 11:56 PM Asia/Manila on October 23. Its standard backend image did not contain `/release/read-context.json`, although the inherited environment still required that file. The protected results endpoint therefore returned 503. The database retained correction 388, the three observations and active zones 77–79.

Recovery preserved private API/trigger configuration and database fingerprints, disabled trigger `ed5fa3a8-22f7-4a9a-9a4c-e29b267709b8`, verified v30's tagged endpoint, then restored v30 traffic. No source, extraction, event or zone was recreated.

## Permanent repair and release

The normal Docker image now packages the same nonsecret v2 reader manifest separately from inference assets. Its canonical hash remains `d6676e09e364d79b509c5dce0bcabc112ce359a41f247314bcfadbca417b1270`. Deployment explicitly sets the packaged `/data/news-reader/read-context.json` path, hash and required-reader flag. Startup verifies reader integrity and database binding in a read-only transaction before readiness; errors cannot enter the best-effort seeding handler. Unconfigured legacy-only installations retain their behavior unless native reading is explicitly required.

`cloudbuild.yaml` invokes the checked API deployer. It stages zero-traffic revisions, creates a bounded read-check job with existing API database/signing credentials only, compares protected results to the database and serving revision, checks details/articles/collection/filtering/pagination/authentication, then promotes only after success and unchanged serving traffic. Credentials stay out of command arguments and logs; the temporary private descriptor is removed. The check has zero retries and does not import the API lifespan, run RSS, infer, publish or receive Gemini credentials. API releases no longer overwrite discovery/expiry/manual-worker specifications or execute discovery as a readiness probe. Existing migration steps remain separate and unchanged.

- Serving revision: `lanes-api-reader-recovery-20261024-v1`.
- Image: `asia-east1-docker.pkg.dev/lanes-project-508809/lanes/lanes-api@sha256:48c3dfc90a1fd1c8022699c28061666a7b69a039cc235f60a34f029bfcdfb1c4`.
- Successful check execution: `lanes-api-reader-reader-recovery-20261024-v1-sttdk`.
- Tagged preview and serving acceptance both returned three observations selected from correction 388.
- v30 remains retained for traffic recovery. The manual worker specification is unchanged.

## Verification

- Initial local reader/extraction regressions: 82 passed; final release-specific checks: 23 passed.
- Final frozen Linux image: 126 passed, one repository-only Cloud Build source check skipped because that source lives outside the backend image. That check passed locally.
- Disposable migrated PostGIS: 24 passed. An initial run used development settings and correctly failed two disposable-target guards; rerunning with `ENVIRONMENT=test` passed all cases without weakening those guards.
- Hosted desktop/mobile News Intelligence passed on restored v30, the candidate reader and the repaired serving revision: three cards, source facts, detail tabs, source text, scrolling and responsive width.
- Cloud canary passed database selection, serving compatibility, pagination, filters, group details, articles, collection and authentication. It recorded zero database writes and zero provider requests.
- The spending ledger's content and GCS generation are identical to the prior evidence: stopped, 42 attempts, US$0.7524937 effective conservative commitment. No NER, Gemini or token-count calls were made.
- Final hosted desktop/mobile active-zone panels, all three public-map focuses/popups and unrelated history event 76 passed. History records/exports contain only event 76; the three presentation zones remain excluded from ordinary routing. All 13 protected table fingerprints match the pre-recovery baseline exactly, including accounts, posts, reports/moderation, article/version/run/evaluation history, event/zone/location/timeline records and system settings. Automation remains paused and both expiry switches remain OFF.

## Integration and recovery

The automatic backend trigger remains disabled until this repaired build configuration is reviewed and present on `main`. Do not re-enable it against the old configuration or merge unrelated working-tree changes into this repair. No commit, push or main merge is included in this recovery operation.

On acceptance failure, restore serving traffic to `lanes-api-gma-connected-reader-20261023-v30`; retain the corrected image and receipts. Do not reset the database or rerun article processing. Private snapshots, hashes, check receipts and browser evidence are retained in ignored `data/news-reader-recovery-20261024/`. A sanitized acceptance receipt and reviewed source bundle were uploaded with conditional-create protection and SHA-256 readback verification under `gs://lanes-storage/private/news-reader-recovery/20261024/`; credential-bearing snapshots were excluded. UI, API response shapes, schema, dependencies and trained models are unchanged.


## Documentation consistency audit — October 24

Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe). This follow-up reconciles the conversation against the retained recovery acceptance receipt, source/cleanup/connected-road evaluations and current code. It makes documentation changes only; no tests, cloud mutation, article processing or database output was rerun.

| Authoritative record | Reconciliation |
|---|---|
| Task plan / progress | Current GMA completion, three-article inventory, scoped cleanup history and remaining deployment/article gates; preserve earlier chronology |
| Bug log | Final disposition and root-cause references for provider contracts, wrong capture, missing/duplicate locality, detail scrolling, placement/projection and reader outage |
| System documentation | Current API versus worker release, existing screen/data mapping and explicit earlier-checkpoint headings |
| Feature reference | Update existing news module only; distinguish actual manual NER/Gemini qualification from paused scheduled operation |
| Tech stack | Correct current trained-location runtime/deployment behavior; existing dependencies only |
| Decisions | Record the adopted versioned connected-road/active-only policy and clarify correction versus the earlier verdict auditor |
| Database plan | Exact preservation, earlier scoped 62-row removal and unchanged migration/schema; no repeat cleanup |
| Documentation index | Current work/status links with older outcomes identified as historical |

Public API/UI/schema/model/dependency definitions remain unchanged. Automated deployment remains disabled pending integration of the already implemented repair into `main`; Tribune/Philstar and routine news restart remain pending. Historical immutable source/provider/spending/recovery receipts were not rewritten by this audit.

Documentation validation: 51 current recovery/source/placement links and their referenced anchors passed; every authoritative record has one correctly placed global timestamp. Before/after hashes confirm the backend, deployment files and unrelated frontend edits were unchanged during this documentation-only audit.
