# LANES Database Normalization & Security Architecture Plan

> **Last Updated:** October 07, 2026, 2:17 AM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 7 current cloud migration checkpoint:** Read-only `alembic current` and local `alembic heads` both return `d7e4b9a21c60 (head)` before the performance push. Both performance passes leave models, migrations, indexes and dependencies unchanged; no migration write is needed. Shared sync polling reads existing authoritative zone data and does not cache routing safety queries. Earlier pending-upgrade paragraphs record pre-release checkpoints. [Verification](../evaluations/cloud-performance-20261007.md#senior-planner-pre-push-checkpoint). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 7 auditor policy/storage verification:** Prompt v2 changes the existing evaluation fingerprint; response evidence remains v1. Optional `provider_http_status` is internal result metadata saved in existing JSONB; no SQLAlchemy model/column/migration changed. Twenty native evaluation/lease/policy/history checks pass after existing migrations to `d7e4b9a21c60` in a fresh removed loopback database. Normal/cloud databases remain untouched. [Verification](../evaluations/phase-36-auditor-evidence-options-20261007.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 7 migration verification:** **37 native storage/migration checks pass** against a newly created loopback PostGIS database, removed afterward. Existing full/repeated upgrades and downgrade/re-upgrade preserve prior evidence and reach `d7e4b9a21c60`. No table/model/migration definition changed. The last read-only cloud revision was `c5a7e9d2104f`; the live upgrade remains a future Cloud Build release action. [Verification](../evaluations/phase-36-news-runtime-packaging-20261007.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 6 integration audit:** No SQLAlchemy model, table, column, index, trigger or migration changed. Existing zone source_geometry stores each accepted road centerline; existing decision JSONB holds estimated_news_road provenance, asset digests, 25 m margin and review-attempt asset revision. Public DTOs expose safe news projections only. [Verification](../evaluations/phase-36-estimated-road-zone-integration-20261006.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 5 operational storage follow-up:** Existing approved tables and append-only JSONB hold typed private footprint bindings (source/checksum, geometry/parent/component hashes, exact article/input/claim/incident/observation/locality, SRID, boundary revision, approval record/catalog digest or authenticated staff actor/request). Legacy unbound snapshots remain readable, without authorizing new zone relinks. Existing override columns store accepted depth/severity/access; current supported revisions preserve coverage. No SQLAlchemy model, table, column or migration definition changed. Existing upgrades reach `d7e4b9a21c60` only in disposable databases. No actual current footprint catalog is provisioned. The worker connection is now complete locally using existing tables; map/release integration remains open. [Worker verification](../evaluations/phase-36-automatic-footprint-worker.md). [Verification](../evaluations/phase-36-trusted-footprint-contract.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)


**October 5 evaluation services:** `crud/news_evaluation.py` and `news_evaluation_service.py` now bind completed schema-valid extraction to approved `news_claim_cases`/`sources` and leased `evaluations`, with unique ordinal/hash/policy identity, bounded attempts, skip-locked ownership, lost-lease rejection and immutable terminal results. External auditing occurs after the claim transaction commits. Source bindings/evaluations do not create `news_claim_decisions`, zone links or operational rows. This uses head `d7e4b9a21c60` without new model/migration changes; normal/cloud databases remain untouched. [Verification](../evaluations/phase-36-independent-evaluation-and-spatial-coverage.md), [operator guide](../guides/news-claim-evaluation.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Earlier October 5 pre-push verification:** a fresh full `alembic upgrade head` to `d7e4b9a21c60` and 59 storage/extraction/queue checks pass in two newly created disposable local PostGIS databases. Repeated upgrade and publication downgrade/re-upgrade preserve prior synthetic evidence; both test databases were removed. Normal application/replay/cloud databases remain untouched. Local v11 fragment previews and external boundary catalogs reuse extraction JSONB and add no further schema. [Checkpoint](../evaluations/phase-36-news-publication-storage.md#october-5-pre-push-checkpoint). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

**October 5 approved publication storage — implemented and tested locally:** Explicit approval covers five additive tables: `news_claim_cases`, `news_claim_sources`, `news_claim_evaluations`, `news_claim_decisions` and `news_claim_zone_links`. `app/models/news_publication.py` exports their relationships; revision `d7e4b9a21c60` follows `c5a7e9d2104f`. Cases store stable identity/revision only; normalized RESTRICT links bind immutable extraction evidence to leased audits, append-only decisions and operational zone contributions. Unique run/ordinal, source/policy, request/case-revision and partial unique zone creation ownership constraints preserve identity. UPDATE/DELETE and TRUNCATE guards protect history; automatic evaluations require a completed audit and zone links require active-zone decisions. Active decisions require observation/finite expiry ordering; object snapshots are bounded to 65,536 bytes. No existing columns, spatial types/indexes, ReportSource enums or extraction rows changed. The [exact schema contract](../plans/news-publication-readiness-plan.md#1-storage-reuse-and-required-additions) and [60-check evaluation](../evaluations/phase-36-news-publication-storage.md) document fresh/repeated upgrade, downgrade/re-upgrade and evidence/geometry preservation in disposable PostGIS. No normal application/replay/cloud migration, backfill or public activation. Immutable claim-source identity and evaluation-policy validation are now implemented; publication snapshot validation and locked source-alert decision lifecycle are implemented in the later checkpoint above. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

The October 4 assessment and earlier schema-head notes below are historical; the approval and current repository migration head are recorded above.

**October 4 publication storage assessment — proposed, awaiting approval:** Existing news tables preserve extraction evidence; existing events/locations/zones support verified multi-section incidents. They do not store durable unresolved alerts or per-claim decisions. The [exact five-table proposal](../plans/news-publication-readiness-plan.md#1-storage-reuse-and-required-additions) adds `news_claim_cases`, `news_claim_sources`, `news_claim_evaluations`, `news_claim_decisions` and `news_claim_zone_links`, including unique immutable run/ordinal identity, leased audit work, request/revision guards, finite expiry and contribution ownership. Reuse existing event/zone fields without changing ReportSource or fabricating FloodReports. No SQLAlchemy or migration file has changed; repository head remains `c5a7e9d2104f`. New migration application/backfill/publication is not authorized or tested by this assessment. [Evidence](../evaluations/phase-36-publication-readiness-audit.md). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

**Primary Panel read-contract compatibility:** Queue search, facets and all-member summaries use existing report columns and extraction claim JSON. Added Pydantic response fields are API contracts, not database changes. No SQLAlchemy model or Alembic revision changed. Fresh pre-push local `alembic upgrade head` could not complete with Docker/PostGIS offline; last verified schema is `c5a7e9d2104f`. No cloud database was contacted. [Audit](../evaluations/phase-36-needs-review-inspection.md#october-4-primary-panel-push-audit).

**October 4 reviewed-growth compatibility:** existing `FloodEvent` locations, linked reports and event-owned zones already support multiple roads/barangays/cities and section-specific conditions. Extension preserves the supported polygon and `source_geometry`; corroboration keeps operational fields unchanged; separate sections reuse the same event. Report moderation outcomes, location/timeline updates and merge audit save together. Native tests use a guarded local PostGIS database with outer rollback. This checkpoint modifies no SQLAlchemy model or Alembic revision; schema remains `c5a7e9d2104f`. [Verification](../evaluations/phase-36-needs-review-inspection.md#october-4-cross-boundary-growth-implementation).

**Local v10 storage compatibility:** optional `placement_preview` uses existing extraction JSONB. Source hashing keeps processing identity at 90 characters within existing `String(100)`; old inputs/history remain intact. NOAH tiles are external derived files, not PostGIS tables. No SQLAlchemy/Alembic change or real database reprocessing occurred; prior v9 counts remain unchanged. Durable public state still needs storage assessment/separate schema approval. [Verification](../evaluations/phase-36-backend-placement-preview.md).

**Latest replay state (v9/v1.7):** four articles, five immutable source versions and fourteen extraction runs preserve 38 readable locations. September 9 contributes eleven runs and September 24 three; earlier v8 counts below are verification history. Generic passability uses existing claim JSONB, with no column/model/migration change. Reports/zones remain zero. [Audit](../evaluations/phase-36-four-article-source-audit.md).

**Local replay database:** a separate Docker database `lanes_news_test` uses the complete existing PostGIS/Alembic schema at `c5a7e9d2104f`. Creating it and applying existing migrations changed no model or migration source. The original local `lanes` database and cloud data/config are preserved. The September 24 article retains its five readable street claims and prior runs. The additional September 9 subset has three articles, four immutable source versions, eight runs and 33 readable sites at local v8/v1.6. Reports and avoidance zones remain unchanged. Explicit caution is stored in the existing claim JSONB; the added summary label requires no column or migration. Identical input at the same pipeline revision creates no further run. [Runbook](../guides/local-news-replay.md).

**October 3 pre-push verification:** existing private `alembic upgrade head` succeeds. Fresh disposable local databases verify the full chain to `c5a7e9d2104f`, four queue integrity/concurrency cases and the telemetry downgrade/upgrade round-trip with original article evidence preserved (five passing checks). Only the newly created disposable databases were removed afterward. The replay database and cloud data were not reset; no further migration source was added.

This document details the normalized, secure database architecture designed for **LANES (Localised Alternative Navigation for Environs under Submersion)**. It serves as a comprehensive reference guide to PostgreSQL schema patterns, spatial indexing, table normalization (3NF), and security safeguards.

## Phase 36 F4b approved telemetry (October 3)

The developer approved the four-table monitoring proposal. Additive revision `c5a7e9d2104f` follows `f29b6c8d104e`; [models](../../backend/app/models/news_telemetry.py) and [migration](../../backend/alembic/versions/c5a7e9d2104f_add_news_monitoring_telemetry.py) define:

| Table | Keys and persisted facts |
| --- | --- |
| `news_discovery_runs` | ID, unique correlation UUID, nullable RESTRICT user actor, staff/collector trigger, running/completed/failed/interrupted status, start/finish clocks and sanitized error code. Staff requires an actor; collector requires none. |
| `news_discovery_feed_runs` | RESTRICT parent run FK, source/feed provenance, probe status/check clock/error, nonnegative entries seen/candidates saved/body errors/scope unresolved. Unique parent/source/feed identity; indexed parent. |
| `news_fallback_lookups` | ID, unique correlation UUID, RESTRICT original article and user FKs, original 64-character content fingerprint, retrieval-request flag, start/finish/status/error and nonnegative optional retry delay. Indexed article/start. |
| `news_fallback_lookup_leads` | RESTRICT lookup FK, nonnegative ordinal unique per lookup, URL/source provenance, retrieval timestamp/status/error and optional assessment. Indexed parent; no article body. |

Both attempt tables enforce status/finish consistency and chronological timestamps. Feed and lead facts belong to their own attempts, preserving 3NF without duplicating a mutable publisher registry. Source identity and original fingerprint are provenance snapshots. Conditional finalization prevents duplicate children and replacement of finalized/interrupted outcomes. New work marks attempts older than two hours interrupted; history GETs remain read-only. Per-feed telemetry commits alongside that feed's existing evidence/checkpoint; later failures preserve earlier commits. Fallback finalization and lead insertions are atomic. No synthetic backfill or evidence/lifecycle rewrite.

Fresh disposable PostgreSQL upgrade/head, downgrade to the prior head, re-upgrade and repeated upgrade pass; prior news evidence remains intact. Local and production databases report `c5a7e9d2104f`. Four queue integration checks pass at the new head. The developer explicitly approved production migration/release; job `lanes-migration-j4dnk` succeeded before the corrected API/collector rollout. No dependency changes. Collection-to-alert delay still needs a separately agreed publication schema. See [verification](../evaluations/phase-36-f4b-monitoring-check.md) and [production evidence](../evaluations/phase-36-news-content-quality-investigation.md#completed-production-release). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

**October 2 local migration synchronization:** After recovering Docker/PostgreSQL, the developer explicitly approved applying existing extraction revision `f29b6c8d104e` to local LANES. `alembic upgrade head` succeeded from `a83c1d4e7b92`; the database reports the repository head. The historical Philstar test capture is saved as article #3 with one immutable input and one completed rules-only extraction run. Live F2 desktop/mobile reads pass. No model/migration definition or production schema was changed. See [F2 verification](../evaluations/phase-36-f2-article-browsing-check.md). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

**October 2 Priority 4 artifact extension:** The existing `news_extraction_runs.result` JSONB now carries optional typed per-claim `road_placement` evidence, including immutable catalog/source checksums, snapshot clock, city relation, bounded centerlines, and explicit uncertainty. Pipeline identity includes the full catalog checksum so refreshed map evidence creates a new run for the same immutable article input. Failed/unavailable source identity is distinct from repaired source identity. No table, column, SQLAlchemy model, constraint, or migration definition was changed. Production already applied extraction migration `f29b6c8d104e`; spatial candidates do not create public domain rows.

## Phase 36 RSS evidence storage (approved and migrated)

Revision `a83c1d4e7b92` defines exactly three new tables. Publisher configuration remains in `backend/app/news_sources.json`; `source_id` is the stable registry key. `alembic upgrade head` passed against development PostGIS on September 25, 2026, and the production Cloud Build migration job completed successfully before deploying the API. Two production collector runs and a Scheduler-triggered run then used the migrated Cloud SQL tables.

| Table | Columns and constraints | Purpose |
|---|---|---|
| `news_feed_checkpoints` | Integer PK; `source_id` varchar(100); unique `feed_url` text; nullable `etag`, `last_modified`, `last_checked_at`, `last_success_at`, `last_error` | Conditional polling and feed health across runs. |
| `news_articles` | Integer PK; unique `canonical_url` text; `publisher_source_id` varchar(100); title, excerpt, optional publication/fetch times, first/last seen times, nullable article text/error, SHA-256 content fingerprint, review state | One article evidence record per URL, including metadata-only leads. |
| `news_article_feed_entries` | Integer PK; `article_id` FK to `news_articles.id` with cascade delete and index; source ID, feed URL, feed GUID, first/last seen times, optional JSONB metadata; unique `(source_id, feed_url, feed_guid)` | Separate feed-entry provenance from the article body to avoid duplicate article storage. |

No news table references or activates `flood_reports`, `flood_events`, or `flood_avoidance_zones`. Any later NER or event grouping schema requires separate approval.

**October 2 approved addition — deployed and verified:** The developer approved Priority 3 after the two-table explanation. Migration `f29b6c8d104e` follows `a83c1d4e7b92`. Full `alembic upgrade head`, downgrade to the preceding revision, and upgrade again passed on disposable Cloud SQL PostgreSQL/PostGIS; the test database was then deleted. Production subsequently applied the migration and verified ten saved-body inputs/results, repeat idempotency and unchanged public tables. Priority 4 added map-aware results on those same immutable inputs without changing the schema. See the [contract](../plans/smart-auto-activation-and-hybrid-nlp-plan.md#priority-3-extraction-handoff--october-2-approved-implementation) and [production release verification](../evaluations/phase-36-reusable-road-match-check.md#production-release-verification). ([@roicambe](https://github.com/roicambe) (Roi Cambe))

**Priority 5 storage assessment — proposed, not approved:** The [publication/review/frontend plan](../plans/news-publication-review-frontend-plan.md#2-priority-5-lifecycle-contract-before-screen-implementation) requires durable per-claim decisions, public visibility/expiry, stable incident/revision identity, correction history and domain activation links. Existing extraction JSONB is evidence, not a mutable decision store. Assess existing domain tables and design exact constraints/backfill/transaction boundaries before requesting any additional model/migration approval. No schema change is made by this planning review; Phase 33 origin/evidence-integrity remediation remains open.

| Approved new table | Columns and constraints | Purpose |
|---|---|---|
| `news_article_versions` | Integer PK; indexed `article_id` RESTRICT FK; non-null SHA-256 fingerprint with length-64 check; non-null JSONB snapshot; UTC creation time; unique `(article_id, input_fingerprint)`; PostgreSQL BEFORE UPDATE trigger rejects every mutation | Exact historical URL/publisher/title/excerpt/body/publication input; fetch time and article ID excluded from canonical hash. |
| `news_extraction_runs` | Integer PK; indexed version RESTRICT FK; pipeline version; `rules_only` mode check; status check (`pending`, `processing`, `completed`, `retry_wait`, `failed`); attempts 0..5; nullable due/lease/start/completion times, UUID lease token, safe error code, JSONB result; required creation/update times; unique `(article_version_id, pipeline_version, mode)`; due-work index on status/due/expiry; lease-state and completed-result checks | Durable extraction artifact and attempt ownership, independent of moderation. |

JSONB stores immutable input documents and versioned extraction artifacts, not duplicated mutable domain entities. Results do not link to or activate public flood tables. Lease claims use short `FOR UPDATE SKIP LOCKED` transactions; conditional completion requires an unexpired matching token. Downgrade removes only the two new tables and trigger function; it discards extraction history and must be considered before a release rollback.

---

## 1. Architectural Entity Relationship Diagram (ERD)

```mermaid
erDiagram
    roles {
        int id PK "Auto-incrementing surrogate identifier"
        string name UK "Role name"
        jsonb permissions "JSON permissions matrix"
        boolean is_template "Template toggle"
        datetime created_at "UTC timestamp"
    }

    users {
        int id PK "Auto-incrementing surrogate identifier"
        string username UK "Admin/User identity handle"
        string email UK "Electronic mail address"
        string hashed_password "Salter bcrypt password hash"
        int role_id FK "Reference to roles"
        boolean is_active "Soft deactivation toggle"
        datetime created_at "UTC timestamp of registration"
        datetime deleted_at "Soft delete marker"
    }
    
    profiles {
        int id PK "Unique identifier"
        int user_id FK "Reference to users (UNIQUE)"
        string first_name
        string last_name
        string middle_initial
        string suffix
        string contact_number
        date birthdate
        string avatar_url
        boolean hide_profile_picture "Avatar privacy toggle"
        datetime updated_at
    }

    addresses {
        int id PK "Unique identifier"
        int profile_id FK "Reference to profiles (UNIQUE)"
        string house_number
        string street
        string barangay
        string city_municipality
        string province
        string postal_code
        string country
    }

    otp_verifications {
        int id PK "Unique identifier"
        string email
        string otp_code "Hashed OTP"
        datetime expires_at
        int attempts
        boolean is_verified
        datetime created_at
    }

    system_settings {
        string key PK "Setting key"
        jsonb value "Setting payload"
        int last_updated_by FK "Reference to users"
        datetime updated_at
    }

    flood_reports {
        int id PK "Unique identifier"
        int user_id FK "Nullable link to registered users.id"
        string raw_text "Raw bilingual Taglish input text"
        string source "Origin: twitter, facebook, user_report, manual_seeder"
        string source_url "Nullable URL link to the original article/post"
        string severity "Risk level: low, medium, high, extreme"
        string status "Moderation: pending, approved, rejected"
        int event_id FK "Nullable verified Flood Event reference"
        string image_url "Optional photo evidence"
        string human_readable_location "Normalized landmark"
        string barangay "Cleaned barangay name"
        string city "City or municipality"
        boolean is_public "Consent toggle for feed"
        geometry geometry "PostGIS Point coordinates (SRID 4326)"
        datetime created_at "UTC timestamp of ingestion"
        datetime updated_at "UTC timestamp of latest update"
        datetime deleted_at "Soft delete marker"
    }

    flood_report_locations {
        int id PK "Unique location entity identifier"
        int report_id FK "Cascade reference to flood_reports"
        string location_name "Normalized street or landmark name"
    }

    flood_avoidance_zones {
        int id PK "Unique detour zone identifier"
        int report_id FK "Cascade reference to flood_reports"
        geometry geometry "PostGIS Polygon boundaries (SRID 4326)"
        source_geometry geometry "Nullable original admin road centreline"
        boolean is_active "Status toggle for routing engine"
        int event_id FK "Nullable verified Flood Event reference"
        datetime created_at "UTC timestamp of generation"
        datetime updated_at "UTC timestamp of latest metadata update"
        datetime expires_at "Nullable UTC expiry limit"
    }

    flood_events {
        int id PK "Durable verified incident identifier"
        string status "active or ended"
        datetime first_reported_at "Nullable first linked report time"
        datetime verified_at "Official verification time"
        datetime ended_at "Nullable final-zone end time"
        string peak_severity "Highest verified severity"
        string peak_depth "Nullable highest verified water level"
    }

    flood_event_locations {
        int id PK "Normalized affected-place identifier"
        int event_id FK "Cascade reference to flood_events"
        string location_type "road, barangay, or city"
        string normalized_name "Per-event normalized place key"
    }

    flood_report_moderation_outcomes {
        int id PK "Append-only moderation outcome"
        int report_id FK "Cascade reference to flood_reports"
        int event_id FK "Nullable verified Flood Event reference"
        int zone_id FK "Nullable official zone reference"
        string outcome "approved, linked, or rejected"
    }

    flood_event_timeline_entries {
        int id PK "Readable incident-history entry"
        int event_id FK "Cascade reference to flood_events"
        string entry_type "Lifecycle event type"
        jsonb snapshot_json "Historical display snapshot, not a live relation"
        datetime occurred_at "UTC event timestamp"
    }

    audit_logs {
        int id PK "Append-only surrogate identifier"
        int admin_id FK "SET NULL reference to users"
        string action_type "Moderation action identifier"
        string target_table "Affected table metadata"
        int target_id "Affected record primary key"
        jsonb metadata_json "Diff properties stored in binary JSON"
        string ip_address "Origin IP (IPv4/IPv6)"
        datetime created_at "UTC action timestamp"
    }

    post_interactions {
        int id PK "Unique interaction identifier"
        int user_id FK "Reference to users"
        int report_id FK "Reference to flood_reports"
        string interaction_type "upvote, downvote"
        datetime created_at "UTC action timestamp"
    }

    comments {
        int id PK "Unique comment identifier"
        int user_id FK "Reference to users"
        int report_id FK "Reference to flood_reports"
        string content "Comment body"
        datetime created_at "UTC action timestamp"
    }

    flood_report_surveys {
        int id PK "Unique survey identifier"
        int report_id FK "Cascade reference to flood_reports (UNIQUE)"
        string passable_vehicles "Open text for vehicle types"
        string hidden_hazards "yes, no, unsure"
    }

    community_posts {
        int id PK "Unique post identifier"
        int user_id FK "Reference to users"
        int flood_report_id FK "Nullable reference to flood_reports"
        string content "Text content of the post"
        jsonb media_urls "Array of image/video URLs"
        string location_tag "Display landmark or location name"
        float location_lat "Latitude coordinate for map view"
        float location_lng "Longitude coordinate for map view"
        boolean is_pinned "Pin status toggle"
        datetime pinned_at "Timestamp of pinning"
        datetime created_at "UTC creation timestamp"
        datetime updated_at "UTC update timestamp"
        datetime hidden_at "Nullable moderation hide timestamp"
        int hidden_by_user_id FK "Nullable reference to users"
        datetime deleted_at "Nullable soft delete timestamp"
        int deleted_by_user_id FK "Nullable reference to users"
    }

    saved_places {
        int id PK "Unique identifier"
        int user_id FK "Cascade reference to users"
        string name "Custom waypoint label"
        string icon "Emoji representation"
        string address "Human-readable address"
        float latitude "Explicit WGS84 latitude"
        float longitude "Explicit WGS84 longitude"
        int pin_order "Custom ordering slot"
        geometry geometry "Point (SRID 4326)"
        datetime created_at "UTC timestamp"
    }

    notifications {
        int id PK "Unique notification identifier"
        int user_id FK "Reference to users"
        string type "LIKE, COMMENT, SYSTEM"
        string message "Notification text"
        jsonb payload "Routing metadata"
        boolean is_read "Read status toggle"
        datetime created_at "UTC creation timestamp"
    }

    roles ||--o{ users : "assigns"
    users ||--o| profiles : "has"
    profiles ||--o| addresses : "has"
    users ||--o{ audit_logs : "creates"
    users ||--o{ flood_reports : "submits"
    users ||--o{ post_interactions : "interacts"
    users ||--o{ comments : "writes"
    users ||--o{ system_settings : "updates"
    users ||--o{ community_posts : "writes"
    users ||--o{ saved_places : "bookmarks"
    users ||--o{ notifications : "receives"
    flood_reports ||--o{ flood_report_locations : "maps to"
    flood_reports ||--o{ flood_avoidance_zones : "generates"
    flood_events ||--o{ flood_reports : "is supported by"
    flood_events ||--o{ flood_avoidance_zones : "owns"
    flood_events ||--o{ flood_event_locations : "affects"
    flood_events ||--o{ flood_event_timeline_entries : "records"
    flood_reports ||--o{ flood_report_moderation_outcomes : "receives"
    flood_reports ||--o| flood_report_surveys : "contains"
    flood_reports ||--o| community_posts : "shared as"
    community_posts ||--o{ post_interactions : "receives"
    community_posts ||--o{ comments : "receives"
```

---

## 2. Table-by-Table Data Dictionary

### Table A: `roles`
**Description:** Stores role templates and permissions for access control (RBAC).

| Attribute | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | Primary Key | Unique surrogate key. |
| `name` | `VARCHAR(50)` | UNIQUE, NOT NULL, Index | Name of the role (e.g. admin, commuter). |
| `permissions` | `JSONB` | Default: `{}` | Detailed access matrix for sections. |
| `is_template` | `BOOLEAN` | Default: `FALSE` | Toggle indicating if it's a default template. |
| `created_at` | `TIMESTAMP` | Default: UTC Now | When the role was created. |

### Table B: `users`
**Description:** Stores account credentials and status flags for administrators and commuter clients.
**Security Level:** Critical.

| Attribute | Data Type | Constraints | Description & How it Works | Security / Performance Impact |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | Primary Key, Auto-increment | Unique surrogate key generated automatically for each user record. | Indexed by default. Keeps foreign key relations compact. |
| `username` | `VARCHAR(50)` | UNIQUE, NOT NULL, Index | Unique alphanumeric handle used by administrators and users to authenticate. | Indexed for fast login query performance. |
| `email` | `VARCHAR(100)` | UNIQUE, NOT NULL, Index | The primary electronic contact address of the account holder. | Indexed for account recovery checks and credential uniqueness. |
| `hashed_password` | `VARCHAR(255)` | NOT NULL | A secure one-way hash of the user's password generated using the **bcrypt** algorithm. | **Critical Security:** Never store plain text. Bcrypt adds a random salt and runs stretching loops to neutralize brute-force attacks. |
| `role_id` | `INTEGER` | Foreign Key, Index | Reference to `roles.id`. | Enforces Role-Based Access Control (RBAC) linking via the roles table. |
| `is_active` | `BOOLEAN` | Default: `TRUE` | Soft-deactivation toggle. Set to `FALSE` to suspend an account instead of deleting it. | Deactivated users are blocked from logging in, preserving historical records without losing referential integrity. |
| `deleted_at` | `TIMESTAMP` | Nullable | Soft-delete marker for the Archive Center. | Keeps the account structurally intact for historical audit logs, but fully removes access and visibility. |
| `created_at` | `TIMESTAMP` | Default: UTC Now | Record of when the account was initially created. | Used for registration auditing and chronological user reports. |

### Table C: `profiles`
**Description:** Stores personal and contact details attached to users.

| Attribute | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | Primary Key | Profile identifier. |
| `user_id` | `INTEGER` | Foreign Key, UNIQUE, Index | One-to-one mapping to `users`. |
| `first_name` | `VARCHAR(100)` | NOT NULL | User's first name. |
| `last_name` | `VARCHAR(100)` | NOT NULL | User's last name. |
| `middle_initial` | `VARCHAR(10)` | Nullable | User's middle initial. |
| `suffix` | `VARCHAR(20)` | Nullable | e.g. Jr, Sr, III. |
| `contact_number` | `VARCHAR(20)` | Nullable | Phone number. |
| `birthdate` | `DATE` | Nullable | User's date of birth. |
| `avatar_url` | `VARCHAR(255)` | Nullable | Link to user avatar image. |
| `hide_profile_picture` | `BOOLEAN` | Default: `FALSE` | Privacy preference to hide avatar and display uppercase initial fallback. |
| `updated_at` | `TIMESTAMP` | Default: UTC Now | Last profile update. |

### Table D: `addresses`
**Description:** Stores physical location info for a profile.

| Attribute | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | Primary Key | Address identifier. |
| `profile_id` | `INTEGER` | Foreign Key, UNIQUE, Index | One-to-one mapping to `profiles`. |
| `house_number` | `VARCHAR(100)` | Nullable | House/Unit string. |
| `street` | `VARCHAR(255)` | Nullable | Street name. |
| `barangay` | `VARCHAR(100)` | NOT NULL | Barangay. |
| `city_municipality` | `VARCHAR(100)` | NOT NULL | City or municipality. |
| `province` | `VARCHAR(100)` | NOT NULL | Province. |
| `postal_code` | `VARCHAR(20)` | Nullable | ZIP or postal code. |
| `country` | `VARCHAR(100)` | Default: 'Philippines' | Country name. |

### Table E: `otp_verifications`
**Description:** Temporary storage for email verifications and password resets.

| Attribute | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | Primary Key | ID. |
| `email` | `VARCHAR(100)` | Index | Email requesting the OTP. |
| `otp_code` | `VARCHAR(255)` | NOT NULL | Hashed OTP code (bcrypt). |
| `expires_at` | `TIMESTAMP` | NOT NULL | Expiry threshold. |
| `attempts` | `INTEGER` | Default: 0 | Number of attempts used. |
| `is_verified` | `BOOLEAN` | Default: FALSE | Has the OTP been verified? |
| `created_at` | `TIMESTAMP` | Default: UTC Now | Timestamp of request. |

### Table F: `flood_reports`
**Description:** Stores processed Taglish flood alerts mined from social feeds or manual submissions.

| Attribute | Data Type | Constraints | Description & How it Works | Security / Performance Impact |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | Primary Key, Auto-increment | Unique identifier for each ingested report. | Acts as the primary key for spatial relations and active detour lookups. |
| `user_id` | `INTEGER` | Foreign Key (`ON DELETE SET NULL`), Index | References `users.id`. Nullable link representing the registered account that submitted the report. | Nullable. Allows tracing submitted reports back to web/mobile users for moderation, trust metrics, and block handling. |
| `raw_text` | `TEXT` | NOT NULL | The original, unmodified social media post, emergency feed, or user message. | Kept for review and debugging NLP parsing algorithms. |
| `source` | `VARCHAR(50)` | NOT NULL | Origin channel of the report (e.g., `'twitter'`, `'facebook'`, `'direct_user'`, `'manual_seeder'`). | Allows analytics regarding data feed trust and channel frequency. |
| `source_url` | `VARCHAR(500)` | Nullable | Original URL link referencing the web article, social post, or feed bulletin. | **Fact-checking & Future AI:** Enables operators to click and verify raw sources. Will be used by the future AI model as citation references. |
| `image_url` | `VARCHAR(500)` | Nullable | Uploaded photo evidence URL. | Provides visual verification of floods. |
| `human_readable_location` | `VARCHAR(255)` | Nullable | Normalized street name or landmark resolved via reverse geocoding or user input. | Replaces complex joins with `flood_report_locations` for fast Community Feed reads. |
| `barangay` | `VARCHAR(100)` | Nullable, Index | Cleaned barangay name resolved via reverse geocoding. | Used for spatial analytics, filtering, and localized moderation. |
| `city` | `VARCHAR(100)` | Nullable, Index | City or municipality resolved via reverse geocoding. | Enables multi-city support across Metro Manila / nationwide. |
| `is_public` | `BOOLEAN` | Default: `FALSE` | Toggle indicating if the user consented to share this report on the Community Feed. | Ensures privacy compliance before making reports visible to all users. |
| `severity` | `VARCHAR(50)` | NOT NULL | Classified risk level of the flood. Allowed: `'low'`, `'medium'`, `'high'`, `'extreme'`. | Directly determines detour routing weights and map visual color-coding. |
| `status` | `VARCHAR(50)` | Default: `'pending'` | Moderation queue status. Allowed: `'pending'`, `'approved'`, `'rejected'`. | Approved reports link to a verified Flood Event; rejected reports remain internal moderation records, not archived evidence. |
| `event_id` | `INTEGER` | Nullable FK (`RESTRICT`), Index | Verified Flood Event supported by this approved report. | Keeps evidence distinct from incident counts. The foreign key protects the referenced event from deletion; it does not by itself prevent a report from being removed or require an origin report. |
| `geometry` | `GEOMETRY(Geometry, 4326)` | Spatial Index (GIST) | Latitude and longitude GPS coordinates. | **Performance:** Uses a GIST index. Essential for finding nearby flood reports quickly without doing expensive math on every record. |
| `deleted_at` | `TIMESTAMP` | Nullable | Soft-delete marker for the Archive Center. | If set, the report is moved to the Archive Center and hidden from the public feed. |
| `created_at` | `TIMESTAMP` | Default: UTC Now | Timestamp of when the report was ingested. | Used to determine report freshness (old reports are automatically archived). |
| `updated_at` | `TIMESTAMP` | Default: UTC Now | Timestamp of the latest state modification (e.g., approval time). | Tracks modification latency and moderation response speeds. |

### Table G: `flood_report_locations`
**Description:** Normalizes the NLP-extracted location landmarks and street names associated with a flood report.

| Attribute | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | Primary Key | Unique ID. |
| `report_id` | `INTEGER` | Foreign Key (CASCADE) | Associated report. |
| `location_name` | `VARCHAR(100)` | Index | Normalised street or place name. |

### Table H: `flood_avoidance_zones`
**Description:** Stores polygonal buffer regions representing impassable areas. Used directly by the routing engine to detour traffic.

| Attribute | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | Primary Key | Zone ID. |
| `report_id` | `INTEGER` | Foreign Key (CASCADE) | Source report. |
| `geometry` | `GEOMETRY(Polygon, 4326)` | GIST Index | Routing blockage polygon. |
| `source_geometry` | `GEOMETRY`, nullable | No spatial index | Original LineString/MultiLineString selected for an administrator-created road zone; preserves the active map road core while `geometry` is the buffered routing boundary. |
| `is_active` | `BOOLEAN` | Default: TRUE | Is the detour currently active. |
| `created_at` | `TIMESTAMP` | Default: UTC Now | Creation timestamp. |
| `updated_at` | `TIMESTAMP` | Default: UTC Now | Latest zone metadata update, used as the optimistic baseline for account-private Edit Zone drafts. |
| `expires_at` | `TIMESTAMP` | Nullable | When the detour naturally expires. |
| `event_id` | `INTEGER` | Nullable FK (`RESTRICT`), composite index with `is_active` | Permanent Flood Event that owns this operational zone. | Separates live routing state from historical incident identity. |

### Flood Event History Tables

`flood_events` is the permanent verified incident record (`active` or `ended`) with community-report, official-verification, and official-end timestamps plus the peak verified severity/depth. `flood_event_locations` stores normalized road, barangay, and city rows with a unique `(event_id, location_type, normalized_name)` key and an optional SRID-4326 GIST-indexed geometry.

`flood_report_moderation_outcomes` is append-only staff outcome history. Rejections require a structured reason, and `other` requires an internal note. `flood_event_timeline_entries` is the readable event chronology with snapshot JSON; it is intentionally separate from `audit_logs`, which retains technical actor/IP accountability.

**Historical analytics contract:** planning analytics query `flood_events` as the primary aggregation relation. `flood_event_locations` contributes each normalized road or barangay at most once per event; approved `flood_reports` are counted only as a separately named corroboration measure. No analytics table duplicates raw evidence, reporter identity, media, or exact report geometry.

#### Cloud SQL Integrity Finding and Required Hardening (Investigating)

On September 22, 2026, Cloud SQL verification found active Flood Events **#6** and **#8** whose timeline snapshots reference reports/zones that no longer exist (`#30`/`#22` and `#36`/`#25`, respectively). Both events therefore return zero linked reports and zero linked zones in Flood History. Timeline `snapshot_json` preserves display identifiers but has no foreign-key relationship to those source records, so it cannot guarantee that a referenced report or zone remains available.

The currently deployed nullable `flood_reports.event_id` and `flood_avoidance_zones.event_id` columns allow an event to exist without either relationship. They also permit direct official-zone creation to create an event without an admin-origin report. This conflicts with the approved product rule: every Flood Event must retain exactly one origin report—submitted by a user, created by an administrator, or created by a future AI ingestion path—and may retain many supporting reports.

**Required design before a schema migration (not implemented yet):**

- Introduce a normalized event-to-report association that records the relationship role (`origin` or `supporting`), preserves the report's source (`user_report`, `admin_official`, or future `ai`), and prevents one report from being assigned to multiple events unintentionally.
- Enforce exactly one origin relationship per event with a unique partial index plus a deferred integrity check; ordinary supporting reports remain one-to-many.
- Require every active official zone to belong to one Flood Event, and require an active Flood Event to retain at least one active official zone. Use transactional service validation and a deferred database check/trigger where cross-row enforcement is required.
- Restrict deletion of a report or zone still linked as origin/supporting evidence. Historical deactivation ends the event; it must not erase its evidence relationship.
- Before enabling the stricter constraints, classify/backfill existing orphaned events. When source evidence is genuinely absent, staff must explicitly rebuild an official origin report/zone or mark the event invalid/ended; never silently invent or relink evidence.

This hardening requires human approval before any SQLAlchemy model or Alembic migration change. ([@roicambe](https://github.com/roicambe) (Roi Cambe))

### First-Party Visitor Analytics Table

`visitor_daily_visits` is a 3NF daily fact table with a unique `(visit_date, visitor_hash)` constraint. `visitor_hash` is a server-side HMAC-SHA256 value derived from a browser-generated UUID, so LANES never persists the source UUID, IP address, device fingerprint, or location. `user_id` is nullable with `ON DELETE SET NULL`; aggregate queries use it only to count a signed-in account once across browsers, while anonymous activity remains a unique browser estimate. The table is indexed by date, hash, and account to support the protected 30-day dashboard trend without exposing individual activity.

### Table I: `audit_logs`
**Description:** An append-only security log recording administrative actions.

| Attribute | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | Primary Key | Log ID. |
| `admin_id` | `INTEGER` | Foreign Key (SET NULL) | Actor. |
| `action_type` | `VARCHAR(50)` | Index | E.g. LOGIN, APPROVE_REPORT. |
| `target_table` | `VARCHAR(50)` | NOT NULL | Affected table. |
| `target_id` | `INTEGER` | Nullable | Affected row PK. |
| `metadata_json` | `JSONB` | Nullable | Diff properties. |
| `ip_address` | `VARCHAR(45)` | Nullable | IP trace. |
| `created_at` | `TIMESTAMP` | Default: UTC Now | Action time. |

### Table J: `post_interactions`
**Description:** Records user upvotes and downvotes on community feed posts.

| Attribute | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | Primary Key | ID. |
| `user_id` | `INTEGER` | Foreign Key | The voting user. |
| `post_id` | `INTEGER` | Foreign Key (CASCADE) | The community post voted on. |
| `interaction_type` | `ENUM` | NOT NULL | 'upvote' or 'downvote'. |
| `created_at` | `TIMESTAMP` | Default: UTC Now | When the vote was cast. |

### Table K: `comments`
**Description:** User comments on community posts.

| Attribute | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | Primary Key | ID. |
| `user_id` | `INTEGER` | Foreign Key (CASCADE) | Author. |
| `post_id` | `INTEGER` | Foreign Key (CASCADE) | Associated community post. |
| `content` | `VARCHAR(1000)` | NOT NULL | Comment text. |
| `created_at` | `TIMESTAMP` | Default: UTC Now | Timestamp. |

### Table L: `system_settings`
**Description:** Key-value store for global platform configurations.

| Attribute | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `key` | `VARCHAR` | Primary Key | Configuration key. |
| `value` | `JSONB` | NOT NULL | Configuration payload. |
| `last_updated_by` | `INTEGER` | Foreign Key (SET NULL) | Admin who updated it last. |
| `updated_at` | `TIMESTAMP` | On Update | Timestamp. |

### Table M: `flood_report_surveys`
**Description:** Stores structured survey data attached to flood reports regarding vehicle passability and hidden hazards.

| Attribute | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | Primary Key | Survey ID. |
| `report_id` | `INTEGER` | Foreign Key (CASCADE), UNIQUE, Index | One-to-one mapping to the associated report. |
| `passable_vehicles` | `VARCHAR(500)` | Nullable | Open text response indicating which vehicles can pass. |
| `hidden_hazards` | `ENUM` | NOT NULL | Indicator of hidden hazards ('yes', 'no', 'unsure'). |

### Table N: `community_posts`
**Description:** The core entity for the community feed. Represents standalone user posts or shared flood reports with optional tagged geolocation.

| Attribute | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | Primary Key | Post ID. |
| `user_id` | `INTEGER` | Foreign Key (CASCADE) | Author of the post. |
| `flood_report_id` | `INTEGER` | Foreign Key (CASCADE), Nullable | If set, this post acts as a shared wrapper for a flood report. |
| `content` | `TEXT` | NOT NULL | Text body of the post. |
| `media_urls` | `JSONB` | Nullable | Array of image or video URLs. |
| `location_tag` | `VARCHAR(255)` | Nullable | Geocoded landmark or user label. |
| `location_lat` | `FLOAT` | Nullable | Latitude coordinate for map view/fly-to. |
| `location_lng` | `FLOAT` | Nullable | Longitude coordinate for map view/fly-to. |
| `is_pinned` | `BOOLEAN` | Default: FALSE | Pinned announcement flag. |
| `pinned_at` | `TIMESTAMP` | Nullable | Timestamp of pinning. |
| `created_at` | `TIMESTAMP` | Default: UTC Now | Timestamp. |
| `updated_at` | `TIMESTAMP` | Default: UTC Now | Last update timestamp. |
| `hidden_at` | `TIMESTAMP` | Nullable, Index | Soft-hide timestamp. A hidden post is excluded from public feed reads but remains available to its author and staff moderation workflow. |
| `hidden_by_user_id` | `INTEGER` | Foreign Key (SET NULL), Nullable | Staff user who applied the soft-hide. |

### Table N-1: `community_post_edit_history`
**Description:** Immutable audit snapshots for each author-approved Community Post revision. Before/after values are stored together so public history remains correct even after later edits.

| Attribute | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | Primary Key | History row ID. |
| `post_id` | `INTEGER` | Foreign Key (CASCADE), Index | Edited Community Post. |
| `editor_user_id` | `INTEGER` | Foreign Key (CASCADE), Index | Author who made the edit. |
| `version` | `INTEGER` | UNIQUE with `post_id` | Sequential edit number per post. |
| `previous_*` | `TEXT` / `JSONB` / location fields | NOT NULL for content | Snapshot before the edit. |
| `updated_*` | `TEXT` / `JSONB` / location fields | NOT NULL for content | Snapshot after the edit. |
| `created_at` | `TIMESTAMP` | Default: UTC Now | When the edit occurred. |

### Table N-2: `community_post_reports`
**Description:** Private moderation reports submitted by authenticated non-authors. Reports remain separate from public post history and support one open report per reporter/post pair.

| Attribute | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | Primary Key | Report ID. |
| `post_id` | `INTEGER` | Foreign Key (CASCADE), Index | Reported post. |
| `reporter_user_id` | `INTEGER` | Foreign Key (CASCADE), Index | User who submitted the report. |
| `reason` | `VARCHAR(50)` | NOT NULL | `spam_scam`, `misinformation`, `harassment_hate`, `explicit_violent`, or `other`. |
| `details` | `TEXT` | Nullable | Required explanation when reason is `other`. |
| `status` | `VARCHAR(20)` | Default: `open`, Index | Moderation lifecycle state. |
| `resolution_action` | `VARCHAR(20)` | Nullable | Recorded staff decision: `dismiss`, `warn`, or `hide`. |
| `resolved_by_user_id` | `INTEGER` | Foreign Key (SET NULL), Nullable | Staff reviewer who resolved the report. |
| `resolved_at` | `TIMESTAMP` | Nullable | Resolution timestamp. |
| `created_at` | `TIMESTAMP` | Default: UTC Now | Submission time. |

### Table O: `notifications`
**Description:** Stores in-app alerts for users (e.g., comments, likes, system alerts).

| Attribute | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | Primary Key | Notification ID. |
| `user_id` | `INTEGER` | Foreign Key (CASCADE) | The recipient of the notification. |
| `type` | `VARCHAR(50)` | NOT NULL | Category (e.g., 'COMMENT', 'LIKE', 'SYSTEM'). |
| `message` | `VARCHAR(255)` | NOT NULL | Human-readable notification text. |
| `payload` | `JSONB` | NOT NULL | Metadata for routing (e.g., `{"post_id": 12}`). |
| `is_read` | `BOOLEAN` | Default: FALSE | Read status. |
| `created_at` | `TIMESTAMP` | Default: UTC Now | Timestamp. |

### Table P: `saved_places`
**Description:** User-customized bookmarked waypoints with explicit coordinates and spatial geometry.

| Attribute | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | Primary Key | Saved place ID. |
| `user_id` | `INTEGER` | Foreign Key (CASCADE), Index | Associated user. |
| `name` | `VARCHAR(50)` | NOT NULL | Custom waypoint label. |
| `icon` | `VARCHAR(50)` | NOT NULL | Emoji icon representation. |
| `address` | `VARCHAR(255)` | Nullable | Street address or landmark. |
| `latitude` | `FLOAT` | NOT NULL | Latitude (WGS84). |
| `longitude` | `FLOAT` | NOT NULL | Longitude (WGS84). |
| `pin_order` | `INTEGER` | Nullable | User's preferred pin ordering. |
| `geometry` | `GEOMETRY(Point, 4326)` | Spatial Index (GIST) | PostGIS spatial geometry for proximity queries. |
| `created_at` | `TIMESTAMP` | Default: UTC Now | Timestamp. |

---

## 3. Referential Integrity & Deletion Rules

When designing relational schemas, handling deletion cascades is critical to preventing orphaned rows and data loss:

1. **`ON DELETE CASCADE` (Used for Locations, Surveys, Detours, Comments, Interactions, Profiles, Addresses):**
   * If a `flood_report` is deleted, its child zones (`flood_avoidance_zones`), locations, surveys, comments, and interactions are automatically deleted. This prevents child rows from being orphaned, but it can leave a separately stored Flood Event/timeline snapshot without its originating evidence when the event links are nullable. The hardening design above addresses that historical-integrity gap.
   * If a `user` is deleted, their `profile` and `address` cascade drop.
2. **`ON DELETE SET NULL` (Used for Audit Logs, Report Authors, Settings):**
   * If an administrator or user account is deleted, the user_id fields in reports, settings, or audit logs are set to `NULL`. **The core data is preserved.**

---

## 4. Key Database Security Controls

* **Transactional DDL:** PostgreSQL runs database modifications inside transactions.
* **SQL Injection Shielding:** Parameterized SQL via SQLAlchemy.
* **Bcrypt Password Storage:** High-entropy salted hashes.
* **Append-Only Auditing:** No update or delete endpoints exist for `audit_logs`.

---

## 5. Audit Log Action Types & Metadata Schemas

To ensure structured logging and avoid raw text entries, the `action_type` string must conform to a predefined category catalog. The `metadata_json` field contains a JSONB structure specific to each type.

### 🚨 What NOT to Log (Security Restrictions)
* **Plain text passwords** or attempted password strings.
* **JWT auth tokens** or session credentials.
* **Full credit card numbers**.

---

## 6. Audit Integrity & Retention Policy

* **`ON DELETE SET NULL` Enforcement:** If an administrator account is deleted, the log's `admin_id` column is set to `NULL`, but the log entry itself **remains fully intact**.
* **Recommended Retention Period:** **365 Days (1 Year)**.
