# Targeted independent-test collection and desktop history handoff

> **Last Updated:** October 17, 2026, 3:25 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**The saved-capture review and desktop inventory handoff are complete. Acquisition compliance and training readiness remain blocked.** Preserve the **402 qualified development candidates / proposed 345 training + 57 validation**, all historical datasets, drafts, reviews, tokenizer, models and results. This task collects independent-test evidence; new test articles do not become training samples. Better training performance is not established by collection or silver-reference review.

This follows the [archive and saved-test selection review](../flood-ner-archive-history-test-selection-20261017/README.md). The user authorized targeted independent-test collection within the existing limits. Development collection stays closed. No corpus admission, partition freeze, training-format export, neural inference, training, upload, commit or push occurs. Public APIs, dependencies and database schemas remain unchanged.

## Acquisition accounting and failure

The isolated curator reconciles **185 previously exposed URLs / 32 capture attempts / 27 successes / five failures**. Earlier transport-retry receipts are already represented in those attempts and are not silently discarded, double-counted or reset. Record dispositions for 12 eligible-or-rejected uncaptured discoveries before proceeding with bounded additional discovery. Preserve alias/exposure distinctions instead of reducing the count through retrospective canonicalization.

Five pre-breach capture requests succeed: **four previously discovered sources and one newly discovered source**. The largest capture batch is four, within the batch limit of ten; cumulative attempts become **37/100**. Read all five complete bodies, verify publication dates against **January 1, 2017–October 14, 2026**, and review operational language, location-reference completeness, source origin, scoped passage-use evidence and known source/event/reporting relationships. No source-policy expansion occurs.

**The URL ceiling was exceeded.** At 191 exposed URLs, a final search fan-out returned 11 unseen URLs with nine remaining slots. Preserve the resulting **202 exposed URLs / 17 new URLs**, against ceilings of 200 cumulative and at most 15 new. Acquisition compliance is **false**. This is a protocol failure, not a compliant search whose last two results can be erased from the record.

Stop collection immediately. All five captures preceded the breach; there are zero later searches, fetches or retries. The **entire final 11-URL batch remains unreviewed, held and ineligible**, with zero captures/selections from it. No retrospective nine-of-eleven allowance is created. The numerical overrun is two URLs; that does not mean only two final-batch rows are held. The unused capture-attempt allowance does not authorize further discovery or cure the failure. Future collection requires explicit scope resolution and an exposure-bounding method before any requests.

Private acquisition records bind cumulative ledgers, search fan-out evidence, capture timestamps, aliases, baseline receipts, dispositions and hashes. The coordinator reads only the curator's two permitted safe aggregate files; individual test sources, URLs, passages, labels and judgments remain isolated.

## Reference and joint-selection outcome

All **77 prior alternatives / 27 earlier saved articles** are preserved. The five new captures produce **12 proposed windows: nine complete positive silver references and three unresolved references**. The combined pool has **89 proposals / 72 complete references / 17 unresolved**, across 32 saved articles. Unresolved references remain unscored and are not genuine empty-location negatives. Alternative proposals are not all simultaneously selectable.

One new source receives bounded local conditional clearance, one has a supported reporting-history exclusion, and three retain specific history or extent holds; a new third-party extent hold is recorded among these overlapping categories. A flood-related article is not automatically independent or eligible. Do not turn a distinct URL/body hash into proof of event independence, or extend an older use decision automatically to its new passages.

The fixed design remains **60 passages = 30 English + 30 operational Taglish**, each with **27 positives and three genuine no-location negatives**, at most **three simultaneously selected passages per article**, mutually exclusive alternatives and source-exact non-overlapping windows.

| Finite-pool diagnostic | English positives | Taglish positives | English negatives | Taglish negatives | Joint total |
|---|---:|---:|---:|---:|---:|
| Source/reference-only witness | 25 | 25 | 3 | 3 | 56 |
| After known local history and scoped-use filters | 17 | 14 | 3 | 3 | 37 |

The filtered joint witness gains one supported slot over the preceding 36-passage witness; it still lacks **ten English and 13 Taglish positives**. A different filtered witness reaches 21 English positives with ten Taglish positives, also totaling 37. The source/reference-only English-max witness is 27 English plus 23 Taglish positives and six negatives, totaling 56. Never add per-language maxima from incompatible witnesses or pad positive quotas with surplus negatives.

These are diagnostics for enumerated supported alternatives, not a bound over every conceivable segmentation of the articles. They also explicitly ignore the unresolved **global acquisition failure and external-history gap** to describe conditional support. Under all actual requirements, eligible/admitted/scored records remain **zero**; target feasibility, readiness, freshness certification and sealing remain false.

Fresh shared-schema/source-exact Unicode-offset/non-overlap/frozen-tokenizer checks pass **72 complete references / 109 spans**, with zero errors. Retain 17 unresolved full references outside scoring. Nine inherited selection/reference guards and eight additional budget/alias/output guards pass. All **186 predecessor hashes**, five tokenizer vocabulary files and **48 private curator output hashes** verify unchanged. These are static tokenizer checks; no neural pipeline or model inference is loaded. The known development alignment failure remains held and unchanged through protected input hashes.

References remain **AI-assisted silver**. Neither human verification nor measured model improvement is implied. The development proposal's missing Taglish ROAD/LANDMARK and short-code-theme validation coverage remains visible and is not repaired by independent-test collection.

## Desktop inventory handoff

The new [standard-library history helper](../../../backend/training/flood_ner/history_inventory.py) accepts an explicit LANES checkout, repeated optional collection roots, explicit exclusions, optional safe source-metadata files and a **new** output destination. It streams file hashes and records paths, sizes and modification times; it does not export article bodies, annotations, secrets or model results. Recognized isolated-test packages, environment/dependency/cache trees, model weights and secrets are excluded. Links/reparse points are not followed. Archives are hashed without extraction; archived helper scripts are never executed. Existing outputs and overlapping roots are rejected. Read errors and file mutations make completion false.

Source metadata is opt-in, projected only from explicitly named historical source-capture JSON/JSONL files: source identity, sanitized URL, recorded dates, hashes and recorded grouping IDs. Strip query strings/fragments, reject URL credentials and nested annotation/model structures, and never copy titles, source text or entity labels. Metadata and path outputs remain private. Explicit exclusions are required for any private test folder whose name is not recognized. No extraction is used in the actual laptop smoke run.

See the [short desktop instructions](../../guides/ner-desktop-history-inventory.md). A private portable copy of the single Python helper, instructions and a hash manifest is prepared separately; it has not been uploaded or executed on the desktop. Python 3.10+ and its standard library are sufficient. The user's original recorded desktop checkout is distinct from the current laptop checkout.

The laptop smoke run uses Python's `-I -S -B` mode, with third-party packages disabled. Explicitly exclude the two unrelated routing-tile trees and record those exclusions; do not claim them inventoried. The earlier whole-checkout attempt was intentionally stopped before producing a report because it traversed those unrelated large assets; preserve its empty destination and attempt receipt. Verify the completed scoped inventory's manifest/helper hash, privacy exclusions, absence of decoded source documents, read-error count and comparison with the recorded backup. Exact counts are in [laptop smoke verification](laptop-smoke-verification.json). Entries outside its named scope are not automatically missing files.

The helper has **14 boundary tests: 13 pass and one native symlink test is skipped because Windows does not permit creating it**. A separate deterministic reparse-point test passes. Four coordinator privacy/readiness fault tests also pass, giving **17 passing / one skipped** local checks. Test existing destinations, overlapping roots, unsafe metadata inputs, secrets/fresh-test exclusions, no archive execution, no default source decoding, source projection, read errors, concurrent file mutation, unsafe coordinator outputs and attempted sealing/admission. Curator checks are separate and not added as distinct records.

## Readiness and next action

Run the inventory on the **original desktop**, naming any known extra collection folders. Return `inventory.json` and `manifest.json` through the private handoff when requested, with a statement of included locations and any remaining uncertainty. Reconcile those metadata/hash records with the October 16 backup and source-exposure supplement before deciding whether omitted historical sources, collections or related reporting exist. Do not assume another folder exists; do not assume unspecified folders were checked.

External history remains **unknown / user not sure**. A successful laptop run, verified recorded archives and a portable helper do not resolve that status. The prior missing detailed source-use predecessor remains a separate provenance limitation. Independently resolve the acquisition failure and remaining positive-reference, use/extent and grouping evidence gaps before sealing. No automatic collection-budget expansion, quota reduction, taxonomy change or held-record substitution is authorized.

After the independent-test boundary passes, actual admission, grouped freeze, qualified export and the **desktop GPU training handoff** can be prepared. Laptop work remains review/preparation. No training begins under the old launchers in this task.

Verify **5,269 protected prior files unchanged**, including the preceding archive/history package and source-evidence bindings; these overlapping preservation sets are not additive article/record counts. See [readiness](readiness.json), [safe curator aggregate](curator-safe-status.json), [safe curator verification](curator-safe-verification.json), [local checks](test-results.json), [prior-file preservation](preservation-verification.json) and [publication checks](publication-checks.json). The private coordinator package includes reproducible integration/preservation checks and the portable desktop helper bundle. Original dataset, draft, review, tokenizer, model and score bytes remain unchanged.
