# Offline location shadow adapter: implementation qualified, comparison pending

> **Last Updated:** October 19, 2026, 2:08 PM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

The internal location-only adapter is implemented. **The Linux comparison has not completed.** One attempt stopped during startup, before readiness or article processing. It was not retried. The startup repair passes constructed checks and read-only preparation verification; a separate explicit execution is still required.

The retained model is v19 corrected control seed 0. Membership remains **345 training / 60 validation / 60 completed research-holdout passages**. No validation/holdout content, annotations or saved predictions were supplied to the new worker. No training, collection, live connection, upload, commit or push occurred.

## Delivered behavior

`ner_shadow_service.py` accepts an opaque ID, unchanged body and SHA-256, with an injected predictor. Importing the service loads no model or application rules module. Results retain independent neural and rules mentions, original-body Unicode offsets, provenance and explicit per-method errors. There is no merged result or fallback.

All six neural labels remain intact. Existing rules types map to the corresponding labels; unknown rules types and contextual locality fields stay separate. LOCAL_AREA is not fabricated from a rules context field. Source-slice equality is mandatory, repeated mentions retain their own offsets, and malformed or overlapping neural predictions fail. Existing overlapping rules candidates remain visible and flagged.

Exact span/type pairs are matched one-to-one, followed by same-span type disagreements. Remaining overlapping boundaries are diagnostic many-to-many links. The unpaired lists include those boundary-linked mentions; these categories must not be summed as mutually exclusive errors. Neither method provides ground truth, so this task supplies no accuracy, precision, recall or improvement claim.

The separate controller defaults to read-only preflight. Its grant binds implementation, tests and original test-command receipts, qualified image, model/resources, raw workload and complete application-source/consumed-CSV hashes. It permits only the same six saved training articles plus fictional inputs. Full-extent source-use assessments were renewed for this private comparison, preserving attribution, prior basis and limitations; no publisher-policy expansion or public excerpt permission is implied.

## Attempt and demonstrated startup conflict

The attempt used the previously qualified immutable Linux image, two CPUs, 4 GiB RAM, networking disabled, read-only model/input/source mounts and no credentials. Inspection verified isolation. The worker exited with **RuntimeError / exit 2**, without OOM. No readiness file or comparison rows were produced. Its stopped named container, single-use claim, lease and all receipts remain preserved.

The original worker recorded the exception type but omitted a private traceback. Its exact failing stack cannot be recovered from that receipt. A separate constructed import probe, with no model or article inputs, reproduces a demonstrated startup conflict: the existing rules module imports a report enum through ORM package initialization, which imports the application's database module and attempts engine construction. The worker's strict construction guard rejects this path. This explains a concrete startup defect consistent with the recorded failure; it is not a measured model incompatibility.

The repair reuses the **unchanged frozen offline rules guard**. Import-time declarations receive its inert `OfflineEngine` facade, while real driver imports, connections, queries, network and process dispatch remain blocked. No production database/application file was modified. The worker verifies the inert facade and now preserves an exclusive private traceback on failure. Constructed subprocess checks exercise fictional rules extraction and prove that connection and DNS attempts are rejected.

**No comparison retry followed the repair.** The failed grant now correctly fails stale-implementation checks; its original source/test bytes are preserved privately. A separate repair package binds the new implementation and passes read-only preflight. This does not prove repaired Linux execution or article-comparison success.

## Verification and readiness

- Before the attempted run: **602 passing checks**, including 60 new adapter/controller checks and existing rules/runtime/research regressions.
- After the repair: **604 passing checks**, including 62 new checks. The added subprocess probe uses fictional text and performs no neural inference.
- **1,099 protected file hashes**, 55 stat-only holdout entries and 27 stat-only prior-validation entries remain unchanged.
- Compatibility/performance Gate 3 remains passed for its earlier frozen Linux workload. New shadow comparison counts and performance are **unmeasured**.
- The adapter has no production caller registration, API/UI/configuration/schema change, report/zone creation, geographic resolution or routing action.

The next task is an **explicit new offline comparison attempt**, after verifying the stopped failed container and archiving its lease without deleting evidence. Use the repaired hash-bound preparation, a fresh destination and the same fixed limits; preserve single-use claims and never reuse the failed grant. Claim-context integration remains after a completed comparison and review. The `rules_only` database constraint is unchanged.

References remain AI-assisted silver with incomplete-history/accounting limitations. Location recognition cannot establish current flooding, depth, affected geometry or publication eligibility. [Operator guide](../../guides/ner-shadow-comparison.md) · [Aggregate verification](verification.json).
