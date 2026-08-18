# LANES: Localised Alternative Navigation for Environs under Submersion

LANES is a real-time, flood-adaptive alternative navigation platform designed for commuters in Pasig City. By leveraging crowdsourced community flood reports, real-time admin verification, and interactive map displays, the system dynamically recalculates driving routes to bypass active inundation zones.

---

## 🎓 Capstone Project Context
Developed in partial fulfillment of the requirements for the degree of **Bachelor of Science in Information Technology** at the **College of Computer Studies, Pamantasan ng Lungsod ng Pasig (PLP)**.

**Authors:**
* Bellen, Jace H.
* Cambe, Roi Yvann M.
* Folloso, Chris Nicolai Z.

**Adviser:** Noreen A. Perez, DIT  
**Target Region:** Pasig City, Philippines (localized commuting sectors)

---

## 📖 Documentation Index

* **For AI Agents & Developers:** [`AGENTS.md`](file:///e:/Files/Documents/GitHub/LANES/AGENTS.md) contains all collaboration protocols, operational boundaries, and coding standards. **AI agents must consult this file for interaction rules.**
* **For System Architecture:** [`DESIGN.md`](file:///e:/Files/Documents/GitHub/LANES/DESIGN.md) serves as the single source of truth for technical design, database schemas, processing flows, and non-functional requirements.

---

## 🚀 Local Development Setup

### Prerequisites
* **Git** (For cloning the repository)
* **Node.js** (v18 or higher)
* **Python** (v3.11 or v3.12)
* **Docker Desktop** (For running the local PostGIS spatial database and Valhalla routing engine).

---

### 0. Clone the Repository
Open your terminal and run:
```bash
git clone https://github.com/roicambe/LANES.git
cd LANES
```

---

### 1. Map Data & Routing Engine Setup (One-time only)
LANES has migrated to a dual-engine routing architecture. For the online backend, we use a self-hosted **GraphHopper** engine to calculate dynamic flood-adaptive routes. You need to download the map data and the engine first.
1. Make sure you have **Java 8 or higher** installed.
2. Open a PowerShell terminal at the root of the project.
3. Create a folder for the routing data and download the files:
   ```powershell
   New-Item -ItemType Directory -Force -Path graphhopper_data
   cd graphhopper_data
   Invoke-WebRequest -Uri "https://github.com/graphhopper/graphhopper/releases/download/9.1/graphhopper-web-9.1.jar" -OutFile "graphhopper-web.jar"
   Invoke-WebRequest -Uri "https://raw.githubusercontent.com/graphhopper/graphhopper/9.1/config-example.yml" -OutFile "config.yml"
   Invoke-WebRequest -Uri "https://download.geofabrik.de/asia/philippines-latest.osm.pbf" -OutFile "philippines.osm.pbf"
   ```

---

### 2. Start Background Services (Database & GraphHopper)
First, spin up the pre-configured PostgreSQL + PostGIS database using Docker:
```bash
docker-compose up -d
```
*(Note: Docker Desktop must be open and running).*

Next, start the GraphHopper routing engine (open a dedicated terminal):
```powershell
cd graphhopper_data
java -D"dw.graphhopper.datareader.file=philippines.osm.pbf" -jar graphhopper-web.jar server config.yml
```
*The database will run on port `5432` and GraphHopper will bind to `http://localhost:8989`.*
*(Note: The very first time you run GraphHopper, it will take a few minutes to process the map data and build the graph. Wait until it completes before testing).*

---

### 3. Backend Setup & Run (FastAPI)
1. Open a new terminal and navigate to the `backend` folder:
   ```bash
   cd backend
   ```
2. Set up and activate the virtual environment:
   ```bash
   # On Windows
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # On Mac/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy the environment variables:
   * Copy `.env.example` and rename it to `.env`.
   * Update any values if necessary (the defaults usually work for local dev).
5. Run the database migrations to build the tables (Ensure Docker is running first):
   ```bash
   alembic upgrade head
   ```
   *(Note: If you are pulling new code on a computer that already has an existing LANES database, run `alembic stamp head` instead to sync the history).*
6. Start the development server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   *The backend server runs at `http://localhost:8000` (and is accessible via your network IP).*

---

### 4. Frontend Setup & Run (Next.js)
1. Open a third terminal window and navigate to the `frontend` folder:
   ```bash
   cd frontend
   ```
2. Set up the frontend environment variables:
   * Create a new file named `.env.local` inside the `frontend` directory.
   * Add the following line to it: `NEXT_PUBLIC_API_URL=/api/v1`
3. Install dependencies and start the dev server:
   ```bash
   npm install
   npm run dev
   ```
   *The interactive dashboard will be available at `http://localhost:3000`.*

---

## 4. Map Routing Engines (GraphHopper & Valhalla)

LANES uses a dual-engine architecture:
- **GraphHopper**: Used for fast, online routing with dynamic flood avoidance (Custom Models).
- **Valhalla WebAssembly (WASM)**: Runs completely offline inside the browser as a PWA, providing disconnected intelligent routing.

### Setting up GraphHopper (Online)
1. Download a `.osm.pbf` file (e.g., `philippines.osm.pbf`) from Geofabrik.
2. Place it in the `graphhopper_data` folder.
3. Start GraphHopper with the configuration provided in the repository:
   ```bash
   cd graphhopper_data
   java -D"dw.graphhopper.datareader.file=philippines.osm.pbf" -jar graphhopper-web.jar server config.yml
   ```

### Setting up Valhalla (Offline PWA)
Valhalla requires the map data to be pre-compiled into a `.tar` file so it can be mounted into the browser's Emscripten Origin Private File System (OPFS).
1. Ensure Docker Desktop is installed and running.
2. Create a `valhalla_data` folder and place the same `philippines.osm.pbf` inside it.
3. Open a terminal in the `valhalla_data` directory and run the official Docker container:
   ```bash
   docker run -d --name valhalla_builder -v "${PWD}:/custom_files" ghcr.io/gis-ops/docker-valhalla/valhalla:latest
   ```
4. Wait for the container to finish building. It will automatically detect the `.pbf` file and generate a `valhalla_tiles.tar` file.
5. Move the generated `valhalla_tiles.tar` file into `backend/data/valhalla/`. The FastAPI backend will serve this as a static file to the Next.js frontend, which will cache it in IndexedDB for offline use!

## 5. Development Workflow
1. Turn on background services: `docker-compose up -d`
2. Start the backend: `cd backend` -> Activate `venv` -> `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
3. Start the frontend: `cd frontend` -> `npm run dev`

---

## 🛠️ Troubleshooting & Fallback
* **GraphHopper Download Timeout:** If the `Invoke-WebRequest` fails to download the map data (e.g., `Connection timed out`), it is likely being blocked by your firewall or network proxy. You can manually download the `.pbf` file from [https://download.geofabrik.de/asia/philippines-latest.osm.pbf](https://download.geofabrik.de/asia/philippines-latest.osm.pbf) and place it in the `graphhopper_data` folder.
* **TypeError: Failed to fetch (Frontend):** Check that the backend server is running at `http://localhost:8000`.
* **Database Connection Warnings:** If PostgreSQL is offline, the backend logs a startup warning and operates in fallback mode, letting you test routing options using GraphHopper without crashing the server.
* **Resetting the Database:** If you need to clear all dummy data (reports, zones, logs) but keep the default `admin` user intact, open a PowerShell terminal in the `backend` folder and run:
  ```powershell
  $env:PYTHONPATH="."; .\venv\Scripts\python.exe scripts\clear_db.py
  ```
  *(Note: If you completely wipe the database by dropping the tables, restarting the Uvicorn server will automatically re-seed the default roles and admin account on startup).*
