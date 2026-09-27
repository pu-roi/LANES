# LANES — Task Plan

> Tracking active sprints, backlog, and development priorities.
> **Last Updated:** September 27, 2026, 8:42 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

> Completed work and delivery history are recorded in [progress.md](progress.md). This plan contains the active sprint, unresolved work, and future backlog.

---

## Active Sprint

### Capstone Phase 38: Interactive MMDA Flood Gauge Visual & Vehicle Clearance Rules (🟢 COMPLETED)
> **Delivered:** Interactive split-view MMDA flood depth gauge on Landing Page (`/`). Integrates an interactive depth table with expanding vehicle clearance guidelines (PATV, NPLV, NPATV) linked via hover/tap interactions to an animated SVG human silhouette (modern commuter design with flat planted soles, balanced 50/50 golden ratio proportions, calibrated to 165 cm DOST-FNRI adult reference height) featuring dynamic Framer Motion spring water fill, prominent centimeter tick ruler, water level line, and high-visibility depth measurement callout badge. Fully optimized for both desktop and mobile/PWA layouts. (Delivered by [@roicambe](https://github.com/roicambe) (Roi Cambe))

---

### Capstone Phase 37: Official MMDA Flood Depth Measurement Integration (🟢 COMPLETED)
> **Delivered:** Single-source-of-truth physical depth measurement system in backend (`flood_depth.py`) and frontend (`floodDepth.ts`) mapping MMDA depth levels (`gutter`..`neck`) to metric meters/cm and imperial inches. Fully integrated and verified across both desktop and mobile/PWA layouts (Landing Page, Hazard Reporting, Spatial Operations `ZoneDataEditorForm`, `OfficialZoneDrawer`, `MergeWorkspacePanel`, Details Modals, Moderation Queue, and Flood History) with zero database schema alterations. (Delivered by [@roicambe](https://github.com/roicambe) (Roi Cambe))

---

### Capstone Phase 36: Trusted Flood Intelligence — News Discovery, Taglish Extraction & Admin-Reviewed Map Suggestions (🟡 IN PROGRESS)
> **Focus:** Build a server-side assistant that discovers recent flood reports from approved public news sources across the Philippines, extracts Filipino/English/Taglish flood evidence, ranks likely map locations, and gives staff a review path for uncertain claims. Any future automatic activation must pass separately verified evidence and geometry gates before affecting an official zone or routing. The Pasig DRRMO history strengthens Pasig-specific ranking; it is not a geographic limit. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

**Current next task:** Finish Gate 1 below by checking complete article bodies, every listed location, and cross-paragraph context against the [three August 2026 publisher examples](phase-36-three-article-check.md). Short checked passages now have reviewed expected facts and passing regression fixtures. RSS-to-extractor integration follows the validation and safety gates. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

> **Nationwide scope decision:** The Pasig City map border is a visual reference, not an ingestion, geocoding, moderation, or flood-zone boundary. Preserve completed Pasig-only milestones below as historical implementation records. The current source implements a nationwide discovery filter and PSGC-backed extraction baseline; representative cross-region evaluation and live deployment verification remain open. Pasig DRRMO history is an extra Pasig ranking signal. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

> **RSS, NLP & Physical Depth Measurement status:** The [RSS news discovery plan](plans/rss-news-discovery-plan.md) records 50 Feedspot candidates plus News5. Six feeds were verified in the prior production rollout. Taglish extraction and nationwide location ranking exist in source, with the 50-item constructed evaluation set reporting 100% barangay and depth recall; this does not establish real-article or nationwide accuracy. Extracted canonical depths map to the Phase 37 MMDA measurement registry (`flood_depth.py` / `floodDepth.ts`). The collector currently persists pending evidence and does not invoke `NewsAutoIngestionService`; staff review UI and a validated automatic activation gate remain open. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

#### Phase 36 Recovery Plan — Ordered Gates

> The three-article check was an exploratory diagnostic, not an RSS replay or an acceptance test. Work through these gates before claiming that news can safely create live map zones. The deployed collector uses Cloud SQL; development tests use fixtures or a disposable development database, never production rows. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

1. **Gate 1 — Define expected facts and repair extraction (first).**
   - [x] Record the developer-reviewed facts for the checked paragraphs of three 2026 articles: locations and parent cities, depth wording and numeric values, observation/report time versus unknown onset, and source links. Add false-city (`Calamba Street`), multi-road, and abbreviation (`p.m.`, `M.H.`) regression fixtures. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
   - [x] Repair those checked paragraphs' sentence boundaries, hyphenated/initialed road names, clause-specific numeric depth, city context, and segment/local-area evidence; parse the additional Malabon named-road list with its shared range and no invented per-road depth. Keep extraction read-only. Focused tests: 21/21; combined extraction/location/news discovery: 40/40. The 50-item constructed set retains 100% canonical barangay/depth recall; its article-level negation metric is 96% on two mixed-status items and is not real-article accuracy. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
   - [ ] Inspect the complete article bodies and all listed locations, including cross-paragraph context and approximate or ranged depths; label any unsupported location, timing, or geometry before treating Gate 1 as complete.
2. **Gate 2 — Validate location suggestions and the activation decision.**
   - [ ] Require map suggestions to carry evidence for the exact road segment or landmark and a verified geometry source. Do not promote fixed offline anchors, city centroids, broad barangays, or an entire OSM way to an automatic road closure. Missing or conflicting geometry goes to staff selection.
   - [ ] Replace the post-decision `0.98` score with explicit prerequisites: observed recent flooding, non-forecast and non-subsided condition, supported canonical depth when claimed, exact place, verified geometry, and source provenance. Auditor failure or absence goes to review. Do not advertise `95%` as a probability until it is calibrated against a labeled real-article set.
   - [ ] Test each failed prerequisite, stale historical news, repeated names, and contradictory updates; assert zero report/event/zone activation on every review or suppression path.
3. **Gate 3 — Design durable claim review before any database change.**
   - [ ] Specify where per-claim evidence, extraction version, geometry candidates, review decisions, and activation links live. Reuse existing tables only if they preserve these facts and idempotency. Obtain explicit developer approval before changing SQLAlchemy models or Alembic migrations, then apply and verify any approved migration against development PostGIS.
   - [ ] Design staff actions to inspect, correct, approve, reject, or defer a claim with an audit trail; require staff authentication and role checks. Separate news review state from Flood Report moderation state and flood condition.
4. **Gate 4 — Connect article processing in a non-publishing mode.**
   - [ ] Run one idempotent processing path for both saved RSS articles and staff-submitted candidates. Start with a dry-run or review-only mode that persists or displays extracted claims without creating public zones. Re-fetches, Scheduler retries, and syndication must not duplicate processing or events; surface per-article errors.
   - [ ] Verify metadata-only leads remain labeled as such, and validate full-text capture, URL/publisher provenance, publication time, and article age before extraction. Do not infer current flooding from an old article merely because it was fetched today.
5. **Gate 5 — Complete the staff review flow and publish only approved claims.**
   - [ ] Build or reuse a protected review UI showing original source, exact evidence sentence, raw and canonical depth, observed time, ranked geometry and rationale, and uncertainty. Verify correction and approval on desktop and mobile/PWA, including locations outside Pasig.
   - [ ] Connect an approved claim to the existing server-owned Flood Report, Flood Event, and avoidance-zone workflow with duplicate prevention. Pending, rejected, deferred, historical, forecast, and subsided claims must never alter the public map or routing.
6. **Gate 6 — Broaden evaluation, then consider automatic activation.**
   - [ ] Begin with the three developer-readable cases, then add a separate labeled set of real permitted articles across Luzon, Visayas, and Mindanao, including no-flood and multiple-location cases. Report exact-place, depth, condition, event-time, geometry, and false-activation results separately; the 50-item constructed benchmark is not a substitute.
   - [ ] Exercise RSS entry → saved article → extracted claim → staff decision → map/routing in development or a controlled environment. Verify release image, Cloud Run job, Cloud SQL migration state, and rollback path before production rollout. Enable automatic activation only after the decision and geometry gates pass on real articles and the developer has reviewed the measured false-activation risk.

#### 1. Historical Location Input (Completed)

- [x] Clean the 2020–2025 Pasig DRRMO CSV into [726 traceable historical records](../data/flooded_areas_pasig_clean.csv), with the raw CSV, original workbook, and PSGC barangay reference preserved in `data/`. This dataset is a location prior; it has no coordinates and is not NER training text. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

#### 2. Trusted News Discovery and Source Evidence (In Progress)

- [x] Build a configurable 51-publisher research registry, bounded RSS/Atom parser, live feed probe, basic Pasig flood shortlist, staff-authenticated source/probe API, and one-run local discovery command. Verify six current feeds directly and cover parsing, source safety, deduplication, and auth with offline tests. This is the local collection slice; it does not persist candidates or run on a schedule. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Design and approve three durable feed/article/provenance tables; implement SQLAlchemy models, Alembic migration, conditional checkpoints, URL/GUID deduplication, a staff-only evidence list and trigger, and offline retry tests. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Apply migration against local development PostGIS and run the persistent collector twice: six healthy checkpoints, three conditional `304` responses on the repeat pass, and no current Pasig flood candidates in the sampled feeds. The 12 RSS tests pass; a mocked article run against the same PostGIS database retained one article and one provenance row across two runs, then removed the synthetic records. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Verify the production migration job, deploy `lanes-news-discovery`, confirm two manual runs parse all six enabled feeds with persisted `304` checkpoints, and verify a Scheduler-triggered run. The three-hour schedule is enabled with job-scoped invoker access. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Add RSS job image updates to the backend release process before changing collector code again; added Step 5 to `cloudbuild.yaml` deploying the built image to `lanes-news-discovery` in `asia-east1`. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [ ] Add an on-demand or scheduled flood-keyword lead source such as Google News RSS, searching Filipino, English, and Taglish terms (“baha,” “flood,” “lubog,” “pagbaha,” “lagpas tuhod”) with Philippine province, city, and municipality terms when useful. Keep publisher-domain verification before article retrieval.
- [x] Replace the deployed Pasig-only shortlist with a Philippines-wide relevance filter in `likely_philippine_flood`. Evaluates Philippine provinces and cities nationwide across Luzon, Visayas, and Mindanao, filters out explicit international events, and retains headlines without a recognized place for full-text extraction/review. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Investigate ABS-CBN, GMA News, News5, Inquirer, and Rappler first, while keeping the Feedspot 50 as candidate publishers. ABS-CBN blocks automated RSS with HTTP 403 / Cloudflare bot protection; News5 feed timed out. GMA News, Inquirer, Rappler, Philstar, Manila Bulletin, and SunStar are active and verified. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [ ] Define the candidate fields during implementation: source/canonical URL, publisher, title, byline when available, publication/fetch times, captured text, flood-relevance score, evidence sentences, extracted places, canonical depth (`depth_canonical`), raw depth text (`depth_raw`), physical depth measurements (`depth_meters`, `depth_inches`, `depth_formatted` from MMDA spec), flood condition, ranked location candidates, confidence, and review state. (Cross-section task; deferred to Section 5 moderation/review UI).
- [ ] Preserve canonical URL, publisher/domain, title, byline when available, publication/fetch times, retrieved text, and evidence excerpts for staff review. (Cross-section task; deferred to Section 5 moderation/review UI).
- [ ] Deduplicate re-fetches and syndications by canonical URL and normalized title/content fingerprint; make retries idempotent and surface partial fetch failures.
- [x] Keep Facebook ingestion outside the automated MVP; permit administrator-supplied public post text/link as a manual input path. Implemented `POST /api/v1/admin/news/manual-candidate` allowing staff to submit DRRMO announcements, citizen social posts, or links directly into the ingestion pipeline without paid APIs. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

#### 3. Taglish NLP Extraction and Normalization (Pasig baseline completed; nationwide coverage pending)

> **Delivered scope and owner:** The completed extractor is a Pasig-focused baseline for evidence-linked, structured flood facts. It does not choose map geometry, create official zones, or change routing. The [cleaned DRRMO CSV](../data/flooded_areas_pasig_clean.csv) is a later Pasig location-ranking prior, not NER training text. Nationwide place extraction and evaluation remain open below. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

**3.1 Model feasibility and reproducible runtime**

- [x] Check calamanCy's package and model licenses (MIT for toolkit/model), supported spaCy versions (`>=3.8.3` requiring PyTorch and `spacy-transformers`, conflicting with pinned `spacy==3.7.5`), 203.7 MB wheel size, and coarse Tagalog NER labels (`LOC`, `ORG`, `PER` without flood attributes). Feasible CPU rule-based extraction baseline established per Section 3.1 instructions. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Run a CPU-only spike and feasibility analysis: Documented that `tl_calamancy_md` pulls 350+ MB of PyTorch/Transformers dependencies and lacks depth/condition labels. Built a deterministic, explainable, lightweight rule/gazetteer and regex extraction engine running at 0.71 ms/item on CPU with zero heavy dependencies. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

**3.2 Input contract and evaluation set**

- [x] Define a read-only extractor input from persisted `news_articles`: article ID, canonical URL, publisher, title, excerpt, `article_text`, publication time, and fetch time. Process full text only when capture succeeded; keep metadata-only leads visible for staff without claiming full-text extraction. Preserve original text, offsets, and source timestamps via `NewsArticleExtractorInput`. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Assemble an initial 50-item, manually labeled evaluation set in `data/taglish_flood_eval_set.json` spanning Filipino/English/Taglish, positive and negative flood mentions, negation, forecasts, historical reports, aliases, ambiguous places, multiple locations, and absent depth/time. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Build automated evaluation runner in `backend/scripts/evaluate_taglish_extraction.py` recording accuracy across place span, canonical barangay recall (100%), canonical depth match (100%), condition match (100%), and CPU latency (0.71 ms/item). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

**3.3 Place and flood-fact extraction**

- [x] Combine deterministic Pasig rules/gazetteer matches for city, barangay, road/street, and landmark names; retain the original mention and character offsets. Use [PSGC-backed Pasig barangays](../data/pasig_barangay_reference.csv) to normalize “Brgy.”/“Barangay,” “Sta.”/“Santa,” and known spelling variants. Leave conflicting or out-of-Pasig matches unresolved for later ranking or staff review. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Extract flood mentions and supporting sentences; associate each depth, condition, place, and time with the flood statement it describes. Handle multiple incidents/locations in one article without treating every named place as flooded. Distinguish an observed flood from a warning, forecast, historical reference, quoted denial, or negated report. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Map explicit depth language and measurements to the existing canonical depth keys (`gutter`, `half-knee`, `half-tire`, `knee`, `tires`, `waist`, `chest`, `neck`) only where an explainable rule supports the match. Keep ranges, vague phrases, contradictory values, or unmatched units unknown; record the original phrase and rule used. Integrated with Phase 37 single-source-of-truth MMDA physical depth registry (`flood_depth.py` / `floodDepth.ts`), ensuring claims bridge vernacular Taglish/cm/inch terms with exact metric (`0.20m`–`1.52m`) and imperial (`8"`–`60"+`) measurements without altering DB tables. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Extract condition as `active`, `rising`, `receding`, `subsided`, or `unknown`, independent of moderation state (`pending`, `approved`, `rejected`). Extract explicit event dates/times and cautiously resolve relative phrases using the article's publication time and Asia/Manila context; keep uncertain time unknown and never substitute fetch/publication time as an observed event time. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

**3.4 Output, integration, and acceptance gate**

- [x] Define a versioned backend extraction result `NewsExtractionResult` with per-claim raw span, normalized value or unknown, evidence sentence/offset, source article ID/URL, rule or model provenance, and uncertainty reason. Keep separate claims when an article reports different places or times. Make reruns deterministic and idempotent. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Implement extraction service in `backend/app/services/taglish_extraction_service.py` as a server-side, staff-only dry run or batch step over persisted candidates, with surfaced extraction errors and no public-map or routing side effect. Zero new third-party dependencies required. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Pass offline regression tests in `backend/tests/test_taglish_extraction.py` for aliases, depth/status phrases, negation, multiple places, missing full text, time ambiguity, provenance, and repeat processing (11/11 passing, 27/27 total backend discovery & extraction tests passing). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

**3.5 Nationwide place coverage and Multi-Tier Ensemble Extraction (In Progress)**

> **Owner:** [@roicambe](https://github.com/roicambe) (Roi Cambe)

- [x] Expand place extraction beyond Pasig with Philippine province, city/municipality, and barangay references and aliases. Preserve the original mention and supporting sentence; resolve repeated names only with administrative and article context. Implemented in `taglish_extraction_service.py` using dynamic PSGC provinces (82), major regional cities, national expressways/corridors, generic road patterns, and nationwide prefixed barangays with PSGC grounding and island group resolution (16/16 tests passing, 0.73 ms/item on 50-item benchmark). ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Ingest the official PSA Philippine Standard Geographic Code (PSGC) reference dataset (covering 82 provinces, 1,634 cities/municipalities, and 42,000+ barangays) into `data/philippines_psgc_reference.csv` and implement `PhilippineLocationService` with dynamic in-memory indexing, resolving place hierarchies and aliases while eliminating hardcoded place names in Python application code (33/33 tests passing, 0.66 ms/item). ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Implement the Multi-Tier Hybrid Extraction Pipeline in `hybrid_extraction_service.py`:
  - **Tier 1 (Fast Deterministic Rules & PSGC Grounding):** Local rule/gazetteer engine in `taglish_extraction_service.py` provides instant (0.66 ms) baseline parsing, canonical depth mapping (`gutter`..`neck`), and PSA PSGC code anchoring. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
  - **Tier 2 (planned, not installed):** Evaluate `calamanCy` (`tl_calamancy_md`) only if real-article errors justify its CPU and deployment cost.
  - **Tier 3 (planned, not integrated):** Evaluate Google Cloud Natural Language API only if it adds measurable accuracy to the nationwide evaluation set.
  - **Supporting auditor prototype:** `audit_claim_with_llm` sends candidate claims to a configured OpenRouter Gemini model, with a local fallback when no key is present or the request fails. This fallback does not provide independent confirmation. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
  - **Action prototype (`evaluate_claim_action`):** Categorizes claims into `auto_approved`, suppression, or `flagged_review`; its stated >=95% confidence threshold is not checked before approval. The score is currently assigned afterward and must not be described as a calibrated probability. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [ ] Extend the labeled evaluation set with reports from multiple Philippine regions (Luzon, Visayas, Mindanao), ambiguous same-name roads/barangays, articles naming several cities, and flood reports with no precise place. Report nationwide results separately from the completed 50-item Pasig-focused benchmark.
- [ ] Repair the road-span, city-context, abbreviation, and event-time errors in the [three August 2026 publisher passages](phase-36-three-article-check.md), then rerun them against source-preserving excerpts and broaden the real-article evaluation. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

#### 4. Location Ranking and Suggested Geometry (Pasig Baseline & Nationwide Expansion)

- [x] Build a Pasig gazetteer and rank extracted places using the cleaned DRRMO history (ingesting all 726 records from `data/flooded_areas_pasig_clean.csv` including historical water levels and centimeter depths), PSGC barangays, OSM roads/landmarks, and article context. Link place names to map geometry; rank exact road/landmark combinations above barangay-only matches and show the score rationale. Implemented via `PasigHistoricalService` (304 streets, 301 landmarks, recurrence counts) and integrated into `NationwideGeometryService` and `taglish_extraction_service.py`. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
  - [x] Implemented in `NationwideGeometryService`: Resolves province and city/municipality first, then barangay, road, and landmark using nationwide 43,778 PSA PSGC administrative references, OpenStreetMap (OSM) road ways, and article context. Ranks exact road/landmark combinations above barangay-only matches, disambiguates repeated place names, and outputs clear score rationales. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Use historical recurrence and available NOAH/LiPAD/Phil-LiDAR hazard layers as location-ranking signals, calibrating depth severity against MMDA vehicle clearance thresholds (Low <= 0.25m, Medium 0.33m-0.48m, High 0.66m-1.14m, Extreme >= 1.40m). Return-period hazard scenarios do not establish that a street is currently flooded. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
  - [x] Cleaned Pasig DRRMO recurrence integrated as priority flood corridor ranking signal (+0.04 bonus). Missing historical or hazard data outside Pasig never excludes a valid Philippine report. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [ ] Return point/road/area geometry only when evidence supports it; otherwise mark location unresolved and require staff map selection/editing.
  - [x] Implemented in `NationwideGeometryService`: Constructs 50m road corridor polygons along OSM centerlines for exact roads and 50m circular buffer polygons for landmarks/barangays. City-only or ambiguous mentions are marked unresolved to prevent closing entire cities. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
  - [x] OpenStreetMap (OSM) Road Corridor Buffering (`buffer_osm_linestring_to_polygon`): Buffer multi-point OSM road centerlines retrieved via Nominatim GeoJSON (`polygon_geojson=1`) into 50m avoidance corridor polygons following real road curves in `NationwideGeometryService`. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

#### 5. Staff Review, Persistence, and Safety

- [ ] Add an admin-only pending AI-ingestion review surface or reuse the current moderation queue so staff can inspect source evidence, extracted fields, physical depth measurements (`depth_formatted`, `depth_meters`, `depth_inches`), ranking rationale, and proposed geometry; allow correction, approval, rejection, or deferral with an audit record.
  - [x] Enqueued ambiguous, incomplete, or broad city-level reports (`flagged_review`) with candidate pre-rendered geometry for 1-click staff review in `hybrid_extraction_service.py`. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [ ] On approval, use existing server-side moderation services to create/link the verified Flood Event and official zone. On approval or auto-activation, `FloodReport` and `FloodAvoidanceZone` record canonical depth, automatically exposing dynamic `depth_meters`, `depth_inches`, and `depth_formatted` properties maintaining strict 3NF database compliance. Pending or rejected candidates must not affect the public map, routing, analytics, or citizen notifications.
  - [x] Implement the `NewsAutoIngestionService` activation prototype that can create approved reports, events, and zones when explicitly invoked; the scheduled collector and staff routes do not invoke it. Its confidence and independent-auditor gates require correction before production connection. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
  - [x] Strict safety suppression: Flood reports stating water has subsided ("humupa na") or weather predictions ("posibleng bahain") are strictly suppressed with zero created avoidance zones, keeping clear roads open. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
  - [x] News Auto-Ingestion Pipeline (`NewsAutoIngestionService`): Atomically creates approved `FloodReport`, durable `FloodEvent`, and operational `FloodAvoidanceZone` in PostGIS and Valhalla routing. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [ ] Obtain explicit schema approval before adding/changing SQLAlchemy models, Alembic migrations, or Cloud SQL tables. Preserve source provenance and account for the unresolved Phase 33 integrity work.
  - [x] Zero database schema modifications required; 100% compliant with existing 3NF tables (`flood_reports`, `flood_events`, `flood_avoidance_zones`, `news_articles`). ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [ ] Protect ingestion/review endpoints with staff-role checks, rate limits, surfaced errors, and IDOR protections.

#### 6. Agreed Delivery Order

- [x] Clean the DRRMO CSV into a usable Pasig historical location-prior dataset. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Deploy the verified-feed RSS collector with persistent evidence, URL/GUID deduplication, and a three-hour production schedule. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Complete the Pasig-focused NLP feasibility, labeled evaluation, extraction rules, provenance, and acceptance gate in Section 3; nationwide place coverage remains open in Section 3.5. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Implement the deterministic extraction and optional auditor prototype in `hybrid_extraction_service.py`; calamanCy and Cloud Natural Language tiers are not integrated. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Implement the unconnected `NewsAutoIngestionService` prototype for reports, events, and avoidance zones; production connection and safety validation remain open. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Implement strict safety suppression gates for subsided waters ("humupa na") and forecasts ("posibleng bahain") with 0 active zones. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Implement OpenStreetMap (OSM) multi-point way LineString buffering (`buffer_osm_linestring_to_polygon`) with Nominatim `polygon_geojson=1` for 50m road corridor polygons. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [ ] Execute Gates 1–2 above: fix real-article extraction and geometry errors, then validate explicit activation prerequisites before connecting the collector. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [ ] Execute Gates 3–5 above: design durable review, obtain any needed schema approval, connect both article entry paths in review-only mode, and complete staff-approved map publication. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [ ] Execute Gate 6 above: broaden real-article evaluation, verify desktop/mobile and nationwide behavior, and assess automatic activation only after the measured safety gate passes. Additional feed/search leads can be added when the validated pipeline needs them. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

#### 7. Definition of Done

- [ ] Staff can discover a deduplicated Philippine flood candidate from an approved source, inspect preserved evidence, extracted facts, and physical depth measurements (`depth_formatted`), see explainable location suggestions inside or outside Pasig, correct the result, and approve it through the existing verified-zone workflow.
- [ ] Smart Auto-Activation Gate: Validate observed-event time, exact place evidence, road geometry, canonical depth, and independently confirmed active condition before connecting article processing to zone creation. Auditor failure must not authorize activation; score thresholds require calibration on real articles. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Strict Safety Suppression: Reports of subsided water ("humupa na") and forecasts ("posibleng bahain") are strictly suppressed with zero created avoidance zones, keeping passable roads open. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] OpenStreetMap Integration: Road geometries are grounded on OSM centerlines and buffered into 50m corridor polygons. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [ ] Tests cover sources and flood locations from multiple Philippine regions, same-name place ambiguity, missing historical/hazard priors, filtering/deduplication, extraction, authorization, and 1-click staff review for ambiguous candidates. Desktop and mobile review must show and allow editing suggested geometry outside the Pasig border without a Pasig-only geocoding bias.
- [ ] Document any dependency, model, migration, endpoint, or UI added during implementation.

---

## Backlog

### Capstone Phase 33 — Flood Event History and City Planning Analytics (🔴 BLOCKED: Cloud SQL evidence integrity)

- [ ] Obtain approval for the normalized origin/supporting-report relationship and migration/backfill policy before schema changes.
- [ ] Classify orphaned Cloud SQL Events #6 and #8 with staff. Rebuild origin evidence only where official evidence exists; otherwise end or invalidate the event. Do not fabricate or silently relink evidence.
- [ ] Enforce exactly one origin report per event, require active events to retain an active official zone, protect linked evidence from deletion, and verify the migration/services against Cloud SQL.
- [ ] Re-run the integrity and quality gates in the original Phase 33 definition of done after remediation.

### Capstone Phase 18 — Intelligent Flood-Report Merging and Spatial Operations (🟡 STATUS NEEDS RECONCILIATION)

- [ ] Reconcile the remaining developer-led desktop/mobile workflow verification against delivered work in [progress.md](progress.md); complete any gaps and update the phase status.

### Capstone Phase 25 — Fast Map Startup and Live-Sync Resilience (🟡 MANUAL VERIFICATION PENDING)

- [ ] Verify MapTiler initial load, OSM fallback, automatic MapTiler recovery, and desktop/mobile recovery-notice placement in a clean browser and deployed Firebase build.
- [ ] Create/restrict the Firebase maptiler-api-key secret for the intended origins if this deployment is still required.

### Capstone Phase 24 — Unified Flood-Routing Policy (🟡 CLOUD VERIFICATION PENDING)

- [ ] Verify provider behavior against deployed Valhalla and ORS services, including the routing policy and responsive route presentation.

### Capstone Phase 22 — Private Valhalla Cloud Run Recovery (🟡 READY FOR CLOUD DEPLOYMENT)

- [ ] Assign an explicit service account to lanes-api, deploy infrastructure/valhalla/deploy.ps1 from an authenticated Google Cloud SDK environment, and smoke-test private Valhalla plus ORS fallback.

### Spatial Operations — Zone Update Broadcasts

- [ ] Confirm whether real-time SSE broadcasts for zone updates remain required; if so, add the scoped implementation and verification task to a numbered active phase.

---

## Future Backlog

### External Integrations and IoT

- [ ] Evaluate Open-Meteo GloFAS river-discharge data for flood-risk prediction and define how predictions would be reviewed before affecting public routing.
- [ ] Define secure IoT sensor webhook requirements for coordinate and water-level ingestion.

### Machine Learning

- [ ] Assess whether historical weather and flood records support a useful training dataset.
- [ ] Evaluate predictive flood-expiration models only after sufficient labeled records and a measurable evaluation plan exist.
