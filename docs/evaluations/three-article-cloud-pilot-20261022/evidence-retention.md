# Gemini evidence retention — one frozen GMA batch

> **Last Updated:** October 22, 2026, 11:34 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

The retention repair is deployed to the manual worker. **Exactly one real four-target GMA request returns HTTP 200, is retained before validation, and fails precise evidence-reference validation.** Two network-disabled replays reproduce the same rejection. No second batch, NER rerun, article acceptance, extraction-run write, spatial qualification or seeding follows. Tribune and Philstar remain pending.

## Exact finding and limits

Execution `lanes-news-verified-k5vkz` uses the unchanged complete original article, saved NER run **375**, version **574** derived from original source version **137**, original quote ordering, model `gemini-3.5-flash-lite`, compact schema, temperature 0 and 8,192 output-token limit. There are **59 quote options, numbered 0–58**. All four requested targets are present; nine evidence fields contain nonexistent option numbers:

| Target | Source mention | Evidence field | Returned invalid reference | Valid range |
|---|---|---|---|---|
| `n1` | España Blvd., occurrence starting at character 274 | `place_evidence` | 327 | 0–58 |
| `n1` | Same occurrence | `status_evidence` | 318 | 0–58 |
| `n1` | Same occurrence | `time_evidence` | 318 | 0–58 |
| `n2` | España Blvd., occurrence starting at character 327 | `place_evidence` | 327 | 0–58 |
| `n2` | Same occurrence | `status_evidence` | 318 | 0–58 |
| `n2` | Same occurrence | `time_evidence` | 318 | 0–58 |
| `n3` | Antipolo Street, occurrence starting at character 347 | `place_evidence` | 347 | 0–58 |
| `n3` | Same occurrence | `status_evidence` | 318 | 0–58 |
| `n3` | Same occurrence | `time_evidence` | 318 | 0–58 |

No duplicate indices are reported in this response. References 327 and 347 equal the source-character starts of `n2` and `n3`; 318 starts the article's flood statement. **Inference:** Gemini appears to have confused source-character offsets with backend-owned quote-option indices, despite the prompt requesting quote indices. The confirmed failure is the invalid index namespace; the provider's internal reasoning is unavailable. Missing ownership/time/depth or other semantic errors may still exist: this phase stops at the first validation layer. Do not translate these numbers into guessed passage IDs, deduplicate or weaken source checks.

This diagnoses the retained new batch. The original failed run **376** has no retained response, so its exact offending target/field cannot be retroactively proved. Run 375 and failed run 376 remain unchanged. A future cause-specific request-contract repair must be qualified offline before any separately resumed paid execution. Full GMA correction, spatial qualification and three-article seeding remain pending.

## Retention and execution controls

- `news_gemini_receipts.py` provides create-only private GCS objects, bounded raw-response retention before parsing, exact request/context/reservation bindings, strict target/schema checks and immediate per-batch evidence diagnostics. Every request is preceded by a durable budget reservation and immutable dispatch intent. Storage failure blocks continuation; interrupted/uncertain attempts cannot silently resend.
- Receipt stages distinguish transport, retention, evidence-reference validation, article validation and unconfirmed database commit. This diagnostic has HTTP transport success and response retention, **failed evidence validation**, article acceptance **not evaluated**, database writes **zero**. A Cloud Run nonzero exit truthfully represents rejection; it does not mean the response was lost or the API could not connect.
- Exact configured key/headers are excluded from request artifacts and logs. An echoed key is redacted and makes the body nonreplayable. Oversized bodies retain only a bounded prefix and cannot pass replay. No credentials enter source, frontend or evaluation output.
- Runtime receives conditional `storage.objectCreator` and `storage.objectViewer` only for `private/news-pilot/20261022-5512bbaa/diagnostics/evidence-20261022-v1/`. The new grants do not permit overwrite/delete. Existing exact-ledger and authority permissions are retained. Objects use generation-zero create preconditions; reads pin object generations. No public-access or bucket configuration change.
- Diagnostic-only authority permits one exact first batch from the immutable old parent, one provider request and zero SQL writes. It binds database, source/parent/payload/release hashes, budget identity, session, ordered quotes and target count. The ordinary processing authority and global provider execution remain disabled; the job defaults to read-only preflight.
- `replay_news_gemini_receipt.py` validates a private exported request/response pair against its externally pinned bundle hash with no provider or database dependency. The actual bundle replays twice in the frozen Docker image with `--network=none`, read-only mounts and no credentials. Both exit 1 with identical nine-field diagnostics and zero provider calls. [Operator instructions](../../guides/news-gemini-runtime.md#private-batch-retention-and-offline-inspection).

## Qualification and release

**91 local tests pass**, including disposable PostGIS reader/preservation/concurrency tests and strict evidence, target/schema, tamper, interruption, credential, storage and first-batch-stop cases. Tests retain rejection rules and cover malformed/oversized bodies, missing/duplicate/unexpected targets, unsupported facts and zero-network repeated replay. The initial disposable harness used unavailable `psycopg2`; correcting the harness to installed `psycopg` resolves setup without a dependency change. No tests are removed.

The image passes all seven network-disabled contracts and exact reader/asset identity verification. Cloud execution `lanes-news-verified-nzl65` repeats all seven contracts with zero provider calls/model inferences/database writes. Storage execution `lanes-news-verified-5872b` uses a simulated response, verifies rejected-body retention, two offline replays and failed overwrite, with zero provider calls/database writes. Diagnostic preflight `lanes-news-verified-qvdf9` verifies the exact real payload/parent with zero provider calls/inferences/writes.

The initial software-only launch `lanes-news-verified-km9hw` exits before application execution: Windows consumed the caret-delimited argument separator. Its retained log identifies the nonexistent combined Python filename. Dispatch is corrected to a structured JSON flags file; the explicit subsequent execution's four arguments are verified. No Gemini request, budget reservation or application change results from that launch failure. Earlier v6 packaging evidence is retained; v7 adds isolation between mock software contracts and the configured real receipt journal.

| Release property | Frozen value |
|---|---|
| Manual image | `asia-east1-docker.pkg.dev/lanes-project-508809/lanes/lanes-news-verified@sha256:a73e28f403dbdffc221c2ee1af325aae67a4f7c0b36c99d6458c39a645c4c05f` |
| Release SHA-256 | `fd654acbb768295469d3a313ee9adaae99e5df75d6381c2c845cf9af08b7587d` |
| Reader descriptor SHA-256 | `6e1bb677b526edb380cc2bb6f064addc534aff36323ce4b5879efaead0567cc2` |
| Original request SHA-256 | `35be3bd3917a156796057312b21958da5aa17beab62bd7cf4a0151bb0b98d732` |
| New request/reservation identity | `b04b2a8a9fff9d23957f72508857b08596f0cca497ef3818d6d17356382436f8` |
| Exported replay bundle SHA-256 | `c2042c6f02df5febba6b6709248324059a6d037135d115e7e4e435daa05b317a` |
| Cloud task | Linux amd64, 1 CPU, 3 GiB, 600 seconds, zero retries, manual only |
| Runtime credential | LANES Secret Manager version 2; personal version 3 unused |
| Serving API | `lanes-api-gemini-fix-20261022-v5`, unchanged at 100% |

The model bundle/inference worker/spatial assets are unchanged. Application hash is re-frozen after the repair; the narrow diagnostic verifies the original parent's accepted identity separately. No generic compatibility bypass, public API shape, UI, dependency, source fact or database schema/migration change is introduced. Existing migration head remains `f1a9c7e2b604`.

## Spending and preservation

All **17 previous attempts remain identical**, preserving **US$0.6481486** conservative reservations. One diagnostic reserves exactly **US$0.04043** before dispatch. The ledger ends **stopped**, with **18 attempts and US$0.6885786 reserved** under the unchanged US$1 cap, no in-flight attempt and stop reason `single_evidence_diagnostic_completed_requires_review`. Reservations are not confirmed charges and are not reset/refunded. Provider usage reports 6,222 input and 897 output tokens; actual billing is unconfirmed. No additional generation request is made for software checks or replay.

Final read-only comparison matches **every database table fingerprint**, original articles, run 375/result hash, failed run 376, constraints, triggers and sequences. Counts remain 175 articles, 226 versions, two runs, eight accounts, 37 community posts, zero reports/events/zones. Community-report links remain unchanged. A pre-release comparison to older pilot evidence found one intervening general audit row; a fresh baseline was captured **before this release** and final fingerprints match that baseline exactly. Earlier evidence is retained rather than rewritten.

API specification and serving traffic match their baseline; old seed specification is unchanged. News scheduler remains PAUSED and all collection/processing/publication switches false. Both expiry switches remain OFF. The existing expiry scheduler stays enabled with unchanged configuration; only its normal last/next-attempt timestamps advance. No account, community, moderation, routing or flood data is changed by this diagnostic.

Private inputs, immutable receipts, authorities, frozen images/manifests, software-check logs, database/configuration snapshots, ledger snapshots and replay artifacts are retained under ignored `data/evidence-retention-20261022/` and the dedicated private GCS prefix. They are not published in this evaluation. Recovery retains the accepted API revision and previous worker snapshot/image; disable further manual execution and keep the ledger stopped while preserving database/receipt evidence. No reset, destructive cleanup, guessed corrections or activation is part of recovery.
