# Offline flood NER preparation

> **Last Updated:** October 16, 2026, 10:34 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Current Gate 3 status:** Improvement preparation is complete; additional-dataset readiness/admission remains open. Development has 244 drafts (179 candidates / 65 holds); isolated test curation has 56 prospective entries, zero admitted independent test records and no seal. Resolve coverage, reference/language, source-use, historical-overlap and the single development tokenizer-alignment failure before corpus admission/export or further training. Original 400-sample results and model roles remain frozen. [Readiness report](../../../docs/evaluations/flood-ner-additional-dataset-20261016/README.md). No research package or trained model is carried by Git; current private checkpoints must be transferred and hash-verified separately.

Historical qualification review: all 60 passages and 391 original/A seed 0 error events are reviewed in a separate ignored checkpoint. Fourteen passages retain unresolved AI reference/convention questions; frozen labels, scores and model roles are unchanged. The review is complete; operational qualification remains open. Next prepare the remaining Gate 3 qualification specification before runtime integration. [Review](../../../docs/evaluations/flood-ner-model-qualification-20261016/README.md).

Historical held-out evaluation: original/A seeds 0/1/2 and rules/native baselines complete one frozen test attempt on 60 passages. Original seed 0 remains primary at 63.12 strict test F1; exploratory A seed 0 scores 67.72. The test set is now exposed. Next review Gate 3 model qualification before isolated integration; no test-driven tuning or automatic promotion. [Held-out report](../../../docs/evaluations/flood-ner-heldout-test-20261016/README.md). Earlier checkpoints follow.

Historical primary-training result: primary seed 0 manually completed, selecting development F1 67.15 at step 455. Run frozen seeds 1/2 manually, one at a time, using RUN-TRAINING.ps1 -Seed 1 (or 2) -StartTraining from the repository root; omit -StartTraining for check-only. Existing outputs are refused. Seed 0 remains primary. [Result](../../../docs/evaluations/flood-ner-primary-training-20261016/README.md); [commands](../../../docs/guides/ner-first-manual-training-20261016.md). Earlier checkpoint summaries follow.

Historical desktop preparation: export and baseline/configuration preparation pass. The ignored experiment-preparation-20261016-v2 checkpoint freezes rules mapping and three GPU-initialized seed configurations; seed 0 training is next. No corpus prediction evaluation/training has run. See [preparation verification](../../../docs/evaluations/flood-ner-experiment-preparation-20261016/README.md). Earlier checkpoint summaries below preserve their historical states.

Historical laptop handoff: private Drive delivery is verified through roicambe02@gmail.com; the [owner-only folder](https://drive.google.com/drive/folders/1gnGV2wP0gNHx2LNa64fwc-U4AIQxRdkT) holds the unchanged v2 ZIP and companions. All seven files pass readback hashes. Use the [desktop instructions](../../../docs/guides/ner-desktop-handoff-20261016.md); actual desktop restoration/qualification have not run. The latest software result is 880 passed/one skipped; no software changed in this delivery. Earlier checkpoint details follow.

Historical laptop corpus-tokenizer gate: the new `qualify-corpus-tokenizer` command and evaluation protocol are delivered, but the single isolated run is blocked at import by Windows Application Control error 4551. No passages were tokenized and no predictions/export/training ran. 840 software tests pass/one skipped. Admission remains 400, original datasets are preserved, and the next step is verifying the existing desktop environment/private input paths before a separate qualification run. [Report](../../../docs/evaluations/flood-ner-corpus-tokenizer-20261016/README.md); [local failure/protocol guide](artifacts/corpus-tokenizer-qualification-20261016-v1/START-HERE.md).

Earlier completed private academic-use checkpoint: a separate admitted v5 derivative contains 400 AI silver location samples from 138 articles and 40 paired contextual records, with frozen 200/200 languages and 280/60/60 partitions. Only the three source-policy fields change; original research-only files and all twelve nonacademic outcomes remain unchanged. The ledger retains 69 explicit, 68 desktop-reported and one prior local adoption, without reconstructing the missing detailed desktop predecessor. This is scoped project admission, not publisher permission or a dataset license. Corpus qualification against the pinned calamanCy tokenizer and a frozen evaluation contract is next; no export or training has run. See the [admission report](../../../docs/evaluations/flood-ner-academic-admission-20261016/README.md) and [actual local working folder](artifacts/academic-admission-20261016-v1/START-HERE.md).

Current GPU checkpoint: the actual RTX 3060 Ti desktop passes isolated Python 3.11.17/spaCy 3.7.5/CuPy 13.6.0/Torch 2.11.0+cu128 execution, six-class constructed trial updates and exact saved-model CPU entity replay. 122 focused tests pass. See the [GPU evaluation](../../../docs/evaluations/flood-ner-desktop-gpu-20261015/README.md) and [rerun/setup guide](../../../docs/guides/ner-desktop-preflight.md#qualified-rtx-desktop-environment-october-15-2026). Source admission and full-cohort qualification remain separate.

Current desktop preparation: the standard-library-only `desktop_inventory.py` runs directly before installing research dependencies. It records local hardware/driver facts in a fresh ignored destination and never claims CUDA or training qualification. See the [desktop guide](../../../docs/guides/ner-desktop-preflight.md). Source-use decisions remain independent; publisher correspondence is optional clarification rather than a universal prerequisite when a supported exception applies.

Earlier clarification preparation: four unsent drafts and a 69-article/243-passage register are available in the [local start-here guide](artifacts/held-article-clarification-20261015-v1/START-HERE.md). Recipient identities and response fields remain blank; no hold, recommendation or admission was changed. See the [metadata report](../../../docs/evaluations/flood-ner-held-clarification-20261015/README.md).

Earlier academic-use proposals: 139 articles assessed; 70 GMA articles (157 passages) recommended for private academic use and 69 held for source-use clarification. The 400 accepted AI silver samples, 40 contextual-v3 pairs and frozen partitions remain unchanged. No recommendation is an applied project decision, publisher permission or source admission. academic_proposal.validate_decision_proposal(proposal, records, contexts, root) is a separate read-only Python interface; it does not replace the earlier review validator or add a CLI. New forms carry root-relative path/hash references to facts/guidance/reviews. See [proposals](../../../docs/evaluations/flood-ner-academic-proposals-20261015/README.md) and the [local decision brief](artifacts/academic-decision-proposal-20261015-v1/DECISION-BRIEF.md).

Earlier research checkpoint: 400 corrected AI silver location records from 139 articles, 40 contextual v3 pairs and frozen 280/60/60 partitions. The verified Drive backup is owner-only. Researcher-reported adviser guidance limits use to private research/training; no specific international ethics framework is established. Source-use project decisions remain unresolved, and this guidance does not change admission flags. Next finalize the supported academic-use basis and article-exception dispositions before admission/news-model processing. Read-only hardware inventory and constructed-only GPU environment checks can proceed independently; actual corpus/tokenizer/training and public-inference scope gates remain. Retention uncertainty alone is not a training prohibition. See [current publication audit](../../../docs/evaluations/flood-ner-publication-20261015/README.md) and [private-access record](../../../docs/evaluations/flood-ner-private-access-20261015/README.md).

Run commands from `backend/` using its existing environment (Python 3.12, spaCy 3.7.5). This package prepares research sources and annotated corpora. It does not train a model, access operational SQL, invoke news processing/publication, or change production configuration.

```powershell
.venv/Scripts/python.exe -m training.flood_ner inventory
.venv/Scripts/python.exe -m training.flood_ner capture --url 'https://publisher.example/article' --source-id 'publisher-article' --publisher 'Publisher' --language tagalog --event-group 'review-needed-event'
.venv/Scripts/python.exe -m training.flood_ner inspect-place --name 'Sitio Seis' --context 'Catmon, Malabon' --city 'Malabon'
.venv/Scripts/python.exe -m training.flood_ner collect-news training/flood_ner/artifacts/discovered_urls.json
.venv/Scripts/python.exe -m training.flood_ner import-browser-news training/flood_ner/artifacts/rendered_snapshot.json --source-id 'abs-rendered-report' --language english
.venv/Scripts/python.exe -m training.flood_ner capture-wikipedia --title 'Typhoon Noru' --language en
.venv/Scripts/python.exe -m training.flood_ner verify-news ../docs/evaluations/flood-news-corpus-100-20261014/collection_outcomes.json --output training/flood_ner/artifacts/collection100/verified
.venv/Scripts/python.exe -m training.flood_ner prepare-pilot ../docs/evaluations/flood-news-corpus-100-20261014/news_register.json --output training/flood_ner/artifacts/readiness/review-v1
.venv/Scripts/python.exe -m training.flood_ner review-passages training/flood_ner/artifacts/readiness-20261014/review-queue-v3/candidate_passages.jsonl ../docs/evaluations/flood-ner-editorial-20261014/editorial_reviews.json --output training/flood_ner/artifacts/editorial/replay-v1
.venv/Scripts/python.exe -m training.flood_ner validate training/flood_ner/artifacts/annotations.jsonl
.venv/Scripts/python.exe -m training.flood_ner export training/flood_ner/artifacts/annotations.jsonl --output training/flood_ner/artifacts/datasets/v1
.venv/Scripts/python.exe -m training.flood_ner export training/flood_ner/artifacts/location_annotations.jsonl --profile location-only-v1 --output training/flood_ner/artifacts/datasets/location-v1
```

`capture` needs an actual explicitly supplied public HTML URL. It follows bounded redirects, caps responses at 4 MiB, and refuses a page with no article/main container or JSON-LD article body. It never falls back to treating the entire page as an article. It retains raw response HTML bytes, frozen extracted text, extraction method, hashes, known timezone-qualified publication metadata and capture time. HTML-visible text is a reproducible extraction, not the raw HTML; all downstream offsets refer to the frozen text. Navigation/body pollution still needs review. Captures default to research-only with unknown reuse terms. Repeated capture preserves the same immutable record; identical bodies from different URLs retain separate source identities.

`inventory` imports preserved `docs/evaluations/**/source_manifest.json` text captures, the explicitly captured-original `mcp_saved_news.json` article texts, and locally fetched captures. It validates known text hashes, preserves URL/capture-version identities, including versions with matching body hashes, and reports missing files or unsupported manifests. It does not import the constructed 50-item rule fixture as news. Results are `sources.jsonl`, metadata-only `report.json` and research evidence pointers in `case_matrix.json`. Unknown language and timestamps remain unknown. Inventory succeeds with explicitly listed per-source issues; inspect `issues` before proceeding.

`inspect-place` reuses existing cardinal normalization, PSGC hierarchy lookup and identified OSM locality assets. `--city` is explicit source context, not inferred from a guess. It returns candidates, including ambiguity metadata; it writes no annotations and establishes no flood geometry.

The annotation contract is defined in `annotation/schema.py`, with a generated JSON Schema in `annotation/schema.json`. See the [annotation guide](../../../docs/guides/flood-ner-annotation-v1.md) and [research findings](../../../docs/research/flood-ner-semantics-20261014.md). Each JSONL line is one full `AnnotationRecord`; the source object contains the unchanged complete source text so validation can verify passage offsets without mutable external files.

`validate` checks schema/extra fields, source and passage hashes, exact spans, token alignment, non-overlapping entity spans, typed relationship references, evidence coverage, parent/override cycles and split leakage. It prints errors and exits nonzero on invalid input. It cannot prove semantic correctness, licensing, independent review or physical flooding.

`export` additionally requires complete accepted review, reviewer identity, a teacher for silver labels, explicit training admission with allowed reuse, and frozen article/event/syndication grouping and train/dev/test membership. It refuses any unqualified record rather than silently omitting it. Unsyndicated sources need their own reviewed syndication-group identifier. Copied text, URLs, article revisions and related event/syndication groups cannot cross splits. Negative passages have empty entity lists only after complete annotation review; incomplete labeling must not become negative training evidence.

Exports contain train/dev/test `.spacy` files, full records in `relationships.jsonl`, `tokenizer.bin`, and an immutable manifest with schema/annotation versions, record and split identities, quality, source hashes, tokenizer identity and file hashes. Empty splits are represented and counted; they do not establish benchmark readiness. Destination directories must be empty. `--allow-constructed` is solely for explicitly marked test exports and stamps the manifest; it does not turn test fixtures into research ground truth.

AnnotationRecord.annotation_profile is context-rich-v1 by default, preserving older records. The explicit location-only-v1 profile contains the six place labels and rejects DEPTH/TIME/facts/relations; save rich references separately. Export --profile must match every record, and its manifest records profile and vocabulary. Both profiles retain all admission/group/split/quality guards. The [developer-authorized AI pilot](../../../docs/evaluations/flood-ner-ai-pilot-20261014/README.md) has twelve research-only location records (ten same-teacher accepted, two unresolved) and twelve paired rich drafts, not 24 independent samples. Actual pilot export remains blocked by unqualified admission/group/split prerequisites. No human verification or model accuracy is claimed.

Earlier tokenizer `lanes.xx.address-v1` used spaCy's multilingual blank tokenizer with an additional final-period boundary for address codes such as `25-A.`. It changes token boundaries, never source characters. The tokenizer is saved and hashed. Switching to a future trained model's tokenizer requires revalidation and a new corpus export; this tokenizer is not a trained NER model.

All generated sources, corpus exports, checkpoints and model artifacts belong under ignored `artifacts/`; the production Docker build also excludes that directory. New sources and reports do not alter shared flood records. No runtime aliases, schema migrations or dependency upgrades are introduced.

`collect-news` consumes a JSON array of discovered public publisher URLs. It inventories existing sources, avoids known canonical article identities and records successful candidates and failed fetches explicitly in `candidates.json`. It does not approve a candidate based on keywords. Review bodies/publication evidence, language, duplicates and event/syndication relationships before marking entries accepted. The collection schema/report is `lanes-flood-news-collection-v1`; the source schema remains `lanes-flood-ner-v1`.

The capture parser prefers an explicit JSON-LD article body, decoding embedded HTML when present, and supports HTML publication meta fields. ABS-CBN static bodies use the publisher's body container; a site shell cannot qualify as a body. `import-browser-news` preserves a deliberately saved public rendered DOM snapshot with `url`, `title`, `body_text`, `headers` and timezone-qualified `captured_at`. A Published/PHT header supports an instant; a reviewed Philstar article-date header supports only a calendar day. Unknown/conflicting headers fail. It freezes the unchanged rendered body plus the hashed snapshot; import never fabricates missing bodies or publication headers. Existing snapshots cannot be overwritten with a different identity. `reextract-source` repairs a specifically supported malformed script closure in saved JSON-LD markup, writes an additional extraction version and preserves raw HTML and the original capture.

`verify-news` requires the explicit positive --expected-count (default 100) of accepted research-only articles, each backed by an inventoried source, reviewer/notes, publication evidence and hashed body offsets. It checks local text/raw files, canonical publisher identity, publication window/evidence and exact/near-copy or version duplicates before writing the news register, outcome manifest and coverage report. All paths are repository-relative and must stay within the repository. Missing files fail explicitly. Two old captured-original fixtures explicitly preserve unknown raw HTML/retrieval times; their printed date headers support publication days only. Another checkout needs matching frozen captures to verify this register.

`capture-wikipedia` uses the official revision API to freeze a revision at or before the collection cutoff, with main-slot wikitext, permanent/history links, timestamp, attribution and site license metadata. These reference records count zero toward news and remain excluded from primary training. Page-specific reuse and geographic identity checks remain separate.

The [completed-work review](../../../docs/evaluations/flood-ner-review-20261014/README.md) records stricter source-bound canonical identity, original timestamp/reuse checks, capture-bound publication evidence, actionable malformed-input errors and exact CRLF/LF preservation. Export compares normalized URL/article aliases for split leakage and rejects explicitly provisional/unresolved group names. Wikipedia revision files now include language; repeated captures preserve existing metadata and verify content, including legacy revision-only filenames. The existing 100-article register remains unchanged.

The [100-article acceptance report](../../../docs/evaluations/flood-news-corpus-100-20261014/README.md) links the metadata register, separate supporting inventory, exclusion/failure outcomes and measured gaps. Case-type counters are research cues, not reviewed training entities or fact relations. Article-level language and provisional grouping require passage-level review before the pilot.

Tests:

`review-passages` consumes original candidate JSONL plus an explicit JSON array of EditorialReview decisions. It binds source/candidate/version/hash identities to the inventory, rejects lost non-whitespace text and overlapping/corrupt ranges, and preserves separate contiguous blocks around reviewed exclusions. No cleaned-text concatenation occurs. Full sources/blocks remain under ignored artifacts; metadata carries selection/exclusion hashes/reasons, source-relative context notes and reviewer kind. AI-assisted decisions retain a research-team manual-review hold; Tagalog/unknown blocks are distinguished from the paper's English/Taglish scope. Group/reuse/annotation holds remain, and all admission/label/split counts stay zero. Prior queues cannot be overwritten. See the [editorial/paper report](../../../docs/evaluations/flood-ner-editorial-20261014/README.md); the paper's target is 400 total manually annotated samples with 280/60/60 splits, not 400 articles or 400 fitted-training examples.

`prepare-pilot` rechecks reviewed source identities and local file/evidence hashes, then creates one proposed context window per accepted article. Its candidate JSONL includes full source/passage text under ignored artifacts only; metadata registers exclude both text objects. Article-level language and provisional groups remain separate from unknown passage language and pending review. It creates no entity/fact labels, split assignments or training admission. Destinations must be empty and beneath the repository's training artifacts directory. See the [initial readiness report](../../../docs/evaluations/flood-ner-readiness-20261014/README.md) for publisher policy evidence, draft groups and measured holds. A candidate cannot be passed directly to AnnotationRecord export.

The [readiness review](../../../docs/evaluations/flood-ner-readiness-review-20261014/README.md) additionally binds candidate/article identities to the captured source/version/bounds, requires unresolved review/provenance holds and carries existing source-review notes into the draft. Interface text, captions, truncation, omitted numbered cues and known measurement-role ambiguity generate explicit review holds. These diagnostics do not establish passage correctness or admit training data. Existing draft queues are preserved; use a new output directory for a corrected proposal.

```powershell
.venv/Scripts/python.exe -m pytest --noconftest tests/test_flood_ner_editorial.py tests/test_flood_ner_preparation.py tests/test_flood_ner_collection.py tests/test_flood_ner_tooling.py tests/test_philippine_location_service.py tests/test_locality_number_service.py tests/test_news_locality_anchor.py tests/test_news_heading_context.py -q
```

`--noconftest` deliberately avoids the repository's application/database fixtures. The latest readiness review records 378 preparation, location, temporal, source and processing checks under explicit isolated source-mode settings. Earlier temporal failures were repaired in the preceding milestone; their history remains in that evaluation.

## 400-sample cohort assembly

The [400-sample report](../../../docs/evaluations/flood-ner-corpus-400-20261014/README.md) records 400 silver location records from 132 articles, 200 English/200 Taglish, exact 280/60/60 research partitions and three publishers below 200 samples. Training admission/export remains zero. Article language tags are preserved; AnnotationRecord.passage_language records reviewed sample language.

```powershell
.venv/Scripts/python.exe -m training.flood_ner verify-news training/flood_ner/artifacts/cohort400-20261014/reviewed-source-register-v2/collection_outcomes.json --expected-count 142 --output training/flood_ner/artifacts/cohort400-20261014/source-replay
.venv/Scripts/python.exe -m training.flood_ner build-cohort training/flood_ner/artifacts/cohort400-20261014/annotations-v1/location_annotations.jsonl --group-reviews training/flood_ner/artifacts/cohort400-20261014/group_reviews-v1.json --news-register training/flood_ner/artifacts/cohort400-20261014/reviewed-source-register-v2/news_register.json --pilot-records training/flood_ner/artifacts/cohort400-20261014/annotations-v1/retained_pilot_ids.json --output training/flood_ner/artifacts/cohort400-20261014/replay-new
```

Destinations must be empty. GroupReview binds source/version/body/publication evidence and records explicit reviewer/rationale. Cohort assembly preserves capture metadata, applies reviewed grouping only to derived annotations, excludes wrong-language/profile/unresolved/duplicate/overlapping records, and refuses infeasible exact quotas. Retained pilots are pinned to training. Existing SciPy/NumPy supplies constrained deterministic selection; no new dependencies. The default command targets 140/140 train and 30/30 dev/test, at least three publishers and at most 200 records per publisher. Reporting components can deliberately overgroup dependencies without declaring one physical event.

Current tokenizer lanes.xx.address-v2 separates source dateline/list delimiters and final periods, retaining internal 25-A codes and original characters. Corpus schema/tokenizer bytes and hashes are frozen. A model using another tokenizer requires revalidation; this tokenizer is not a trained model. Full annotations/context stay ignored, and all real exports still require qualified reuse/admission. Software counts, language judgments, teacher agreement and independently verified accuracy are distinct.

The [follow-up review](../../../docs/evaluations/flood-ner-corpus-400-20261014/followup_review.json) corrects auxiliary contextual serialization in context-v2/context_evidence.jsonl. The context.write_context_jsonl helper uses the existing compact JSONL writer and refuses an existing destination. All 400 original contextual objects are preserved with raw text and unreviewed cues; context-v1 remains intact. Final isolated verification passes 425 checks. Before running the broader source-mode regressions, explicitly set all auditor options rather than inheriting workstation configuration. No operational configuration was changed.

## Frozen-cohort qualification

Run this read-only diagnostic command with a new ignored output directory:

```powershell
.venv/Scripts/python.exe -m training.flood_ner qualify-cohort training/flood_ner/artifacts/cohort400-20261014/cohort-v2 --news-register ../docs/evaluations/flood-ner-corpus-400-20261014/source_register.json --model-register training/flood_ner/artifacts/qualification-20261014/model-evidence/model_register.json --reuse-register ../docs/evaluations/flood-ner-readiness-20261014/reuse_register.json --output training/flood_ner/artifacts/qualification-20261014/new-run
```

Model/reuse registers are optional; omitting them leaves those checks unperformed. The command verifies frozen artifacts and original selected source evidence, reports per-language/label support, publisher dependence and model metadata compatibility, and writes a candidate tokenizer without promoting it. It never resolves source use or admits/trains/loads a model. Default remains lanes.xx.address-v2; lanes.xx.address-v3 is explicit opt-in for research assembly/validation/export. JSONL representations escape alternate Unicode separators while decoding exact original text. See the [first qualification report](../../../docs/evaluations/flood-ner-qualification-20261014/README.md) for its historical 455-test checkpoint and the [stronger revision attempt](../../../docs/evaluations/flood-ner-revision-400-20261014/README.md) for its historical 508-test result and quota holds. The [completed continuation](../../../docs/evaluations/flood-ner-continuation-400-20261015/README.md) records 525 checks and a qualifying frozen revision.

## Bounded stronger revision

`--publication-start` and `--publication-end` configure inclusive dates on collection, verification, validation, assembly and qualification. Legacy defaults remain 2022-01-01/2026-10-14. Qualification reads a frozen manifest's window; an explicit override must match. Date-only assembly requires an accepted news-register entry whose saved publication evidence verifies. Validation with an explicit window similarly needs `--news-register` for sources without a qualified publication instant.

`build-cohort --coverage-policy` loads a strict `lanes-flood-ner-coverage-v1` JSON policy. Default policy values encode the authorized stronger publisher/article/group/label quotas. The old command without a policy retains its original publisher/selection behavior. `--report-infeasible` saves the reviewed pool, exclusions and necessary coverage failures and exits **2**, without freezing partitions. This is not a successful 400-sample selection. Invalid input still exits 1 and is not converted into an infeasibility pool. Exit 0 denotes successful assembly.

Supply `--candidate-ledger` and `--baseline-inventory` together to enforce 300 cumulative additional URLs and 200 additional admitted articles. The baseline is an immutable pre-revision array of source objects containing URLs. The ledger is a JSON URL array; collection updates it only within the cap, and assembly rechecks admitted articles against it. Tracking/version aliases do not inflate article counts. Admitted articles still require complete source reading and verified evidence.

Historical incomplete-pool replay from `backend/`:

```powershell
.venv/Scripts/python.exe -m training.flood_ner build-cohort training/flood_ner/artifacts/revision400-20261014/reviewed-v8/location_annotations.jsonl --group-reviews training/flood_ner/artifacts/revision400-20261014/reviewed-v8/group_reviews.json --news-register training/flood_ner/artifacts/revision400-20261014/reviewed-v8/news_register.json --pilot-records training/flood_ner/artifacts/cohort400-20261014/annotations-v1/retained_pilot_ids.json --coverage-policy training/flood_ner/artifacts/revision400-20261014/reviewed-v8/coverage_policy.json --publication-start 2017-01-01 --publication-end 2026-10-14 --tokenizer lanes.xx.address-v3 --candidate-ledger training/flood_ner/artifacts/revision400-20261014/candidate-ledger.json --baseline-inventory training/flood_ner/artifacts/revision400-20261014/baseline-inventory.json --report-infeasible --output training/flood_ner/artifacts/revision400-20261014/new-replay
```

The v3 rules additionally cover slash-delimited names, ordinal boundaries and punctuation/byline joins. Earlier saved v3 candidate bytes remain unchanged; reproduce a checkpoint using its actual tokenizer bytes/hash, not its name alone. The final v3 assembly tokenizer is saved before validation mutates the vocabulary. Source characters are never rewritten to fix alignment.

`review-context-pilot FROZEN_COHORT --annotations CONTEXT_JSONL --reviews CATEGORY_REVIEW_JSON --output NEW_IGNORED_FOLDER` checks exact pairing, training-only membership, 20 records per language, five articles per language, and four cases per category including both languages. It requires complete source-supported rich facts/relationships and rejects mismatched spans, evidence, overrides and fabricated clocks. Pairing adds zero independent location samples. The October 15 continuation freezes a qualifying 400-record revision and validates 40 contextual pairs; the earlier proposals remain preserved drafts.


## Completed continuation and replay

`build-cohort --selection-time-limit 300` uses an explicit optimizer bound while retaining the 60-second default. Allowed values are integer seconds 1–3600; nondefault limits are recorded in manifests. A resource-limited solve is unresolved, not evidence of infeasibility. Source inventory retains `(canonical URL, capture version)` identities, including versions with matching body hashes. Collection paths bind to the actual version. Verified Philstar pipe/hyphen publication headers and Inquirer bylines can establish date-only evidence; conflicting dates remain held.

Preserved continuation checkpoint: the corrected input was `artifacts/continuation400-20261015/reviewed-final-location_annotations.jsonl`; source/group registers are in `reviewed-v5/`, final frozen selection in `assembly-corrected-300s-v1/`, and historical superseded context in `contextual-reviewed-v1/`; that checkpoint used `artifacts/review-qualification400-20261015/contextual-reviewed-v2/`. A byte-identical replay is saved in `assembly-corrected-replay/`. The original legacy replay is byte-identical too.

The dedicated ignored `artifacts/stronger-400-continuation-20261015/` folder contains 342 article links/captures, 400 sample links, frozen location/context records and a verified hash manifest. It needs an external backup independently of Git. [Report](../../../docs/evaluations/flood-ner-continuation-400-20261015/README.md).


## Follow-up review and current qualification

Current location records are in `artifacts/annotation-correction-20261015-v1/cohort-v2/`; accepted paired contexts are in its sibling `contextual-v3/`. Earlier cohorts and contextual v1/v2 remain preserved. The existing context-review guards still apply; no runtime parser changes.

`qualification_report` binds candidate-tokenizer bytes before validation grows vocabulary, so reported SHA matches the candidate_tokenizer.bin written by qualify-cohort. The corrected saved diagnostics are in `artifacts/review-qualification400-20261015/qualification-v2/`. The dedicated `artifacts/stronger-400-reviewed-20261015/` bundle contains current contextual-pilot-v2, frozen location data, source/sample CSVs, qualification diagnostics and a verified hash manifest. A frozen silver-evaluation protocol is preparation only: no model is installed, evaluated or trained and source-use holds remain enforced. [Report](../../../docs/evaluations/flood-ner-review-qualification-20261015/README.md).


## Isolated constructed-only model preflight

Production requirements only comment-link `requirements-qualification.in`; do not install this optional recipe into backend/.venv. Bootstrap uv 0.13.1 in a new ignored research folder, install managed CPython 3.11 with explicit --install-dir plus --no-bin --no-registry, and create a separate environment with include-system-site-packages=false. Use only task-local caches. Resolve a binary-only, hash-locked recipe using an exact official CPU Torch wheel URL, then sync that lock with --require-hashes. Record interpreter build/binary hashes and package versions. Do not replace the main Python/spaCy environment.

The successful run uses Python 3.11.17, spaCy 3.7.5 and pinned calamanCy md 0.1.0 revision 51a40433059d8a2c25b98a48eca854f8789a491a. The complete artifact, current lock/environment manifests and failed/successful runs are in ignored `artifacts/preflight-use-20261015/`. `requirements-v2.lock` adds Click 8.5.0 to satisfy the observed spaCy import; earlier locks/failures remain preserved.

From backend/:

```powershell
.venv/Scripts/python.exe -m training.flood_ner preflight-model --python training/flood_ner/artifacts/preflight-use-20261015/research-env/Scripts/python.exe --model-manifest training/flood_ner/artifacts/preflight-use-20261015/model_manifest.json --cases training/flood_ner/configs/preflight_constructed_cases.jsonl --output training/flood_ner/artifacts/preflight-use-20261015/new-replay
```

The command is offline and refuses the main interpreter, nonconstructed provenance, malformed spans/hashes and existing destinations. Inputs are exactly 24 probes with 12 English/12 Taglish and all six expected place classes. Model predictions remain LOC/ORG/PER. Output uses a revalidated UTF-8 byte protocol, records one warm-up plus ten measured CPU passes and peak working set, and retains failures without fabricated resources. Exit0 means research loading/inference passed; exit2 denotes a documented execution/output failure; invalid input exits1. Alignment gaps are diagnostics, not an automatic tokenizer change. No news data is inferred, exported or trained. [Results](../../../docs/evaluations/flood-ner-preflight-use-20261015/README.md).

## Constructed model-tokenizer qualification

qualify-model-tokenizer compares the native pinned calamanCy tokenizer with a separate lanes.tl.calamancy-address-v1 candidate and the existing corpus v3 tokenizer. It requires exactly 48 hash-bound constructed cases (24 per language), preserving the original 24, with explicit reference spans and separate token-boundary controls. No news corpus is processed. Run from backend/; choose a new ignored output directory.

```powershell
.venv/Scripts/python.exe -X utf8 -m training.flood_ner qualify-model-tokenizer --python training/flood_ner/artifacts/preflight-use-20261015/research-env/Scripts/python.exe --model-manifest training/flood_ner/artifacts/preflight-use-20261015/model_manifest.json --cases training/flood_ner/configs/tokenizer_qualification_cases.jsonl --output training/flood_ner/artifacts/tokenizer-qualification-local-repeat-v1
```

Exit 0 means constructed qualification passed; 2 means execution or qualification failed with a saved report; invalid inputs exit 1. Native and candidate run in separate isolated CPU processes. Saved tokenizer bytes exclude vocabulary and are bound to verified model vocabulary hashes. Output includes tokenizers, manifests, constructed predictions, parent-recomputed controls/alignment, prediction differences, resource measurements and explicit failure evidence. The existing preflight-model command remains native with its original 24-case input contract.

The completed run has zero candidate alignment errors and 56 passing controls across 48 cases. Twelve prediction changes are reported without claiming accuracy. Corpus v3 is compared unchanged; its expanded constructed gaps do not rewrite the validated frozen dataset. Before training, admit source use and qualify the chosen model tokenizer against the actual corpus; train and infer with consistent tokenization. [Measured qualification](../../../docs/evaluations/flood-ner-tokenizer-qualification-20261015/README-v2.md).

## Private study/use-review bundle

prepare-use-bundle validates the frozen 400-record cohort, forty paired contexts, original source-use packet/forms, 139-source register, captured evidence and fifteen scoped assessments. It performs no network requests, grants no admission, and preserves source records. Use a new ignored destination.

```powershell
.venv/Scripts/python.exe -X utf8 -m training.flood_ner prepare-use-bundle --cohort training/flood_ner/artifacts/annotation-correction-20261015-v1/cohort-v2 --context training/flood_ner/artifacts/annotation-correction-20261015-v1/contextual-v3 --review-packet training/flood_ner/artifacts/annotation-correction-20261015-v1/review-packet-v3.json --output training/flood_ner/artifacts/400-sample-study-package-local-repeat-v1
```

The START-HERE.md file explains four numbered folders: private study, paper appendix draft, download candidate and use review. It includes source/sample CSV links, a balanced training-only appendix, passage-only JSONL and a local ZIP, evidence, editable unresolved forms and a hash manifest. Appendix selection greedily maximizes newly covered classes, then publishers, then record ID, with five examples per language. Its achieved coverage is reported rather than assumed.

The separate lanes-passage-share-candidate-v1 format contains raw passage text, Unicode offsets, labels, provenance and public source metadata. It excludes full-source fields/HTML, private paths and model weights. Whole-article passages become metadata-only entries with text=null; all original records remain intact privately. It is not an AnnotationRecord training export. Context pairs remain separate and do not increase the sample count. No dataset license is assigned.

Exit 0 means the private package was prepared with holds, not cleared for training or distribution. Invalid inputs/refused destinations exit 1 before copying. Copy/serialization failures save failure.json where possible, return nonzero and leave the partial folder for inspection; choose a new destination after fixing the issue. The new package is a local copy, not an external backup. [Assessment, measured limits and current folder](../../../docs/evaluations/flood-ner-study-use-20261015/README.md).


## Explicit annotation corrections

`revision.py` applies reviewed `EntityCorrection` objects to hash-bound original records. Corrections contain the complete original-record hash, passage hash, expected/replacement entities and actual review provenance. `write_cohort_revision` preserves membership, splits, immutable source metadata and saved tokenizer bytes, refreshes selection/coverage hashes and refuses existing destinations. It never invokes the selection solver. `revise_contexts` retains fact/target/override IDs and applies explicit road-segment qualifiers without assigning facts to new local-area entities.

The preserved correction checkpoint has 1,497 location spans across the same 400 samples and 139 articles. One of forty contexts changes in v3. Bundle preparation uses the explicit safe context/packet revision names, preserving v2 defaults for older manifests and copying hash-linked predecessor packets when supplied. [Correction evidence](../../../docs/evaluations/flood-ner-annotation-correction-20261015/README.md). Its preserved organized folder is `artifacts/400-sample-study-package-corrected-20261015-v1/START-HERE.md`; old folders remain unchanged.


## Academic-use review without admission

`academic_use.py` validates source-exact UTF-8 clause pointers, the corrected cohort/context/review-packet bindings, 139 distinct article reviews, three dated AI publisher conclusions and the unchanged twelve nonacademic-use outcomes. Publisher display aliases are normalized through the existing URL-based publisher identity without rewriting captures. It does not expose an admission setter or new CLI command. Completed assessments cannot change source flags or bypass export holds.

Preserved publisher-review checkpoint: `artifacts/academic-use-review-20261015-v1/START-HERE.md`, with `DECISION-SHEET.md`, three readable assessments, `academic_review-v2.json`, article exceptions, editable academic decisions and a hash manifest. Review-v2 corrects a private draft's caption-overlap description after checking source intervals; the dataset is unchanged. Raw snapshots and complete review evidence remain ignored. [Metadata report and decisions still needed](../../../docs/evaluations/flood-ner-academic-use-20261015/README.md).

## Optional reference-preserving research revisions

The existing Python `build_cohort` function accepts optional `reference_records`, `fixed_record_ids` and `max_reference_changes`. References must be validated frozen split-bound records. Hard-fixed records must remain eligible, substantively unchanged and in their original split. Removals, replacements, span/language changes and split moves consume the budget; reviewer/notes/group-overlay metadata alone do not. New boundaries require distinct IDs and supported provenance.

With references enabled, soft overlapping/near-copy alternatives remain eligible and explicit conflict constraints prevent selecting both. Hard-fixed records win eligibility conflicts. The solver prioritizes unchanged references, then its stable secondary objective. Time-limited incumbents are checked against actual integer/linear constraints and reported without claiming optimality. The 60-second default remains; bounded one-off workflows may retry once at 300 seconds after an unresolved timeout. Constrained manifests record reference hashes, fixed IDs, budget, actual changes and solver status. Without these options, legacy behavior and manifest fields stay unchanged. No CLI, production API or dependency is added.

The [bounded revision](../../../docs/evaluations/flood-ner-research-revision-20261016/README.md) is in `artifacts/research-revision-20261016-v1/START-HERE.md`: final **cohort-v4** (400/138 articles) and **contextual-v4** (40 pairs), with 54 new-boundary selections, 16 reviewed reserves and 330 preserved references. Two additional training references change; test samples/pilots remain fixed. Original checkpoints and intermediate drafts are preserved. The study-bundle command above still targets its original 139-source packet; do not substitute the new 138-source cohort into that bound interface.

Source-use assessments and a hash-bound derived index retain 12 held articles/49 passages. Source flags/export holds remain unchanged; no model processing or training occurred. The detailed desktop predecessor remains unreconciled.

## Admitted corpus tokenizer command

`python -m training.flood_ner qualify-corpus-tokenizer --python RESEARCH_PYTHON --model-manifest MODEL_MANIFEST --tokenizer-manifest TOKENIZER_MANIFEST --cohort ADMITTED_COHORT --context ADMITTED_CONTEXT --admission-manifest ADMISSION_PACKAGE_MANIFEST --output NEW_IGNORED_OUTPUT`

Use verified existing paths; placeholders are not directories to create blindly. The command validates the frozen private admission package, pinned model/vocabulary and candidate bytes before one isolated tokenizer-only worker. It preserves failures and returns nonzero unless qualification passes. It runs no NER components or model predictions and leaves legacy constructed-only commands unchanged. Never overwrite a frozen output. The evaluation protocol can be prepared while qualification is blocked; that does not qualify the tokenizer or permit the next export gate.

## Qualified location training-format export

Run the following from backend/, using the existing CLI interpreter:

    python -B -m training.flood_ner export-qualified-corpus --python RESEARCH_PYTHON --qualification PASSING_QUALIFICATION_DIRECTORY --output NEW_IGNORED_DIRECTORY

The command requires the passing qualify-corpus-tokenizer output directory, including its frozen evaluation contract and all bound inputs. It revalidates the admission ledger/evidence, 400 location records/40 contextual pairs, pinned model/vocabulary, candidate bytes and saved comparison. It refuses research-only inputs, changed or incomplete qualification, mismatched partitions/profiles and existing or unignored output destinations. It adds no constructed-data override and never falls back to a legacy corpus tokenizer.

An isolated existing Python 3.11/spaCy 3.7.5 worker uses vocabulary/tokenizer only. It writes train.spacy/dev.spacy/test.spacy with 280/60/60 location documents, preserving original text, strict six-class labels, negatives and record_id user data. The 40 contextual pairs are bound references, not extra NER samples. All documents reload with exact tokens/offsets/labels before a successful manifest is written; failures retain logs without a success manifest.

tokenizer.bin preserves the qualified candidate bytes with vocab excluded. Its manifest binds the required pinned vocabulary; do not reconstruct defaults or treat the tokenizer as independent of that vocabulary. provenance.json contains IDs, groups, hashes, language/split and silver teacher/reviewer metadata without full article bodies. Request text, DocBins and worker diagnostics stay private under ignored artifacts.

The verified desktop export/replay and metadata-only report are recorded in [qualified export verification](../../../docs/evaluations/flood-ner-qualified-export-20261016/README.md). The legacy export command and its two corpus-tokenizer choices are unchanged. This command performs no training or NER prediction evaluation.

Focused tests need no extra packages or private corpus: from backend/, run the existing CLI Python with python -B -m unittest discover -s tests -p test_flood_ner_qualified_export.py -v. No application database/conftest is loaded by this unittest invocation.

## Baseline/configuration preparation

From backend/, use the existing CLI interpreter:

    venv/Scripts/python.exe -B -m training.flood_ner prepare-experiment --python RESEARCH_PYTHON --export VERIFIED_QUALIFIED_EXPORT_DIRECTORY --output NEW_IGNORED_DIRECTORY

This separate offline command revalidates the passing export, qualification, admission/contract, model files and exact tokenizer before using the same isolated Python 3.11 research interpreter. It freezes direct rules type/Unicode-offset mappings and source/assets hashes. It initializes seed 0/1/2 fresh six-class NER heads, copies the pinned NER encoder and preserves static vocabulary. It performs no optimizer updates, corpus inference, test reading, export or saved-model creation. The existing rules mention adapter receives four constructed-only passages with database connections blocked.

The pinned architecture uses a GPU encoder/lower network and CPU upper classifier by design. The passing desktop run verifies 46 GPU arrays and two CPU upper arrays per seed. The failed v1 all-GPU assertion is preserved; v2 passes without dependency or model changes.

The frozen recipe is batch size 8, dropout 0.1, Adam learning rate 0.001, max_epochs 30, max_steps 1000, eval_frequency 35 and patience 175. It is one initial recipe, not an optimized result. Seeds 1/2 are robustness runs; seed 0 is primary. Configs exclude test.spacy. The actual held-out corpus remains hash-bound for preservation, not supplied to the initializer.

The generated configs require experiment_registry.py to be loaded with the spaCy --code option by the later trainer, using the same qualified Windows DLL/runtime setup. No training command runs as part of this preparation. The custom development selector saves strict improvements to future seed-directory/selected-checkpoint/model and retains earlier steps on equal F1. Use that path for evaluation: the default spaCy 3.7.5 model-best overwrites equal scores. Planned training output must be new; do not overwrite or resume it implicitly.

The rules baseline maps street/landmark/barangay/city/province directly to ROAD/LANDMARK/BARANGAY/CITY/PROVINCE. LOCAL_AREA is unavailable; legacy numbered-locality landmark emissions stay LANDMARK. Use original character offsets, retain diagnostics for invalid/unsupported emissions, deduplicate identical spans only and retain conflicting/overlapping outputs for transparent scoring. Do not use references to repair offsets or infer types. This is mention recognition, not the full flood-claim pipeline. The unmodified pretrained baseline remains a separate coarse native LOC task.

From backend/, run the new standard-library tests without package installation:

    venv/Scripts/python.exe -B -m unittest discover -s tests -p test_flood_ner_experiment_preparation.py -v

[Actual preparation results and next training task](../../../docs/evaluations/flood-ner-experiment-preparation-20261016/README.md).

## First manual training run

The researcher runs seed 0, then Codex reviews its output and handles later runs. From the repository root, run .\backend\training\flood_ner\RUN-SEED-0.ps1 -StartTraining in PowerShell. Without -StartTraining the script only verifies inputs. It leaves all frozen configs unchanged and streams the qualified GPU training output into a new private seed-0/training.log, recording completed/failed/interrupted status. Existing output is refused, not resumed. Seeds 1/2 never launch automatically.

[Exact commands and output guide](../../../docs/guides/ner-first-manual-training-20261016.md). Only check-only execution and launcher tests have run; actual training has not started.

## Validation-only model comparison and preregistered recipes

From backend/, run the repaired CLI interpreter with:

    venv/Scripts/python.exe -B -X utf8 -m training.flood_ner compare-validation --python RESEARCH_PYTHON --preparation PASSING_PREPARATION --training-root PRIVATE_RUN_ROOT --output NEW_IGNORED_OUTPUT

Default expected seeds are 0/1/2. --seeds selects an explicit subset; --allow-incomplete retains failed/missing runs as an explicitly partial report. It never silently claims a completed three-seed experiment. The command revalidates frozen bindings and selected model identities, uses raw development passage strings only, reproduces recorded selected F1, and scores the unchanged rules/native baselines. Native LOC remains a separate coarse task. No test prediction or training occurs.

The study_recipes helper preregisters only approved A/B changes and output-only recovery relocation. All configurations are bound before training; validation rejects any other changed setting even if someone rehashes the configuration. Default helper mode checks inputs only. An explicit --start-training opt-in and an unexpired 50-minute cutoff are required for execution. There is no authorization to bypass the experiment failure rule: preserve the failed attempt and obtain the explicit retry decision first.

Source and prediction text remains private; public reports contain metadata. Forty-three standard-library tests cover launcher, comparison, recipe and existing preparation/export behavior. Existing requirements, public APIs, schemas and legacy export behavior remain unchanged.


### Completed bounded study and safe inspection

The immutable validation-study-20261016-v2 manifest preregisters seven variant configurations; actual run-status.json records identify the five completed new runs. Its training_started:false describes preregistration time. Study recipes change only patience/rate and output identity; each initializes independently from the pinned encoder. The winner uses unrounded seed 0 strict F1 (original, then A, then B on ties). B seeds 1/2 remain unrun configurations.

The study_recipes module defaults to read-only input/output validation; --start-training is an explicit training opt-in and refuses existing outputs or the expired start deadline. Do not repeat these completed runs. Selected checkpoints use selected-checkpoint/model with the earlier-step tie rule. Private comparison requests/logs/predictions and weights remain in ignored artifacts; the completed report contains metadata only. The subsequently completed held-out evaluation is documented below.


### Frozen held-out test evaluation

Two separate offline commands preserve the validation-only command and its defaults:

- freeze-test-experiment --preparation DIR --study-report DIR --output NEW_IGNORED_DIR checks the completed development study and freezes original/A seeds 0/1/2, resolving original seed 2 to its recovery output. It binds selected-checkpoint/model files, development selections, configurations, model/tokenizer/input/contract/rules identities, evaluator code and exact test memberships. It performs no test predictions.
- evaluate-test --freeze DIR --python QUALIFIED_RESEARCH_PYTHON --output NEW_IGNORED_DIR checks the sealed freeze, then evaluates exactly 60 test passages once using the existing isolated GPU environment. Its exclusive attempt.json marker is created before rules/neural inference and survives failure. Changed inputs, existing output and another attempt on the same freeze are refused. Failed results/logs remain private; do not retry automatically.

Completed checkpoints are final-test-freeze-20261016-v1 and heldout-test-evaluation-20261016-v1; logs/audits are in heldout-test-execution-20261016-v1. Preserve them; do not recreate/re-evaluate this experiment to choose models from test scores. Tests and implementation changes must precede a freeze because evaluator hashes are bound. Original seed 0 stays primary, Recipe A exploratory, and Recipe B is excluded. The native LOC task remains separate from strict six-class scoring; rules cannot emit LOCAL_AREA. Inference receives raw strings only. Public reports contain metadata; predictions and offset errors stay ignored. Any future tuning needs a fresh untouched holdout, not another selection round against these exposed cases.
