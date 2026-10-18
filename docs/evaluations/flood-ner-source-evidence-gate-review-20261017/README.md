# Source-evidence gate review for held test leads — October 17, 2026

> **Last Updated:** October 17, 2026, 6:42 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

The source-evidence gate review evaluated whether held leads and identity dispositions from previous collection rounds could be supported using existing saved material in the workspace. With **zero network operations**, all **86 reconsidered held identities** and **19 permanent exclusions** were audited. **Zero holds were resolved** to admitted test references. The compatible conditional independent test selection remains **53/60 passages** (**30 English / 23 Taglish**). All 53 baseline members are preserved intact. Exactly **seven Taglish positive passages remain missing**; the shortage is **unchanged**.

| Conditional test selection | With location entities | Genuine negatives | Total | Target | Deficit |
|---|---:|---:|---:|---:|---:|
| English | 27 | 3 | 30 | 30 | 0 |
| Taglish | 20 | 3 | 23 | 30 | **7** |
| **Combined** | **47** | **6** | **53** | **60** | **7** |

These counts represent contiguous passages selected from captured articles (maximum three passages per article), not whole articles. References remain **AI-assisted silver** under the original operational Taglish convention defined in the annotation guide, not independently adjudicated bilingual or human-gold labels.

---

## Source-evidence gate evaluation

The final collection round recorded 105 new raw identity dispositions under the closed 600-URL / 100-publisher attempt ceiling. These are raw identity tokens (search hits, aliases, third-party URLs, and social/media tokens), not 105 distinct publisher articles. The evidence review audited each held category against preserved workspace material, saved historical bundles, and source-use requirements:

| Hold category | Identity count | Gate disposition | Supported resolutions | Primary blocker / exact missing evidence |
|---|---:|---|---:|---|
| **Unsupported source / media / alias identities** | 67 | RETAINED_HOLD | 0 | External social media, video, media URLs, or search hit tokens. None correspond to saved publisher articles in the workspace. Demonstrable source-specific reuse rights and full captured article bodies are absent. Converting an alias or third-party token without reservation is prohibited. |
| **History & reporting component holds** | 10 | RETAINED_HOLD | 0 | Cross-checked against `source-only-historical-bundle.jsonl`. All 10 share named weather episodes (Quinta Oct 2020, Tisoy Dec 2019, Maymay/Habagat Aug 2026), continuous rainfall sequences (Ofel/Pepito, Pangasinan continuous rain), or government flood-control programmes/inquiries (Bayanihan sa Estero, Bulacan ghost project inspection, Oplan Kontra Baha, Mindoro asset) already present in historical training/validation data. Different publication dates, reporting districts, phrasing, or article URLs do not establish event or reporting independence. |
| **Unqualified metadata identities** | 6 | RETAINED_HOLD | 0 | Fragmentary search snippet tokens only; no complete publisher article identity or verified publication instant within January 1, 2017 – October 14, 2026. |
| **Reference type & location capacity holds** | 2 | RETAINED_HOLD | 0 | Mentions lack supported explicit six-class positive location entities or coherent positive mixed passages; generic mentions (agencies, regional water bodies, bare untyped province names) do not qualify as positive place entities. |
| **Target language capacity hold** | 1 | RETAINED_HOLD | 0 | English-only burst pipe report without Taglish lexical mixing clauses. The English test quota is already met (30/30); cannot satisfy Taglish requirements. |
| **Permanent exclusions (historical exact / window / flood role)** | 19 | RETAINED_EXCLUSION | 0 | 3 exact historical sources already exposed, 7 publication dates outside the 2017–2026 window, and 9 non-flood topics (utilities, finance, justice specials). |
| **Total** | **105** | | **0** | **All 86 held identities and 19 exclusions remain retained.** |

No held lead could be converted into an eligible positive test window from existing saved material alone.

---

## Collection and accounting status

Collection remains **strictly CLOSED**. Zero network calls were made during this review.

- **Cumulative raw identities:** 585 recorded raw identities + 4 inherited uncertain slots = 589 conservative possible exposure.
- **Cumulative URL ceiling:** 600 (arithmetic remainder: 11 slots).
- **Publisher capture attempts:** 84 / 100 (arithmetic remainder: 16 attempts).
- **Network operations this task:** 0.
- **Closure rule:** Discovery stopped below the declared 20-slot headroom threshold. The arithmetic remainders (11 slots / 16 attempts) do not authorize further requests. No GDELT troubleshooting, searches, captures, retries, policy expansions, or budget increases occurred.

If further acquisition is pursued, it requires a separate, concrete bounded follow-up proposal with prospective authorization and exact alias accounting.

---

## Archive, selection, and mechanical verification

1. **Archive integrity:** All 194 archive proposals (128 complete references, 66 unresolved rows) and 190 effective proposals (128 complete, 62 unresolved) are accounted for. All 62 effective unresolved references remain held and unscored, never treated as genuine negatives.
2. **Joint witness selection:** Recomputed through the isolated solver. All 53 baseline witness members are preserved without loss or replacement:
   - English: 27 positives + 3 genuine negatives = 30
   - Taglish: 20 positives + 3 genuine negatives = 23
   - Deficit: 7 Taglish positive passages.
   - Usable gain: 0. Usable reduction: 0.
3. **Mechanical validation:** All 128 complete references and 166 entity spans re-verified against `AnnotationRecord` schema, exact half-open Unicode offsets, non-overlapping spans, and frozen tokenizer `lanes.xx.address-v2` (`3f666f61346b7196d931ab9781a3d83f41d688e24b298e8e494b3d92c384a588`). **Zero schema or tokenizer errors.**
4. **Guard checks:** All 27 reference/selection rejection guards passed (covering exposure quarantine, history holds, negative treatment of unknown references, source caps, and premature sealing). All 20 mocked acquisition guards passed.
5. **Coordinator preservation:** Exactly **6,750 protected repository files verified unchanged** against their SHA-256 signatures.

---

## Training and desktop status

**Desktop action: None; desktop GPU can remain off.**

No admission, partition freeze, test sealing, export, inference, or training occurred.
- Successor dataset admission, grouped partition freezing, isolated test sealing, qualified exports, and desktop GPU handoff follow only after test coverage and material independence/source-use requirements are resolved.
- Historical fixed-400 exporters and launchers bind the earlier experiment and cannot be run unchanged for the successor dataset.

---

## Evidence and artifacts

- Safe curator aggregate status: [curator-aggregate-status.json](curator-aggregate-status.json) (`4d41e2fff0f2219aac7f970e95e37d6d429a45ac6e4f26cabdf3ec6463b6a4e8`)
- Safe curator verification: [curator-verification-manifest.json](curator-verification-manifest.json) (`acf8f3fdc31833532dd4c17129841e2ab92f80a5da27b5d1d003b5eacfab9917`)
- Source-evidence gate detail: [source-evidence-gate.json](source-evidence-gate.json)
- Readiness summary: [readiness.json](readiness.json)
- Coordinator verification: [verification.json](verification.json)
- File hash manifest: [metadata_hash_manifest.json](metadata_hash_manifest.json)
