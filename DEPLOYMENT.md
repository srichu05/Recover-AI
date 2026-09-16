# RecoverAI &mdash; Deployment Guide (Render + Vercel)

This guide walks you through deploying **RecoverAI** into production:
- **Backend (FastAPI)**: Hosted on **Render**
- **Frontend (Vite + React)**: Hosted on **Vercel**

---

## Architecture Overview

```
[ User Browser ]
       │
       ▼
[ Vercel Frontend ] ── (REST API requests via VITE_API_URL) ──▶ [ Render Backend ]
 (Vite + React SPA)                                              (FastAPI + Policy Engine)
                                                                            │
                                                                            ▼
                                                                     [ GroqCloud API ]
                                                                   (openai/gpt-oss-120b)
```

---

## Part 1: Deploy Backend to Render

### Step 1: Create Web Service on Render
1. Log in to [Render Dashboard](https://dashboard.render.com/).
2. Click **"New +"** &rarr; **"Web Service"**.
3. Connect your GitHub repository: `RecoverAI`.
4. Configure the Web Service:
   - **Name**: `recoverai-backend` (or any name you choose)
   - **Region**: Choose the closest region (e.g. `Singapore` or `Frankfurt` or `Oregon`)
   - **Branch**: `main`
   - **Root Directory**: Leave blank (root of repo)
   - **Runtime**: `Python 3`
   - **Build Command**:
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     uvicorn backend.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Instance Type**: `Free`

### Step 2: Set Environment Variables on Render
In the **Environment** section of your Render Web Service, add the following key-value pairs:

| Key | Recommended Value | Note |
| :--- | :--- | :--- |
| `PYTHON_VERSION` | `3.11.9` | Ensures compatible Python environment |
| `DEBUG` | `False` | Production mode |
| `APP_NAME` | `RecoverAI` | Service name |
| `GROQ_API_KEY` | `gsk_...` | Your real Groq API key |
| `GROQ_BASE_URL` | `https://api.groq.com/openai/v1` | GroqCloud OpenAI-compatible endpoint |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | High-performance reasoning model |
| `USE_MOCK_LLM_IF_UNAVAILABLE` | `True` | Ensures 100% uptime with fallback |

### Step 3: Deploy & Copy Backend URL
1. Click **"Create Web Service"**.
2. Wait 2–3 minutes for the build to complete.
3. Once live, test your backend URL in the browser:
   - `https://your-backend-name.onrender.com/api/health`
   - You should see: `{"status": "healthy", "app": "RecoverAI", "version": "1.0.0"}`
4. **Copy your Render backend URL** (e.g. `https://recoverai-backend.onrender.com`). You will need this for Vercel.

---

## Part 2: Deploy Frontend to Vercel

### Step 1: Import Project into Vercel
1. Log in to [Vercel Dashboard](https://vercel.com/dashboard).
2. Click **"Add New..."** &rarr; **"Project"**.
3. Import your `RecoverAI` GitHub repository.

### Step 2: Configure Project Settings
In the Vercel project configuration screen:
- **Framework Preset**: `Vite`
- **Root Directory**: Click **Edit** and select `frontend` (Important!)
- **Build Command**: `npm run build` (Default)
- **Output Directory**: `dist` (Default)
- **Install Command**: `npm install` (Default)

### Step 3: Set Frontend Environment Variable
Under **Environment Variables**, add:

| Key | Value | Example |
| :--- | :--- | :--- |
| `VITE_API_URL` | `https://your-backend-name.onrender.com` | `https://recoverai-backend.onrender.com` |

*(Do **not** add a trailing slash `/` at the end of the URL).*

### Step 4: Deploy & Verify
1. Click **"Deploy"**.
2. Once the build finishes (approx. 30–60 seconds), click on your Vercel domain (e.g. `https://recoverai.vercel.app`).
3. Your frontend will load and communicate with the live Render backend.

---

## Part 3: Verify Deployment End-to-End

1. **Overview Screen**: Verify that live KPI metrics and system status load.
2. **Incident Simulator**:
   - Select a scenario (e.g. *UPI Timeout Spike*).
   - Click **"Run Simulation"**.
   - Click **"RUN RECOVERAI WORKFLOW"** to execute recovery.
3. **Audit Trail**: Check that transactions and policy decisions appear and click **"Export CSV"**.
4. **Evaluation Benchmark**: Click **"Run Benchmark"** to verify 7-scenario execution.

---

## Part 4: Updating Your GitHub Repository

Run the following commands in your terminal to stage, commit, and push all deployment configuration changes:

```bash
# 1. Check status
git status

# 2. Stage all updated and newly created deployment files
git add .

# 3. Commit the changes
git commit -m "feat: configure Render backend and Vercel frontend deployment support"

# 4. Push to GitHub main branch
git push origin main
```

When you push to `main`, both Render and Vercel will automatically trigger new deployments!
