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
* **For Architecture Decisions:** [`docs/decisions.md`](file:///d:/Documents/Github/LANES/docs/decisions.md) tracks major technical decisions and historical shifts.
* **For Technical Blueprint:** [`docs/tech-stack.md`](file:///d:/Documents/Github/LANES/docs/tech-stack.md) details all components of the technology stack.

---

---

## 🔄 Daily Workflow: Pulling Updates (`git pull`)

Whenever you or your groupmates pull new changes from `main`, execute these exact commands according to the folder specified:

### 1. Root Directory: `LANES/`
```bash
# 📍 In the ROOT folder:
git pull origin main
```

### 2. Backend Directory: `LANES/backend/`
```bash
# 📍 Navigate to backend:
cd backend

# Activate virtual environment (Windows):
.\venv\Scripts\Activate.ps1
# (Or on Mac/Linux: source venv/bin/activate)

# Install any new python packages:
pip install -r requirements.txt

# Apply new database schema migrations:
alembic upgrade head
```

### 3. Frontend Directory: `LANES/frontend/`
```bash
# 📍 Navigate to frontend:
cd ../frontend

# Install any newly added npm packages (e.g. terra-draw):
npm install
```

---

## 🚀 First-Time Local Development Setup

### Prerequisites
* **Git** (For cloning the repository)
* **Node.js** (v18 or higher)
* **Python** (v3.11 or v3.12)
* **Docker Desktop** (For running the local PostGIS spatial database and Valhalla routing engine).

---

### Step 0: Clone the Repository
📂 **Where to run:** Anywhere on your system (e.g., your projects folder)
```bash
git clone https://github.com/roicambe/LANES.git
cd LANES
```

---

### Step 1: Start Background Services (Database & Valhalla)
📂 **Directory:** `LANES/` *(Root Folder)*

Spin up the pre-configured PostgreSQL + PostGIS database and Valhalla engine using Docker:
```bash
docker-compose up -d
```
*(Note: Docker Desktop must be open and running. The database runs on port `5432` and Valhalla binds to `http://localhost:8002`).*

---

### Step 2: Backend Setup & Run (FastAPI)
📂 **Directory:** `LANES/backend/`

1. Open a new terminal and navigate to the backend folder:
   ```bash
   cd backend
   ```
2. Set up and activate your Python virtual environment:
   ```bash
   # On Windows (PowerShell):
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # On Mac/Linux:
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install backend packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up Environment Variables:
   * We use **dotenvx** for encrypted secrets.
   * Please follow the [Environment Setup Guide](file:///d:/Documents/Github/LANES/docs/ENV_SETUP_GUIDE.md) to get the decryption keys.
5. Apply database schema migrations:
   ```bash
   alembic upgrade head
   ```
6. Start the backend development server:
   ```bash
   # Windows:
   npx @dotenvx/dotenvx run -f .env -- .\venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000 --reload

   # Mac/Linux:
   npx @dotenvx/dotenvx run -f .env -- uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   *The backend server will run at `http://localhost:8000`.*

---

### Step 3: Frontend Setup & Run (Next.js)
📂 **Directory:** `LANES/frontend/`

1. Open a separate terminal window and navigate to the frontend folder:
   ```bash
   cd frontend
   ```
2. Set up the frontend environment variables:
   * Follow the [Environment Setup Guide](file:///d:/Documents/Github/LANES/docs/ENV_SETUP_GUIDE.md) to add your `.env.keys` file. You do NOT need to manually create `.env.local`.
3. Install dependencies and start the dev server:
   ```bash
   npm install
   npm run dev
   ```
   *The web application will be live at `http://localhost:3000`.*

---

### ⚡ Shortcut: Running via VS Code (Windows)
If you are using VS Code, you can press **`Ctrl + Shift + B`** (or go to `Terminal` -> `Run Build Task...` -> `Start LANES Dev Server`). This automatically starts both the backend and frontend simultaneously in split terminals!

---

## 🧭 Routing Architecture

LANES features a triple-path routing engine setup designed for maximum reliability and offline resilience:

| Engine | Mode | Description |
|---|---|---|
| **Valhalla (HTTP)** | Online (Primary) | High-performance self-hosted Docker engine (`ghcr.io/gis-ops/docker-valhalla`) with native `exclude_polygons` flood avoidance, clearance-based vehicle profiles (High Clearance, Low Clearance, Motorcycle, Walk), and multiple route alternatives (`alternates=2`). |
| **OpenRouteService** | Online (Secondary) | Cloud-hosted routing API providing a fast second opinion and fallback if local routing encounters restrictions. Switchable directly by commuters in the sidebar. |
| **Valhalla WASM** | Offline (PWA) | Runs completely in the browser via WebAssembly and a dedicated Web Worker. Automatically activated when connectivity drops (`navigator.onLine === false`), querying locally cached IndexedDB map tiles and flood polygons. |

---

## 🛠️ Troubleshooting & Commands
* **TypeError: Failed to fetch (Frontend):** Check that the backend server is running at `http://localhost:8000`.
* **Database Connection Warnings:** If PostgreSQL is offline, the backend operates in fallback mode.
* **Resetting the Database:** If you need to clear all dummy data (reports, zones, logs) while keeping the default `admin` user intact, run:
  ```powershell
  cd backend
  $env:PYTHONPATH="."; .\venv\Scripts\python.exe scripts\clear_db.py
  ```
