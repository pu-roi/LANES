# Bounded discovery and isolated-test outcome — October 17, 2026

The research adapter and verification are complete. **The provider route is blocked:** its first and only one-record GDELT request returned HTTP 429. The isolated curator stopped without retries, alternate search, publisher requests or new passages. Provider conformance to the requested bound remains unverified.

The proposal remains **345 training / 60 validation**, with **42/60 conditional test passages**. One compatible witness contains 21 English positives + three genuine negatives and 15 Taglish positives + three genuine negatives. The remaining shortage is **six English and twelve Taglish positive passages**. These are conditional AI-assisted silver references, not admitted or sealed records. No improvement has been measured.

## Acquisition accounting

| Measure | Outcome |
| --- | ---: |
| Starting exposed URLs / article attempts | 202 / 66 |
| Provider metadata requests / new article requests | 1 / 0 |
| Newly counted diagnostic URLs | 2 |
| Actual cumulative URL exposures | 204 / 300 |
| Unresolved reservation debit | 1 |
| Conservative exposure including reservation | 205 / 300 |
| Remaining unreserved URL slots / article attempts | 95 / 34 |
| New captures / new passage proposals | 0 / 0 |

Error-response diagnostic URLs count before relevance filtering. The pending reservation survives reopening; it is not automatically refunded. The historical 202/200 overrun remains recorded. Current revised ceilings are respected; that does not make the earlier run compliant.

The [standalone adapter](../../../backend/training/flood_ner/bounded_discovery.py) reserves three URL slots per requested record, requires a successful nonempty one-record probe before batches of at most five, retains raw aliases and receipts, and halts on unexpected fields, shapes, excess URLs/records, redirects or failures. A single writer maintains a hash-chained append-only private journal. This checks a documented provider contract; no client can prove a nonconforming server will never over-return. The live error response demonstrated no successful bound. [Official GDELT contract](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/) and [operator guide](../../guides/ner-bounded-test-discovery.md).

GDELT is discovery metadata only. Full publisher captures must independently support publication eligibility, original-text English/Taglish classification, exact-source use and all six location classes. Dates and provider language tags cannot qualify a passage. No source policy or eligibility convention expanded.

## History evidence

Three of fifteen unavailable desktop payloads were recovered byte-exact from the existing October 16 Drive handoff: the archive checksum sidecar, companion checksums and instructions. All eighteen companion checksums reconcile. The additional-artifact accounting now totals **35 = 20 available payloads + one prior inventory hash + two archive byte ranges + twelve unavailable payloads**. The immutable dispatch snapshot retains its earlier subtotal; a separate metadata addendum supplies this reconciliation without changing source identity or eligibility.

The twelve remaining items are named with exact hashes and sizes in private evidence requests. Prioritize `source-stats.json`, which may clarify collection scope; other helper/transport filenames alone do not establish another article corpus, and their contents remain unverified. Recorded inventory coverage remains **6,369 files / zero read errors** and **3,863 backup payloads = 3,382 identical + 478 rule exclusions + three explicit exclusions**. The user's statement that older collections stayed inside LANES is preserved as an attestation, distinct from verified file coverage. Excluded, deleted, unrecorded or unspecified history is not certified absent. No archives were restored and no archived scripts executed.

## Verification and isolation

**54 unit tests passed; one Windows symlink test was skipped**, including 40 focused adapter tests. The curator additionally passes 29 fault guards and validates 92 complete references / 116 spans with zero schema, Unicode-offset, non-overlap or frozen-tokenizer errors. Unknown references stay held, never converted into empty-location negatives. The known development tokenizer failure remains held. All 6,103 protected coordinator inputs and 353 curator predecessor files verify unchanged.

The original 402 qualified development candidates plus three previously qualified validation additions remain unchanged: training 170 English / 175 Taglish; validation 38 English / 22 Taglish. Taglish validation still has zero ROAD examples, one LANDMARK example and no short-code theme. Historical fitted-source components remain training-only; conservative related-report grouping does not assert a physical incident identity.

All 133 existing test proposals remain accounted for: 92 complete references and 41 unresolved. No new source was available for annotation or grouping review. Selection reuses the jointly compatible witness; at most three passages per article, non-overlap, mutually exclusive alternatives, history/group exclusions and positive quotas remain enforced. The frozen tokenizer and vocabulary hashes are unchanged. Only the curator-approved aggregate and verification files reached the coordinator; individual test text, labels, identities, URLs, titles, raw provider evidence and ledgers remain private and Git-ignored.

## Readiness and next action

The test remains **unsealed**, with zero admitted/scored records. Review the provider failure and unresolved reservation before any separately scoped future attempt; do not reset the baseline, retry the halted journal or use unbounded/paid fallback. Obtain the eighteen missing eligible positives and resolve material history/use/reference evidence without reducing quotas. Then assess admission, freezing, export and a desktop GPU handoff as a separate task. **The desktop can remain off.**

No production ingestion, public API, dependency or database schema changed. No development collection, training, inference, corpus admission, partition freeze, training-format export, upload or push occurred.

Aggregate evidence: [curator status](curator-aggregate-status.json), [curator verification](curator-verification-manifest.json), [history](history-summary.json), [readiness](readiness.json), [verification](verification.json), [hashes](metadata_hash_manifest.json). Predecessor reports remain byte-unchanged.
