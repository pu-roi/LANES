# GMA v3 city-heading repair — cloud continuation stopped on duplicate locality

> **Last Updated:** October 23, 2026, 6:05 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

The v3 source-layout repair is implemented and deployed to the restricted manual worker. **The three-location News Intelligence rollout is incomplete.** Two real Gemini requests returned retained, reference-valid responses, but the second proposed an additional barangay observation from the same Rizal Avenue passage. The required-target safeguard stopped processing before the third request. Serving API v23 and its two accepted run-384 cards remain unchanged; no polygon, historical event, active instance or accepted replacement correction was saved.

## Original defect and implemented repair

GMA article **47**, original source **140** / native **569**, contains three plain-text road entries: Rizal Ave Extn and Tañong F. Sevilla Blvd. (Bayan) under **Malabon City**, then Marcos Highway Underloop under **Marikina City**. The complete original body is 1,297 characters, SHA-256 `f5ff7d13e255ed82ab9c024bcd1aae02fee4ce5806c4a7411bc818e2f58ed763`. All three report gutter-deep water, passage for all vehicle types and September 9, 2026, **2:47 PM Asia/Manila**; no measured inches/meters are supplied.

The old v2 parser recognized locality headings only before bullet lists and cleared context on unbulleted road entries. Gemini therefore received no governing Malabon heading for F. Sevilla and returned `city: null`. The authenticated catalog already resolves Malabon and Tañong; missing reference locality was not the cause.

The separately selected `scoped-quote-options-v3` contract recognizes source-supported city/barangay headings governing bullet or plain flood-detail road entries. It retains context across consecutive entries, resets at locality changes, narrative, clearance and updates, and preserves the complete article, original quote ordering and raw NER labels. Each observed road must cite its exact governing city heading and road passage. V2 identities and replay behavior are retained. Dates, depths, access, references and source ownership remain strictly validated.

An exact older-parent bridge reuses immutable **NER 382** with its pinned result, input, manifest and original frozen release. It verifies unchanged model, tokenizer, inference runtime, location/context rules and spatial identities before recomputing current source bindings. No NER inference or rewriting of existing runs occurred. New correction identity, restricted count/resolve commands and a generation-protected accounting extension preserve all earlier authorities and spending history.

## Qualification

- **209 regression tests passed** before deployment, plus the **13-case v3 suite** after adding the actual new failure as a regression fixture. The latter consists of the original 12 passing v3 cases plus one new retained-response case.
- **29 disposable PostGIS tests passed.** One existing scheduler assertion was updated to include its already implemented paused collection/extraction/evaluation stages; scheduler code and behavior were not changed.
- Fresh and repeated upgrades reached existing migration head `f1a9c7e2b604`; no migration/model/dependency changes.
- **Seven frozen Linux worker contracts passed** with networking disabled and no provider calls.
- A frozen-image disposable copy of the selected real records saved three source-supported mocked observations, exposed three through compatible readers, preserved every other selected record, and reused the completed correction with zero additional requests/rows. Changed parent, model/runtime/spatial identities were rejected. This establishes software behavior, not Gemini accuracy.
- Original NER 382 verified in the original v23 image with networking disabled. Actual cloud preflight checked the target, schema, reader, authenticated assets, paused configuration, LANES secret **2** and disabled general processing.

## Actual cloud sequence and exact failure

Manual worker image:
`asia-east1-docker.pkg.dev/lanes-project-508809/lanes/lanes-news-verified@sha256:4cf040f062e1838c96312db71d24cb2bb27971b7d988c18abf68d9d4f8ae86c4`

Release SHA-256 `f7875caabdec9cd58d4a1b8c4294217864a0bde0259cf6f4aee36e02785a1f87`; derived pipeline `ner-v1:cea7814c6acb204bfdb2649fbc598969f8c91b90005a2dbd5b13ee74fc0e7f19`. Linux amd64, **1 CPU / 3 GiB / 600 seconds / zero retries**, supervised shutdown, default read-only preflight and general processing disabled remain pinned. The no-traffic API canary is `lanes-api-gma-heading-20261023-v24`; **serving API remains `lanes-api-source-correction-20261023-v23`**. The frontend is unchanged.

| Stage | Execution / result |
|---|---|
| Read-only cloud preflight | `lanes-news-verified-zwlw7`; passed; zero database writes/provider requests |
| Three exact countTokens calls | `lanes-news-verified-zqqln`; 5,900 / 5,899 / 5,810 tokens; unchanged request hashes |
| Sequential correction | `lanes-news-verified-sl678`; two generation requests, then stopped |
| New correction receipt | **386**, failed `native_resolution_unexpected_observation`; no accepted result |

Batch one, targets n0–n3, returned unsupported outcomes. Batch two, targets n4–n7, independently passed reference and source-fact validation for **n6 (Rizal Avenue)** and **n7 (Brgy San Agustin)**. Gemini assigned n7 the same `Rizal Ave Extn` road section, gutter depth, clock and passability as n6, citing the same road passage. This is an unexpected additional locality observation, outside the reviewed road set **n6/n8/n10**. The manual gate correctly rejected the batch rather than saving a duplicate incident.

The new city-heading contract was present in the exact sent request; this failure is distinct from the prior missing-city response. **F. Sevilla n8 and Marcos n10 were in the unsent third batch. Their real v3 outcomes have not been established.** Do not label the three-location correction accepted or claim F. Sevilla is now visible.

Both HTTP-200 responses were saved before validation; usage was settled independently. Immutable dispatch, response, reference, article-failure and accounting receipts remain private. Two externally pinned bundles reproduced reference acceptance and the exact unexpected-n7 outcome **twice with networking disabled and zero provider calls**. The new retained-response fixture verifies that this failure prevents the third request. No automatic retry, fallback, reference rewriting or manual source-fact correction followed.

## Budget and preservation

The stopped baseline **39 attempts / US$0.7418188 effective commitment** was preserved through an immutable versioned transition permitting at most 42 attempts under the same US$1 cap. The complete three-request maximum schedule was **US$0.071466**, giving a reviewed maximum commitment of **US$0.8132848** before dispatch.

Only two generation requests were sent: **11,799 prompt + 1,393 candidate tokens**, zero thinking tokens. Their usage estimate totals **US$0.0070222**. The final ledger is **stopped at 41 attempts / US$0.748841 effective commitment**. These are token-based estimates/conservative commitments, not verified invoice charges. Earlier attempts, reservations and settlements remain exact; the unused third request was not dispatched. Cloud hosting and ordinary weather usage remain outside this news allowance; the personal key was unused.

Application-database fingerprints show exactly one changed table: `news_extraction_runs` increased **8 → 9**, adding only failed run 386. Every pre-existing selected row, all other table fingerprints, schema head, triggers and foreign keys remain unchanged. This includes original versions, runs 375/376/378/379/380/382/383/384, accounts, posts, citizen reports/moderation, cases/sources/evaluations and all old events/zones/supersession markers.

Protected hosted and local readers continue selecting **two run-384 observations**. Current history cards/maps, analytics/exports and active zones remain empty; five superseded archive records remain retained and excluded. Hosted/local desktop/mobile News Intelligence details, source text, historical raw-input inspection and scrolling pass. Local reader selection was not advanced to the failed pipeline. News automation stays paused, expiry switches OFF and the old seed disabled.

## Evidence and next boundary

Private evidence is retained under ignored `data/gma-heading-repair-20261023/`, including original-parent proof, before/after snapshots, frozen manifests, canary/worker specifications, authorities, count receipts, accounting transition, exact request/response bundles and pins, two-pass offline replay, failed correction, preservation checks and desktop/mobile screenshots. Cloud receipt prefix is `private/news-pilot/20261022-5512bbaa/diagnostics/gma-heading-20261023-v3/`.

**Stop for review.** Before another continuation, distinguish an inline barangay belonging to a specific road entry from a genuinely independent locality-only flood report, then qualify that behavior against the retained response without paid calls. Do not simply discard n7, fabricate citations, change the raw NER label, resend consumed requests or resume the stopped ledger. Any further generation/continuation needs a newly frozen, reviewed request/adoption schedule and cumulative allowance check. Polygon qualification, Tribune 25, Philstar 274 and active presentation instances remain separate and unperformed.

Recovery retains the current serving v23 and all database/spending evidence; the previous worker specification is saved privately if needed. No reset, deletion, destructive cleanup, commit or push was performed.
