# Academic NER source-use review

> **Last Updated:** October 15, 2026, 12:11 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

Three publisher AI reviews and source-bound credit/amount reviews for all **139 articles / 400 samples** are complete. All three academic-use admission decisions remain unresolved. The corrected dataset, 40 contextual v3 pairs, frozen partitions and original study package are unchanged. This completes the review deliverable, not training permission or admission.

| Publisher | Articles / samples | Conclusion |
|---|---:|---|
| ABS-CBN | 50 / 158 | No express scope-matched NER permission established; research-exception basis and content-provider questions need documentation. |
| GMA | 71 / 160 | Educational/noncommercial downloading has express policy support; team NER processing and AFP-credit content require separate consideration. |
| Philstar | 18 / 82 | Personal-use copying terms do not expressly cover the team workflow; opinion material and attribution/QA-host issues require specific treatment. |

GMA's educational-download language is narrower than a demonstrated license for this complete workflow. The publishers' internal AI policies describe newsroom practice and supply no external training authorization. [GMA user policy](https://www.gmanetwork.com/news/user-policy/), [ABS-CBN terms](https://www.abs-cbn.com/terms), [Philstar copyright notice](https://www.philstar.com/copyright-notice), [Philstar agreement](https://www.philstar.com/member-agreement).

## What was assessed

The declared audience is the research team and adviser, with local private NER experiments only. The actual user/access controls, storage/copy arrangements, retention period and school rules remain undocumented. No requirement for institutional approval is presumed. AI recommendations, a later researcher project decision, publisher permission and any legal determination remain distinct.

Section 185 is evaluated as a possible case-specific research/fair-use basis. Purpose, nature, amount/substantiality and market effects are considered separately, including full-source retention and repeated embeddings. Sections 173/175 distinguish compilation/facts from underlying prose; section 184 conditions do not follow from student status alone; section 187's single-natural-person private copy is not adopted as a blanket basis for team copies. No NER-specific exemption or percentage safe harbor is claimed. [Consolidated IP Code](https://www.wipo.int/wipolex/en/legislation/details/18399), [IPOPHL guidance](https://www.ipophil.gov.ph/news/ipophl-releases-statutory-fair-use-guidelines-to-clarify-rules-on-copyright-exceptions/?news_page=6).

The publisher terms and statutory exception analysis are separate: this review neither treats terms as a final copyright ruling nor assumes fair use overrides contractual obligations. No permission from publishers was requested or received.

## Article-specific findings

The article register contains 139 rows, of which 78 have one or more follow-up flags. Flags overlap and do not count as prohibited articles. Captured structured/byline credits are available for 71 articles; 68 lack captured bylines. Eight Philstar articles are opinion/editorial pieces. Nine GMA samples contain complete captured articles. There is one explicit AFP-credit story, one possible Reuters-origin lead, one AFP photo-caption credit and one AFP acronym referring to the Armed Forces of the Philippines. One Philstar capture uses a QA subdomain. These are evidence observations, not verified rights ownership.

The AFP photo caption is present in selected training record continuation-1601d9976fab438f9cbb; no image is included in the text dataset. Review-v2 corrects an initial private draft that said the caption was excluded. The dataset itself is unchanged. An unrelated body phrase beginning with a time after “By” is not treated as an author byline. Source offsets and hashes support the distinctions.

Complete unique article bodies total 317,476 Unicode characters; selected nonoverlapping passage intervals total 142,136. Those are different amounts from physical-copy counts. The preserved current study bundle alone has 718 clean full-article representations under its existing defined counting scope, excluding raw captures and other folders; this review adds no full article copies. No copying fraction determines legal clearance.

## Verification result

The final selected NER/location regression suite passes **664 tests in 42.17 seconds**, retaining the 638-test focused baseline and adding 26 academic-review guards. The historical 666-test result used a different selection and is not presented as this run. There is one existing spaCy/Click deprecation warning. Checks verify 16 clause pointers, 24 bound evidence files, all 139 sources, unchanged twelve nonacademic outcomes, the corrected dataset/context/package, all 23 model files and the unchanged main Python environment. The 1,774-file milestone snapshot and earlier 26,679- and 9,145-file preservation sets match. Export refuses all 400 research-only records. Software checks are not permission or model-accuracy results.

## Evidence and decision package

Nine current ordinary HTTP checks produced six readable captures and three unsuccessful content checks: ABS-CBN terms/AI returned 403; IPOPHL returned a 200 challenge page without readable guidance. Earlier ABS-CBN snapshots and separate readable web observations are retained. The earlier IPOPHL raw snapshot also lacked substantive text and is not relied upon as readable guidance. Failures do not establish policy changes. NCDA's amendment transcription contains visible typographical errors; exact consolidated statutory wording is taken from WIPO, with the amendment used as corroboration.

The ignored local folder is `backend/training/flood_ner/artifacts/academic-use-review-20261015-v1/START-HERE.md`. Its decision sheet and three readable assessments explain the next action for each publisher. Editable forms leave final decision-maker, date, use basis, evidence, exception dispositions and retention requirements unresolved. A checkbox or adviser signature cannot by itself confer publisher rights or establish fair use.

Public metadata: [publisher conclusions](publisher_assessments.json), [all article reviews](article_review_register.json), [exceptions](article_exceptions.json), [bound clauses](clause_register.json), [retrieval evidence](evidence_register.json), [corrected input bindings](review_bindings.json), [unchanged twelve other-use outcomes](unchanged_nonacademic_outcomes.json), [status](status.json), [verification](audit.json), [decision summary](decision-summary.md) and [paper-method notes](methods-notes.md).

The next task is to document the missing researcher facts and a supported scope-specific project decision or permission/clarification where necessary. Applying a supported decision through a versioned admission process remains separate. Unresolved portions remain research-only; no quotas or partitions are changed to mask a hold. GPU preparation follows the existing ordered plan.

No new news collection, external messages/uploads, public demonstrations, Google-document edits, admission changes, model inference/training, GPU setup, runtime/schema changes, deployment or Git publication occurred. Full text and raw policy evidence remain ignored.
