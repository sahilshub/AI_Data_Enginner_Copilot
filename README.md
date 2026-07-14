# AI Data Engineering Copilot

Welcome to the backend service of the **AI Data Engineering Copilot** project. This project serves as a learning platform for software engineering and AI engineering, architected to grow into a multi-layered, robust backend system.

---

## Architecture Overview

This backend is designed using clear separation of concerns (Layered Architecture):

1. **API Layer (`app/api/`)**: Controller entrypoints. Handles HTTP routing, path parameters, validations, and returns responses.
2. **Service Layer (`app/services/`)**: Orchestrates business logic, application rules, and workflows.
3. **Repository Layer (`app/repositories/`)**: Interfaces with databases and storage engines (future database integrations).
4. **Models Layer (`app/models/`)**: Defines database schemas / ORM entities (future database integrations).
5. **Schemas Layer (`app/schemas/`)**: Houses request/response data shapes using Pydantic models.
6. **Core Layer (`app/core/`)**: Holds shared utilities, environment settings, logging, and security.

---

## Directory Structure

```text
ai-data-copilot/
├── app/
│   ├── api/             # API Endpoints & Routers
│   │   ├── __init__.py
│   │   └── health.py
│   ├── services/        # Business Logic Services
│   │   ├── __init__.py
│   │   └── health_service.py
│   ├── repositories/    # Database Data Access (Placeholder)
│   │   └── __init__.py
│   ├── models/          # Database Models (Placeholder)
│   │   └── __init__.py
│   ├── schemas/         # Request & Response Pydantic Schemas
│   │   ├── __init__.py
│   │   └── health_schema.py
│   ├── core/            # Configs & Shared Utils
│   │   └── __init__.py
│   └── main.py          # FastAPI App Entrypoint
├── docs/                # Step guides and documentation
├── requirements.txt     # Python Dependencies
├── .env                 # Environment Configs
└── README.md            # Readme Documentation
```

---

## Installation & Running the Application

### 1. Requirements
Ensure you have **Python 3.12** installed on your system.

### 2. Setup Virtual Environment
Run the following commands in your terminal:
```bash
python -m venv venv
# On Windows (PowerShell)
.\venv\Scripts\Activate.ps1
# On Linux/macOS
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
(Or, if you use [uv](https://github.com/astral-sh/uv): `uv sync` — `pyproject.toml` is the source of truth for dependencies.)

### 4. Configure Environment Variables
Copy the example env file and fill in your own values:
```bash
cp .env.example .env
```
`SECRET_KEY` is **required** — it's the Fernet key used to encrypt registered
target-database passwords at rest (see `app/core/security.py`). There is no
insecure default, so the app will fail to start without it. Generate one with:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
Paste the output into `SECRET_KEY` in `.env`. Use a different key per
environment (dev/staging/prod) — never reuse one.

### 5. Apply Database Migrations
```bash
alembic upgrade head
```

### 6. Start Redis and a Celery Worker
`POST /metadata/sync` and `POST /metadata/refresh` run as async jobs via
Celery, queued on Redis (see `docs/phase-1/step-13.md`). Start Redis:
```bash
docker run -d -p 6379:6379 redis:7-alpine
```
Then start a worker in its own terminal:
```bash
celery -A app.core.celery_app worker --loglevel=info
```
(On Windows, add `--pool=solo`.) Without a running worker, sync/refresh jobs
will queue but never complete — poll `GET /connections/{id}/jobs/{job_id}`
to check.

### 7. Run the Server
Start the development server using Uvicorn:
```bash
uvicorn app.main:app --reload
```

The application will be running on `http://127.0.0.1:8000`.
- **Interactive Documentation**: `http://127.0.0.1:8000/docs`
- **Health Check Endpoint**: `http://127.0.0.1:8000/health` (add `/details` for a dependency check, e.g. catalog DB connectivity)
- **Metrics**: `http://127.0.0.1:8000/metrics` (in-memory request/refresh counters)
- **Async Jobs**: `POST /connections/{id}/metadata/sync` and `/refresh` return a `job_id` immediately — poll `GET /connections/{id}/jobs/{job_id}` for status/results.

Or start everything (API, worker, Postgres, Redis) via Docker Compose:
```bash
docker compose up -d
```
