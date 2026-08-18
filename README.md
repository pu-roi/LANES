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
LANES uses a local Valhalla engine to calculate dynamic flood-adaptive routes. You need to download the map data and compile the routing graph first.
1. Open a PowerShell terminal at the root of the project.
2. Run the automated setup script to download the Philippines OpenStreetMap data and build the Valhalla routing graph:
   ```powershell
   .\setup_valhalla.ps1
   ```
   *(Note: This downloads ~200MB of data and may take a few minutes. Wait for it to say "Valhalla Graph successfully built!" before proceeding).*

---

### 2. Start Background Services (Database & Router)
Spin up the pre-configured PostgreSQL + PostGIS database and the local Valhalla routing engine using Docker:
```bash
docker-compose up -d
```
*This starts the database on port `5432` and the Valhalla engine on port `8002`.*
*(Note: Docker Desktop must be open and running).*

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

### 📅 Your Daily Workflow
Since Step 1 is a one-time setup, your daily development routine is just:
1. Turn on background services: `docker-compose up -d`
2. Start the backend: `cd backend` -> Activate `venv` -> `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
3. Start the frontend: `cd frontend` -> `npm run dev`

---

## 🛠️ Troubleshooting & Fallback
* **setup_valhalla.ps1 Connection Timeout:** If the script fails to download the map data (e.g., `Connection timed out`), it is likely being blocked by your firewall or network proxy. Try temporarily disabling your firewall, disconnecting from a VPN, or using a different network. Alternatively, you can download the file manually from [https://download.geofabrik.de/asia/philippines-latest.osm.pbf](https://download.geofabrik.de/asia/philippines-latest.osm.pbf), place the `.pbf` file inside the `data/valhalla/custom_files/` directory, and run the script again.
* **TypeError: Failed to fetch (Frontend):** Check that the backend server is running at `http://localhost:8000`.
* **Database Connection Warnings:** If PostgreSQL is offline, the backend logs a startup warning and operates in fallback mode, letting you test routing options using Valhalla without crashing the server.
* **Resetting the Database:** If you need to clear all dummy data (reports, zones, logs) but keep the default `admin` user intact, open a PowerShell terminal in the `backend` folder and run:
  ```powershell
  $env:PYTHONPATH="."; .\venv\Scripts\python.exe scripts\clear_db.py
  ```
  *(Note: If you completely wipe the database by dropping the tables, restarting the Uvicorn server will automatically re-seed the default roles and admin account on startup).*
