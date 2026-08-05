# **LANES (Lanes PH) Finalized Tech Stack Blueprint**

### **Project: Flood-Adaptive Route Calculation and Visualization Web Platform**

### **Focus: Web Application (Responsive Desktop & Mobile Browser Layouts)**

This document serves as the official technical stack reference for the LANES platform. It outlines the specific tools, libraries, and frameworks utilized to build a fully self-hosted, free, and highly performant geospatial routing web application.

## **🛠️ Technical Stack Components**

### **1\. Client / Frontend Tier (Responsive Web Interface)**

* **Core Framework:** **Next.js (App Router) & React (TypeScript)**  
  * *Role:* Full-stack React framework providing SSR/SSG capabilities, file-based routing, and building modular, component-driven user interfaces.
* **Styling & Design System:** **Tailwind CSS v4**  
  * *Role:* Utility-first CSS framework for rapidly building premium, highly responsive, and dynamic user interfaces without writing custom CSS.
* **State Management & Fetching:** **TanStack React Query**  
  * *Role:* Asynchronous state management, caching, background synchronization, and automatic revalidation (configured with staleTime: 0 for instant revalidation on mount/navigation).
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
* **Map Base Tiles:** **OpenStreetMap Tiles & Photon API**  
  * *Role:* Rendering completely free street-level basemap imagery and providing rate-limited geocoding autocomplete features with zero commercial licensing caps.
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
* **Rate Limiting & Security:** **slowapi**
  * *Role:* Preventing brute-force attacks and DDoS by applying strict rate limits on authentication and OTP verification endpoints.
* **Authentication Stack:** **JWT, python-jose, & bcrypt**  
  * *Role:* Securing API endpoints via JSON Web Tokens, cryptographically signing tokens, and securely hashing user passwords for role-based access control.
* **Transactional Email & OTP:** **Brevo REST API & httpx**
  * *Role:* Generating async HTTP requests to the Brevo API to securely dispatch 6-digit One-Time Password verification codes to user emails during account onboarding.
* **Image Processing & Storage:** **Cloudinary Python SDK**  
  * *Role:* Managing direct upload, scaling (down to 1024px), and WebP format compression of user-submitted flood evidence photos to a dedicated cloud CDN, ensuring lightweight database records and fast frontend loading.
* **NLP & Information Extraction:** **spaCy**  
  * *Role:* Managing the custom, locally executed Bilingual Named Entity Recognition (NER) pipeline to isolate street-level locations and severity parameters from Taglish text feeds.

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

* **Engine Core:** **Valhalla**  
  * *Role:* Handling high-performance routing calculations natively supporting dynamic polygon avoidance. Replaced OSRM to enable true intelligent detouring around real-time flood polygons while strictly respecting OpenStreetMap traffic laws like one-way streets. Run locally in Docker.
* **Source Graph Data:** **OpenStreetMap Data**  
  * *Role:* Providing the raw baseline network structure (nodes and edges representing physical streets) utilized by the routing engine.

### **5\. Evaluation & Testing Tier (Quality Assurance)**

* **Verification Libraries:** **scikit-learn & seqeval**  
  * *Role:* Running isolated validation scripts to compute linguistic extraction performance metrics (precision, recall, and F1-scores) for the custom NLP model.