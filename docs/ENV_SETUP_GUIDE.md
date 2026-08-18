# 🔐 Environment Variables & Decryption Setup Guide

The `.env` and `.env.local` files in this repository are encrypted using [dotenvx](https://dotenvx.com/) so we can safely track them in Git without exposing secrets or API keys.

Follow this quick guide to decrypt your environment files locally.

---

## Prerequisites

1. Ask the project lead/admin for the **two private keys**:
   - Backend Private Key (`DOTENV_PRIVATE_KEY`)
   - Frontend Private Key (`DOTENV_PRIVATE_KEY_LOCAL`)

---

## 🛠️ Step-by-Step Setup

### Step 1: Pull the Latest Code
Make sure you have the latest encrypted files and code:
```bash
git pull origin roi-branch
# or if merged to main:
git pull origin main
```

---

### Step 2: Set up Backend Keys & Decrypt

1. Go to the `backend` folder:
   ```bash
   cd backend
   ```
2. Create a file named `.env.keys` inside `backend/`:
   ```env
   #/------------------!DOTENV_PRIVATE_KEYS!-------------------/
   DOTENV_PRIVATE_KEY=<PASTE_BACKEND_PRIVATE_KEY_HERE>
   ```
3. Decrypt the `.env` file:
   ```bash
   npx @dotenvx/dotenvx decrypt
   ```
   > ✅ Output: `◈ decrypted (.env)`

---

### Step 3: Set up Frontend Keys & Decrypt

1. Go to the `frontend` folder:
   ```bash
   cd ../frontend
   ```
2. Create a file named `.env.keys` inside `frontend/`:
   ```env
   #/------------------!DOTENV_PRIVATE_KEYS!-------------------/
   DOTENV_PRIVATE_KEY_LOCAL=<PASTE_FRONTEND_PRIVATE_KEY_HERE>
   ```
3. Decrypt the `.env.local` file:
   ```bash
   npx @dotenvx/dotenvx decrypt -f .env.local
   ```
   > ✅ Output: `◈ decrypted (.env.local)`

---

## ⚡ Daily Development

Once decrypted, you can run the backend and frontend normally:

```bash
# Backend (from /backend directory)
.\venv\Scripts\uvicorn.exe app.main:app --reload

# Frontend (from /frontend directory)
npm run dev
```

---

## ⚠️ Important Rules
- **NEVER** commit `.env.keys` to GitHub. (It is already added to `.gitignore`).
- If you add or modify secrets in `.env` or `.env.local`, remember to re-encrypt before pushing:
  ```bash
  # In backend
  npx @dotenvx/dotenvx encrypt

  # In frontend
  npx @dotenvx/dotenvx encrypt -f .env.local
  ```
