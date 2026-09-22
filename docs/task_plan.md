# LANES — Task Plan

> Tracking active sprints, backlog, and development priorities.
> **Last Updated:** September 23, 2026, 2:44 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

> Completed work and delivery history are recorded in [progress.md](progress.md). This plan contains the active sprint, unresolved work, and future backlog.

---

## Active Sprint

### Capstone Phase 36: Trusted Flood Intelligence — News Discovery, Taglish Extraction & Admin-Reviewed Map Suggestions (🟡 IN PROGRESS)
> **Focus:** Build a defense-ready, server-side assistant that discovers recent flood reports from approved public news sources, extracts Filipino/English/Taglish flood evidence, ranks a likely Pasig map location using the cleaned DRRMO history and map context, and presents every result for administrator review before it can affect an official flood zone or routing. It is decision support, not automatic public reporting or routing activation. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

#### 1. Scope and Product Contract

- [ ] Define one canonical AI candidate contract: source/canonical URL, publisher, title, publication/fetch times, captured text, flood-relevance score, evidence sentences, extracted places, canonical depth, condition, ranked location candidates, confidence, and review state.
- [ ] Keep extracted flood condition (active, rising, receding, subsided, unknown) separate from admin moderation (pending, approved, rejected); neither state alone activates routing.
- [ ] Preserve existing manual-report depth labels and routing behavior. Translate phrases such as “lagpas tuhod” and “hanggang baywang” internally to existing canonical depth/severity values.
- [ ] Limit the MVP to Pasig and a trusted publisher allowlist. Facebook/social media is out of scope without permitted API access or administrator-supplied public text/link.

#### 2. Trusted Discovery and Source Evidence

- [ ] Implement server-side scheduled or on-demand discovery using publisher RSS feeds or publicly accessible article pages at a respectful rate. Do not bypass paywalls, bot protections, rate limits, or source restrictions.
- [ ] Search Filipino, English, and Taglish flood terms (“baha,” “flood,” “lubog,” “pagbaha,” “lagpas tuhod”) with Pasig place terms; apply the publisher allowlist before full-text processing.
- [ ] Preserve canonical URL, publisher/domain, title, byline when available, publication/fetch times, retrieved text, and evidence excerpts for staff review.
- [ ] Deduplicate re-fetches and syndications by canonical URL and normalized title/content fingerprint; make retries idempotent and surface partial fetch failures.

#### 3. Taglish Extraction and Normalization

- [ ] Evaluate a Filipino/Tagalog-capable open-source NER baseline and its license; pair general location entities with LANES rules and a Pasig gazetteer instead of training a model from scratch.
- [ ] Extract evidence for city, barangay, road/street, landmark, numeric or language-based depth, flood condition, event date/time, publisher, and supporting sentences.
- [ ] Normalize aliases (for example, “Brgy.”/“Barangay,” “Sta.”/“Santa”) to PSGC-backed canonical barangays while preserving source wording. Keep ambiguous matches unresolved instead of guessing.
- [ ] Map Taglish phrases and explicit measurements to the established depth/severity scale with explainable rules; ambiguous wording stays unknown for staff review.

#### 4. Pasig Location Ranking and Suggested Geometry

- [ ] Use [the cleaned DRRMO history](../data/flooded_areas_pasig_clean.csv) as a historical location prior, retaining the raw export and PSGC reference as traceable evidence. The cleaned data has no coordinates and does not itself create map zones.
- [ ] Resolve extracted places against Pasig barangays, road geometry, landmarks, and article context. Rank exact road/place matches above barangay-only matches and show score rationale.
- [ ] Use historical recurrence and permitted hazard layers only as location-ranking signals, not as proof of a currently flooded road.
- [ ] Return point/road/area geometry only when evidence supports it; otherwise mark location unresolved and require staff map selection/editing.

#### 5. Staff Review, Persistence, and Safety

- [ ] Add an admin-only review surface or extend Spatial Operations so staff can inspect source evidence, extracted fields, ranking rationale, and proposed geometry; allow correction, approval, rejection, or deferral with an audit record.
- [ ] On approval, use existing server-side moderation services to create/link the verified Flood Event and official zone. Pending or rejected candidates must not affect the public map, routing, analytics, or citizen notifications.
- [ ] Obtain explicit schema approval before adding/changing SQLAlchemy models, Alembic migrations, or Cloud SQL tables. Preserve source provenance and account for the unresolved Phase 33 integrity work.
- [ ] Protect ingestion/review endpoints with staff-role checks, rate limits, surfaced errors, and IDOR protections.

#### 6. One-Week Delivery Order

- [ ] **Day 1:** Set the candidate contract, publisher policy, Pasig gazetteer input, and representative language fixtures.
- [ ] **Day 2:** Implement discovery, allowlist filtering, evidence capture, and deduplication with mockable tests.
- [ ] **Days 3–4:** Integrate NER baseline and LANES rules; test depth/status normalization and evidence extraction.
- [ ] **Day 5:** Implement location ranking from the historical dataset and map geometry; cover resolved, ambiguous, and no-match cases.
- [ ] **Day 6:** Connect admin review to the existing official-zone/event workflow; confirm pending/rejected candidates cannot alter routing.
- [ ] **Day 7:** Run backend tests, desktop/mobile review checks, authorization/source-policy review, and a fixture-based defense demo; document limitations and manual fallback.

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
