# LANES — Task Plan

> Tracking active sprints, backlog, and development priorities.
> **Last Updated:** September 25, 2026, 10:16 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

> Completed work and delivery history are recorded in [progress.md](progress.md). This plan contains the active sprint, unresolved work, and future backlog.

---

## Active Sprint

### Capstone Phase 36: Trusted Flood Intelligence — News Discovery, Taglish Extraction & Admin-Reviewed Map Suggestions (🟡 IN PROGRESS)
> **Focus:** Build a defense-ready, server-side assistant that discovers recent flood reports from approved public news sources, extracts Filipino/English/Taglish flood evidence, ranks a likely Pasig map location using the cleaned DRRMO history and map context, and presents every result for administrator review before it can affect an official flood zone or routing. It is decision support, not automatic public reporting or routing activation. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

**Current next task:** Deploy and manually verify a dedicated RSS Cloud Run job before enabling Cloud Scheduler. Continue with event grouping and NER after the discovery pipeline is reliable.

> **RSS implementation status:** The [RSS news discovery plan](others/rss-news-discovery-plan.md) records all 50 Feedspot candidates plus News5. Six publisher feeds are enabled after local checks; others can be added through the registry. The approved three-table storage model, migration, checkpoint-aware collection, and staff trigger are implemented in code. The migration and two collector runs passed against local development PostGIS on September 25; Cloud SQL migration, Cloud Run network/scheduling, event grouping, and NER remain pending. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

#### 1. Historical Location Input (Completed)

- [x] Clean the 2020–2025 Pasig DRRMO CSV into [726 traceable historical records](../data/flooded_areas_pasig_clean.csv), with the raw CSV, original workbook, and PSGC barangay reference preserved in `data/`. This dataset is a location prior; it has no coordinates and is not NER training text. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

#### 2. Trusted News Discovery and Source Evidence (In Progress)

- [x] Build a configurable 51-publisher research registry, bounded RSS/Atom parser, live feed probe, basic Pasig flood shortlist, staff-authenticated source/probe API, and one-run local discovery command. Verify six current feeds directly and cover parsing, source safety, deduplication, and auth with offline tests. This is the local collection slice; it does not persist candidates or run on a schedule. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Design and approve three durable feed/article/provenance tables; implement SQLAlchemy models, Alembic migration, conditional checkpoints, URL/GUID deduplication, a staff-only evidence list and trigger, and offline retry tests. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [x] Apply migration against local development PostGIS and run the persistent collector twice: six healthy checkpoints, three conditional `304` responses on the repeat pass, and no current Pasig flood candidates in the sampled feeds. The 12 RSS tests pass; fixture coverage verifies article persistence and deduplication. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [ ] Deploy and manually verify a dedicated Cloud Run job before enabling Cloud Scheduler; verify the production migration and feed access separately.
- [ ] Build a server-side, on-demand or scheduled discovery service using public publisher RSS feeds and a flood-keyword feed such as Google News RSS. Search Filipino, English, and Taglish terms (“baha,” “flood,” “lubog,” “pagbaha,” “lagpas tuhod”) with Pasig place terms.
- [ ] Investigate ABS-CBN, GMA News, News5, Inquirer, and Rappler first, while keeping the Feedspot 50 as candidate publishers. Enable any publisher only after verifying its identity, feed, article domains, and access method. Apply the resulting publisher-domain allowlist before article retrieval; fetch publicly accessible pages respectfully when the feed lacks full text. Do not bypass paywalls, bot protections, rate limits, or source restrictions.
- [ ] Define the candidate fields during implementation: source/canonical URL, publisher, title, byline when available, publication/fetch times, captured text, flood-relevance score, evidence sentences, extracted places, canonical depth, flood condition, ranked location candidates, confidence, and review state.
- [ ] Preserve canonical URL, publisher/domain, title, byline when available, publication/fetch times, retrieved text, and evidence excerpts for staff review.
- [ ] Deduplicate re-fetches and syndications by canonical URL and normalized title/content fingerprint; make retries idempotent and surface partial fetch failures.
- [ ] Keep Facebook ingestion outside the automated MVP; permit administrator-supplied public post text/link as a manual input path. Do not make paid APIs or Facebook access a defense dependency.

#### 3. Taglish Extraction and Normalization

- [ ] Verify the license, compatibility, and CPU behavior of calamanCy's Tagalog spaCy NER model, then integrate it as the baseline for general location entities. Pair it with LANES rules and a Pasig gazetteer instead of training a model from scratch.
- [ ] Extract evidence for city, barangay, road/street, landmark, numeric or language-based depth, flood condition, event date/time, publisher, and supporting sentences.
- [ ] Normalize aliases (for example, “Brgy.”/“Barangay,” “Sta.”/“Santa”) to PSGC-backed canonical barangays while preserving source wording. Keep ambiguous matches unresolved instead of guessing.
- [ ] Map Taglish phrases and explicit measurements to the established depth/severity scale with explainable rules; ambiguous wording stays unknown for staff review.
- [ ] Keep extracted flood condition (active, rising, receding, subsided, unknown) separate from admin moderation (pending, approved, rejected). Preserve existing manual-report depth labels and routing behavior; translate Taglish depth phrases internally to the existing values.

#### 4. Pasig Location Ranking and Suggested Geometry

- [ ] Build a Pasig gazetteer and rank extracted places using the cleaned DRRMO history, PSGC barangays, OSM roads/landmarks, and article context. Link place names to map geometry; rank exact road/landmark combinations above barangay-only matches and show the score rationale.
- [ ] Use historical recurrence and available NOAH/LiPAD/Phil-LiDAR hazard layers as location-ranking signals. Return-period hazard scenarios do not establish that a street is currently flooded.
- [ ] Return point/road/area geometry only when evidence supports it; otherwise mark location unresolved and require staff map selection/editing.

#### 5. Staff Review, Persistence, and Safety

- [ ] Add an admin-only pending AI-ingestion review surface or reuse the current moderation queue so staff can inspect source evidence, extracted fields, ranking rationale, and proposed geometry; allow correction, approval, rejection, or deferral with an audit record.
- [ ] On approval, use existing server-side moderation services to create/link the verified Flood Event and official zone. Pending or rejected candidates must not affect the public map, routing, analytics, or citizen notifications.
- [ ] Obtain explicit schema approval before adding/changing SQLAlchemy models, Alembic migrations, or Cloud SQL tables. Preserve source provenance and account for the unresolved Phase 33 integrity work.
- [ ] Protect ingestion/review endpoints with staff-role checks, rate limits, surfaced errors, and IDOR protections.

#### 6. Agreed Delivery Order

- [x] Clean the DRRMO CSV into a usable Pasig historical location-prior dataset. ([@roicambe](https://github.com/roicambe) (Roi Cambe))
- [ ] Build trusted-source server-side article discovery, filtering, evidence capture, and deduplication. Define the candidate fields and representative fixtures within this task.
- [ ] Integrate the verified calamanCy CPU Tagalog NER baseline.
- [ ] Add flood-specific Filipino/Taglish rules and map extracted depth/status to the existing canonical values.
- [ ] Rank candidate Pasig road segments or areas using the historical dataset, OSM place geometry, article context, and available hazard layers; show ambiguity and confidence.
- [ ] Add pending AI-ingestion review or reuse moderation, then connect approved candidates to the existing official-zone/event workflow.
- [ ] Test with real recent permitted articles and representative fixtures; show source evidence for every suggested location and verify the desktop/mobile review flow, authorization, and non-activation of pending/rejected candidates.

#### 7. Definition of Done

- [ ] Staff can discover a deduplicated candidate from an approved source, inspect preserved evidence and extracted facts, see explainable Pasig location suggestions, correct the result, and approve it through the existing verified-zone workflow.
- [ ] Tests cover source filtering/deduplication, extraction, ambiguous locations, authorization, and prevention of automatic activation; desktop and mobile review flows are checked.
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
