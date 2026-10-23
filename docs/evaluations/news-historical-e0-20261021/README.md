# E0 — September source preparation

> **Last Updated:** October 21, 2026, 11:58 PM Asia/Manila

Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe). **Preparation complete; neural processing and activation have not run.** [Task checklist](../../task_plan.md#e0--prepare-and-freeze-real-article-inputs) · [Operator guide](../../guides/historical-news-preparation.md) · [Aggregate verification](summary.json).

The implemented operator command read the configured Cloud SQL `lanes` database in a repeatable-read transaction with database-enforced read-only mode, bounded statement/lock timeouts and rollback. It authenticated pinned immutable source fingerprints, exact Unicode text hashes, original source metadata and the five retained inactive, ended, valid-SRID-4326 history links. It generated private files only. No articles, versions, runs, events or zones were inserted or changed.

| Source | Saved input | Characters | Existing history | Selection |
|---|---|---:|---|---|
| Tribune September 24 | Article 25 / version 66 | 1,136 | Run 134 / claim 4 / event-zone 59 | Quirino/Guazon: primary `active_demo` candidate |
| Same Tribune input | Same capture | Same input | Run 134 / claim 5 / event-zone 60 | Gov. Pascual: backup `active_demo` candidate |
| GMA September 9 | Article 47 / version 137 | 1,970 | Run 137 / claims 7, 11, 12 / event-zones 61–63 | Three `historical_archive` references |

## Frozen private evidence

Ignored directory `data/news-historical-e0-20261021/package` contains `inventory.json`, `native-25.json`, `native-47.json`, `manifest.json` and `receipt.json`. Each native wrapper binds its original article/version and legacy fingerprint to a native input snapshot, its new fingerprint and a compatible runtime request. Native capture creation is local processing preparation, not creation of a second article or flood occurrence. Original text and whitespace remain exact; no offsets are transplanted from the differently spaced local GMA capture.

- Dataset: `capstone-september-2026-v1`.
- Session: `ee30c69d-32cd-555f-bb90-26899cb74810`.
- Canonical manifest SHA-256: `0beb452c80dd0a805bada20dffd6c92dfdee3cd99e1951bf5eaf0862ce9f8439`.
- Authenticated asset/pipeline manifest SHA-256: `d8e78eaff5e274ff314dc890def6f91bbcac5439140f88618adc61ddced04d2f`.

The session derives deterministically from dataset, source fingerprints and candidate dispositions. A second complete command returned `existing_package_verified` with the same session, document hashes and manifest hash. Existing packages are verified without rewriting files; changed or partial packages are refused and preserved. This establishes preparation repeatability. Future E1–E2 persistence still needs its own session-based duplicate protection.

## Evidence limits and next gate

Both inputs retain their saved publication timestamps but lack original feed wording bound to the exact stored body. The native captures correctly preserve `basis=legacy_unknown`, `raw=null`, `timezone_known=false`; runtime publication is null. This is an explicit provenance limitation, not source verification or permission to infer an observation instant from publication. E1 must resolve supported source dates separately or return a visible unresolved outcome.

All inspected cloud extraction runs remain `rules_only` (120 completed). The previously approved C3b workload is authenticated by frozen SHA-256 `d701b2a7de90b362c19ce8409fff785edcdf10c7455b216d00af3050a8f49ea1`; neither September body matches it exactly or after whitespace tokenization. No cached neural result is therefore accepted as proof for these selected sources. No model, annotation partition or neural output was opened for scoring or inference.

Legacy evidence quotations are bound to exact positions in the selected body. Legacy claim and geometry hashes remain references, explicitly separate from new neural results. Actual source/NER/geometry qualification is `not_evaluated` for every candidate. The primary and backup must each pass independently. Future qualified active examples target **both the public map and Spatial Operations**, labeled **Historical demonstration — September 2026**; E0 changes neither map.

## Verification

The targeted suite passes **27 checks**, with existing multipart/Pydantic warnings. Tests cover exact whitespace/Unicode preservation, immutable input tampering, trustworthy versus unknown feed proof, history identity/state/geometry rejection, deterministic session/dispositions, asset mismatch, database confirmation and read-only transaction enforcement, package repeatability and preservation of changed/partial evidence. Tests prohibit real SQL connections and neural session startup. The actual operator command additionally completed one read-only preparation and one read-only repeat verification against the configured cloud database.

Independent package verification recomputes canonical document/native/source hashes, exact text and evidence offsets, session identity and preparation code identity. Source diff and documentation links are checked. No new dependency, endpoint, frontend, model, migration, cloud deployment, collection, inference or database write is included.
