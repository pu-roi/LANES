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

Whenever you or your groupmates pull new changes from `main` or your feature branch, execute these exact commands in the specified folders:

### 1. Root Directory: `LANES/`
```powershell
# 📍 In the ROOT folder:
git pull origin main
```
*(Or your current feature branch, e.g. `git pull origin roi-branch`)*

### 2. Backend Directory: `LANES/backend/`
Always navigate into `backend/` so your virtual environment and `.env` are detected:
```powershell
# 📍 Navigate to backend:
cd backend

# Activate virtual environment (Windows PowerShell):
.\venv\Scripts\Activate.ps1
# (Or on Mac/Linux: source venv/bin/activate)

# Install any newly added python packages:
pip install -r requirements.txt

# Apply new database schema migrations with the pinned Dotenvx CLI:
npx --yes @dotenvx/dotenvx@2.21.0 run -f .env -- .\venv\Scripts\alembic.exe upgrade head
# (Or on Mac/Linux: npx --yes @dotenvx/dotenvx@2.21.0 run -f .env -- alembic upgrade head)
```

### 3. Frontend Directory: `LANES/frontend/`
```powershell
# 📍 Navigate to frontend:
cd ../frontend

# Install any newly added npm packages:
npm install
```

---

## 🚀 First-Time Local Development Setup

### Prerequisites
* **Git** (For cloning the repository)
* **Node.js** (v20.9 or higher) & **npm**
* **Python** (v3.11 or v3.12)
* **Docker Desktop** (Must be running for the local PostGIS spatial database and Valhalla routing engine)
* **Private Decryption Keys** (Ask the project lead/admin for the 2 keys: `DOTENV_PRIVATE_KEY` for backend and `DOTENV_PRIVATE_KEY_LOCAL` for frontend)

---

### Step 0: Clone the Repository
📂 **Where to run:** Anywhere on your system (e.g., your projects folder)
```powershell
git clone https://github.com/roicambe/LANES.git
cd LANES
```

---

### Step 1: Start Background Services (PostGIS & Valhalla)
📂 **Directory:** `LANES/` *(Root Folder)*

Prepare the Valhalla map data first. The initial Philippines download and tile build can take several minutes:
```powershell
.\setup_valhalla.ps1
```

Then start the pre-configured PostgreSQL + PostGIS database and Valhalla routing engine:
```powershell
docker compose up -d --wait
```
*(Docker Desktop must be running. PostGIS listens on `5432`; Valhalla listens on `http://localhost:8002`.)*

---

### Step 2: Set up Decryption Keys (`.env.keys`)

The repository uses **dotenvx** for encrypted secrets. You do **not** need to manually decrypt `.env` files into plaintext on disk; the applications inject secrets directly into memory.

1. **Backend Key (`backend/.env.keys`)**:
   Inside the `backend/` folder, create a file named `.env.keys`:
   ```env
   #/------------------!DOTENV_PRIVATE_KEYS!-------------------/
   DOTENV_PRIVATE_KEY=<PASTE_BACKEND_PRIVATE_KEY_HERE>
   ```

2. **Frontend Key (`frontend/.env.keys`)**:
   Inside the `frontend/` folder, create a file named `.env.keys`:
   ```env
   #/------------------!DOTENV_PRIVATE_KEYS!-------------------/
   DOTENV_PRIVATE_KEY_LOCAL=<PASTE_FRONTEND_PRIVATE_KEY_HERE>
   ```

> [!CAUTION]
> **NEVER commit `.env.keys` to GitHub.** Both are strictly ignored by `.gitignore`.

---

### Step 3: Backend Setup & Run (FastAPI)
📂 **Directory:** `LANES/backend/`

1. Open a terminal and navigate to `backend`:
   ```powershell
   cd backend
   ```
2. Create and activate your Python virtual environment:
   ```powershell
   # Windows (PowerShell):
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # Mac/Linux:
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
4. Apply database schema migrations:
   ```powershell
   # Windows:
   npx --yes @dotenvx/dotenvx@2.21.0 run -f .env -- .\venv\Scripts\alembic.exe upgrade head

   # Mac/Linux:
   npx --yes @dotenvx/dotenvx@2.21.0 run -f .env -- alembic upgrade head
   ```
5. Start the backend development server:
   ```powershell
   # Windows:
   npx --yes @dotenvx/dotenvx@2.21.0 run -f .env -- .\venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000 --reload

   # Mac/Linux:
   npx --yes @dotenvx/dotenvx@2.21.0 run -f .env -- uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   *The backend API will be available at `http://localhost:8000` (docs at `http://localhost:8000/docs`).*

---

### Step 4: Frontend Setup & Run (Next.js)
📂 **Directory:** `LANES/frontend/`

1. Open a separate terminal window and navigate to `frontend`:
   ```powershell
   cd frontend
   ```
2. Install npm dependencies:
   ```powershell
   npm install
   ```
3. Start the Next.js development server:
   ```powershell
   npm run dev
   ```
   *The web application will be live at `http://localhost:3000`.*

---

### ✏️ Editing or Adding Environment Secrets
If you ever need to add or edit an environment variable:
1. **Decrypt temporarily:**
   ```powershell
   # In frontend:
   npx --yes @dotenvx/dotenvx@2.21.0 decrypt -f .env.local

   # In backend:
   npx --yes @dotenvx/dotenvx@2.21.0 decrypt -f .env
   ```
2. **Edit the values** in `backend/.env` or `frontend/.env.local`.
3. **Re-encrypt before staging/committing:**
   ```powershell
   # In frontend:
   npx --yes @dotenvx/dotenvx@2.21.0 encrypt -f .env.local

   # In backend:
   npx --yes @dotenvx/dotenvx@2.21.0 encrypt -f .env
   ```
4. Commit and push the encrypted file safely to Git.

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
* **ModuleNotFoundError: No module named '<package>' (e.g. `cachetools`):**
  This happens after a `git pull` when new packages have been added. Navigate to `backend/`, activate your virtual environment, and install the updated requirements:
  ```powershell
  cd backend
  .\venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```
* **Alembic Migration Connection Errors (`alembic upgrade head`):**
  Alembic needs a live database connection to record migrations. Make sure Docker Desktop is open and run `docker compose up -d --wait` in the root `LANES/` directory before running the migration command.
* **TypeError: Failed to fetch (Frontend):** Check that the backend server is running at `http://localhost:8000`.
* **Database Connection Warnings:** If PostgreSQL is offline, the backend operates in fallback mode.
* **Resetting the Database:** If you need to clear all dummy data (reports, zones, logs) while keeping the default `admin` user intact, run:
  ```powershell
  cd backend
  $env:PYTHONPATH="."; .\venv\Scripts\python.exe scripts\clear_db.py
  ```
