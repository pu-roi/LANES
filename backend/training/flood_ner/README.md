# Offline flood NER preparation

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

The final corrected input is `artifacts/continuation400-20261015/reviewed-final-location_annotations.jsonl`; source/group registers are in `reviewed-v5/`, final frozen selection in `assembly-corrected-300s-v1/`, and historical superseded context in `contextual-reviewed-v1/`; current accepted context is `artifacts/review-qualification400-20261015/contextual-reviewed-v2/`. A byte-identical replay is saved in `assembly-corrected-replay/`. The original legacy replay is byte-identical too.

The dedicated ignored `artifacts/stronger-400-continuation-20261015/` folder contains 342 article links/captures, 400 sample links, frozen location/context records and a verified hash manifest. It needs an external backup independently of Git. [Report](../../../docs/evaluations/flood-ner-continuation-400-20261015/README.md).


## Follow-up review and current qualification

The unchanged 400-record location cohort remains `artifacts/continuation400-20261015/assembly-corrected-300s-v1/`. Current accepted rich pairs are `artifacts/review-qualification400-20261015/contextual-reviewed-v2/`; earlier contextual v1 is superseded and preserved. The new `annotation/context_review.py` provides source-exact access-phrase review and explicit self-contradiction guards, with independent place association still required. No runtime parser is changed.

`qualification_report` binds candidate-tokenizer bytes before validation grows vocabulary, so reported SHA matches the candidate_tokenizer.bin written by qualify-cohort. The corrected saved diagnostics are in `artifacts/review-qualification400-20261015/qualification-v2/`. The dedicated `artifacts/stronger-400-reviewed-20261015/` bundle contains current contextual-pilot-v2, frozen location data, source/sample CSVs, qualification diagnostics and a verified hash manifest. A frozen silver-evaluation protocol is preparation only: no model is installed, evaluated or trained and source-use holds remain enforced. [Report](../../../docs/evaluations/flood-ner-review-qualification-20261015/README.md).


## Isolated constructed-only model preflight

Production requirements only comment-link `requirements-qualification.in`; do not install this optional recipe into backend/.venv. Bootstrap uv 0.13.1 in a new ignored research folder, install managed CPython 3.11 with explicit --install-dir plus --no-bin --no-registry, and create a separate environment with include-system-site-packages=false. Use only task-local caches. Resolve a binary-only, hash-locked recipe using an exact official CPU Torch wheel URL, then sync that lock with --require-hashes. Record interpreter build/binary hashes and package versions. Do not replace the main Python/spaCy environment.

The successful run uses Python 3.11.17, spaCy 3.7.5 and pinned calamanCy md 0.1.0 revision 51a40433059d8a2c25b98a48eca854f8789a491a. The complete artifact, current lock/environment manifests and failed/successful runs are in ignored `artifacts/preflight-use-20261015/`. `requirements-v2.lock` adds Click 8.5.0 to satisfy the observed spaCy import; earlier locks/failures remain preserved.

From backend/:

```powershell
.venv/Scripts/python.exe -m training.flood_ner preflight-model --python training/flood_ner/artifacts/preflight-use-20261015/research-env/Scripts/python.exe --model-manifest training/flood_ner/artifacts/preflight-use-20261015/model_manifest.json --cases training/flood_ner/configs/preflight_constructed_cases.jsonl --output training/flood_ner/artifacts/preflight-use-20261015/new-replay
```

The command is offline and refuses the main interpreter, nonconstructed provenance, malformed spans/hashes and existing destinations. Inputs are exactly 24 probes with 12 English/12 Taglish and all six expected place classes. Model predictions remain LOC/ORG/PER. Output uses a revalidated UTF-8 byte protocol, records one warm-up plus ten measured CPU passes and peak working set, and retains failures without fabricated resources. Exit0 means research loading/inference passed; exit2 denotes a documented execution/output failure; invalid input exits1. Alignment gaps are diagnostics, not an automatic tokenizer change. No news data is inferred, exported or trained. [Results](../../../docs/evaluations/flood-ner-preflight-use-20261015/README.md).
