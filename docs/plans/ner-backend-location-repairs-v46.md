# V46 qualified location repairs in the backend preview

> **Last Updated:** October 20, 2026, 12:58 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Executed outcome:** Backend integration passes cached parity, 1,281 tests, the single real-worker API request and independent preservation/isolation/cleanup checks. [Report](../evaluations/flood-ner-backend-location-v46-20261020/README.md). The flag remains off; the admin interface is next.

Implement the approved backend task: trained v19 locations → unchanged v40 proposals → authenticated v44 combined repairs → unchanged v42 grouping. Preserve original neural mentions, explicit rule provenance and unresolved fields. Admin-panel work remains subsequent.

## Backend contract

Promote v44 verbatim and use one pure adapter in worker and host validation. Return ordered v40/v44 proposals without altering their hashes, stage-labeled abstentions and final effective mentions. Boundary replacements retain original IDs/source evidence and never change the neural list. Recompute both the proposal chain and v42 graph on the host, rejecting stale/tampered/mismatched results without fallback.

Keep the existing endpoint and `lanes-ner-preview-v1` fields, article link, groups and unassigned facts. Set `provenance.location_rules` to `lanes-location-repair-v40+v44`, add `location_method: combined`, and retain v42 context provenance. Document type-family and remaining recognition/language limits.

## Verification and completion

Authenticate v44/v45 and snapshot application/tests before changes. Require parity on all 788 cached inputs, 407 saved graphs, 418 applicable cases and three repaired-view checks before wiring. Preserve eight corrected article occurrences, 40 restored facts, 11 unresolved rows, all 93 affected facts and eight earlier complete rows.

Retain authorization, disabled/error, tampering, source-offset, qualifier/time-role, isolation, concurrency and cleanup tests. Bind passing tests and final code before making one real isolated-worker API request from the existing article snapshot with fake read-only storage. Require all 53 original neural mentions and grouped output to match saved qualified results. Use the qualified image/bundle, two CPUs, 4 GiB RAM, no network and read-only code/assets; inspect actual isolation and cleanup. Preserve failures; no automatic inference retry. If verification fails, retain predecessor wiring and report the blocker.

Explicitly reconcile intended application changes against predecessor snapshots while preserving all frozen research, references, model/data artifacts and validation/holdout exclusion. Publish aggregates and synchronize task/progress/roadmap/index/guide/issues. Feature remains disabled by default; no `.env`, frontend, normal-processing, storage, plotting or routing changes. No retraining, rule tuning, new articles, reference revisions, database access, uploads, commits or pushes. Passing establishes backend-preview readiness only.
