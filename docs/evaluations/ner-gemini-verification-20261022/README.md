# NER → Gemini resolution — local acceptance

> **Last Updated:** October 22, 2026, 7:56 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

This preserves the earlier local checkpoint. A later [guarded cloud release](../ner-gemini-cloud-release-20261022/README.md) is deployed; its single real request returned HTTP 402. Successful model correction remains unqualified.

Implemented using the existing Gemini key configuration, with no live Gemini request, shared database mutation, deployment, UI change, migration, model retraining or new dependency. This is software acceptance with deterministic provider fixtures, not an accuracy benchmark for a real Gemini model.

## Verified behavior

- Full original articles, publication metadata, candidate IDs, original native groups and unassigned facts reach the mocked provider. Backend-owned quotation offsets bind facts to exact source text. Strict response JSON and target coverage are enforced.
- Corrected claims use a separate run on the same article version; the original run/neural graph is unchanged. Saved recomputation detects edited claims or evidence. No neural inference is needed for saved-run resolution or a completed repeat.
- Quoted observation clocks take priority. The agreed contemporaneous publication proxy occupies the existing starting-time field with internal JSON basis. Calendar-day-only evidence keeps its date without inventing a clock. Clearance/report/forecast/negation, cross-road clocks and contradictory dates do not become active observation timestamps.
- Source suppression during an API request prevents correction commit. Changed authority is rejected before insertion/requests. Concurrent workers send only one request. Retryable provider failures persist bounded backoff; no immediate retry or hidden fallback occurs.
- Reader context v2 selects explicitly approved derived and raw versions together. Unprocessed native articles remain visible; failed selected verification appears as failed in existing article/collection views. Cards, source details, pagination/counts and downstream evaluation use the selected saved projection.
- The complete disposable coordinator orders resolution before evaluation/publication. Unmapped fictional roads produce no operational polygon. Repeats must not add API calls, neural inference, runs or publication decisions. Existing citizen event/report/active-zone fingerprints are unchanged by resolve-only processing.
- CLI startup/import/settings/interruption tests run in fresh interpreters with database connections, sockets and subprocesses denied; bounded JSON errors conceal private sentinel diagnostics.

## Target and preserved assets

Disposable PostGIS cases clone the owned local empty template and assert approved Alembic head `f1a9c7e2b604`; each case drops only its own verified disposable clone. No new migrations or models were introduced. Review confirms protected staff dependencies remain in place, SQL values are parameterized and Gemini credentials stay in an HTTP header to a fixed Google endpoint with redirects disabled. Provider error bodies and keys are excluded from saved receipts.

The authenticated original Part 2A model bundle and runtime code are unchanged. A new current application/placement asset manifest and source hash inventory are retained privately under `data/ner-gemini-implementation-20261022/`. Original Part 2A receipts/manifests remain untouched. The final Gemini-derived release identity depends on the exact model/prompt/config selected for real-provider qualification.

## Tests and remaining release gate

**297 distinct checks pass across the final expanded run and focused correction rerun.** The expanded run completed 296 passing checks and one failure caused by an overly strict test expectation of exactly one initial publication decision. The existing coordinator can append separate stage decisions; the corrected test fingerprints the actual first-run decision IDs and verifies that repeating the pipeline adds none. Its focused rerun passes. The earlier 256-check regression checkpoint also passed; counts are not additive. Three dependency warnings remain recorded.

Coverage includes both new resolution test modules, native durable/integration regressions, retained auditor/CLI checks and historical E1 interpretation/policy tests. Private logs: `pytest-final.txt` (256 passes), `pytest-acceptance.txt` (expanded checkpoint before correcting the test expectation) and `pytest-coordinator-final.txt` (passing correction). Failed/intermediate attempts remain retained; no failing test was deleted. The final private acceptance JSON records the union and file hashes.

A bounded real-model/key/billing acceptance request and matching backend/manual-worker/reader release remain pending. The exact screenshot 4:34 PM source has not been identified or replayed. Scheduled RSS method and disabled historical seed execution remain unchanged. No hosted success is claimed from local mocks.

[Implementation/release plan](../../plans/ner-gemini-verification.md) · [Operator steps](../../guides/ner-gemini-verification.md).
