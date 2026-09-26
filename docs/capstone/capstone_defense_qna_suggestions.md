# LANES Capstone Defense Q&A and Suggestions

This document contains potential questions from various defense panelists and target users, complete with answers directly sourced from your documentation. It also provides specific suggestions for improving the documentation where gaps or inconsistencies exist.

---

## 🎙️ Part 1: Potential Panelist Questions & Answers

### 👨‍🏫 Panelist 1: The IT Professor / Doctorate (Focus: Methodology & Research Justification)

**Q1: Why did you choose to use Natural Language Processing (NLP) over physical IoT water sensors, considering sensors are highly accurate?**
* **Answer:** While IoT sensors like ultrasonic arrays are highly accurate (as proven by Abana et al., 2019 and FLONAV), they present substantial financial and scalability constraints for a local government unit like Pasig City. NLP allows us to bypass physical hardware costs by mining existing public textual data and transforming it into spatial intelligence, matching routing performance at a significantly lower operational cost.
* *(Source: 1.2 Review of Related Literature - Flood Evacuation Routing and Spatial Network Modeling)*

**Q2: How did you determine the size of your training dataset for the NER model, and why is that number sufficient?**
* **Answer:** We targeted 300 to 500 annotated text samples. Because our model needs to recognize multiple entity types (street names, landmarks) across a bilingual Taglish format, a smaller dataset (like 50-100) would lack the necessary variation, resulting in low precision and recall. 
* *(Source: 2.2.2 Algorithm - Bilingual Named Entity Recognition and Severity Mapping)*

**Q3: How are you evaluating the success and quality of your platform?**
* **Answer:** We are using a dual-evaluation approach. For the NLP extraction, we use standard ML metrics (Precision, Recall, F1-Score). For the software platform itself, we use the ISO/IEC 25010 Software Product Quality Model, specifically testing Functional Suitability, Performance Efficiency, Usability (using the System Usability Scale), and Reliability via user assessment questionnaires with commuters, DRRM personnel, and IT experts.
* *(Source: 2.2 Research Design)*

---

### 💻 Panelist 2: The Software Engineer / Full Stack Developer (Focus: Architecture)

**Q4: Can you explain why you chose a decoupled 3-tier architecture instead of a traditional monolithic MVC application?**
* **Answer:** The decoupled architecture isolates our client-side map rendering (Next.js/MapLibre) from the highly resource-intensive background tasks. By separating the Presentation tier from the Application Logic tier (FastAPI/Valhalla), the server can dedicate its processing power to NLP tokenization and spatial routing calculations without bogging down the user interface.
* *(Source: DESIGN.md - 1. High-Level Architecture & 2.2.1 Architectural Framework)*

**Q5: During a severe typhoon, many users will be submitting and validating reports. How do you ensure the frontend maps update in real-time without the user needing to refresh the page?**
* **Answer:** We implemented a native WebSocket connection between our React frontend and FastAPI backend. When the DRRM admin approves a report, the backend broadcasts a WebSocket event. The frontend intercepts this, invalidates the TanStack React Query cache, and triggers a silent background refetch of the map layers.
* *(Source: Feature Reference - 5. Real-Time Event Signaling)*

---

### 🗄️ Panelist 3: The API / Database Specialist (Focus: Data Integrity & Routing Logic)

**Q6: Your system accepts highly variable and unstructured text data. How do you maintain database normalization under these conditions?**
* **Answer:** We strictly enforce Third Normal Form (3NF). Unstructured text is parsed and separated into structured relational tables (e.g., `flood_reports` for the text, `flood_avoidance_zones` for the spatial polygon). For highly variable scraper metadata, we utilize PostgreSQL's native `JSONB` columns to maintain structural flexibility without violating relational constraints.
* *(Source: DESIGN.md - 2. Core Database Schema & Relations)*

**Q7: Exactly how does the system turn a text report into a blocked road on the map? Explain the algorithmic flow.**
* **Answer:** First, the NER model extracts the street name and severity. Second, the OSM Geocoder converts the street name to a Lat/Long coordinate. Third, upon admin approval, PostGIS uses `ST_Buffer` to draw a 50-meter polygon around that coordinate. Finally, the routing engine (Valhalla) intersects the commuter's path with that polygon and dynamically updates the road's cost matrix (edge weight) to Infinity (∞), forcing a detour.
* *(Source: 2.2.2 Algorithm - Graph Network Routing and Cost Matrix Optimization)*

**Q8: How do you secure administrative access and ensure passwords are safe?**
* **Answer:** We do not store plaintext passwords; they are hashed using the **bcrypt** algorithm with an adaptive salt. For session security, we issue signed JSON Web Tokens (JWT) via `python-jose`. FastAPI routes intercept these tokens to validate signatures and enforce Role-Based Access Control (RBAC) before granting admin privileges.
* *(Source: DESIGN.md - 6. Security & Access Architecture)*

---

### 🎨 Panelist 4: The Graphic Designer / UI-UX Expert (Focus: Usability)

**Q9: Disaster applications are often used during highly stressful situations. What was your design philosophy to ensure the app is usable during an emergency?**
* **Answer:** We utilized an "Illustrated Minimalist Spatial System" philosophy. The map is the primary source of truth, and we explicitly avoid decorative elements or heavy animations that cause visual noise. The interface is distraction-free, ensuring every screen can be read within 3 seconds, focusing entirely on "Clarity Under Stress."
* *(Source: DESIGN.md - 4. UI Philosophy: Illustrated Minimalist Spatial System)*

**Q10: How do you visually communicate the danger level of a flooded street to a commuter who is driving?**
* **Answer:** We translate depth phrases into a standardized four-tier visual map overlay: White (passable/ankle-deep), Yellow (moderate/knee-deep), Orange (high/waist-deep), and Red (extreme/submerged). This immediate color-coding allows users to instantly gauge risk without reading text.
* *(Source: 1.5 Scope and Limitation of the Study)*

---

### 🚶‍♂️ Panelist 5: The Regular Person / Commuter (Focus: Practical Usage)

**Q11: Do I need to download this app from the Apple App Store or Google Play Store to use it during a storm?**
* **Answer:** No, you don't need to visit an app store. LANES is built as a Progressive Web Application (PWA). You can access it instantly via your web browser, which saves phone storage, uses less data, and allows us to push critical updates immediately without waiting for app store approvals.
* *(Source: 1.5 Scope and Limitation of the Study - Cross-Platform Delivery & Feature Reference - 7. Offline Resiliency & PWA Capabilities)*

**Q12: What happens if someone submits a fake flood report as a prank? Will it ruin my route?**
* **Answer:** No, it will not affect your route. The system has a built-in safety measure: the Admin Moderation Queue. All incoming reports are held in a pending status. They are not broadcast to the public map, and they do not affect the routing engine, until a verified DRRM administrator reviews and explicitly clicks "Approve."
* *(Source: 2.2.2 Algorithm - Spatial Geocoding and PostGIS Geometric Buffering & Feature Reference - 4. Queue-Based Admin Moderation)*

---

### 🚨 Panelist 6: The DRRMO Chief / Head of Disaster Risk Reduction (Focus: Civic Integration & Management)

**Q13: My team is already overwhelmed during a typhoon. How does this system make our job easier instead of giving us more work?**
* **Answer:** Currently, your team has to manually sift through thousands of informal "Taglish" social media posts to figure out where the floods are. LANES automates the hardest part. The NLP engine instantly reads the text, extracts the exact street name, and calculates the severity for you. It lines them up in a clean dashboard, so all your team has to do is verify and click "Approve" to instantly update the map for the entire city, drastically streamlining your municipal resource deployment.
* *(Source: 1.3 Significance of the Study - The City of Pasig and Local DRRM Units)*

**Q14: For accountability, can we track the history of approved reports and see which of my officers made map changes?**
* **Answer:** Yes, absolute transparency is built into the system. Every time an officer approves a report, rejects a submission, or deactivates a hazard zone, the action is securely recorded in the `audit_logs` database table. This provides a full historical ledger of who did what and when, ensuring complete administrative accountability.
* *(Source: DESIGN.md - 9. Audit Logging & Moderation Logs)*

---

## 📝 Part 2: Suggestions for Documentation Improvement

While analyzing your manuscript (`LANES_documentation.md`), a few areas could be strengthened for your defense:

1. **Provide an Example of the Raw Taglish Dataset:**
   * **The Gap:** In Section 2.4 (Data Collection Methods), you mentioned gathering a "curated test dataset of 300 to 500 simulated and real-world flood-related text samples". Panelists often ask to see what this raw data actually looks like.
   * **Suggestion:** Add a small table or appendix in your manuscript showing 3-5 examples of these Taglish texts alongside their expected NLP extraction (e.g., Raw: "lagpas tao na sa rosario", Extracted Location: "rosario", Extracted Severity: "Red").

2. **Justify the 80% Benchmark for NLP Metrics:**
   * **The Gap:** In Section 2.5 (Data Analysis Procedures), you state: "A precision and recall target of 80% or higher will be considered acceptable". A panelist with an IT or Data Science background will likely ask, "Why 80%? Why not 90%?"
   * **Suggestion:** Explicitly state in the document *why* 80% was chosen. You can mention that parsing informal bilingual text (Taglish) with heavy conversational noise makes a 90%+ score extremely difficult, and 80% is the accepted baseline in crisis informatics studies (you can cite Imran et al., 2018 from your references here).

3. **Clarify Data Retention for Privacy:**
   * **The Gap:** In Section 2.6 (Ethical Considerations), you have a strong paragraph on the Data Privacy Act of 2012, mentioning that location data will be anonymized. However, privacy laws usually require a specific retention policy.
   * **Suggestion:** Add a single sentence stating how long the raw location data from commuters will be kept before deletion (e.g., "All raw user interaction logs will be permanently deleted 30 days after the conclusion of the evaluation period to comply with data retention limits").
