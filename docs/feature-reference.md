# LANES Feature Reference Document

This document serves as the central technical reference for all currently implemented and future planned functionality of the **LANES (Localised Alternative Navigation for Environs under Submersion)** platform. It maps high-level feature behaviors directly to the underlying frontend components, backend routers, databases, and algorithms.

---

## 🛠️ Current Features

### 1. Bilingual Taglish NLP Ingestion & Named Entity Recognition (NER)
*   **Purpose:** Bypasses the need for expensive physical IoT sensors by converting raw, informal text reports from public channels into structured geospatial hazards.
*   **What it does:** Extracts location tokens (street names, landmarks) and classifies flood depth indicators from conversational, bilingual Taglish text feeds (e.g., *"Baha sa may Caruncho Ave, lagpas tuhod"*).
*   **How it works:** 
    1. Normalizes raw text inputs (lowercasing, punctuation stripping).
    2. Runs a custom-trained **spaCy Named Entity Recognition (NER)** sequence-labeling pipeline to identify geographic tokens.
    3. Matches extracted depth entities (e.g., *tuhod*, *dibdib*) against a rule-based dictionary to map Taglish colloquialisms to standardized severity metrics (Low, Moderate, High, Extreme).
    4. Automatically scores the parsing reliability with two metrics: `location_confidence` and `severity_confidence`.
*   **Access & Roles:** Public users can submit reports; DRRM officers review and validate the outputs.
*   **Related Components:**
    *   **Frontend:** [FloodReportPanel.tsx](file:///e:/Files/Documents/GitHub/LANES/frontend/src/features/hazards/FloodReportPanel.tsx) (for manual text submission and incident reporting).
    *   **Backend:** [reports.py](file:///e:/Files/Documents/GitHub/LANES/backend/app/api/v1/endpoints/reports.py) endpoint (`POST /api/v1/reports`), `app.services.spacy` pipelines.

---

### 2. Structured Flood Incident Survey (3NF Normalized)
*   **Purpose:** Collects precise, structured data about flood scenarios directly from users on the ground, bypassing NLP for explicit facts.
*   **What it does:** Allows a user to rapidly fill out a categorical survey (e.g., Hidden hazards, Passable vehicle types, Receding status) via a streamlined inline panel interface.
*   **How it works:** 
    1. Replaces standard text fields with responsive UI checkboxes and toggle groups within the `FloodReportPanel`.
    2. Payload is sent alongside the standard incident report data.
    3. The backend maps the survey to a dedicated `flood_report_surveys` table holding a strict foreign key to the root report, ensuring full Third Normal Form (3NF) relational integrity.
*   **Access & Roles:** Public users can submit surveys; DRRM officers review them.
*   **Related Components:**
    *   **Frontend:** [FloodReportPanel.tsx](file:///e:/Files/Documents/GitHub/LANES/frontend/src/features/hazards/FloodReportPanel.tsx) (survey state & UI).
    *   **Backend:** [report.py](file:///e:/Files/Documents/GitHub/LANES/backend/app/models/report.py) (SQLAlchemy schemas), `POST /api/v1/reports` endpoint.

---

### 3. Identity-First Citizen Onboarding & Zero-Click OTP Verification
*   **Purpose:** Provides a seamless, identity-first registration wizard with secure email validation, spam resistance, network-latency resilience, and instant verification.
*   **What it does:** Breaks registration into an Identity-First sequence (`Email -> OTP -> Account Credentials -> Personal Profile -> Demographic Address`). Delivers zero-click automatic verification as soon as 6 digits are entered, while managing progressive resend cooldowns and sliding grace windows.
*   **How it works:**
    1. **Identity-First Stage:** User submits their email address first. The backend verifies uniqueness and dispatches a 6-digit OTP via the Brevo REST API using a crisp, zero-attachment CDN brand seal.
    2. **Progressive Rate Limiting & Cooldowns:** Enforces progressive resend cooldown tiers (**1 minute** -> **3 minutes** -> **5 minutes**) to prevent gateway spamming while providing ample time to check inbox/spam folders.
    3. **Sliding Grace Window for Network Latency:** Retains up to **3 unexpired active codes** (5-minute lifetime) per session. If a delayed email arrives after a resend, entering the older code still succeeds. All codes are purged immediately upon verification.
    4. **Zero-Click Verification & Attempt Throttling:** 6 distinct pin boxes auto-advance, handle paste events, and automatically fire verification when the 6th digit is entered. Wrong attempts auto-clear and refocus with remaining attempt warnings; exceeding 5 failed attempts locks verification for 5 minutes.
    5. **Demographic & Address Profile:** Upon verification, the user sets their username/password, completes their profile, and selects Province -> City -> Barangay using live PSGC API data.
    6. **Seamless Auto-Login:** Successfully creating the account automatically logs the user in and redirects to the landing page with zero manual login redirects.
*   **Access & Roles:** Public users.
*   **Related Components:**
    *   **Frontend:** [RegisterForm.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/auth/components/RegisterForm.tsx), [DatePicker.tsx](file:///d:/Documents/Github/LANES/frontend/src/shared/ui/DatePicker.tsx), [LocationPickerModal.tsx](file:///d:/Documents/Github/LANES/frontend/src/features/auth/components/LocationPickerModal.tsx).
    *   **Backend:** [auth.py](file:///d:/Documents/Github/LANES/backend/app/api/v1/endpoints/auth.py), [auth_service.py](file:///d:/Documents/Github/LANES/backend/app/services/auth_service.py), [crud/otp.py](file:///d:/Documents/Github/LANES/backend/app/crud/otp.py), [email_service.py](file:///d:/Documents/Github/LANES/backend/app/services/email_service.py).

---

### 2. Flood-Adaptive Route Calculation & Rerouting
*   **Purpose:** Ensures commuter safety by dynamically routing vehicles around active flood hazards.
*   **What it does:** Calculates optimal navigation paths between origin and destination coordinates, ensuring that any road segments intersecting active flood zones are bypassed.
*   **How it works:**
    1. When a user requests a route, the backend fetches all active avoidance polygons (Red, Orange, Yellow) from the PostGIS database.
    2. The routing service queries the local **Valhalla** engine using a dynamically built HTTP request.
    3. The avoidance polygons are passed natively into Valhalla's `avoid_polygons` parameter.
    4. The routing algorithm mathematically treats the polygons as impassable barriers, generating a safe alternative detour route. If trapped, it falls back to allowing Yellow zones, then Orange zones.
    5. The commuter can toggle "Ignore Floods" to compare the safe path against the default flooded route.
*   **Access & Roles:** Open to all public commuters.
*   **Related Components:**
    *   **Frontend:** [RoutePanel.tsx](file:///e:/Files/Documents/GitHub/LANES/frontend/src/features/routing/RoutePanel.tsx) (input panels, turn-by-turn lists, flood toggle), [MapCanvas.tsx](file:///e:/Files/Documents/GitHub/LANES/frontend/src/features/map/MapCanvas.tsx).
    *   **Backend:** [reports.py](file:///e:/Files/Documents/GitHub/LANES/backend/app/api/v1/endpoints/reports.py) router (`POST /api/v1/reports/route`), [routing.py](file:///e:/Files/Documents/GitHub/LANES/backend/app/services/routing.py) service (`calculate_flood_safe_route`).

---

### 3. Dynamic AI Weather Insights
*   **Purpose:** Helps everyday users understand raw meteorological data (PoP%, mm/h) by converting it into simple, educational interpretations.
*   **What it does:** Provides a completely automated, on-demand AI explanation of the next 4 hours of weather data via a dedicated modal on the homepage.
*   **How it works:**
    1. The frontend parses the 12-hour forecast array from Open-Meteo.
    2. The user clicks "Generate AI Insights" in the Weather Modal.
    3. The backend compiles the first 4 hours of data into a highly constrained system prompt, commanding the AI to act as a "teacher."
    4. The server securely calls the **OpenRouter API** (`openrouter/free` model routing) to avoid costs while maintaining dynamic NLP generation.
    5. The AI returns a strict JSON object containing short interpretations of both Storm Risk and Environmental Conditions, which is rendered dynamically in the UI.
*   **Access & Roles:** Public users.
*   **Related Components:**
    *   **Frontend:** [WeatherInsightsModal.tsx](file:///e:/Files/Documents/GitHub/LANES/frontend/src/features/landing/WeatherInsightsModal.tsx).
    *   **Backend:** [weather.py](file:///e:/Files/Documents/GitHub/LANES/backend/app/api/v1/endpoints/weather.py) (`POST /api/v1/weather/insights`).

---

### 3. Height-Aware Rerouting (Dynamic Vehicle Profiles)
*   **Purpose:** Customizes detour calculations based on vehicle clearance constraints (e.g., Pedestrian, Motorcycle, Sedan, SUV).
*   **What it does:** Allows commuters to select their vehicle profile and intelligently decides which flood polygons to avoid. High-clearance vehicles (SUVs) can safely cross knee-deep water (Yellow/Orange) but incur a 35% safety penalty to account for hidden hazards, while low-clearance vehicles (Sedans) are completely blocked.
*   **How it works:**
    1. Commuters select their vehicle profile in the route panel.
    2. The backend dynamically builds avoidance polygons by analyzing the `blocked` vs `penalized` zones based on the specific vehicle type.
    3. The 8 MMDA visual severity options (Gutter, Half-Knee, Tire, etc.) are mapped to exact routing logic penalties.
*   **Access & Roles:** Open to all public commuters.
*   **Related Components:**
    *   **Frontend:** [RoutePanel.tsx](file:///e:/Files/Documents/GitHub/LANES/frontend/src/features/routing/RoutePanel.tsx), [routingOptions.ts](file:///e:/Files/Documents/GitHub/LANES/frontend/src/features/routing/routingOptions.ts).
    *   **Backend:** [reports.py](file:///e:/Files/Documents/GitHub/LANES/backend/app/api/v1/endpoints/reports.py) router, [routing.py](file:///e:/Files/Documents/GitHub/LANES/backend/app/services/routing.py) service (`calculate_flood_safe_route`).

---

### 4. Queue-Based Admin Moderation & Approval Workflow
*   **Purpose:** Implements a "human-in-the-loop" validation workflow to prevent automated NLP ingestion errors or mapping hallucinations from misdirecting drivers.
*   **What it does:** Queues all raw NLP-parsed flood reports into a staging feed, allowing authorized local disaster risk managers to inspect, adjust, approve, or discard reports before public broadcast.
*   **How it works:**
    1. Newly parsed reports are inserted with a status of `pending`.
    2. DRRM operators review the reports, verify the geolocations, and click "Approve".
    3. Upon approval, PostGIS automatically calculates a spatial buffer (using `ST_Buffer` with a 50m to 200m radius depending on whether the asset is a Point or LineString) around the coordinate.
    4. This buffer is saved to the `flood_avoidance_zones` table as an active polygon, which immediately updates Valhalla route requests.
    5. Discarded reports are marked as `rejected`.
*   **Access & Roles:** Restricted to `admin` / `drrm` roles.
*   **Related Components:**
    *   **Frontend:** [ReportsPage.tsx](file:///e:/Files/Documents/GitHub/LANES/frontend/src/features/admin/ReportsPage.tsx) (interactive queue cards, map coordinates auditor).
    *   **Backend:** [admin.py](file:///e:/Files/Documents/GitHub/LANES/backend/app/api/v1/endpoints/admin.py) endpoints (`/reports/pending`, `/reports/{report_id}/approve`, `/reports/{report_id}/reject`).

---

### 4. Interactive Spatial Map Visualization (WebGL Tiles & Autocomplete)
*   **Purpose:** Renders real-time hazard layers, detour vectors, and geocoding on a performant mobile canvas.
*   **What it does:** Displays an interactive street map overlaying color-coded pins (White, Yellow, Orange, Red) for flood heights, outlines avoidance zone shapes, and handles address geocoding search.
*   **How it works:**
    1. Utilizes **MapLibre GL JS** to render vector maps on the client side using WebGL.
    2. Feeds OpenStreetMap tiles for zero-cost, self-hosted base imagery.
    3. Integrates the **Komoot Photon API** (`photon.komoot.io`) for geocoding search, localized and scored specifically for Pasig City bounds to provide relevant location autocomplete results.
    4. Renders geo-coordinates as visual icons and polygon vectors in real time.
*   **Access & Roles:** Public commuters and system administrators.
*   **Related Components:**
    *   **Frontend:** [MapCanvas.tsx](file:///e:/Files/Documents/GitHub/LANES/frontend/src/features/map/MapCanvas.tsx), [MapContext.tsx](file:///e:/Files/Documents/GitHub/LANES/frontend/src/features/map/MapContext.tsx), [geocodingApi.ts](file:///e:/Files/Documents/GitHub/LANES/frontend/src/features/geocoding/geocodingApi.ts).

---

### 5. Real-Time Event Signaling (Server-Sent Events)
*   **Purpose:** Ensures instant, reactive visual updates across commuter and admin maps without forcing manual browser refreshes.
*   **What it does:** Signals active database events (approvals, deactivations, database cleans) from the backend directly to active frontend sessions.
*   **How it works:**
    1. The React app connects to a native `EventSource` on the FastAPI server at `/api/v1/sse/stream`.
    2. The backend maintains an active connection manager mapping open client streams.
    3. When an admin approves a report or deactivates a zone, the server broadcasts an event (e.g. `report_approved`).
    4. The frontend intercepts the payload and automatically invalidates the React Query cache, triggering a silent background refetch of map layers.
*   **Access & Roles:** Public clients and administrative dashboards.
*   **Related Components:**
    *   **Frontend:** [useSSE.ts](file:///e:/Files/Documents/GitHub/LANES/frontend/src/hooks/useSSE.ts), `providers.tsx`.
    *   **Backend:** [sse.py](file:///e:/Files/Documents/GitHub/LANES/backend/app/api/v1/endpoints/sse.py), `app.core.sse`.

---

### 6. Role-Based Access Control (RBAC) & JWT Security
*   **Purpose:** Secures sensitive admin interfaces, settings, and database endpoints from public modifications.
*   **What it does:** Separates authorization levels between `commuters` and `admin` / `drrm` profiles, enforcing login parameters and auditing.
*   **How it works:**
    1. Hashes passwords using **bcrypt** with adaptive salt rounds before database storage.
    2. Issues signed **JSON Web Tokens (JWT)** via `python-jose` containing the user ID and role during login.
    3. FastAPI route handlers intercept calls using dependency injection (`get_current_active_admin`) to validate JWT signatures and enforce permissions.
*   **Access & Roles:** Registration is open to all; admin pages require role-checks.
*   **Related Components:**
    *   **Frontend:** [LoginForm.tsx](file:///e:/Files/Documents/GitHub/LANES/frontend/src/features/auth/LoginForm.tsx), [SignupForm.tsx](file:///e:/Files/Documents/GitHub/LANES/frontend/src/features/auth/SignupForm.tsx).
    *   **Backend:** [auth.py](file:///e:/Files/Documents/GitHub/LANES/backend/app/api/v1/endpoints/auth.py), [users.py](file:///e:/Files/Documents/GitHub/LANES/backend/app/api/v1/endpoints/users.py), [deps.py](file:///e:/Files/Documents/GitHub/LANES/backend/app/api/deps.py).

---

### 7. Offline Resiliency & PWA Capabilities
*   **Purpose:** Ensures mobility tool usability when mobile cellular networks degrade during severe weather.
*   **What it does:** Caches static assets, intercepts network failures, and alerts commuters when they go offline.
*   **How it works:**
    1. Operates as a Progressive Web App using `@ducanh2912/next-pwa` service workers.
    2. Caches maps, styles, and dashboard templates locally in browser storage.
    3. Uses `idb-keyval` (IndexedDB utility) to store basic state configuration variables.
    4. Triggers an offline banner warning when the browser's `navigator.onLine` state toggles off.
*   **Access & Roles:** Public commuters.
*   **Related Components:**
    *   **Frontend:** [OfflineBanner.tsx](file:///e:/Files/Documents/GitHub/LANES/frontend/src/features/offline/OfflineBanner.tsx), `frontend/package.json`.

---

### 8. System Audit Logging & Trail
*   **Purpose:** Maintains organizational transparency and logs all administrative updates to prevent accidental or malicious map changes.
*   **What it does:** Logs admin actions (report approval, rejection, user deletion, backups, data clears, configurations) to a central ledger.
*   **How it works:**
    1. Every admin-restricted route wraps its database transaction with an `audit_log` write operation.
    2. Saves details including `admin_id`, `action_type`, `target_table`, `metadata_json` (containing changes details), `ip_address`, and a UTC timestamp.
*   **Access & Roles:** Admins can view this ledger.
*   **Related Components:**
    *   **Frontend:** [AuditTrailPage.tsx](file:///e:/Files/Documents/GitHub/LANES/frontend/src/features/admin/AuditTrailPage.tsx).
    *   **Backend:** [admin.py](file:///e:/Files/Documents/GitHub/LANES/backend/app/api/v1/endpoints/admin.py) (`/audit-logs`), [audit.py](file:///e:/Files/Documents/GitHub/LANES/backend/app/models/audit.py) schema & models.

---

### 9. Database Backup, Exports & Cleanup Management
*   **Purpose:** Protects database integrity, enables archival, and exports research data.
*   **What it does:** Creates and restores SQL dumps of the PostgreSQL/PostGIS database, exports reports/avoidance zones as CSV or JSON, and implements records cleaning.
*   **How it works:**
    1. Exports query database tables using standard Python `csv` and `json` libraries.
    2. Backup calls trigger shell processes (`docker exec` executing `pg_dump` and `pg_restore`) to compress or import dump files.
    3. Cleanup sweeps database tables, purging old flood incident logs and zones older than user-specified date ranges.
*   **Access & Roles:** Limited to admins.
*   **Related Components:**
    *   **Frontend:** [DataManagementPage.tsx](file:///e:/Files/Documents/GitHub/LANES/frontend/src/features/admin/DataManagementPage.tsx).
    *   **Backend:** [data.py](file:///e:/Files/Documents/GitHub/LANES/backend/app/api/v1/endpoints/data.py), [data_service.py](file:///e:/Files/Documents/GitHub/LANES/backend/app/services/data_service.py).

---

### 10. Cloudinary Photo Evidence Upload & Edge Compression
*   **Purpose:** Allows commuters to submit visual proof of flood hazards and community posts, while minimizing server memory overhead and saving mobile bandwidth.
*   **What it does:** Uploads user-provided media alongside the text report, securely hosts it, and displays it in the feed. Large files are aggressively optimized.
*   **How it works:**
    1. The frontend uses `browser-image-compression` to resize images (max 1200px) and converts them to `WebP` before network transmission, vastly reducing mobile data costs.
    2. A strict 20MB payload limit is enforced on the frontend UI and the FastAPI backend (via `Content-Length` interception) to prevent malicious massive uploads.
    3. The FastAPI backend streams the file to **Cloudinary** via their Python SDK.
    4. Cloudinary automatically transcodes the delivery format (`f_auto`) and quality (`q_auto`), serving optimal formats like AV1 or WebP based on the viewer's browser.
    5. The resulting CDN URL is saved as `image_url` or `media_urls` in the PostgreSQL database.
*   **Access & Roles:** Public users can upload; administrators and peers can view.
*   **Related Components:**
    *   **Frontend:** [FloodReportPanel.tsx](file:///e:/Files/Documents/GitHub/LANES/frontend/src/features/hazards/FloodReportPanel.tsx), [CreatePostModal.tsx](file:///e:/Files/Documents/GitHub/LANES/frontend/src/features/feed/CreatePostModal.tsx).
    *   **Backend:** [cloudinary_service.py](file:///e:/Files/Documents/GitHub/LANES/backend/app/services/cloudinary_service.py), [reports.py](file:///e:/Files/Documents/GitHub/LANES/backend/app/api/v1/endpoints/reports.py), [posts.py](file:///e:/Files/Documents/GitHub/LANES/backend/app/api/v1/endpoints/posts.py).

---

### 11. Archive Center (Soft Deletes)
*   **Purpose:** Centralizes the management of suspended user accounts, rejected flood reports, and deactivated zones without destroying relational data integrity.
*   **What it does:** Uses `deleted_at` timestamps to hide records from active queries while retaining them for historical analytics and administrative audit trails.
*   **How it works:**
    1. Instead of a SQL `DELETE`, a record is updated with `deleted_at = NOW()`.
    2. Active database queries filter with `WHERE deleted_at IS NULL`.
    3. The Archive Center provides a dual-pane or vertical sidebar interface to browse these hidden records.
*   **Access & Roles:** Restricted to `admin` / `drrm` roles.
*   **Related Components:**
    *   **Frontend:** `src/features/archive/` (Components), `src/app/(admin)/archive/page.tsx`.

---

### 12. Community Feed & Social Validation
*   **Purpose:** Provides commuters with localized, real-time crowdsourced updates, general disaster discussion, and enables peer validation of flood reports.
*   **What it does:** Displays a 3-column feed containing shared `FloodReport`s and general `CommunityPost`s. Enables highly interactive community discussions via a rich, threaded comments section supporting quote replies, user mentions, upvote/downvote sorting, auto-collapsing low-score replies, and admin pinning.
*   **How it works:**
    1. Fetches feed items using PostGIS `<->` operators for distance-based sorting or chronological ordering.
    2. Users interact via upvote/downvote and comments, which updates the `post_interactions` and `comments` tables.
    3. The Comment Engine structures threads recursively in the backend, supporting infinite nesting via adjacency lists (`parent_comment_id`).
    4. The frontend utilizes React `useRef` based focus-within compound input forms to safely manage complex multi-input layouts without triggering React re-renders or cursor jumping.
    5. Interaction events (Likes, Mentions, Replies) trigger real-time `Notification` rows stored in the database for the post author, accessible via the global Bell icon.
*   **Access & Roles:** Public users can post and reply. Admins and Authors can Pin comments.
*   **Related Components:**
    *   **Frontend:** `src/features/feed/` (Feed components, PostCard, tabs), `src/features/notifications/` (NotificationDropdown), `src/app/(feed)/feed/page.tsx`.

---

### 13. Persistent Post Drafting (IndexedDB)
*   **Purpose:** Prevents accidental data loss when users navigate away from the post creation modal or lose connection.
*   **What it does:** Seamlessly saves typed text and massive binary file selections in the browser's persistent storage, restoring them when the user returns.
*   **How it works:**
    1. Text content is saved to `sessionStorage`.
    2. Large binary blobs (images/videos) exceed `sessionStorage` space quotas, so they are serialized into the browser's native **IndexedDB** using `idb-keyval`.
    3. When the `CreatePostModal` mounts, a StrictMode-safe `useEffect` hook reconstructs the binary blobs back into JavaScript `File` objects and generates new `URL.createObjectURL` previews.
*   **Access & Roles:** Public commuters.
*   **Related Components:**
    *   **Frontend:** [CreatePostModal.tsx](file:///e:/Files/Documents/GitHub/LANES/frontend/src/features/feed/CreatePostModal.tsx) (Draft logic, IDB restoration).

---

## 🔮 Future Features

### 1. User-Submitted Image Depth Classifier (Computer Vision AI)
*   **Purpose:** Automates flood severity validation via crowdsourced visual proof.
*   **Why it is needed:** Text descriptions are often subjective or exaggerated. While we currently accept photo evidence (via Cloudinary), human admins must still verify them. An AI classifier will automate the objective verification of street conditions.
*   **Expected functionality:**
    *   Commuters upload a photo of the road flood (already implemented).
    *   A deep learning model (e.g., CNN or YOLO) analyzes the uploaded image URL from Cloudinary.
    *   It detects key anchor references (submerged wheels, fire hydrants, doors) to classify water height.
    *   Populates the moderation queue with the visual estimation of severity.
*   **How it will integrate:**
    *   Establish a secondary Python ML worker (or use FastAPI background tasks) running a PyTorch pipeline to process image URLs.
*   **Dependencies:** Host machine GPU acceleration, a trained reference dataset of street-level urban flooding photos.

---

### 3. Automated Social Media Scraper Service (X/Twitter and Facebook APIs)
*   **Purpose:** Dramatically speeds up data ingestion by eliminating reliance on manual reports.
*   **Why it is needed:** During typhoons, emergency data updates are shared at high velocity across social media platforms like X (Twitter) and Facebook. An automated crawler will capture these inputs in real time.
*   **Expected functionality:**
    *   A celery-based background worker continuously queries X and Facebook search endpoints for keyword patterns (e.g., "baha Pasig", "Caruncho Ave baha").
    *   Parsed matches are run through the spaCy NER pipeline and loaded directly into the admin moderation queue.
*   **How it will integrate:**
    *   Add a new scraper microservice to the project stack.
    *   Pipes scraped JSON outputs into the backend `/api/v1/reports` API.
*   **Dependencies:** Developer API keys from Twitter/X and Meta Platforms.

---

### 4. Bilingual Speech-to-Text Voice Reporting
*   **Purpose:** Enables motorists in transit to report active hazards hands-free.
*   **Why it is needed:** Typist reporting is dangerous for active drivers. Letting users dictate short reports keeps eyes on the road during severe storms.
*   **Expected functionality:**
    *   Commuters tap a microphone button, record a Taglish description (e.g., *"Baha rito sa San Joaquin, lagpas bewang na"*), and submit.
    *   The system transcribes the speech and pipes the raw text into spaCy.
*   **How it will integrate:**
    *   Integrate browser MediaRecorder APIs in [FloodReportPanel.tsx](file:///e:/Files/Documents/GitHub/LANES/frontend/src/features/hazards/FloodReportPanel.tsx).
    *   Create a backend utility using a bilingual transcription framework (e.g., OpenAI Whisper).
*   **Dependencies:** Speech-to-Text model pipeline, micro-permissions access in browser clients.

---

### 5. Turn-by-Turn Voice Navigation (Text-to-Speech)
*   **Purpose:** Prevents driver distractions by dictating detour directions audibly.
*   **Why it is needed:** Drivers cannot safely read map paths or turn-by-turn lists while navigating heavy rain and storm conditions.
*   **Expected functionality:**
    *   The PWA speaks directions aloud (e.g., *"In 200 meters, turn left to bypass the flooded street ahead"*).
*   **How it will integrate:**
    *   Hook into the HTML5 **Web Speech API (`SpeechSynthesis`)** inside [RoutePanel.tsx](file:///e:/Files/Documents/GitHub/LANES/frontend/src/features/routing/RoutePanel.tsx).
    *   Trigger directions audio prompts based on geolocation tracking updates relative to the Valhalla path coordinate array.
*   **Dependencies:** Secure HTTPS deployment (for geolocation sensor permissions).

---

### 6. IoT Telemetric Sensor Nodes Integration
*   **Purpose:** Automatically registers baseline hazard metrics at high-risk municipal points.
*   **Why it is needed:** Certain low-lying streets (e.g., Pasig Mega Market perimeter) flood during every minor rainfall event. Real-time telemetry ensures instant database updates.
*   **Expected functionality:**
    *   Ultrasonic water-level sensors measure current road water levels.
    *   The sensor microcontrollers transmit depth values directly to the spatial database.
    *   Avoidance zones are automatically updated without manual administrator intervention.
*   **How it will integrate:**
    *   Build a dedicated backend route handler `POST /api/v1/telemetry/report` restricted to authenticated IoT gateway tokens.
    *   Pipes telemetric depth metrics directly into the PostGIS database.
*   **Dependencies:** Physical ESP32 microcontrollers, ultrasonic sensors, and cellular/LoRa transmitters.
