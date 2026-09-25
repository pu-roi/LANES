# LANES Capstone Defense Reviewer & Comprehensive Guide

This document is a detailed study guide covering the core concepts, methodologies, and architectural decisions of LANES (Localised Alternative Navigation for Environs under Submersion). Use this guide to deeply understand the "why" and "how" of your system, rather than just memorizing keywords.

---

## 📖 CHAPTER 1: The Problem and its Background

### 1. The Core Problem and Justification
* **The Reality of Pasig City:** Pasig City is highly urbanized and frequently experiences severe localized flooding due to its proximity to interconnected waterways and the Pasig River. This paralyzes urban mobility, delays emergency response, and traps commuters.
* **The Technological Gap:** Currently, most road users rely on conventional navigation apps (like Google Maps or Waze). These apps are excellent at monitoring traffic congestion, but they completely fail to map active, real-time flooded roads. Furthermore, crucial updates about flooded streets are fragmented—scattered across local news, municipal announcements, and informal "Taglish" social media posts. Commuters have no way to compile this scattered data into a safe driving route quickly.
* **The LANES Solution:** LANES aims to bridge this exact gap. Instead of relying on manual reporting or expensive physical water sensors, LANES uses Natural Language Processing (NLP) to read unstructured bilingual (Taglish) flood reports, extract the exact street names and water depths, and automatically calculate safe alternative routes that bypass these flooded areas.

### 2. Key Literature & Citations (How LANES builds upon past research)
* **UP NOAH (Lagmay et al., 2024):** UP NOAH is the gold standard for hazard mapping in the Philippines, providing 5, 25, and 100-year rain return scenarios. However, *UP NOAH is a static predictive model meant for long-term urban planning.* It does not provide active, turn-by-turn routing for commuters currently driving on the road. LANES fills this tactical gap.
* **Project Agos by Rappler (2014):** This was a pioneer in using crowdsourced digital data via social media to map disasters. While successful for search and rescue dispatch, *Project Agos lacked an automated machine learning pipeline to calculate depth severity* and did not possess a routing engine to calculate detour paths.
* **FLONAV (Betchayda et al., 2025) & Automated Road Flood Warning (Abana et al., 2019):** These local studies successfully demonstrated that dynamic routing around floods is possible. However, *they relied heavily on physical Internet of Things (IoT) hardware*, such as ultrasonic sensors and microcontrollers. Physical hardware is expensive to scale and maintain across an entire city. LANES proves that you can achieve the same dynamic routing using purely software (NLP text extraction) at a fraction of the cost.
* **Alizadeh et al. (2022):** This global study proved that adding user-shared crowdsourced text to official transit models significantly cuts travel time and optimizes route safety.

### 3. Significance of the Study
* **For the City of Pasig & DRRMO:** It provides an automated safety net. Instead of DRRM officers manually reading thousands of Facebook comments or answering scattered phone calls, the system automatically parses the Taglish text into a structured dashboard. The DRRM officer simply clicks "Approve," streamlining municipal resource deployment and emergency dispatch paths.
* **For Commuters and Motorists:** It provides a Progressive Web App (PWA) that acts as a real-time safety layer. It visualizes flood severity using easy-to-understand colors and physically prevents the routing engine from sending vehicles into deep water, preventing engine damage and saving lives.
* **For IT Students & Future Researchers:** It demonstrates how advanced AI (Named Entity Recognition) and spatial databases (PostGIS) can be combined using open-source tools to solve a massive community infrastructure problem without the massive budget required for IoT sensor networks.

### 4. Statement of the Problem (4 Core Questions)
The research fundamentally seeks to answer four questions:
1. How can Natural Language Processing (NLP) extract specific flood information from bilingual reports (English/Tagalog) and convert it into structured location data?
2. How can the system standardize flood severity and visually represent it on a map for users to easily understand?
3. What software architecture is required to take a verified coordinate and turn it into a physical geometric barrier inside a routing engine to force a detour?
4. How can the platform provide a secure validation queue so the DRRMO can verify reports before they are published to commuters?

### 5. Scope and Limitations
* **What the system DOES (Scope):** 
  * Uses a custom NER model to extract street names and depths from Taglish text.
  * Translates depths into a 4-tier visual scale: White (Passable/Ankle), Yellow (Moderate/Knee), Orange (High/Waist), Red (Extreme/Neck).
  * Forces route recalculations using Valhalla to bypass Orange and Red zones.
  * Operates a Queue-Based Admin Dashboard for the DRRM to moderate reports.
  * Runs as a cross-platform Progressive Web App (PWA) accessible via browser.
* **What the system DOES NOT do (Limitations):**
  * It will **not** use any physical IoT hardware, water sensors, or microcontrollers.
  * It will **not** connect directly to private enterprise Twitter/Facebook APIs due to developer paywalls (it relies on accessible feeds, news, and manual submissions).
  * It will **not** feature audio-based turn-by-turn voice navigation or autonomously drive a vehicle.
  * It will **not** use computer vision to analyze photos of floods (it strictly processes text).

---

## ⚙️ CHAPTER 2: Methodology

### 1. Research Design & Evaluation Standard
* **Developmental Research Design:** The study doesn't just collect data; it requires building, deploying, and testing a fully functional software artifact.
* **ISO/IEC 25010 Software Product Quality Model:** This is the international standard used to evaluate the finished system. We are focusing on four specific characteristics:
  1. **Functional Suitability:** Does the NLP accurately extract the right street? Does the routing engine generate the correct detour?
  2. **Performance Efficiency:** How fast does the system respond and recalculate a route when a new flood is approved?
  3. **Usability:** Is the interface clear during an emergency? Evaluated using the System Usability Scale (SUS).
  4. **Reliability:** How consistent is the DRRM validation process without the system crashing?

### 2. The Horizontal 3-Tier Software Architecture
To ensure the system doesn't crash under heavy load during a typhoon, the architecture is strictly decoupled into three layers:
* **Presentation Tier (The Interface):** Built with Next.js and MapLibre GL. This is what the user and admin see. It is completely separated from the heavy database math. It handles the display of the map, the color-coded flood pins, and the route lines.
* **Application Logic Tier (The Brain):** Built with FastAPI and Python. This tier houses the spaCy NLP parser and the Valhalla Routing Engine. When a user submits a Taglish report, this tier breaks down the grammar, extracts the entities, and runs the complex routing algorithms.
* **Data Persistence Tier (The Storage):** Built with PostgreSQL and PostGIS. This is not just a standard database; it is a *spatial* database. It is responsible for geocoding (turning a street name into coordinates) and mathematically drawing 50-meter polygons around those coordinates.

### 3. The Core Algorithm (The 3-Phase Pipeline)
Understanding exactly how a text message becomes a detour is the most critical part of your defense:
1. **Bilingual NLP Extraction & Severity Mapping:**
   * A commuter posts: *"Baha sa Caruncho Ave, lagpas tuhod."*
   * The **Named Entity Recognition (NER) Model** scans the sentence, ignoring the conversational noise, and securely extracts the location token: *"Caruncho Ave"*.
   * Simultaneously, a **Rule-Based Dictionary** catches the phrase *"lagpas tuhod"* and maps it to the standardized "Yellow / Moderate" severity tier.
2. **Spatial Geocoding and PostGIS Geometric Buffering:**
   * The system sends *"Caruncho Ave"* to the OSM Geocoder, which translates it into exact GPS coordinates (e.g., Lat 14.559, Long 121.080).
   * This point goes to the DRRM dashboard. Once the Admin clicks "Approve," the database uses a PostGIS function (`ST_Buffer`) to draw a 50-meter geometric circle/polygon around that exact coordinate. A single point can't block a road, but a 50-meter polygon can.
3. **Graph Network Routing & Cost Matrix Optimization (Valhalla):**
   * The Valhalla routing engine sees the city map as a massive web of Nodes (intersections) and Edges (streets). Normally, the "cost" of traveling an edge is just the distance and speed limit.
   * However, if Valhalla detects that a commuter's path intersects with our newly approved 50-meter flood polygon, the system intercepts the calculation and changes the "cost" of that specific road segment to **Infinity (∞)**.
   * Because the cost is infinity, the pathfinding algorithm treats the street as an impassable brick wall and is forced to calculate an alternative detour around it.

### 4. Software Engineering (SE) Paradigm
* **Agile Software Development:** We use the Agile methodology (working in short, repeating cycles or "sprints") rather than a traditional Waterfall model. 
* **Why Agile?:** The LANES platform relies on highly interconnected pieces. If the NLP model fails to extract the correct street, the PostGIS database will draw a polygon in the wrong city, and the routing engine will calculate a useless detour. Agile allows us to test and perfect the linguistic accuracy of the NLP model continuously before we ever attempt to integrate it with the spatial routing features.
