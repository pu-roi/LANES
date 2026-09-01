# LANES: AI Vibe Coding Protocol & Global Rules

This document defines the core operational boundaries, architecture, and required rules for any AI agent interacting with the LANES repository.

> [!CAUTION]
> **CRITICAL RULE**: You MUST use your file-reading tool to read [`DESIGN.md`](file:///d:/Documents/Github/LANES/DESIGN.md) before writing or modifying any code to ensure you follow the established architecture.

---

## 1. Project Knowledge (The Stack)
- **Frontend**: React 18, Next.js (App Router), Tailwind CSS, MapLibre GL JS, Lucide React.
- **Backend**: Python, FastAPI, SQLAlchemy (GeoAlchemy2), spaCy NLP.
- **Database**: PostgreSQL with PostGIS extension.
- **Routing**: Valhalla Engine.

---

## 2. Global Boundaries & Vibe Coding Rules

### ✅ Always Do:
- **Keep logic on the server**: All data manipulation, pricing, permissions, and database queries must occur in the FastAPI backend, NEVER in the Next.js frontend.
- **Proactively Use Specific Skills**: You MUST independently determine if your task relates to any of the specialized agents defined in `.agents/skills/` (such as `api-agent`, `security-agent`, `test-agent`, `ui-agent`, or `senior-planner-agent`). If a task matches a skill's domain, you MUST automatically read and follow that skill's instructions, even if the human developer does not explicitly mention them or use a slash command.
- **Surface Errors to the User**: Do not swallow errors (e.g., `catch (err) { console.error(err) }` without updating UI state). Ensure the user is notified if a request fails.
- **Verify Sessions**: Ensure backend FastAPI endpoints have proper dependency injection checks for authentication and role validation.
- **Future-Proof for Mobile (APK) & PWA Dual-Screen Verification**: This application is a Progressive Web App (PWA) designed for both mobile and desktop. Whenever making UI changes, you MUST explicitly double-check and update both the small screen (mobile) and big screen (desktop) implementations. Keep the architecture compatible with a future Android `.apk` wrapper (e.g., Capacitor). Prefer Server-Sent Events (SSE) over WebSockets for battery/connection stability. Use `localStorage` for JWTs instead of `HttpOnly` cookies to avoid WebView cross-origin auth issues.

### 🚫 Never Do:
- **Never work or commit directly to the `main` branch**: The `main` branch is protected. Always ensure you are working on a feature or personal branch (e.g., `roi-branch` or your groupmate's branch). If you are on `main`, switch branches before writing code or committing.
- **Never commit secrets**: Do not hardcode API keys, Stripe tokens, or DB URLs (`http://localhost`, `postgres://`) in the source code.
- **Never perform direct DB queries from the frontend**: The frontend must only interact with the FastAPI endpoints via standard HTTP requests.
- **Never alter database schemas without asking**: Always confirm with the human developer before modifying SQLAlchemy models or Alembic migrations.

---

## 3. Git Push Protocol

When the human developer says **"push"** (or similar phrases like "save my work", "push to main"), you MUST execute the following steps automatically without asking for further input:

1. **Verify Branch:** Check the current branch (`git branch --show-current`). If you are on `main`, STOP immediately and ask the human developer which feature branch you should switch to. Do NOT commit or push to `main`.
2. **Stage all changes:** `git add -A`
3. **Synthesize the commit message:** Review the conversation and create a message following Conventional Commits (e.g., `feat(map): added heatmap layer`). Write a bulleted body explaining the *what* and *why*.
4. **Commit:** `git commit -m "<summary line>" -m "<bulleted body>"`
5. **Push:** `git push origin <current-branch>`

If the push fails (e.g., non-fast-forward), report the git error and suggest the correct resolution (e.g., `git pull --rebase`). Do not force-push without explicit approval.
