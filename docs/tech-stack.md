# **LANES (Lanes PH) Finalized Tech Stack Blueprint**

> **Last Updated:** October 05, 2026, 7:02 PM by [@roicambe](https://github.com/roicambe) (Roi Cambe)

**October 5 publication/lifecycle follow-up:** Automatic source-labeled **text-only news alerts**, atomic append-only decisions, supported observation refresh, matched clearance and two-hour evidence expiry are implemented locally. Read-time expiry becomes **Unconfirmed** even before maintenance; the default current feed retains it for 24 hours after expiry (configurable 1–72 hours), while safe historical detail remains available. Staff correction/defer/reject/reopen/clearance controls and desktop/mobile public-map News alerts are connected. Operational flood-zone activation/routing remains blocked by missing verified current affected polygons; OSM/NOAH/community boundaries remain placement evidence. No live deployment, paid provider request, new schema/dependency or normal/cloud database migration occurred. [Verification](evaluations/phase-36-news-publication-lifecycle.md), [operator guide](guides/news-publication-lifecycle.md). [@roicambe](https://github.com/roicambe) (Roi Cambe)

**Lifecycle stack audit:** publication uses existing SQLAlchemy/PostGIS advisory and row locks, Pydantic, UUID/hashing and `AuditLog`; public/staff panels reuse React, TanStack Query, shared controls and SSE/refetch. `LANES_NEWS_UNCONFIRMED_RETENTION_HOURS` defaults to 24 and accepts 1–72, independently from the two-hour observation horizon. No package or migration added.


**October 5 auditor/runtime audit:** independent evaluation uses existing HTTPX, Pydantic, SQLAlchemy/PostGIS and standard-library hashing. Explicit `LANES_NEWS_AUDITOR_PROVIDER`, `LANES_NEWS_AUDITOR_MODEL` and nonsecret `LANES_NEWS_AUDITOR_CONFIG_REVISION` select transport/policy; OpenRouter and Gemini use their own credentials with no fallback. No new Python/Node package, model or migration. Offline OSM relation enrichment, read-only asset audit and reviewed catalog provisioning reuse declared spatial libraries. Twenty Pasig OSM community polygons are bundled with ODbL attribution and automated-check provenance; ten omitted barangays, official/legal boundary verification and provider/model/deployment acceptance remain separate. [Evaluator guide](guides/news-claim-evaluation.md), [verification](evaluations/phase-36-independent-evaluation-and-spatial-coverage.md).

**Earlier October 5 dependency audit:** local v11 disconnected placement, reviewed boundary loading, transparent review auras and the approved five-table publication storage reuse the declared Shapely, Pydantic, SQLAlchemy/PostGIS, React/MapLibre and test stack. Offline Pasig qualification/follow-up scripts use existing Python dependencies; no package or lockfile change is required. `LANES_NEWS_BARANGAY_DIR` adds an external versioned polygon catalog alongside `LANES_NEWS_NOAH_DIR`; real reviewed polygons and matching API/evaluator asset release remain pending. Matplotlib/ContourPy remain declared for reproducible research plots. [Placement verification](evaluations/phase-36-disconnected-news-placement.md), [storage verification](evaluations/phase-36-news-publication-storage.md).

**Primary Panel checkpoint compatibility:** Server search/facets and shared report/zone details reuse existing FastAPI, SQLAlchemy, Pydantic, TanStack Query, React/Tailwind, Lucide and shared UI components. No new Python/Node dependency or package/lockfile change. [Audit](evaluations/phase-36-needs-review-inspection.md#october-4-primary-panel-push-audit).

**October 4 checkpoint audit:** Needs Review and reviewed flood growth use existing FastAPI, SQLAlchemy/GeoAlchemy2, PostGIS, Shapely 2.1.2, TanStack Query, MapLibre, shared React/Tailwind UI and Playwright. No new Python/Node import dependency or package/lockfile change is required. NOAH catalog provisioning and automatic news publication remain separate pending work. [Verification](evaluations/phase-36-needs-review-inspection.md#october-4-cross-boundary-growth-implementation).

**Local v10 analytical placement:** existing Shapely 2.1.2, NumPy, Pydantic and standard-library gzip/hashlib/struct support exact tiled vectors and section-matched history. No dependency change. External checksummed assets use `LANES_NEWS_NOAH_DIR`; raw ZIPs and the roughly 90 MB catalog remain outside Git/the API image. Provisioning/release remains pending. [Guide](guides/news-placement-preview.md).

**Latest local audit:** v9/v1.7 adds faithful source-depth/clearance presentation, generic passability and consistent road-parent provinces using existing dependencies and JSONB. All 595 backend tests pass. Production remains v4; the earlier v8 checkpoint below is release history. No library, SQLAlchemy model or migration changed. [Audit](evaluations/phase-36-four-article-source-audit.md).


### **Project: Flood-Adaptive Route Calculation and Visualization Web Platform**

### **Focus: Web Application (Responsive Desktop & Mobile Browser Layouts)**

This document serves as the official technical stack reference for the LANES platform. It outlines the specific tools, libraries, and frameworks utilized to build a fully self-hosted, free, and highly performant geospatial routing web application.

**October 2 spatial runtime data:** Priority 4 adds a compressed server-owned NCR named-road catalog under `backend/runtime_data/osm/`, built offline with the already declared `osmium` and `shapely` libraries. It records OSM attribution, snapshot time, full source/catalog hashes, 17 checked city boundaries, and incomplete/unnamed-road coverage gaps. Runtime matching performs no provider requests and infers no current flood from map data. Administrative/Pasig history CSVs and the catalog are explicitly bundled in the backend image. No Python or Node dependency was added. Source refresh is reviewed and requires rebuild/restart; it is not scheduled automatically.

The Linux image also installs Debian `libexpat1`, required by the existing `osmium` native module. This system-library dependency was exposed by the initial Priority 4 runtime probe; Windows unit tests alone do not verify Linux native imports.

**October 3 dependency and release audit:** approved telemetry revision `c5a7e9d2104f` and matching API/collector/Firebase monitoring releases are deployed, as recorded in the release evaluation. Current body-evidence filtering is production v4. Local v8/v1.6 includes the prior September 24 corrections plus September 9 attribution, cautious passability, publisher correction and retrieval-error fixes; its release remains pending. The private Docker replay uses existing PostgreSQL/PostGIS, dotenvx and loopback launchers with ignored configuration. No Python or Node dependency, SQLAlchemy model or migration was changed in this follow-up. Automatic NOAH/DRRMO-assisted publication and zone activation remain unfinished.

## **🛠️ Technical Stack Components**

### **1\. Client / Frontend Tier (Responsive Web Interface)**

* **Core Framework:** **Next.js (App Router) & React (TypeScript)**  
  * *Role:* Full-stack React framework providing SSR/SSG capabilities, file-based routing, and building modular, component-driven user interfaces.
* **Styling & Design System:** **Tailwind CSS v4**  
  * *Role:* Utility-first CSS framework for rapidly building premium, highly responsive, and dynamic user interfaces without writing custom CSS.
* **State Management & Fetching:** **TanStack React Query**  
  * *Role:* Asynchronous state management, caching, background synchronization, and automatic revalidation (configured with staleTime: 0 for instant revalidation on mount/navigation).
* **Data Visualization:** **Recharts & react-is**
  * *Role:* React-native, responsive SVG charts for the protected Flood History & Analytics dashboard, including trend/evidence combination charts, severity doughnuts, duration distributions, and recurrence rankings.
* **End-to-End Testing:** **Playwright**
  * *Role:* Credential-free, configurable Chromium smoke coverage for protected admin flows at desktop and mobile viewports. Authenticated browser state is supplied locally at test time and never committed.
* **Real-time Event Signaling:** **Server-Sent Events (SSE)**  
  * *Role:* Maintaining a unidirectional persistent connection to the backend to receive instant cache invalidation signals and trigger reactive refetching. More mobile-friendly than WebSockets.
* **Animations & Micro-interactions:** **Framer Motion**  
  * *Role:* Providing fluid, dynamic micro-animations (like expanding panels, fading modals, and dropdown transitions) to create a premium, responsive feel.
* **UI Utility Libraries:** **Lucide React, React Hot Toast, & React Day Picker**
  * *Role:* Providing consistent premium iconography, interactive non-blocking toast notifications, and accessible date selection components.
* **Offline & PWA Support:** **Next-PWA & idb-keyval**  
  * *Role:* Enabling Progressive Web App functionality and IndexedDB caching for offline resilience during poor network conditions.
* **Geospatial Render Canvas:** **MapLibre GL JS**  
  * *Role:* Open-source, WebGL-accelerated interactive 2D map renderer used to display vector basemaps, dynamic alternative routing polylines, and spatial flood avoidance zones.  
* **Interactive Map Drawing Engine:** **Terra Draw (`terra-draw` & `terra-draw-maplibre-gl-adapter`)**  
  * *Role:* Modern, framework-agnostic interactive vector drawing engine integrated into the Admin Map. Supports native Polygons, Freehand sketches, Rectangles, and Circles for defining official DRRMO detour zones without legacy Node.js dependencies.
* **Map Base Tiles & 3D Terrain:** **MapTiler, OpenStreetMap, & AWS Terrarium DEM**  
  * *Role:* Rendering dynamic vector basemap styles (Streets, Dark, Roads, Satellite, OSM) via a custom `MapStylePickerControl`. Integrates AWS `terrarium-dem` S3 raster tiles to provide realistic 3D elevation meshes draped underneath the street vectors.
* **Weather Data & Iconography:** **Open-Meteo API & Meteocons**
  * *Role:* Open-Meteo provides hyper-local, free weather forecasting data without API keys, while Meteocons (Fill SVGs) are served locally to provide a highly granular, premium visual representation of weather states.
* **AI Weather Insights:** **OpenRouter API**
  * *Role:* Integrates free LLMs (e.g., openai/gpt-oss-20b) to dynamically interpret and explain complex weather probability and volume metrics into layperson terminology.
* **Geographic Demographics:** **PSGC API (Gitlab Pages)**
  * *Role:* Providing a unified and accurate list of Philippine Provinces, Cities/Municipalities, and Barangays for user registration and demographic validation.

### **2\. Backend / Core Engine Tier (Application Server)**

* **Programming Language:** **Python 3.11+**  
  * *Role:* Handling data collection scripts, natural language parsing, database queries, and routing logic under a unified, high-performance execution environment.  
* **Web Framework & Real-time Server:** **FastAPI (with Uvicorn & sse-starlette)**  
  * *Role:* Serving as the asynchronous web server handling high-throughput client API requests, managing database transactions, and broadcasting data modification events via SSE.
* **Rate Limiting & Security:** **slowapi & Database-backed Progressive Cooldowns**
  * *Role:* Preventing brute-force attacks and DDoS by applying strict rate limits on authentication endpoints and enforcing progressive cooldown tiers (1m, 3m, 5m) with sliding grace windows for OTP generation.
* **Authentication Stack:** **JWT, python-jose, & bcrypt**  
  * *Role:* Securing API endpoints via JSON Web Tokens, cryptographically signing tokens, and securely hashing user passwords for role-based access control.
* **Transactional Email & Communication:** **Resend REST API & httpx**
  * *Role:* Generating async HTTP requests to the Resend API (from `Lanes <noreply@navlanes.live>`) to securely dispatch 6-digit One-Time Password verification codes to user emails during account onboarding/password recovery, as well as delivering commuter messages from the /about contact form to official project inboxes (lanes@navlanes.live, navlanes.live@gmail.com).
* **RSS News Discovery:** **httpx + Python standard-library XML/HTML parsers + Cloud Run Jobs + Cloud Scheduler**
  * *Role:* Polling six verified publisher feeds every three hours in `asia-east1` under the previously verified Cloud schedule, parsing bounded RSS/Atom responses, and storing source evidence and durable monitoring in migrated Cloud SQL tables. The runtime registry is pruned to six verified active feeds, while the 50 Feedspot candidate entries remain in research documentation (`docs/plans/rss-news-discovery-plan.md`). Title/excerpt shortlisting is followed by affirmative Metro Manila reporting-body evidence checks; matching v4 collector execution is verified in the release evaluation. The staff-only API exposes feed health, saved candidates, monitoring history and manual candidate submission. Collection does not invoke zone activation. No new Python package was added for RSS collection.
* **Open Article Leads:** **Public GDELT DOC API via existing httpx**
  * *Discovery and review:* Existing Taglish/PSGC rules, FastAPI/Pydantic/SQLAlchemy, and standard-library JSON/hash support previews plus approved durable version/run processing. PostgreSQL JSONB artifacts, uniqueness/check constraints, an immutability trigger, SKIP LOCKED claims, UUID leases, and bounded retries add no Python dependency. Approved migrations through `c5a7e9d2104f` are verified/applied locally and in production. Local v6 extraction corrections still require a matching API/collector release.
  * *Retrieval pilot:* Existing frontend Playwright plus installed headless Chrome returned a Cloudflare challenge for the exact Inquirer AMP URL; no backend browser dependency was added. Standard-library `html.entities` supplies known-character compatibility for RSS; DTD/custom entity rejection remains enforced. The collector's read-only extraction diagnostic reuses the existing rules/PSGC service without external model calls.
  * *Connection and fallback:* GDELT overrides the client timeout with 15 seconds to connect (including TLS) and 20 seconds to read. Optional event queries use existing Metro Manila place rules and publication-date bounds. When no approved index alternate exists, recent originals can search existing approved RSS/Atom feeds independently of GDELT, using the existing parser and article retriever. No library was added; current feed snapshots cannot recover arbitrary historical articles.
  * *Role:* A staff-only lookup for blocked publisher candidates returns indexed links and index-seen times without an account, card, or API key. Optional retrieval fetches up to three approved alternate publisher bodies for event review, separately from the original. Standard-library locking, timing, and a bounded 10-minute cache provide per-process pacing and cooldowns with Retry-After handling. The fallback is not scheduled and cannot activate a flood or route change. Live index success and shared coordination across replicas remain unverified. No new Python package was added. [GDELT DOC API](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/).
* **Image Processing & Storage:** **Cloudinary Python SDK**  
  * *Role:* Managing direct upload, scaling (down to 1024px), and WebP format compression of user-submitted flood evidence photos to a dedicated cloud CDN, ensuring lightweight database records and fast frontend loading.
* **NLP & Information Extraction:** **Evidence-linked Taglish extraction and nationwide PSGC location prototypes**
  * *Role:* Uses explainable rules and the 43,778-row PSGC reference to extract Philippine place mentions, canonical flood depth, flood condition, and event time while preserving character offsets and supporting sentences. Full-article fetching enforces a 100,000-character bound without silent truncation, isolates publisher story containers, excludes related-story widgets, rejects unverified multi-page links, and flags contradictory same-road clearing updates. A 51-site expected facts fixture verifies text extraction against real articles; [evaluations](evaluations/phase-36-three-article-check.md) confirm 27/27 Philstar, 16/16 PNA August 17, and 8/8 PNA August 8 sites. `calamanCy` and Google Cloud Natural Language are not integrated. An optional OpenRouter Gemini auditor exists, but article processing is not connected to the scheduled collector and its fallback is not an independent activation check. Exact road geometry and resolved observation datetimes remain open prerequisites.
* **Offline Spatial Audit:** **Pyosmium (`osmium`) & Shapely**
  * *Role:* Reading a local Metro Manila OSM PBF and measuring bounded road-centerline overlap with original NOAH hazard polygons in `backend/scripts/audit_noah_road_intersections.py`. These small geospatial libraries are declared in `backend/requirements.txt`; the script is read-only and is not a production news-zone service.
* **Offline Research Figures:** **Matplotlib 3.10.7**
  * *Role:* Standard Python scientific plots for the saved Pasig duration pilot, exported as 300 dpi PNG and vector PDF/SVG. The collector uses the shared offline plotting helper; Matplotlib and NumPy-compatible ContourPy 1.3.2 are declared in `backend/requirements.txt`. These figures describe dataset coverage and candidate intervals; no fitted duration model is claimed.
* **NOAH Display Asset Export:** **Pillow**
  * *Role:* Rendering the three local Metro Manila NOAH polygon archives into compact transparent PNGs for the commuter map's optional 3D hazard display. This offline presentation export does not supply current flood observations or routing geometry.
* **Encrypted Secrets & Environment Orchestration:** **@dotenvx/dotenvx**  
  * *Role:* Cross-platform AES-256 encrypted environment variable management, enabling safe git repository synchronization without exposing raw API keys or database credentials.

### **3\. Spatial Database Tier (Persistence)**

* **Relational Database Engine:** **PostgreSQL**  
  * *Role:* Managing structured database storage for user reports, admin verification states, and historical logs.  
* **Spatial Extension:** **PostGIS**  
  * *Role:* Extending PostgreSQL to support native spatial geometry types (Points and Polygons), executing real-time spatial calculations (such as generating 50-meter buffer areas around coordinates), and building spatial indexes for fast intersection queries.  
* **Object-Relational Mapper (ORM):** **SQLAlchemy with GeoAlchemy2**  
  * *Role:* Binding database tables and spatial geography columns directly to Python schemas.
* **Database Migrations:** **Alembic**  
  * *Role:* Tracking and applying incremental schema changes and maintaining database state synchronization across environments.

### **4\. Pathfinding Engine (Routing Graph Optimization)**

* **Online Primary Routing Engine:** **Valhalla (Docker / private Cloud Run HTTP API)**  
  * *Role:* High-performance self-hosted routing engine running as the private `lanes-valhalla` Cloud Run service. FastAPI calls it with a Cloud Run ID token; it supports `exclude_polygons`, up to three requested alternates per fastest/shortest search, and pedestrian/motorcycle/auto costing profiles.
* **Online Cloud Routing Engine:** **OpenRouteService (ORS API)**  
  * *Role:* Cloud-hosted secondary routing engine used as an alternative routing provider for dynamic comparison, fallback resilience, and user-switchable routing in the UI.
* **Offline Routing Engine (PWA):** **Valhalla WebAssembly (WASM)**  
  * *Role:* Provides true disconnected intelligent routing inside the browser. A custom Web Worker dynamically mounts .tar map graphs to the Emscripten filesystem, utilizing Valhalla's native `exclude_polygons` parameter to detour around synchronized active floods without an internet connection.
* **Source Graph Data:** **OpenStreetMap (OSM) Data**  
  * *Role:* Providing the raw baseline road network structure (nodes and edges representing physical streets) utilized across the routing engines.

### **5\. Evaluation & Testing Tier (Quality Assurance)**

* **Backend Integration Testing:** **pytest**
  * *Role:* Executing automated backend tests for API endpoints and business logic. Used to verify quota enforcement rules (e.g., 10-place saved places limit), CRUD operations, and edge case handling across FastAPI routes.
* **NLP Verification Libraries:** **scikit-learn & seqeval**
  * *Role:* Running isolated validation scripts to compute linguistic extraction performance metrics (precision, recall, and F1-scores) for the custom NLP model.

### **6\. Cloud Infrastructure & Deployment Tier (Hosting & Production)**

* **Frontend Serverless Hosting:** **Firebase App Hosting (Google Cloud)**
  * *Role:* Next.js App Router (SSR) deployment in `asia-east1` (Taiwan). Automatically handles server-rendered React components, dynamic routes, and asset caching backed by Cloud Run containers with build-time environment variable injection via `apphosting.yaml`.
* **Backend Microservices:** **Google Cloud Run (`asia-east1`)**
  * *Role:* Hosts public `lanes-api` plus private `lanes-valhalla`; the routing service scales to zero and is invokable only by the FastAPI runtime identity.
* **Routing Artifact Storage:** **Google Cloud Storage**
  * *Role:* Private, versioned source for the ignored Philippines Valhalla tile archive and build metadata; Cloud Build bakes a selected version into the Valhalla image.
* **CLI Deployment & Automation:** **Firebase CLI (`firebase-tools`)**
  * *Role:* Local project linking, App Hosting backend lifecycle management, build verification, and deployment orchestration.
* **CI/CD Build Automation & Container Orchestration:** **Google Cloud Build**  
  * *Role:* Automates container image build (`cloudbuild.yaml`), pushes tagged images to Google Container Registry (`gcr.io`), executes automated database migrations ahead of rollouts via Cloud Run Jobs (`lanes-migration`), and deploys new revisions to Cloud Run (`lanes-api`) with hardened service account logging (`CLOUD_LOGGING_ONLY`).
* **Database Migration Jobs:** **Google Cloud Run Jobs (`lanes-migration`)**  
  * *Role:* Serverless batch execution task triggered synchronously during Cloud Build (`gcloud run jobs execute lanes-migration --wait`) to apply latest Alembic schema migrations (`alembic upgrade head`) before new web service revisions are deployed, eliminating schema drift between backend code and production PostgreSQL.


### Offline flood-duration research archive

The standard-library `collect_flood_report_archive.py` validates cached publisher/document evidence and explicit interpretation/pairing rules; `plot_flood_report_archive.py` uses existing NumPy/Matplotlib for standard PNG/PDF/SVG coverage and candidate-interval figures. This research tooling reads no application settings or database. Captured incident occurrence clocks remain separate from clearance; no model library or app schema was added. [Current evidence snapshot](evaluations/metro-manila-flood-duration-20261004/README.md).
