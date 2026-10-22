# Flood-news NER dataset relevance audit

> **Last Updated:** October 16, 2026, 11:32 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**The concern is supported: some selected passages have weak flood-news relevance.** Preserve the completed experiment and prepare a separately versioned, flood-focused successor. Age alone is not a reason to discard correctly annotated historical flood reporting. This audit does not replace records, revise labels, rerun models or establish how much the topic mix affected F1.

## After the v3 Drive upload: transfer verified and development data reviewed

**The missing-file blocker is resolved.** Downloaded the [desktop-to-laptop v3 backup](https://drive.google.com/drive/folders/1JrrMzZ3FyP0LGU00xWKF54enyyC87ffX), verified all eleven transport parts and the companion manifest/helpers against the uploaded checksum list, and joined the original **700,047,334-byte** archive. ZIP SHA-256 is `9e217a78613b1f86ce9fa2c051262fe8a53d4d74b5ec35f906758f2823cb0336`. The reviewed restore helper verifies all **2,357 unique objects / 3,863 logical files** and repository-relative artifact paths. Verification finds **1,642 identical files, 2,221 missing files and zero conflicts**; restoration adds exactly the missing files. Nothing existing is overwritten. Installed environments and credentials are excluded; local `.env` and all 460 original audit inputs verify unchanged.

The restored development manifest matches the previously published checkpoint binding, and **565 development file hashes** verify. All six frozen original/A selected models are present; **66 model files** match their recorded test-freeze hashes, without loading a model. The private path/hash review records how original desktop paths map to these restored files; frozen manifests are not rewritten. Source SHA fields in the capture-screening register bind capture JSON bytes, while each source's `text_sha256` binds its text; both check correctly.

Rechecked the 244 development drafts, their source-exact windows and entity offsets, reference-status register, source inventory, recorded holds and safe held-out aggregate. Reviewed the selected articles' titles/leads and read six unused source bodies fully to prepare a concrete acquisition-free priority queue. This is topic/coverage review, not a new complete annotation adjudication or source-use admission.

| Restored development measure | Verified value |
|---|---:|
| Draft articles / passages / location spans | 49 / 244 / 359 |
| Candidates / unresolved unscored holds | 179 / 65 |
| Positive / empty-location candidate passages | 78 / 101 |
| Candidate English / operational Taglish | 96 / 83 |
| Candidate CITY / PROVINCE / BARANGAY spans | 50 / 45 / 22 |
| Candidate ROAD / LANDMARK / LOCAL_AREA spans | 29 / 13 / **0** |
| Captures awaiting full topic/origin/reference review | 91 |
| Other excluded or held captures | 19 |
| New admission / corpus replacements | 0 / 0 |

The newer selected pool concerns Philippine floods, consequences, recovery, warnings and flood-control reporting; it is not evidence that unrelated initial search results were admitted. Its more immediate sampling problem is **101/179 (56.4%) empty-location candidates**, single-publisher concentration and no candidate LOCAL_AREA spans. Empty-location examples are useful, but cannot supply positive rare-class coverage. All five draft LOCAL_AREA spans are held: four carry occurrence-type/context questions, while the explicit purok example has the saved tokenizer-boundary failure. Neither the class gap nor the negative percentage establishes a universal optimal ratio or a measured cause of the original model's errors.

Theme names also overstate positive support if read without their references: the shared-identifier theme currently has **zero English positives / one Taglish positive**, and short-code themes have **one positive per language**. Locality-designator candidates mainly teach administrative labels, not qualifying LOCAL_AREA examples. Count the actual referenced classes and positive phenomena before deciding training size or recipes.

### Six already captured sources to review next

| Source title | Concrete contribution to investigate |
|---|---|
| Families evacuated as floods hit Dagupan City | Explicit sitio and barangay context in observed flooding/evacuation. |
| Flood hits upland Talisay City, Cebu; over 200 affected | Explicit purok references and shared identifiers, compound road and recovery/recession context. |
| Parts of Quezon City get flooded after Friday afternoon thunderstorms | Two named crossing streets, explicit barangay context and a physical shopping facility. |
| Parts of NLEX not passable due to floods | Expressway codes and differing access status; plaza/interchange taxonomy still requires care. |
| LIST: Thunderstorm floods several roads in Metro Manila on Monday, June 23 | Road crossings, abbreviations and per-road depth/access evidence. |
| LIST: Flooded roads in Metro Manila due to thunderstorm | Flooded and explicitly subsided entries, intersections and road codes. |

All six were already in the 91 pending captures and are outside the 244 draft memberships. The private priority queue binds their exact capture files, source hashes and evidence ranges. They are **sources for further annotation review**, not six admitted samples, final entity references or a frozen partition. Source-use/origin review, complete passage annotation, operational-language review, frozen-tokenizer alignment and historical/event/duplicate grouping remain necessary. Several other pending RMN captures contain Cebuano/Hiligaynon prose; publisher identity or English words cannot establish Taglish eligibility. Their languages were not relabeled in this audit.

Only the fresh-test package's safe aggregate was read, with its published aggregate/verification hashes checked. It still reports **56 prospective records, zero admitted independent test records and no seal**. Its private texts/labels were not opened for development review. Transfer and byte hashing do not certify test independence or dataset readiness. The one saved development alignment failure is retained; no tokenizer or inference rerun occurs.

**Next action in the same Gate 3 task:** Use the six-source queue and the remaining captured sources to build source-backed positive coverage, resolve the existing holds and review publisher/event balance before new dataset admission/export/training. Keep the original experiment and exposed test unchanged. There is no longer a request for the user to locate missing files.

Private continuation checkpoint: `backend/training/flood_ner/artifacts/v3-drive-review-20261016-v1/`, including archive-verification/restoration receipts, `audit_development.py`, `development-review.json`, `development-topic-ledger.json`, `priority-flood-source-review-queue.json` and `checkpoint-path-and-hash-review.json`. Public metadata: [v3 review](v3-review.json), [transfer verification](v3-transfer-verification.json). All writes in this continuation are missing-file restoration, separate review metadata and documentation; there is no corpus replacement, annotation revision, model execution, dependency/schema change, deployment, commit or push.

## Evidence and scope

Fast-forwarded clean `roi-branch` from `4736cea3` to `477c6d4c`. Read the referenced **Build flood news NER check** chat, current task plan, roadmap, source/annotation/selection contracts and the export, training, held-out, qualification and additional-dataset reports. The referenced chat describes the earlier laptop handoff; pulled repository records describe the later desktop experiment.

Inventoried all **138 source titles/provenance entries and 400 selected records** from the original admitted derivative. Performed a focused saved-body/selected-passage review of five questionable sources, with supporting reads of flood, forecast, project and editorial examples. This is **not a new full semantic adjudication of every article or annotation**. The private article ledger explicitly distinguishes inventory/title screening from focused body review; absence from its review queue is not approval.

The local admission checkpoint's **52 recorded file hashes** verify, and four admission/cohort/context bindings match the published qualified-export manifest. All **460 protected admission/capture files** remain unchanged. Standard-library checks pass for passage/source hashes, source-exact windows, six-class span text/offsets/non-overlap, identities, date range and saved grouping-key separation. These checks do not rerun tokenizer qualification or prove complete geographic labels, event independence or accuracy. Historical software/GPU results remain historical.

## Original corpus findings

| Measure | Rechecked value |
|---|---:|
| Location samples / articles / separate contextual pairs | 400 / 138 / 40 |
| Train / validation / exposed test | 280 / 60 / 60 |
| English / operational Taglish | 200 / 200 |
| Location spans / empty-location passages | 1,465 / 48 |
| Publication dates | January 10, 2017–September 4, 2026 |
| Articles / samples dated 2017–2021 | 67 / 188 |
| Focused source review | 5 articles / 19 passages |
| Focused passages by split | 6 train / 9 validation / 4 test |
| Strong future flood-core replacement recommendations | 6 passages: 4 validation / 2 test |

The older dates are inside the explicit `REVISION_WINDOW` (2017–2026); the legacy 2022 collection default is a different window. Date-only publication evidence remains valid where a timezone-qualified `source.published_at` is null. Historical article dates are not current flood observations.

All 138 source bodies contain at least one broad flood lexeme. Nevertheless, 170 selected passages lack those lexemes, and several full articles are predominantly about another subject. **Neither statistic is a semantic relevance verdict.** A surrounding sentence can be a useful source-exact NER example without repeating “flood”; a security or loan article can mention floods incidentally. Keyword filtering cannot settle this task.

| Focused source | Existing samples | Finding and successor-dataset recommendation |
|---|---:|---|
| AFP: NPA rebels attack soldiers despite ceasefire, peace talks | 5 validation | Four selected passages concern attacks/peace talks without flood context: replace these in a future flood-focused core. One concerns attacks on flood-relief operations and may serve as an explicit contextual contrast. None of these five is a training sample. |
| PH, South Korea sign $3B development assistance loan package | 3 test | Two selected passages concern general loans/infrastructure: replace in a future core. One project-list passage mentions flood-control projects and is at most an auxiliary example. Preserve all existing test references/scores. |
| MGB recommends: Vacate site of landslide in Barangay Busay | 6 train | Mainly landslide evacuation/mitigation with generic flood warnings. Review for an intentional adjacent-hazard role or replacement by flood-specific locality examples. These are not automatically incorrect place labels. |
| Students in Opol, Misamis Oriental at risk as they pass through dilapidated bridge everyday | 1 test | Bridge-safety story with a flood-prone alternative route. Useful landmark/susceptibility contrast, with no observed road-flood claim established. |
| Next Pharmally? Palace says Filipino interests 'prioritized' in Kaliwa Dam deals | 4 validation | Dam negotiation/asset prose; one passage explicitly concerns feared future inundation. Keep only with a stated auxiliary/prospective role in a successor corpus. |

The **19 queued passages are not 19 bad labels**, and the six strong recommendations are not a complete count of weak material. The queue contains record/source IDs, hashes, source ranges, split and rationale without copied article text. No source/admission flags change.

## What to keep and what to replace

- Keep accurately annotated historical flooding, road lists, rescue/evacuation and recovery. Add recent independent reports to cover changed road names, phrasing and locations; do not discard older examples simply for age.
- Keep deliberate forecast, clearance/negation, habitual susceptibility, flood-control and editorial contrasts where they represent expected inputs. Label every in-scope place even when no flooding is occurring. A no-flood passage is not necessarily an empty-location NER negative.
- Replace weak general-news windows in a **new corpus version**, prioritizing independently captured flood reports with road sections/intersections, explicit barangay/sitio/purok context and named physical facilities. Do not fill rare-label quotas with unrelated stories merely because they contain useful addresses.
- Retain genuine empty-location flood passages and realistic byline/time/code contrasts. An unresolved place type must not be converted into an empty label list. Original negatives are imbalanced: training has 6 English/33 Taglish; validation has 0 English/6 Taglish. Review balance prospectively rather than declaring all negatives harmful.
- Separate mention recognition from flood status/depth/time associations. This model's six location classes do not by themselves determine flooded roads or safe publication.

These recommendations apply spaCy's requirement that training data represent expected inputs. They do not establish a universal positive/negative ratio or a measured benefit from a particular replacement. [spaCy training guidance](https://spacy.io/usage/training).

## Three seeds and the newer replacement pool

Pulled records confirm completed original seeds **0/1/2**, plus exploratory Recipe A seeds **0/1/2**. The original seed 0 remains primary at **63.12 strict test F1**; original family mean is **68.46**, while A's is **70.24**. These are agreement with AI silver references. Multiple seeds measure training variability; they do not repair sampling/annotation issues. Weights were unavailable during the initial audit. The later v3 continuation above verifies 66 restored files across all six selected checkpoints; no model execution is claimed. [Frozen test report](../flood-ner-heldout-test-20261016/README.md).

The separately reported [additional-dataset checkpoint](../flood-ner-additional-dataset-20261016/README.md) already corrects broad initial searches toward Philippine flooding. It records **244 drafts from 49 articles, 179 candidates and 65 holds**; all 49 represented articles are GMA. There are **107/244 empty-location drafts** and **101/179 empty-location candidates**, so simply adding the pool would heavily change the original 48/400 negative mix. These are recorded counts, not a newly audited draft or an automatic rejection. Rare positive-theme/language capacity is **156/240**, one tokenizer alignment issue remains, and no new corpus admission or fresh test seal exists. Review the 91 remaining captured sources and existing holds against flood relevance and positive coverage before further collection or training.

## Initial Drive and local availability, before the v3 upload

Read both visible study folders under [LANES_NER](https://drive.google.com/drive/folders/1AQatnNai4uIMWZra-60Y0e8sR5lYr6jA). The older Drive article CSV has **139 rows** and matches the local corrected October 15 package after CRLF normalization. It is a predecessor, not the 138-source admitted derivative. The later [desktop handoff](https://drive.google.com/drive/folders/1gnGV2wP0gNHx2LNa64fwc-U4AIQxRdkT) identifies the 400/138 derivative. Its Drive checksum matches the local **28,476,420-byte ZIP**, SHA-256 `afe11aa15398d9b88e7ef268c75f7d51c79107206a60f29ac4313264f4dba65f`. This is a current checksum/local-ZIP comparison, not a new cloud-ZIP download or byte readback.

At the initial audit, the newer private training, qualification-review and additional development/held-out checkpoints were **absent from this checkout** and were not found in those two folder listings or the specific Drive searches. This did not prove they existed nowhere else. The user subsequently uploaded v3, and the verified continuation above resolves that transfer blocker. This paragraph preserves the initial observation; it is not the current availability state. Drive files and permissions are unchanged by this review.

## Initial next-work record, superseded by the v3 continuation above

1. Locate and hash-verify the newer **development** checkpoint, its admission/exclusion/grouping evidence and tokenizer diagnostics. Keep fresh held-out curation isolated. Record the transfer instead of assuming the old ZIP contains these files.
2. Apply an explicit article-topic and selected-passage-role review to the successor pool, using the private 19-record queue as a bounded starting point. Preserve original 400/40 records, exposed test, scores and checkpoint roles; the new six-passage recommendation does not authorize rewriting old test labels or reporting a cleaner retrospective F1.
3. Resolve reference/language/source-use/alignment holds; favor flood-specific positive ROAD/LOCAL_AREA/LANDMARK examples and improve publisher/event coverage. Freeze source/event/syndication groups and training/validation membership before selecting recipes. Freeze a fresh independent test separately before any new training.

No production code, dependency, API, ORM or migration change is needed for this review. CPU/Linux/failure/performance qualification and runtime integration remain separate open work.

Private reproducible audit: `backend/training/flood_ner/artifacts/topic-audit-20261016-v1/` (`audit.py`, `summary.json`, `article-topic-ledger.json`, `future-replacement-review-queue.json`, `input-hashes.json`, `preservation.json`, `drive-review.json`, `output-hashes.json`). Run from the checkout with `backend/venv/Scripts/python.exe -B backend/training/flood_ner/artifacts/topic-audit-20261016-v1/audit.py`. It reads original inputs and writes only this ignored audit directory. Public report contains aggregate findings and source titles, not article passages.
