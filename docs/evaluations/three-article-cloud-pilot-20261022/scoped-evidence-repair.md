# Scoped Gemini evidence repair â€” offline candidate

> **Last Updated:** October 23, 2026, 4:13 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

## Delivered scope

Local implementation only. No Gemini/countTokens request, cloud deployment, cloud database access, ledger change, source registration, inference or seeding occurred in this phase. The serving v11 checkpoint remains the last verified hosted state; this phase did not re-inspect live resources. GMA 47/raw run 375 and failed 376/378/379 remain unchanged. Tribune 25, Philstar 274 and activation remain pending.

The opt-in `scoped-quote-options-v2` contract uses `native-gemini-resolution-v2`, preserving V1 instructions, request identities and strict whole-article failure behavior by default. The new contract keeps complete source text, stable passage ordering, six evidence arrays, four-target batches, compact schema, temperature 0 and output limit 8,192. Search/Maps and model training are unchanged.

## Changes and validation boundaries

- `news_ner_durable/scoped_resolution.py` binds each target to exact passage offsets and describes conservative standalone city/barangay/depth/clock heading context. Repeated names retain distinct occurrences. City/depth/narrative boundaries reset child context. These are navigation hints and rejection constraints, not new affirmative facts or automatic inheritance.
- `gemini_resolution.py` adds distinct field descriptions, date-plus-clock citation instructions and context-only barangay handling. Exact article text and quote ordering remain. Ordinary V1 construction is unchanged; new identities and payloads require new release/grants/accounting.
- V2 records every target outcome. Independently validated observations can project while unsupported semantic rows remain unresolved, with per-field issues. The unchanged strict canonical validator still checks every accepted row. Invalid structure/targets/reference indices, receipt failures, transport and accounting errors remain hard stops. No references are added, repaired or deduplicated.
- Missing place occurrence, flood-status support, date, clock, source ownership, locality lookup and scope errors are collected together. Recognized context-only headings cannot create duplicate independent incidents; genuine locality-only flood statements remain eligible. Shared depth retains raw wording without inventing per-road measured scalars.
- `apply_resolution` recomputes V2 layout hash and all row outcomes before storing derived projections. A tampered outcome fails. Existing saved-result recomputation and reader shapes remain. There are no new models, migrations, UI elements, API endpoints or dependencies.
- The compatible bounded `thinking_tokens` field is accepted in final transport validation. Provider usage is preserved separately from semantic acceptance and reported on failure, without changing the independent budget ledger. Reporting does not constitute an invoice.
- Private semantic receipts distinguish V2 row outcomes from full article acceptance. `replay_scoped_batch` verifies the externally pinned bundle and exact reconstructed request/parent before offline semantic replay. A V1 response cannot be silently adopted under V2.
- `resolve_news_native.py --evidence-contract scoped-quote-options-v2` and frozen release loading support explicit selection; the default remains V1. Existing restricted authority checks still bind identities. No new cloud execution authority was created.

## Qualification evidence

**197 tests passed** (3 existing dependency warnings) in the stable regression run. Coverage includes scoped source formats, repeated headings, row isolation, exact saved recomputation, immutable receipts, malformed/duplicate/out-of-range references, interrupted/storage failures, strict legacy behavior, usage/accounting, budget guards, and actual disposable PostGIS persistence/readers/idempotence. The two new database tests confirm original NER immutability, valid rows alongside an unresolved row, no extra provider calls on repeat, zero flood event/zone/report writes, and truthful usage on failed legacy semantics.

A final Linux amd64 candidate is built locally using the existing authenticated dependency base and unchanged model/spatial assets. Networking is disabled both at Docker and socket level; filesystem is read-only, user 65532, CPU 1, memory/swap ceiling 3 GiB, no capabilities or privilege escalation. No cloud timeout/retry settings were changed; the retained cloud profile remains 600 seconds/zero retries from the prior checkpoint.

**Seven frozen-image worker contracts passed**, plus actual GMA layout/request/retained-failure checks. All 13 candidate batches preserve the complete source and original quote ordering; all four old failed rows remain unresolved with aggregate date/place/status/ownership diagnostics. Two legacy reference replays are network-free, and exact-request replay refuses old-contract adoption. Candidate image ID: `sha256:539e619dfeea7def8613d56bc87c2cbd12cca6a4effb2745e084c8329cc6367a` (Linux `amd64`). All 445 frozen application files match the current checkout and parse as Python.

Frozen release: `537477add36239d76e8572859787b21ec8164181a8945983d15c793900c32d8d`.

The original rejected bundle remains `715c98cc084bbe1e9b9e8070aaffbc1da65161f034448ac9cb0a2bf55a83bd88`. Strict V1 rejection remains; V2 diagnostic evaluation of the unchanged rows still yields **four unresolved rows**, including all four missing-date citations and both missing exact street passages. No retained provider response was rewritten or accepted as a new correction. This is a regression diagnosis, not a replacement Gemini answer.

Private local evidence is ignored under `data/gma-scoped-repair-20261023/`: stable final regression logs, separate initial/final manifests and contexts, pinned-image contract results, original-response diagnostics and offline scripts. Earlier investigation/release evidence is preserved. An initial broader run detected source changes made during execution and rejected four stale asset fixtures; it is retained separately and superseded only by the stable rerun, not hidden or weakened. A subsequent capture/wait wrapper timeout produced no accepted test result; `wrapper-interruption.json` records it. The stable rerun writes output directly and completes successfully.

## Pending cloud/paid acceptance

This repair has **not** been deployed or sent to Gemini. It cannot make flood cards appear on navlanes.live yet. Offline semantic handling cannot guarantee that the model will select correct evidence in future replies.

Before live continuation: review the explicit V2 row-level policy, freeze matching API/manual-worker releases and versioned authorities, count all changed payloads, and fit the complete new request/attempt schedule under the existing US$1 cumulative cap. Do not reuse the previous V1 count receipts or assume V1 cached responses are compatible. Retain the stopped 23-attempt ledger and last verified US$0.6673744 effective commitment; no reset or automatic refund.

Then qualify one controlled V2 batch with durable intent/response/usage/semantic receipts before full GMA processing. Only accepted source observations may reach OSM/NOAH qualification and the separately authorized ended/inactive archive writer. Complete GMA News Intelligence/history acceptance and idempotence before user review; Tribune, Philstar and active instances remain separate pending stages. Existing automation remains paused, expiry OFF, old seed disabled, personal key unused. This phase makes no claim of fresh hosted acceptance or database preservation fingerprints.
