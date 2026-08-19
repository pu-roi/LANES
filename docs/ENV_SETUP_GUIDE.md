# 🔐 Environment Variables & Setup Guide

The `.env` (backend) and `.env.local` (frontend) files in this repository are securely encrypted using [dotenvx](https://dotenvx.com/).

With this setup, **you never have to manually decrypt `.env` files into plain text on disk**. The application automatically decrypts and injects the secrets into memory when you run the development servers.

---

## 🔑 Prerequisites (One-Time Setup)

Ask the project lead/admin for the **two private keys**:
1. **Backend Private Key** (`DOTENV_PRIVATE_KEY`)
2. **Frontend Private Key** (`DOTENV_PRIVATE_KEY_LOCAL`)

---

## 🛠️ Step-by-Step Setup

### Step 1: Set up Backend `.env.keys`

1. Inside the `backend/` folder, create a file named `.env.keys`:
   ```env
   #/------------------!DOTENV_PRIVATE_KEYS!-------------------/
   DOTENV_PRIVATE_KEY=<PASTE_BACKEND_PRIVATE_KEY_HERE>
   ```

### Step 2: Set up Frontend `.env.keys`

1. Inside the `frontend/` folder, create a file named `.env.keys`:
   ```env
   #/------------------!DOTENV_PRIVATE_KEYS!-------------------/
   DOTENV_PRIVATE_KEY_LOCAL=<PASTE_FRONTEND_PRIVATE_KEY_HERE>
   ```

---

## ⚡ Daily Development (Just Run It!)

Whenever you pull code or work on the project, you don't need to decrypt anything. Just start the apps normally:

### Frontend
```bash
cd frontend
npm run dev
```
> `npm run dev` uses `dotenvx run -f .env.local -- next dev` to seamlessly inject your secrets directly into memory.

### Backend
```bash
cd backend
# Run with dotenvx injection:
npx @dotenvx/dotenvx run -f .env -- .\venv\Scripts\uvicorn.exe app.main:app --reload
```

---

## ✏️ Modifying or Adding New Secrets

If you ever need to add or edit an environment variable:

1. **Decrypt temporarily**:
   ```bash
   # In frontend:
   npx @dotenvx/dotenvx decrypt -f .env.local

   # In backend:
   npx @dotenvx/dotenvx decrypt -f .env
   ```
2. **Edit your values** in the file.
3. **Re-encrypt before committing**:
   ```bash
   # In frontend:
   npx @dotenvx/dotenvx encrypt -f .env.local

   # In backend:
   npx @dotenvx/dotenvx encrypt -f .env
   ```
4. Commit and push the encrypted file safely to Git!

---

## ⚠️ Important Security Rules
- **NEVER** commit `.env.keys` to GitHub. (It is strictly ignored by `.gitignore`).
- **NEVER** commit unencrypted `.env` or `.env.local` files with raw production secrets.
