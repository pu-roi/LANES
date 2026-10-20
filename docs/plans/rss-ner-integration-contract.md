# Phase A: RSS-to-NER integration contract

> **Last Updated:** October 21, 2026, 12:36 AM Asia/Manila by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Current implementation checkpoint: C3b controlled local acceptance passed.** [754 distinct checks, retained replay and one real-model attempt](../evaluations/rss-ner-rss-integration-20261021/README.md) cover RSS admission/corrections/provenance, native capture/runtime/storage, intended-method readers, source evaluation, placement/publication compatibility and version-level correction review. Eight mocked-RSS inputs and two pre-existing short controls complete with exact neural/projection parity. Production scheduling remains legacy; frontend acceptance is Phase E and actual cloud rollout is separately gated.

**Phase A remains a completed specification milestone.** Its call-chain table below describes the inspected pre-integration baseline and required seams, not a claim that those gaps still exist. C1 method/history, C2 projection/source checking, C3a runtime/queue and the separately approved schema are completed prerequisite checkpoints; see the [current roadmap](../task_plan.md#phase-c--connect-automatic-article-processing) and [schema verification](../evaluations/rss-ner-mode-schema-20261020/README.md). Full local backend matrix coverage is reconciled in the C3b report; A21 frontend/browser acceptance and A23 production migration/release remain separate.

Owner: [@roicambe](https://github.com/roicambe) (Roi Cambe). Preserve v19 control seed 0, qualified v40/v44 combined location repairs and v42 grouping. Learned DEPTH/TIME recognition remains unfinished; extraction and matching of those fields use rules. V46's [bounded preview qualification](../evaluations/flood-ner-backend-location-v46-20261020/README.md) remains valid within its recorded workload, not a production or unseen-accuracy result.

## 1. Phase A baseline call chain and required seams

Paths below are repository-relative. They identify inspected implementation, not implemented successors.

| Stage | Current caller and behavior | Required integration behavior |
|---|---|---|
| Scheduling | `news_weather_controller_service.run_weather_tick` dispatches the existing job; `news_scheduler_service.run_scheduled_news_tick` rechecks policy/configuration and owns the worker lock | Retain the 15-minute controller heartbeat and adaptive **60/15/30** collection policy; do not run inference in the controller or API status reads |
| Sources / metadata | `configuration_service.selected_news_sources`, `news_sources`, `news_feed_service.probe_feed`, `news_discovery_service._discover_news` | Preserve reviewed publisher identity, selected sources, HTTPS hosts/redirects, feed checkpoints, age, budgets and duplicate controls |
| Body retrieval | `fetch_article_text` checks domain, response, publisher containers, size and continuation pages | Capture complete readable bodies only; RSS metadata is not body evidence; blocked/incomplete responses do not become successful extractions |
| Body admission | `body_has_metro_manila_flood_claim` calls `extract_taglish_flood_facts`; cache reuse and `previously_verified_article` also depend on this logic or readable history | Split candidate capture from flood eligibility so a rules recognizer miss cannot prevent NER from inspecting a potentially relevant body |
| Capture / queue | `crud.news.save_candidate` preserves old input before replacing a body and calls `crud.news_processing.enqueue_article`; immutable versions precede leased processing | Keep those transaction and identity guarantees; make enqueue/claim/capture method-aware after approved schema work |
| Extraction | `process_saved_news` calls `extract_captured_news_article` → `_extract_article_inputs` → `HybridExtractionService.extract_hybrid(mode="rules_only")` | Select an explicit NER-backed processing method and authenticated runtime; run unchanged body → original mentions → v40/v44 → v42 → validated durable envelope |
| Placement | `_extract_article_inputs` calls road-placement and placement-preview services on extracted claims | Keep geography downstream of supported extraction/projection; placement must not manufacture parent city, affected width or present flooding |
| Evaluation | `run_news_pipeline` commits extraction, then seeds/evaluates `NewsClaimSource` records by run/claim ordinal and immutable identities | Seed only explicitly eligible compatibility claims; carry their graph bindings and method; preserve historical source/decision identity |
| Source checks | `news_source_validation_service.validate_source_batch` reparses the old extractor, requires exact occurrence/fact equality and uses a stripped body | Keep legacy behavior for legacy runs; dispatch a separately versioned NER source-consistency check for NER runs, with original-body offsets |
| Publication | `news_publication_service` and `news_footprint_worker_service` apply existing lifecycle/geometry/expiry gates | Preserve those gates and staff/citizen boundaries. Model success alone never publishes or activates a zone |
| Admin readers | `news_browsing_service`, `news_results_service`, SQL readers and `/admin/news` currently read typed legacy results / JSON `claims` | Read legacy and native results explicitly; preserve SQL filtering/counts/pagination; no inference, source fetch or mutation on GET |

All unqualified service filenames in the table are under `backend/app/services/`; CRUD is under `backend/app/crud/`. API routes are in `backend/app/api/v1/endpoints/admin_news.py`; current schemas are `news_extraction.py`, `news_candidate.py`, `news_browsing.py`, `news_results.py` and `news_ner_preview.py`. Check these consumers together; updating only `_extract_article_inputs` is insufficient.

**Four confirmed compatibility gaps:** pre-NER body admission relies on the old recognizer; persisted mode is constrained to `rules_only`; legacy claims are scalar/single-location and have only observation/report/unspecified roles; the source checker expects old-rule output and trimmed-body offsets. V42 additionally emits no resolved absolute instants or numeric depth scalars: its validated `absolute_instants` and `numeric_depths` arrays are empty. Any compatibility normalization must therefore be separately identified and tested, never attributed to the neural model or written into the frozen graph.

## 2. Candidate admission, capture and corrections

### Metadata and network limits

Keep the current enabled/verified/selected publisher gates, canonical URL and redirect checks, maximum seven-day publication age, future-publication rejection, and existing duplicate identity. Retain body limits (1,000,000 response bytes; 120 minimum readable characters; 100,000 maximum processing characters), publisher-container checks and continuation rejection. Do not truncate to obtain an acceptable article.

Keep current retrieval priorities and budgets: metadata-local flood leads first; at most five unknown-location body probes across the run; existing commuter limits of 14 per run/four per feed; at most 20 due article refreshes under the existing 30-minute refresh policy. Conditional RSS 304 responses continue to allow bounded due-body refresh through saved provenance. Do not broaden into arbitrary web crawling or fetch every feed entry.

For new leads, existing flood wording in title/excerpt remains the retrieval shortlist. Missing city names may consume the existing unknown-location probe budget. Metadata naming only explicit non-Metro places stays excluded unless a Metro clue is also present or the article is a known correction; ambiguous names must not count as confirmed non-Metro identity. Commuter metadata retains its separate acquisition path. **Known limitation:** a new article with neither flood nor supported commuter wording in metadata may still be missed. This phase does not promise exhaustive discovery or expand the keyword vocabulary/budget without a separately recorded case and acceptance check.

### Capture is not flood admission

For a successfully fetched shortlisted flood lead, save a candidate and enqueue NER even if the old rules find no usable place. Reuse existing `review_state="pending"` as queue eligibility, **not verified flood status**. Determine flood/result eligibility only after the full body has been processed. No new review-state value or automatic user-facing flood claim is introduced by this contract.

Known explicit non-local metadata remains a retrieval gate; body geography is independently assessed after capture. A readable article may consequently be saved yet excluded from flood cards. Raw graph/history remain inspectable. Metro-only, prevention, forecast, negated, historical, caption-only and unknown-locality outcomes must not be conflated with retrieval or inference failures.

For commuter-only acquisition, keep the existing local-update path. If the readable body also contains affirmative flood evidence, queue it for NER without requiring the legacy location recognizer to succeed. Do not label a new flood-shortlisted body as commuter-only merely because legacy place extraction failed. After extraction, a pure commuter update remains outside flood results and publication.

Cached-body reuse applies the same capture policy and method-aware enqueue checks as a fresh body, without unnecessary re-fetch or a new version for a seen-time update. The old `body_has_metro_manila_flood_claim` must not remain a hidden neural-admission requirement in cache reuse or known-correction detection. Recognize previous NER flood evidence from the latest/prior authenticated native result and recorded lifecycle/source links, alongside existing legacy readable history; caption/forecast-only native output does not establish prior credible flooding.

### Corrections and failure semantics

Preserve canonical URL/feed GUID provenance and immutable prior snapshots before updating body or metadata. A newer complete correction to a known article is captured and processed even if its new headline/body denies flooding, describes clearance, or no longer contains flood keywords. Older revisions cannot replace newer saved evidence. Preserve original clocks; seen/fetch timestamps are not observations.

A failed refresh keeps the last successful body and its original title/publication identity, records the retrieval error, and does not invent a newer observation or erase history. New unreadable leads remain failed discovery attempts/notices; they do not become full-body NER results. Existing counters remain stage-specific until Phase D improves presentation; a body probe/capture is not a verified flood candidate.

Newer native results supersede older main-list output under the existing newest-run rule, including failures and zero-compatible-claim results. They never silently revive an older completed extraction. Forward known-article correction outcomes to the existing lifecycle/correction service even when no compatibility claim was emitted; this requires an article-version reconciliation entry point rather than relying solely on nonempty `claims` seeding. Exact matched denial/clearance evidence can be evaluated under current correction policy. No claims, missing targets, irrelevant new text or extraction failure alone cannot establish clearance; retain the existing uncertainty/expiry handling and record a review reason instead of indefinitely refreshing old evidence. Never rewrite an old source, evaluation or decision.

## 3. Durable envelope and immutable identities

Use **processing mode `ner_rules_v1`** and a result discriminator **`lanes-news-ner-result-v1`**. Keep `NewsExtractionRun.result` as JSONB and retain legacy top-level result fields for existing `claims` SQL projections. No result table, spatial column or new foreign key is proposed. Persist:

| Component | Required contents |
|---|---|
| Legacy-compatible header | Existing article ID/URL, `is_metadata_only=false`, processed original-body character length, extracted time, extractor version, `claims`, `errors` |
| `schema_version`, `processing_method` | Exact new discriminator and `ner_rules_v1`; reject mismatch with the run's mode |
| `source` | Article-version ID, existing immutable input fingerprint, canonical URL, body-field name and body SHA-256; publication metadata and whether its timezone is known |
| `provenance` | Authenticated model/bundle, tokenizer/resources, code/runtime manifest identities; `v19-control-seed-0`, location `lanes-location-repair-v40+v44` / `combined`, context v42; projection/source-check version bindings |
| `native` | Complete original neural mentions, effective mentions, ordered proposals, stage-labeled abstentions, validated graph and grouped view; preserve V46 content and identifiers |
| `projection` | Version `ner-claim-projection-v1`; per-observation/group disposition, exact graph target/relation/fact bindings, stable group identity, emitted claim ordinals, omitted field/fact reasons and backend-resolved locality/time/depth evidence |
| `measurements`, `limitations` | Runtime measurements with their meanings and retained extraction limitations; never report runtime measurements/F1 as per-entity confidence |

Do not duplicate article text in the envelope: the immutable snapshot supplies exact text and its hash. The existing preview response and `lanes-ner-preview-v1` remain unchanged and default-disabled. Durable results reuse its extraction content, not its preview-only status claims. Carry research/language/type/recognition limitations forward; do not label a durable result “no database history” after it has been persisted.

Treat native `graph` as canonical, its grouped view and legacy `claims` as validated derived projections in one immutable artifact. Recompute the pure v40/v44 proposal chain and v42 graph from authenticated original mentions before accepting worker output. Preserve original predictions even when proposals resize/retag/add effective mentions. Recompute/compare the grouped view and projection bindings; partial or invented output fails the run rather than dropping invalid facts.

All native offsets are zero-based half-open **Unicode character** offsets into the exact `NewsArticleVersion.input_snapshot.article_text`. Do not strip, normalize Unicode, concatenate metadata, or relocate a repeated name by first-match search. Evidence must satisfy `body[start:end] == text`. For NER checking, use that coordinate space through every helper; legacy checker behavior stays versioned separately. Store any legacy-view offset translation explicitly rather than mutating native coordinates.

The snapshot fingerprint continues to exclude fetch/seen time. Resolve unknown publication timezones as unknown; do not assign UTC merely to satisfy native input validation. Use a record ID derived from the immutable input fingerprint, not a mutable title. Define pipeline identity as `ner-v1:` plus SHA-256 of canonical JSON binding the model/tokenizer/runtime, v40/v44/v42 code, projection, source-check and geography asset versions. The full manifest is available in provenance; the 71-character identity fits the existing 100-character column.

**Publication provenance at capture:** existing helpers can attach UTC to naive metadata, so an aware database timestamp alone does not prove the publisher supplied a timezone. For new-mode capture, preserve the original feed publication wording and explicit timezone-known flag in feed-entry JSON metadata and in a versioned input-snapshot `publication_evidence` object (`raw`, `timezone_known`, `basis`). Use `basis="publisher_feed"` for captured feed evidence and `basis="legacy_unknown"`, `raw=null`, `timezone_known=false` when earlier provenance is unavailable. Native snapshots add `capture_schema="lanes-news-ner-input-v1"`; their fingerprint covers these fields as well as the existing source fields, with fetch/seen timestamps still excluded. This intentionally creates a different version where evidence differs, without changing legacy fingerprints/snapshots. The aware legacy `published_at` field may remain for compatibility, but must not override a false/unknown evidence flag. Method-aware snapshot serializers and the NER source checker must hash and round-trip the entire native snapshot, not silently drop these extra fields through the old input model. Historical timezone evidence is not reconstructed by assumption or backfilled.

Run uniqueness remains `(article_version_id, pipeline_version, mode)`. Enqueue, capture, lease claim and policy seeding must all select the intended method and identity explicitly. Existing pending legacy work is not relabeled or consumed by a neural worker; no automatic historical bulk reprocessing or backfill is introduced. A lost/expired lease cannot commit a result. Preserve existing five-attempt cap and backoff for retryable runtime failures; Phase B must fit actual deadlines into the lease or specify a tested renewal protocol before wiring.

## 4. Projection, normalization and publication eligibility

### Observation grouping and complete accounting

Build projection units from exact ordered target occurrences and their supported local/shared/collective relations within the same observation evidence. Join relation groups only when they share targets and overlapping evidence or an explicit v42 heading relation; never join by normalized place spelling alone. Distinct source paragraphs/clocks/updates remain distinct observations. A group ID is `g-` plus SHA-256 of canonical JSON containing targets, sorted relation/fact IDs, scope and observation-evidence spans; claim ordering follows first evidence offset, ordered target IDs and group ID.

Every graph fact must be accounted for as projected, retained native-only, context-only or unassigned with a reason. A fact can legitimately support several groups; retain those bindings rather than asserting a one-to-one count. Mention-only locations remain in article inspection without becoming flood cards. Preserve graph `unassigned` reasons and stage abstentions separately from compatibility omissions.

**Legacy operational projection v1 emits only representable single-target observations.** Joint/collective target sets remain native groups, visible as one supported group rather than duplicated independent road measurements. Do not select the sole recognized road from an incomplete junction. Their operational disposition is `joint_or_collective_requires_native_consumer`; this bounded v1 limitation must appear in acceptance/release findings. Supporting their operational placement is a later consumer-contract extension, not permission to flatten them in Phase C.

For single-target groups, map ROAD→street, BARANGAY→barangay, CITY→city, PROVINCE→province and LANDMARK→landmark. LOCAL_AREA remains native with `local_area_requires_native_consumer`; do not coerce it to a city/barangay. A compatible location without a required fact can still project known fields, retaining explicit unknowns and omitted-field reasons. Unknown status or unsupported locality never defaults to an active, Metro observation.

### Field rules

| Field | Projection decision |
|---|---|
| Place / parent | Raw place uses the exact effective mention span. Canonical identity requires a unique existing gazetteer match plus source-supported parent context: same clause or a single governing city/barangay list heading, ending at the next peer heading/narrative update. Never assume Pasig or use an opening dateline as affected parent. Ambiguous parent stays null with a reason |
| Evidence | Use one contiguous unchanged-body slice spanning the target and the local evidence. Keep separate heading/context evidence in projection bindings. If that cannot be represented within existing source-check quote limits, keep the group native-only with `evidence_exceeds_legacy_contract`; do not truncate it into apparent full support |
| Status | Explicit v42 active/rising/receding/subsided map directly. Conflicting updates stay separate/uncertain. Cleared, negated, forecast, historical, habitual, prevention and unknown remain native-only with distinct reasons; cleared is not remapped to active or automatically to subsided |
| Depth | Keep every native measurement/qualifier. For legacy scalar selection, one explicit quantitative measurement takes precedence over a paired verbal gauge; otherwise use one unambiguous verbal gauge. Use the existing depth parser only on the exact bound depth expression, not an entire article. Multiple distinct quantitative measurements, ranges, maximum/relative/collective values retain raw evidence with scalar/canonical null unless the current parser represents their scope without loss. Conflicts prevent scalar selection. Missing depth stays null |
| Access | Map only explicit bound access semantics to existing supported passability values. Preserve caution and vehicle restrictions. Conflicting/unsupported vehicle classes remain unknown with a reason; never imply passable from absent access evidence |
| Time | Preserve all seven native roles. Project observation/report/unspecified to their corresponding legacy kind only. Onset/publication/recession/clearance stay in native evidence and never substitute for observation. Multiple clocks with different roles are retained; conflicting observation clocks leave the scalar time null |
| Absolute time | Native v42 arrays remain unchanged/empty. The projection resolver accepts an explicit calendar date (ISO or English month-name date), valid AM/PM clock and explicit PHT/UTC+08 context governing that observation. Explicit “today”/“yesterday” may supply the date from timezone-aware publication metadata, with that relative-date basis retained; the observation clock must still come from body evidence. No bare-clock previous-day inference, machine timezone, fetch-time anchor, ambiguous weekday/date or unknown-timezone completion. Unsupported forms remain null with `observation_time_not_resolved` |
| Confidence / action | Do not inherit the legacy default confidence of 1.0 or fabricate a zero probability. The NER projected-claim type permits `confidence_score=null` and readers display unavailable; legacy scores stay unchanged. Adapt all numeric consumers to this explicit unknown rather than silently filling it. Never auto-approve from a score. Initial action/audit/geometry fields remain unset until their existing downstream stages run |

The projection normalizer is separately versioned and must be qualified through Phase C tests; it is not a modification to v19/v40/v44/v42. Existing date/quantity helpers can be reused only where their behavior matches this contract. In particular, the current bare-clock `resolve_observation_time` infers a calendar day from publication; do not call it unrestricted for NER projection. Do not infer a timezone from location alone.

Only affirmative body-grounded Metro Manila observations enter compatibility `claims`; graph outcomes explaining forecasts, captions, denial, cleared water, history and non-local reports remain inspectable and drive matched correction review where appropriate. Pass explicit `flood_mentioned`, flags and uncertainty rather than accepting schema defaults. A compatible observation can appear in the admin list without a resolved absolute time; existing operational evaluation still rejects it with missing supported observation time. Subsided observations retain their status/time/history and do not create current wet zones. Recession is not clearance.

`errors` means extraction failure, not “some facts cannot be projected.” A valid graph with zero compatible claims is completed with explicit disposition `native_only` or `no_eligible_observations`, counts/reasons and visible native details. A failed inference/invalid envelope has failed/retry-wait status and no successful-empty placeholder. The article-reader and collection classifier must use the native disposition rather than assuming `claims=[]` means nothing was extracted.

## 5. NER source checking and downstream consumers

Introduce dispatch by **persisted run mode**, not request flags, caller preference or the presence of a convenient JSON key. Legacy `rules_only` uses its existing checker and immutable historical identities. NER uses policy identity **`source-ner-v1`**, with a new policy fingerprint so old audits cannot be reused for different extraction semantics. The selected provider remains credit-free source consistency, not independent AI or field verification.

The NER checker receives the owned immutable input/result, claim ordinal and projection binding. Authenticate all stored hashes/identities; recompute the pure proposals, v42 graph and projection from saved original neural mentions without another neural inference. Validate exact source slices, complete target sets, qualifiers, observation partitions, parent-heading scope, status/access/depth/time evidence and cross-article conflicts. Graph recomputation establishes consistency with the authenticated extraction path, not proof that a predicted name is geographically correct. Gazetteer ambiguity, missing evidence and unsupported facts fail closed into explicit review/omission reasons.

Remove the requirement for an old-rule location/fact counterpart only on this NER path. Do not replace it with “NER said so” or mere substring presence. Require the bound affirmative flood/status evidence, exact occurrence, checked administrative parent, complete source-supported facts, original clock/date/timezone bases, and the existing freshness/conflict/expiry checks. The old offset validator's stripped-body interpretation cannot be reused for NER. Extract/reuse neutral validation helpers with an explicit coordinate contract; keep old source/audit identities reproducible.

Compatibility claims are frozen and hashed after deterministic extraction/projection and placement enrichment, before evaluation. Audit results never rewrite the extraction graph. Seed evaluations only after extraction commits, using the intended pipeline/method and stable claim ordinal; keep projection bindings when serializing through Pydantic, JSON, case-source creation and audit requests. Keep all extraction evidence in history, including native groups without an eligible claim. No operation reads expected answers or scoring fixtures at runtime.

The `preliminary_reason`/publication rules still require supported, timezone-aware observation time inside current age/expiry windows. Missing depth/access, conflict, forecast/negation/history, geometry ambiguity and model limitations retain their current handling. OSM, NOAH and Pasig history are placement/context resources, not current flood confirmation. No model-confidence bypass, full-road activation, arbitrary buffer or automatic clearance is introduced.

### Saved-result interfaces and reader selection

- Keep existing admin paths and active-admin authorization. Extend saved run responses to a discriminated result union: absent discriminator plus persisted `rules_only` is legacy; `lanes-news-ner-result-v1` plus `ner_rules_v1` is native. Unknown/mismatched versions return a visible unsupported-result error, never legacy coercion.
- `/articles/{article_id}` returns original native details and projection dispositions alongside historical runs. Serialization must preserve the envelope; the current `NewsExtractionResult` type alone would drop unknown fields. No preview POST is invoked to populate saved history.
- `/results` returns tagged items: `result_kind="legacy_claim"` with existing claim ordinal, or `result_kind="ner_group"` with `group_id` and nullable compatibility `claim_index`. A NER group appears once even if it maps to a compatibility claim; do not union duplicate projection cards. Preserve the existing pagination/search/publisher/condition/placement behavior and total counts on the server before pagination.
- Keep `/results/{run_id}/{claim_index}` for legacy/projected claim compatibility. Add the saved-read route `/results/{run_id}/groups/{group_id}` for native cards and their exact graph/source/projection evidence. Both routes verify run/article identity and use existing admin dependencies. Native keys use run ID/group ID rather than a fabricated claim ordinal.
- Native cards require supported affirmative body-grounded Metro locality and flood status, with complete group targets; not a resolved publication timestamp. Joint measurements remain one collective group. Noneligible/ambiguous/mention-only groups and all unresolved facts stay in Articles & processing/article inspection. Do not fall back to a broader location to make a card.
- Select the newest intended-method run for each article; failed/pending new runs remain visible issues rather than exposing old results as current. During rollout, configure one active method; old-mode completion cannot displace the current method. Historical mixed-mode runs remain accessible individually. Reader filters, counts and pipeline evaluation must use the same method-selection rule.
- Publication state is read from actual linked decisions, never inferred from card presence, extraction completion, map candidates, severity, confidence or runtime timing. UI reads do not fetch sources, infer, enqueue, evaluate or publish.

## 6. Failure and compatibility decisions

| Condition | Required outcome |
|---|---|
| Missing body / retrieval challenge / incomplete page | Retrieval issue; no NER success; retain last valid history and original clocks |
| Unauthenticated / non-admin saved-result request | Existing authorization denial before exposing saved evidence; no runtime call |
| Invalid input/hash/offset or unsupported result version | Explicit nonretryable binding/contract error; never repair offsets or reinterpret the artifact |
| Missing/corrupt model/tokenizer/runtime configuration | Explicit configuration/assets error, not `invalid_input_snapshot`; operator remediation, no hidden fallback |
| Runtime timeout/crash | Explicit bounded retry under the owned lease; exhausted attempts fail visibly; no concurrent duplicate launch |
| Unsupported locality/ambiguous target/collective scalar | Completed native graph with exact projection omission reasons; no invented compatibility values |
| No eligible observations | Completed classified extraction with graph/dispositions and no publication; distinct from runtime failure |
| No supported observation date/zone | Preserve raw clock and role; current-publication eligibility blocked |
| New denial/clearance or no-compatible-claim correction | New immutable result and explicit lifecycle reconciliation; absence alone cannot clear an event |
| Old reader/worker cannot understand new mode | Do not activate neural writes until all consumers are upgraded; no silent JSON field dropping or legacy coercion |

Stable error families are `ner_input_binding_invalid`, `ner_result_contract_invalid`, `ner_result_version_unsupported`, `ner_assets_unavailable`, `ner_configuration_invalid`, `ner_runtime_timeout` and `ner_runtime_failed`. Persist bounded codes rather than article text/private paths/credentials. Existing HTTP conventions remain; no new public inference endpoint is part of this contract. Phase B chooses exact runtime envelopes and retryable transport handling before implementation.

## 7. Acceptance matrix and Phase A reconciliation

The rows below are **future implementation acceptance requirements**, not executed tests or new accuracy measurements. Use fictional source-only cases and authenticated retained development captures/predictions; keep references outside runtime. No validation/holdout content, new data, inference or shared database replay is required to author this contract.

| ID | Scenario | Required evidence / result |
|---|---|---|
| A01 | Metadata city + flood; old recognizer misses body road | Complete candidate reaches queued NER; no pre-NER legacy-place requirement |
| A02 | Flood metadata with city only in body; no city anywhere | Existing bounded probe admits readable body; supported body geography can qualify; absent parent stays unresolved |
| A03 | Explicit non-Metro metadata / future or old date / missing flood metadata | Existing shortlist exclusions remain, known-correction exception documented, budgets not enlarged; discovery limitation disclosed |
| A04 | Forecast, prevention, habitual, drill, negation, caption-only and mixed actual observation | Save candidate if shortlisted, but only supported actual body observation can become a flood result; mixed evidence must not be globally suppressed |
| A05 | Pure commuter and flood-plus-commuter article | Pure commuter stays separate; flood evidence reaches NER without legacy place recognition |
| A06 | 403, short body, oversized/multipage content, successful RSS with blocked body | No complete-body success or excerpt substitution; feed success distinct from body health |
| A07 | Repeated URL/GUID, RSS 304, unchanged capture | Stable version/run identity, bounded refresh, no duplicate inference work from seen-time updates |
| A08 | Unicode, combining characters, leading/trailing whitespace and repeated road names | Exact original-body half-open slices and occurrence identity; stripped/first-match offsets rejected |
| A09 | Joint intersection / multiple streets sharing one value / incomplete junction | Native complete target sets retained; no fabricated per-road measurement or partial-target compatibility claim |
| A10 | Numeric + verbal depth, range, maximum, conflicting quantities, no depth | Original expressions/qualifiers retained; quantitative precedence only where lossless; scalar unknown rather than invented |
| A11 | LOCAL_AREA, ambiguous parent, dateline, shared city heading, independent city observation | Six-label identity retained, no default Pasig; parent scope explicit, useful city observations not automatically suppressed |
| A12 | Observation/report/onset/publication/recession/clearance/unspecified and competing clocks | Exact native roles retained; only supported observation can satisfy operational freshness |
| A13 | Date/time/PHT explicit; today/yesterday with aware publication; clock alone/unknown zone | Resolver basis retained; no implicit date rollover, machine-zone fill or inferred onset |
| A14 | Caution, light-vehicle closure, cleared/subsided and conflicting status | Preserve per-target access/status; no current wet-zone activation from cleared/subsided or unknown facts |
| A15 | Old rules-only result and new NER result through typed readers | No legacy mutation or native field loss; method visible, unknown discriminator rejected |
| A16 | Pure proposal/graph tampering, stale bundle, mixed source, missing graph references | Host/checker reject binding mismatch without fallback or inference retry |
| A17 | Native occurrence differs from old extractor but has bound source evidence | NER consistency checker examines actual bound evidence; old-recognizer disagreement alone is not rejection or approval |
| A18 | Latest run fails/pends or graph has zero compatibility claims | Honest article state, native-only details visible, no revived old main-list card or success-empty disguise |
| A19 | New body denies earlier flood / clears same location / changes event / loses usable targets | Prior snapshots/decisions preserved; exact matched correction evaluated; absence/failure alone cannot clear or refresh old evidence |
| A20 | Concurrent delivery, crashed attempt, expired lease and late completion | Existing idempotency/lease caps upheld; only owner commits; typed runtime errors stay separate from source input errors |
| A21 | Native/projected cards with filters, multiple pages, detail navigation and legacy history | Server counts match visible group semantics; one native observation once; detail routes bind exact run/group/claim |
| A22 | Existing source, geography, historical replay, publication/expiry and citizen moderation gates | No source-check/geometry/freshness bypass; historical fixtures cannot activate current production floods |
| A23 | Migration and mixed deployment | Existing legacy rows/constraints retained, unsupported mode rejected, neutral upgraded consumers precede new writes, rollback refuses lossy downgrade |

| Phase A task-plan item | Specification evidence |
|---|---|
| Trace complete path and consumers | Section 1 call-chain table and confirmed gaps |
| Identify pre-NER filters and define admission | Section 2, A01–A07 and A19 |
| Specify durable output and source coordinates | Section 3, A08 and A16 |
| Preserve rich facts and compatibility | Sections 4–5, A09–A14 and A17–A18 |
| Distinguish methods and historical readers | Sections 3/5/6, A15/A18/A21 |
| Prepare minimal approval-gated schema proposal | [Separate proposal](rss-ner-processing-mode-schema-proposal.md), A23 |

**Gate A outcome:** specification/consumer/schema-proposal deliverables were completed without executing the full integration matrix in Phase A. The later runtime/schema/C1/C2/C3a prerequisites and [C3b controlled local verification](../evaluations/rss-ner-rss-integration-20261021/README.md) now provide backend acceptance evidence. Frontend/browser acceptance and production resources/migration/activation are not claimed. Next is monitoring Phase D, interface Phase E and 403 investigation Phase F, followed by release gates. Preserve 11 unresolved reviewed-article rows, three held references, non-flood access omission, type-family and language/training limitations. No extra training/research gate is imposed.
