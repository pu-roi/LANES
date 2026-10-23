# Scoped GMA cloud gate — one batch accepted, execution stopped

> **Last Updated:** October 23, 2026, 10:27 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Verified result and boundaries

Exactly one token-count call and one real Gemini generation were made for GMA article **47**, native version **574**, immutable NER parent **375**, targets **n12–n15**. No NER inference was rerun. The generation returned **HTTP 200**, was privately retained before parsing, passed strict reference validation and the expected semantic checks, and reproduced on two independent offline replays with networking disabled. This establishes **one-batch acceptance only**. Complete article correction, spatial qualification, seeding, Tribune, Philstar and activation remain pending.

| Target | Source role | Actual outcome |
|---|---|---|
| n12 | First barangay heading | Unsupported as an independent observation; context retained |
| n13 | Don Jose Street observation | Accepted: Quezon City/Brgy. Sienna; September 9, 2026, 8:55 AM Asia/Manila |
| n14 | Palali Street observation | Accepted with the same supported city/locality/date/clock |
| n15 | Repeated barangay heading | Unsupported as an independent observation; context retained |

Both accepted rows preserve the source's shared waist-deep measurement (37 inches). No individual measured-depth scalar is invented. Actual place evidence includes exact road passages **15/16**; status cites the flooded-list introduction **9** and depth heading **13** with each road. Time evidence includes consistent date passages **2/8**, clock heading **12**, and each road passage. Depth evidence is **13 + 15/16**. All four target outcomes have empty issue lists. Geometry and operational eligibility were **not** evaluated.

## Implementation and qualification

New private worker modes `gma-scoped-count` and `gma-scoped-gate` use the separate `news-scoped-gma-diagnostic-v1` authority. Grants bind the exact database, release/application/assets, source/parent/layout/request hashes, four targets, accounting policy, existing ledger, one stable session and private receipt prefix. Count intent/response are immutable and retained before parsing; generation retains the existing durable reservation, intent, bounded response, accounting and separate semantic/quality receipts. Repeated or uncertain dispatch cannot automatically resend. The gate stops the ledger on success, semantic/infrastructure failure or pre-dispatch validation failure for its resumed session. General processing remains disabled.

Offline qualification exposed an additional source-ownership defect: raw NER labels the leading editorial rubric **FLOOD ALERT** as ROAD. A date cited from the title was then rejected as evidence owned by another road. Scoped validation now recognizes only an exact leading flood/weather/traffic alert/update/bulletin token followed by a colon as editorial context. Raw NER remains immutable; such a token cannot become an observed road. A genuine name such as Flood Alert Road is not exempt. Legacy V1 remains strict. The live response chose supported body/publication date passages instead of title passage 0; the editorial-title case is separately covered by actual-GMA and negative offline fixtures. No source facts or citations were guessed or inserted.

The worker also rechecks configured publisher eligibility inside its read-only source transaction. **231 regression tests passed** (three existing dependency warnings), including disposable PostGIS and new authority/tamper/retention/cap/interrupt/repeat-send/editorial tests. Seven Linux worker contracts, exact original GMA request reconstruction, source-authored positive diagnostic fixtures, unchanged historical-failure rejection, and cloud preflight/contracts/immutable-storage checks passed with zero generation calls. No UI, public API shape, schema, dependency, model training or RSS changes.

## Release and actual executions

- Final worker release: `6bfd576a384fa33829772d272dc5a9cb2d8cf62be1ba8a9f3c50c6bd35fa770a`; all **447 application files** match the frozen candidate.
- Worker image: `asia-east1-docker.pkg.dev/lanes-project-508809/lanes/lanes-news-verified@sha256:70486d67a4dd1ac394f9af0af93daf8ba3a3d702d1c59be9d05ec0673f144e62`.
- Exact unchanged request: `af01fd06dab994a4180a018eb6201598b1c23ec72f0c5008dba72eb59461ff26`; parent result: `93de1cc2436171660376ee466b0fd9f37b413d80582a8f8a9d37d83957c4fe54`.
- Cloud preflight `lanes-news-verified-vtmzt`, seven-contract check `lanes-news-verified-pts2t`, storage smoke `lanes-news-verified-thkmb`, token count `lanes-news-verified-h4n5c`, and live gate `lanes-news-verified-p859j` all completed successfully.
- Retained live bundle: `ccab75b20fefc9f53d206d82f05cbe7fa2ca9fcfe4c8310ce406dd018bf1eead`; two Docker `--network=none` replays reproduce acceptance with zero provider calls/database writes/inference.
- Runtime retains Linux amd64, 1 CPU, 3 GiB, 600-second timeout, zero retries, supervised shutdown, default read-only preflight and general execution disabled. LANES secret version **2** is used; no personal key or Search/Maps tools were used.
- Serving API remains **`lanes-api-gma-budget-20261023-v11`** at 100%; its specification is exact to baseline. No API or frontend rollout was performed.

## Spending and preservation

The count-backed maximum reservation was **US$0.0252998**, giving a pre-dispatch commitment bound of **US$0.6926742**. Actual metadata reports **9,710 input tokens / 952 output tokens / zero additional thinking tokens**, yielding **US$0.005293** at the pinned policy rates. These are usage estimates and bounds, not a verified Google invoice. Hosting and ordinary website weather remain outside the news allowance.

The ledger is **stopped at 24 attempts**, with effective commitment **US$0.6726674** under the unchanged US$1 cap. Historical maximum reservations remain **US$0.8709786**. All preceding 23 attempt objects and earlier settlements are unchanged; no history reset, cap increase, attempt-limit increase or automatic refund occurred.

Final repeatable-read fingerprints show **no changed application tables**, exact original runs **375/376/378/379**, and unchanged migration head `f1a9c7e2b604`, FK/trigger definitions, sequences, community links and notifications. Counts remain 175 articles, 226 versions, four extraction runs, eight accounts, 37 community posts, and zero flood events/polygons/reports. News automation stays paused, both expiry switches OFF, old seed specification unchanged/disabled, and scheduler states unchanged. No public flood cards or map data were created.

Private ignored evidence under `data/scoped-gma-cloud-20261023/` retains control/DB baselines, separate v12/v13/v14 candidates, original offline fixture failure and repairs, regression/image/cloud receipts, authority/count/dispatch records, live bundle with external pin, replay results, spending ledger and final audit. Conditional create/read permissions apply to the dedicated diagnostic prefix; the bucket has no public-member bindings. Credentials/authorization headers are excluded from request/response artifacts and public logs.

## Review stop, continuation and recovery

This phase is complete and stopped for review. **Do not rerun the consumed diagnostic.** A later full-GMA plan must review the complete remaining request/cost/attempt schedule, adopt this exact accepted response where compatible without another charge, prepare matching API readers and separately authorize correction/archive writes. Tribune, Philstar and active instances remain pending. Full-article accuracy, OSM/NOAH placement, populated-interface acceptance and complete-command archive idempotence are not established by this batch.

The previous manual-worker specification/image is retained for recovery. Restore that specification if rollback is needed, leave the ledger stopped and retain all evidence. API v11 was never replaced. There is no application-data rollback or destructive cleanup to perform because this phase made zero application-database writes.
