# Bounded 400-sample NER research revision

Completed October 16, 2026. Project attribution: [@roicambe](https://github.com/roicambe) (Roi Cambe).

**Research revision complete: 400 reviewed location samples from 138 articles, with 40 paired contextual records.** All hard quotas pass. References remain AI-created silver labels. Training admission/export are zero; no model inference, training or deployment occurred.

| Partition | English | Taglish | Total |
|---|---:|---:|---:|
| Training | 140 | 140 | 280 |
| Validation | 30 | 30 | 60 |
| Testing | 30 | 30 | 60 |

The separate final inputs are **cohort-v4** and **contextual-v4**, inside ignored `backend/training/flood_ner/artifacts/research-revision-20261016-v1/`. Open its START-HERE.md. The original corrected 400/139-article cohort, contextual-v3 and every prior checkpoint are unchanged. Intermediate cohort-v3 files in the new folder are superseded drafts. No upload or Git publication occurred.

## Candidate review and selection

Reviewed **120 windows in six batches of 20**: 110 accepted and ten rejected. Sources were existing captures; no new URL collection or collection-budget extension. Rejected cases include Filipino-only paragraphs and unresolved jurisdiction/office boundaries. Actual language was reviewed independently of parent tags. Many parent-tagged Taglish paragraphs were English when isolated. Taglish follows the existing lexical-mixing convention, including some borrowed English; independent language adjudication remains absent.

After every batch, selection first fixed all 332 unaffected records, then tried the approved maximum-20 fallback. The first five batches were infeasible in both settings. In the sixth batch the fixed-332 case remained infeasible, but fallback selection succeeded with **two additional reference changes**. Final curated assembly and an independent one-change infeasibility check confirm that result. Optimality concerns this finite reviewed pool and objective, not every possible source window. All runs used the 60-second bound; no 300-second retry was needed.

Preserved **330 unaffected records/splits**, every **60 test samples** and all **ten pilots**. The two removed nonpilot training references are `cohort-958ddaeee287978235ee` and `cohort-95fea3f819908a5f942d`. Together with replacing the 68 held slots, 70 old IDs leave and 70 enter: 54 new-boundary records and 16 re-reviewed saved reserves. New boundaries retain source text, offsets, hashes and predecessor links. Unknown geographic identities remain unresolved.

Reserve re-review excluded a candidate containing related-story text and removed the nested CITY label inside Lake Baao, retaining both actual municipality mentions. Final cohort-v4 supersedes the intermediate assembly; earlier frozen datasets are untouched.

| Publisher | English | Taglish | Total |
|---|---:|---:|---:|
| ABS-CBN | 60 | 100 | 160 |
| GMA | 93 | 67 | 160 |
| Philstar | 47 | 33 | 80 |

Every publisher meets the 25-per-language minimum and 160-total/100-per-language caps. Eight-per-article, 80-per-connected-group, five-groups-per-partition and every per-language label/ROAD quota pass unchanged. RMN is not selected; saved reviewed English support remains absent. There are **1,468 location spans** and 47 location-negative passages. [Coverage](coverage.json).

## Context and source use

Preserved 35 contextual pairs exactly; freshly reviewed five training replacements (two English/three Taglish). All 40 match selected locations, with 20 per language, 14 English-source articles and 19 Taglish-source articles. Shared observations, local overrides, collective ranges and temporal transitions retain source-supported evidence. Replacements preserve negative/unknown-time and prospective statements without fabricated clocks, depths or targets. Pairs do not increase the 400 count. [Context coverage](context-coverage.json).

Read complete bodies and proposed selections for **24 changed represented articles**, plus two removed articles whose archive holds remain historical. Each has an explicit content/extent finding, four factors, archive/retention discussion, contractual uncertainty and disposition. Verified unchanged scope/evidence carries forward for 114 articles. Derived project bases cover **126 articles/351 samples**; **12 articles/49 samples remain held**. This includes 57 explicit adopted-basis entries, 68 prior desktop-summary-reported adoptions and one prior local adoption. The missing detailed desktop predecessor remains unreconciled; no consolidated desktop-v2 completion is claimed.

Holds address editorial expression, Reuters/AFP origin, a newly represented whole-article dispatch and enlarged near-whole selections. Shortening and annotation acceptance did not automatically resolve source use. Twelve nonacademic outcomes, Unknown / Codex collected, undecided retention, original decisions and admission flags remain unchanged. These are AI project assessments, not permission, legal approval or independent human verification. Verified saved statute/policy/court evidence was reused; official [IPOPHL guidance](https://www.ipophil.gov.ph/news/ipophl-releases-statutory-fair-use-guidelines-to-clarify-rules-on-copyright-exceptions/?news_page=6) was checked again for its separate four-factor analysis. [Assessments](source-use-assessments.json), [dispositions](source-use-register.csv).

## Tooling and verification

Existing offline cohort functions accept optional reference records, hard-fixed IDs and a substantive-change budget. Removal, replacement, annotation/language changes and split movement count; reviewer/group-overlay metadata alone does not. Eligibility protects fixed records and retains competing soft alternatives for explicit overlap/near-copy constraints. Reference preservation has objective priority. Time-limited incumbents are checked against actual integer/linear constraints without claiming optimality. Legacy behavior/manifests remain unchanged absent options. No new CLI, API or dependency.

Verified exact offsets, strict saved-tokenizer alignment, capture/publication hashes, quotas, 440 JSON Unicode round trips, pairwise overlap/duplicate/near-copy rejection, grouped leakage and test/pilot preservation. spaCy stays 3.7.5 with identical lanes.xx.address-v3 bytes. Cohort and context regenerations are byte-identical. **2,661 prior files**, including 23 model hashes, remain unchanged without loading a model. Export refuses all 400 research-only records before creating a destination.

Final software run: **772 passed, one Windows symlink test skipped**, four existing dependency warnings. Twenty constructed reference-selection checks cover preservation, 20-change limits, conflicts, grouped leakage, malformed references, timeout incumbents and defaults. An initial fixture was corrected to exercise eligibility after an earlier validation rejected it; no test was removed. Software checks do not establish NER accuracy or substantive/legal adequacy. [Verification](verification.json).

A separate constructed replay compares the unchanged default interface with the version of cohort.py at HEAD: all eight output files are byte-identical. This is additional artifact verification, not another test-count claim or news-model processing.

Next: address the twelve source-specific holds for this new scope; reconcile the missing detailed desktop predecessor when available. Supported admission, news-corpus model-tokenizer qualification, export, training/evaluation and deployed integration remain subsequent tasks. No universal publisher-reply requirement is introduced.

See [status](status.json), [comparison](comparison.json), [samples](400-sample-links.csv), [articles](138-article-links.csv), [changes](selection-change-register.csv), [candidate reviews](candidate-review-register.csv), [solver outcomes](selection-attempts.json) and [method notes](paper-method-notes.md). Tracked reports contain metadata and original assessment prose only; article bodies/passages remain ignored.
