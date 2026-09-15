# 🚀 AI-Powered Application Deployment Agent (MVP Prototype)

An autonomous developer agent that analyzes public GitHub repositories, generates secure deployment plans, and orchestrates cloud deployments to **Vercel** and **Render** via official REST APIs. Includes real-time status monitoring, streaming logs, and human-in-the-loop self-healing error diagnosis.

---

## 📑 Table of Contents
1. [Core Features & Highlights](#-core-features--highlights)
2. [Project Architecture](#-project-architecture)
3. [Quickstart Guide](#-quickstart-guide)
   - [Prerequisites](#prerequisites)
   - [1. Configure Environment Variables](#1-configure-environment-variables)
   - [2. Run the FastAPI Backend](#2-run-the-fastapi-backend)
   - [3. Run the React Frontend](#3-run-the-react-frontend)
4. [Connecting Cloud Platforms](#-connecting-cloud-platforms)
   - [Vercel API Integration](#vercel-api-integration)
   - [Render API Integration](#render-api-integration)
5. [End-to-End Workflow Walkthrough](#-end-to-end-workflow-walkthrough)
6. [API Reference](#-api-reference)
7. [Security Strategy & Command Allowlist](#-security-strategy--command-allowlist)
8. [What is Implemented (v1) vs Version 2 Roadmap](#-what-is-implemented-v1-vs-version-2-roadmap)

---

## ✨ Core Features & Highlights

- 🔍 **Automated Repository Inspection**: Reads GitHub repositories via GitHub REST API without requiring private keys. Analyzes root and nested files (`package.json`, `requirements.txt`, `pyproject.toml`, `Dockerfile`, `vercel.json`, `render.yaml`, `.env.example`, lockfiles).
- 🧠 **Smart Framework & Architecture Detection**: Accurately classifies language, package manager (`npm`, `pnpm`, `yarn`, `pip`, `poetry`), project architecture (`frontend`, `backend`, `full_stack`, `static`), and framework (React, Vite, Next.js, FastAPI, Flask, Express, Django).
- 🛡️ **Safe Command Allowlist**: Prohibits arbitrary shell injections (`rm -rf`, `sudo`, piping, multiple chained statements); strictly enforces allowlisted tool prefixes.
- 🩺 **Pre-Flight Readiness & Security Audit**: Scores projects (0-100%, Grades A-D) across manifest integrity, lockfile reproducibility, build scripts, and env configurations with automated recommendations.
- 📋 **Structured Deployment Plan**: Suggests optimal cloud targets (e.g. Next.js/React &rarr; Vercel, Python/Node API &rarr; Render) with step-by-step rationale.
- 🛠️ **Automated CI/CD & IaC Generator**: Automatically creates production-ready GitHub Actions CI/CD workflows (`.github/workflows/deploy.yml`), optimized multi-stage Dockerfiles, and platform manifests (`vercel.json` / `render.yaml`) with 1-click preview, copy, and download.
- ⚡ **Official Cloud APIs**: Directly interacts with **Vercel REST API v13** and **Render REST API v1**—never fakes deployment outcomes.
- 📊 **Real-time Pipeline & Logs**: Progress stepper, color-coded terminal logs, real-time log search, level filtering (`All`, `Info`, `Success`, `Warn`, `Error`), `.txt` logs export, and live GitHub status badge generation.
- 📜 **Deployment History & Activity Manager**: Full activity timeline allowing developers to track past deployments, inspect logs, and navigate back to live deployments.
- 🩹 **Self-Healing Error Diagnosis**: On build or provisioning failure, the AI Diagnosis Agent isolates root cause, formulates remedial parameters (adjusted build command or missing environment variables), and requires user approval before retrying (prevents runaway loops).

---

## 🏗️ Project Architecture

```text
deploymentai/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI application factory & CORS
│   │   ├── config.py                   # Environment settings & command allowlists
│   │   ├── models/
│   │   │   └── schemas.py              # Pydantic v2 schemas for all requests/responses
│   │   ├── services/
│   │   │   ├── github_service.py       # GitHub repository inspector
│   │   │   ├── analyzer_service.py     # Framework & project heuristics
│   │   │   ├── agent_service.py        # AI deployment planner & diagnosis agent
│   │   │   ├── deployment_manager.py   # Async state store & pipeline coordinator
│   │   │   └── providers/
│   │   │       ├── base.py             # Abstract DeploymentProvider interface
│   │   │       ├── vercel_provider.py  # Vercel REST API v13 provider
│   │   │       ├── render_provider.py  # Render REST API v1 provider
│   │   │       └── browser_provider.py # Architecture abstraction for future browser automation
│   │   └── api/
│   │       └── routes.py               # REST endpoints
│   ├── tests/
│   │   ├── test_backend.py             # Unit tests for analyzer, planner, security
│   │   └── test_api.py                 # FastAPI TestClient endpoint tests
│   └── requirements.txt                # Python backend dependencies
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.jsx              # Brand header & cloud provider status pills
│   │   │   ├── RepoInput.jsx           # GitHub URL input & quick-load presets
│   │   │   ├── AnalysisView.jsx        # Project analysis & deployment plan configuration
│   │   │   ├── DeploymentConsole.jsx   # Real-time stepper, live logs & live URL card
│   │   │   ├── ErrorModal.jsx          # AI error diagnosis & approved fix retry modal
│   │   │   └── SettingsModal.jsx       # Custom token management modal
│   │   ├── App.jsx                     # Master state controller
│   │   ├── main.jsx                    # React entrypoint
│   │   └── index.css                   # Tailwind styles & dark developer theme
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js                  # Vite bundler & backend proxy
│   └── tailwind.config.js              # Theme design system tokens
│
├── .env.example                        # Template for secrets and API keys
└── README.md                           # Comprehensive documentation
```

---

## ⚡ Quickstart Guide

### Prerequisites
- **Python**: 3.10+ (tested on Python 3.12)
- **Node.js**: 18+ (tested on Node 20 / 26)
- **Git**

### 1. Configure Environment Variables
Copy the template file to `.env` in the project root:
```bash
cp .env.example .env
```
Edit `.env` with your API tokens (or pass them dynamically inside the frontend Settings modal):
```env
HOST=0.0.0.0
PORT=8000
DEBUG=true

# Optional but recommended (prevents public GitHub rate limits):
GITHUB_TOKEN=ghp_...

# Required for Vercel deployments:
VERCEL_TOKEN=vcp_...

# Required for Render deployments:
RENDER_API_KEY=rnd_...

# Optional LLM Key (Gemini or OpenAI):
LLM_API_KEY=
```

### 2. Run the FastAPI Backend
From the project root:
```bash
# Windows PowerShell:
python -m venv backend/venv
backend\venv\Scripts\pip install -r backend/requirements.txt
$env:PYTHONPATH="backend"
backend\venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Linux/macOS:
python3 -m venv backend/venv
source backend/venv/bin/activate
pip install -r backend/requirements.txt
PYTHONPATH=backend uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
The backend will start at `http://127.0.0.1:8000`.
- Swagger API Docs: `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/api/health`

### 3. Run the React Frontend
Open a separate terminal window:
```bash
cd frontend
npm install
npm run dev
```
Open `http://127.0.0.1:5173` in your browser.

---

## ☁️ Connecting Cloud Platforms

### Vercel API Integration
1. Go to your [Vercel Account Tokens](https://vercel.com/account/tokens).
2. Create an access token with standard permissions.
3. Add `VERCEL_TOKEN=vcp_...` to your `.env` or paste it into the frontend **Settings** modal.
4. **How it works**:
   - `VercelProvider.prepare`: Validates user authentication using `GET https://api.vercel.com/v2/user`.
   - `VercelProvider.deploy`: Creates or checks the target project (`POST /v10/projects`), registers environment variables (`POST /v10/projects/{name}/env`), and triggers the deployment with git reference tracking (`POST /v13/deployments`).
   - `VercelProvider.get_status`: Polls `GET /v13/deployments/{id}` for states (`INITIALIZING`, `ANALYZING`, `BUILDING`, `READY`, `ERROR`), extracting live `https://*.vercel.app` URLs upon completion.

### Render API Integration
1. Go to your [Render Account API Keys](https://dashboard.render.com/u/settings#api-keys).
2. Create an API key.
3. Add `RENDER_API_KEY=rnd_...` to your `.env` or paste it into the frontend **Settings** modal.
4. **How it works**:
   - `RenderProvider.prepare`: Queries `GET https://api.render.com/v1/owners` to extract account/workspace ID.
   - `RenderProvider.deploy`: Creates a Web Service (`POST /v1/services`) with the detected runtime (`python` or `node`), sets build/start commands, and triggers an initial deployment (`POST /v1/services/{serviceId}/deploys`).
   - `RenderProvider.get_status`: Polls `GET /v1/services/{serviceId}/deploys/{deployId}` and returns the live `https://*.onrender.com` URL once live.

---

## 🔄 End-to-End Workflow Walkthrough

1. **User enters GitHub URL**: e.g., `https://github.com/vitejs/vite` or a custom repository.
2. **Analysis**: Click **Analyze Repository**. The agent fetches file manifests, checks dependencies, and infers language, framework, and required `.env` variables.
3. **Review AI Plan**:
   - Inspect recommended platforms (Vercel for frontend, Render for backend).
   - Customize build or start commands if needed.
   - Provide values for any detected environment variables.
4. **Confirmation & Launch**: Click **Deploy Project**.
5. **Real-time Console**: Watch the pipeline stepper and live logs stream in real-time.
6. **Error Diagnosis (Self-Healing)**:
   - If an error occurs (such as missing environment variables or invalid build commands), the AI Diagnostic Agent summarizes the root cause.
   - Click **View AI Fix & Healing**, review proposed modifications, and click **Approve Fix & Retry Deployment**.
7. **Live URL**: Once verified, the live URL is displayed with direct link access.

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health and configured provider indicators |
| `GET` | `/api/config/providers` | Provider configuration status (without exposing secrets) |
| `POST` | `/api/analyze` | Ingests GitHub URL; returns project manifest, AI plan, and pre-flight readiness audit |
| `POST` | `/api/deploy` | Queues and starts a cloud deployment job |
| `GET` | `/api/deploy/{id}` | Polls deployment stage, progress (0-100), and live URLs |
| `GET` | `/api/deploy/{id}/logs` | Returns real-time log entries with timestamps |
| `POST` | `/api/deploy/{id}/retry` | Applies user-approved changes and retries deployment |
| `POST` | `/api/deploy/{id}/diagnose` | Triggers error analysis on a failed deployment |
| `GET` | `/api/deployments` | Lists recent deployment runs and current statuses |
| `POST` | `/api/generate-iac` | Generates GitHub Actions workflow, Dockerfile, and cloud manifests |

---

## 🛡️ Security Strategy & Command Allowlist

- **Zero Arbitrary Execution**: The agent never blindly executes arbitrary shell scripts. Commands must begin with approved tools:
  `npm`, `pnpm`, `yarn`, `npx`, `pip`, `poetry`, `uvicorn`, `gunicorn`, `python`, `node`, `cargo`, `go`, `docker`.
- **Injection Filtering**: Any command containing shell operators (`;`, `&&`, `||`, `|`, `` ` ``, `$(`, `rm -rf`, `sudo`, `curl`) is immediately blocked and reported.
- **Credential Protection**: Secrets and tokens are never printed in logs or sent back in response bodies.

---

## 🚀 What is Implemented (v1) vs Version 2 Roadmap

### ✅ Implemented in Prototype (v1)
- [x] Full-stack architecture with FastAPI backend and React/Vite/Tailwind CSS frontend.
- [x] GitHub repository inspector parsing manifests (`package.json`, `requirements.txt`, `pyproject.toml`, `Dockerfile`, `vercel.json`, `render.yaml`, `.env.example`, lockfiles).
- [x] Framework detection for React, Vite, Next.js, Vue, Nuxt, FastAPI, Flask, Django, Express.
- [x] Safe command validator with strict allowlists.
- [x] AI deployment planner with intent explanation and step-by-step execution sequence.
- [x] Fallback heuristic planner ensuring 100% functionality without requiring an external LLM key.
- [x] Official Vercel REST API v13 integration (project creation, environment injection, deployment, status, logs, live URL).
- [x] Official Render REST API v1 integration (owner resolution, service provisioning, deployment, live URL).
- [x] Multi-stage progress tracker and color-coded live terminal console.
- [x] Automated AI error diagnosis and user-approved self-healing retry workflow (capped to prevent infinite loops).
- [x] Complete automated test suite covering analyzer, planner, security, and REST API.

### 🔮 Version 2 Roadmap
- [ ] **BrowserDeploymentProvider (Playwright)**: Browser automation for hosting providers that do not offer public REST APIs.
- [ ] **Monorepo Split Deployments**: Automated parallel deployment of monorepos where frontend deploys to Vercel and backend concurrently deploys to Render.
- [ ] **Managed Database Provisioning**: One-click provisioning of PostgreSQL / Redis databases with automatic connection string binding.
- [ ] **Custom Domain & SSL Mapping**: Automatic DNS record generation and CNAME verification.
- [ ] **GitHub Webhook Sync**: Continuous deployment triggers upon push to the main branch.
