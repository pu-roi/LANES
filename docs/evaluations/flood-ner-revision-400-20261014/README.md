# Stronger 400-sample NER revision — incomplete reviewed pool

> **Last Updated:** October 14, 2026, 10:30 PM (Asia/Manila)
> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

The new revision is **not complete**. The bounded collection attempted 300 additional candidate URLs and admitted 50 additional articles after complete source reading, publication and capture-evidence review. Together with the preserved research sources, the register contains 192 articles. There are 639 accepted silver location annotation inputs; 629 remain eligible after duplicate/overlap and language exclusions. These are a research pool, not a new 400-sample selection.

| Check | Required | Current reviewed pool |
|---|---:|---:|
| Publishers with at least 25 English and 25 Taglish samples | 3 | 2 |
| English LOCAL_AREA spans across the three disjoint partitions | At least 40 | 38 |
| Taglish ROAD passages across the three disjoint partitions | At least 50 | 36 |
| New selected revision samples | 400 | 0 |
| Complete contextual pilot reviews | 40 | 0; 40 paired drafts prepared |
| Training admission / actual exports / trained models | Separate gates | 0 / 0 / 0 |

The necessary pool checks fail before partition optimization. No quotas were lowered, no fresh validation/test set was frozen, and no successful revision or accuracy result is claimed. Publisher/article/group caps and every label-support constraint are implemented and tested, but they have not passed on a selected new cohort. The report proves that **this reviewed pool** is infeasible; it does not prove that every unannotated capture or every discoverable article is unusable. Another 156 captured candidates still need source/passage review. Capture failures and incomplete/out-of-window captures remain separately recorded.

The publication window is January 1, 2017–October 14, 2026. The older 2022–2026 command defaults and original manifests remain unchanged. Verified date-only evidence is accepted without inventing an instant or flood-observation clock; one new Philstar source demonstrates this. Unknown/conflicting publication evidence is rejected. Browser capture recovered 14 complete ABS-CBN bodies and one Philstar body; two malformed GMA script closures were repaired into additional immutable extraction versions from saved raw HTML.

The revision uses explicit `lanes.xx.address-v3` and spaCy 3.7.5. Its finalized rules handle numeric/letter typographic-dash delimiters, slash boundaries, ordinal delimiters and period/byline joins while retaining `006-A` and unchanged text. The earlier qualification candidate's saved bytes are preserved. **Tokenizer name alone is insufficient to reproduce an evolving candidate: use the saved bytes and SHA-256 recorded in each artifact.** Default v2 remains unchanged.

Source versions, original grouping decisions and conservative new cyclone/city/reporting-interval connections are retained in separate overlays. Publication month alone does not establish an incident. These components may overgroup uncertain dependencies and do not certify that all included locations shared a physical flood. Geographic identities remain unresolved; explicit source-supported parent mentions are retained separately.

Software verification: **508 passed**, one existing spaCy/Click warning, 32.82 seconds. This retains the 455-test baseline. Real-source v3 span validation and Unicode JSONL checks pass. A fresh legacy assembly is byte-identical to the original 400 cohort; all 496 original checkpoint/backup files checked before this work remain unchanged. No new dependencies, operational database access, model installation, runtime integration, Google-document edits, deployment or Git publication occurred.

Reports:

- [Measured status](status.json), [hard-quota coverage](coverage.json) and [infeasibility](infeasibility.json).
- [192-source register](source_register.json), [629-passage pool register](pool_register.json), [300 collection outcomes](collection_outcomes.json) and [exclusions](exclusion_register.json).
- [Empty selection register](selection_register.json) and [unfrozen partition status/targets](partition_status.json).
- [40 contextual proposals](contextual_pilot_register.json), [language correction](language_revision.json), [case coverage](case_matrix.json) and [paper-method notes](methods-notes.md).
- [Old-versus-new comparison](revision_comparison.json), [preservation/replay](preservation.json), [verification audit](audit.json) and [dedicated folder/hash register](bundle_register.json).

The dedicated local folder is `backend/training/flood_ner/artifacts/stronger-400-revision-20261014/`. Start with `article-links.csv`, `sample-links-v3.csv`, `dataset-v3/`, `reports-v3/` and `hash_manifest-v3.json`. Previous revision snapshots remain available. Full text, annotations and captures are ignored by Git; this folder has not been backed up externally. The original [400-sample dataset and backup](../flood-ner-corpus-400-20261014/bundle_register.json) are unchanged.

Next: review the already captured pending material, especially third-publisher bilingual support and additional English local-area/Taglish road cases; then rerun the unchanged hard policy. The 300-URL collection budget is exhausted. Complete contextual source review and category support only against qualifying training assignments. Research labels remain AI silver until independently verified.
