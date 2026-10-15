# Source-use review and organized 400-sample study package

> **Last Updated:** October 15, 2026, 10:53 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

The source-use preparation and local organization milestone is complete. **666 regression tests pass**, retaining the 625-test baseline and adding 41 bundle checks. The 41 bundle checks were rechecked after adding saved-file indexes. The private study folder retains **400 accepted AI silver location samples from 139 articles**, with **40 contextual v2 training pairs**. Ten appendix examples cover all six location classes and all three publishers, with five English/five Taglish passages. They come exclusively from training.

| Outcome | Measured result |
|---|---|
| Academic / paper-excerpt / dataset assessments | 9 AI assessments completed |
| Production / model-distribution assessments | 6 deferred |
| Unresolved use outcomes | 15; original 12 forms preserved |
| Training admission / DocBin export | 0 / 0 |
| Distribution-ready / published | No / no |
| Download candidate | 400 identities: 391 passage texts and 9 metadata-only entries |
| Context candidate | 40 paired identities: 38 text-bearing and 2 metadata-only |
| Private study | All 400 original location records and 40 context pairs intact |
| Bundle replay | 603 files plus the manifest match byte-for-byte |

The selected article split is ABS-CBN 50 articles/158 samples, GMA 71/160 and Philstar 18/82. The partitions remain 280 training, 60 validation and 60 testing, with 200 English/200 Taglish overall. Context pairs do not increase the sample total to 440. The annotations were created and reviewed within the same Codex workflow, not independently verified human/gold references. Model accuracy and training are not measured by package creation.

[Bundle register](bundle_register.json), [status](status.json), [source amounts and rights cues](source_amounts_and_rights.json), [fifteen assessments](scoped_assessments.json), [policy evidence](policy_evidence.json), [appendix register](appendix_register.json), [method notes](methods-notes.md), [audit](audit.json).

## Finding the local files

Open backend/training/flood_ner/artifacts/400-sample-study-package-20261015-v4/START-HERE.md. The folder contains:

- 01-private-study: exact frozen cohort/context files, selected capture bodies/raw evidence, article/sample CSV links.
- 02-paper-appendix-draft: ten partial-article training passages, location labels and attribution, in Markdown and JSONL.
- 03-download-candidate: passage-only records, separate contextual pairs, attribution metadata and a local research-only ZIP.
- 04-use-review: refreshed and earlier policy evidence, original packet/forms, versioned assessments and editable unresolved decision forms.

Every text-containing section is research-only with distribution unresolved. The candidate excludes full-source fields, capture HTML, private paths and weights. Nine selected passages are themselves complete captured articles; their text and full textual contextual payloads are withheld from the candidate instead of modifying or truncating them. All nine remain intact privately. This is a prepared candidate with explicit gaps, not a released 400-text dataset.

The package is another local copy, not an external backup. Its 603-file hash manifest is verified and a separate replay is preserved. Full text, raw policy/article captures and generated ZIP files remain ignored by Git and excluded from production builds.

## Evidence and assessment limits

New ordinary HTTP checks read the GMA policy, Philstar notice/agreement, IPOPHL guidance, NCDA amendment text, WIPO consolidation and the Lawphil statute copy. ABS-CBN ordinary HTTP returned 403; a separately documented current web-text observation and earlier hash-bound policy captures are retained. Both Supreme Court endpoint failures are also retained. A failed endpoint does not establish a changed policy.

The review distinguishes personal/educational downloading from proposed NER training, appendix publication and dataset distribution. It records purpose, nature, amount/substantiality and market effects as separate factors, with uncertainty. The assessment references amended section 185.1, quotation/teaching conditions and private-copy limitations; it does not treat academic purpose, attribution or the model's MIT license as automatic clearance. [IPOPHL guidance](https://www.ipophil.gov.ph/news/ipophl-releases-statutory-fair-use-guidelines-to-clarify-rules-on-copyright-exceptions/?news_page=6), [consolidated statute](https://www.wipo.int/wipolex/en/legislation/details/18399), [RA 10372](https://ncda.gov.ph/disability-laws/republic-acts/republic-act-no-10372-an-act-amending-certain-provisions-of-republic-act-no-8293-otherwise-known-as-the-intellectual-property-code-of-the-philippines-and-for-other-purposes/).

Complete article bodies total **317,476 Unicode characters**. Selected unique passage intervals total **142,136 characters**; this does not erase the fact that complete articles were retained. Within the new private bundle, source JSON/body copies and embedded source text account for **718 clean full-article representations**, excluding every raw capture file (HTML or rendered JSON) and all previous folders. This is a count of the listed clean-text representations, not a total physical-copy census. Per-source measurements retain these distinctions. No word-count or percentage safe harbor is claimed.

Captured author/byline cues are present for 71 articles and unknown for 68; four articles contain agency-name cues. These are evidence observations, not ownership or syndication determinations. Corporate site notices do not establish the rights holder for every article. All nine current assessments have actual AI assessor/date provenance; unsupported human sign-off, permissions, institutional requirements, retention periods and release conditions remain unresolved. The six future scopes are explicitly deferred.

The versioned [tokenizer report correction](../flood-ner-tokenizer-qualification-20261015/README-v2.md) replaces the earlier “400-source” wording with “400-sample.” The original report and metadata hash manifest remain intact.

No new news articles, external uploads/messages, Google-document edits, model training, GPU installation, runtime/database changes, deployment or Git publication occurred.
