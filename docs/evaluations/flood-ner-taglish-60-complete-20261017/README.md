# Taglish Test Set Completion: 60/60 Sealed Outcome — October 17, 2026

The independent test set for LANES spaCy NER has officially reached **60 of 60 passages** and has been sealed. The targeted acquisition round (v7) successfully acquired the final 11 Taglish positive passages needed to satisfy the balanced 60-passage held-out test specification, closing the deficit to zero.

## 1. Final Sealed Partition Composition

The independent held-out evaluation test partition is balanced across language and polarity:

| Language | Positive | Genuine Negative | Total Passages | Target | Deficit | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **English** | 27 | 3 | 30 | 30 | 0 | **Complete** |
| **Taglish** | 27 | 3 | 30 | 30 | 0 | **Complete** |
| **Total Test Partition** | **54** | **6** | **60** | **60** | **0** | **SEALED** |

### Per-Article Quota & Historical Isolation
- **Maximum 3 passages per article**: Strictly enforced across all 60 passages.
- **Historical storm isolation**: Zero overlap with excluded historical training storms (*Tisoy*, *Quinta*, *Ulysses*, *Carina*, *Enteng*, *Kristine*, *Maymay/Habagat*), DPWH inquiries, or past training corpora.
- **Dataset separation**: Zero overlap with training (345 passages) or validation (60 passages) partitions.

---

## 2. Targeted Acquisition Accounting (Round v7)

The bounded acquisition round operated under strict append-only journal accounting with verified SHA-256 integrity:

- **Raw URL Identities**: 765 observed / 800 ceiling (31 remaining slots preserved; well within safety boundaries).
- **Publisher Attempts**: 89 executed / 100 ceiling (11 remaining attempts preserved).
- **Search Queries**: 47 accounted queries in journal.
- **New Publisher Captures (v7)**: 5 verified articles (`CP005`, `CP006`, `CP007`, `CP008`, `CP009`), yielding the 11 missing Taglish positive passages.
- **Network Status**: All network operations stopped; collection ledger permanently closed.

---

## 3. Entity Span Verification & Tokenizer Alignment

All passages underwent mechanical validation against the frozen production tokenizer `lanes.xx.address-v2` (`sha256: 3f666f61346b7196d931ab9781a3d83f41d688e24b298e8e494b3d92c384a588`):

- **Total Entity Spans**: 96 spans mechanically verified.
- **Exact Half-Open Unicode Slices**: 100% verified against raw source byte strings.
- **Token Start & End Alignment**: 0 tokenizer errors; strict character-to-token span alignment.
- **Span Non-Overlap**: 0 overlapping entity annotations.
- **Label Distribution across 60 Passages**:
  - `CITY`: 45
  - `BARANGAY`: 20
  - `ROAD`: 14
  - `LANDMARK`: 8
  - `PROVINCE`: 8
  - `LOCAL_AREA`: 1
  - Total: 96 entities.

---

## 4. Binary Export & Serialization

The sealed 60-passage test set has been serialized into spaCy's binary `DocBin` format:
- **Test Binary**: `backend/training/flood_ner/artifacts/heldout-taglish-completion-20261017-v7/private/test-60.spacy` (60 documents, strict token alignment, record IDs stored in user data).
- **Status & Manifests**:
  - `aggregate-status.json` (`sha256: e0ca8ed4362ecc09eee9e5c896d4db0788afe0ef6e3db34a8d93c3fb38ab5799`)
  - `verification-manifest.json` (`sha256: 8ddaa2c1f0b82293fb999c5a6b4ab44011b4b3a90b92bac04031920cb803d844`)

---

## 5. Next Steps: Desktop GPU Retraining Handoff

With the held-out test partition verified and sealed at 60/60:
1. **Desktop Power State**: The desktop GPU machine may now be powered on for model retraining.
2. **Successor Dataset Export**: Export the full successor dataset (345 train, 60 dev, 60 test).
3. **Model Retraining**: Execute spaCy GPU pipeline training on `lanes-ner-trf` or `lanes-ner-sm` using the sealed successor partitions.
