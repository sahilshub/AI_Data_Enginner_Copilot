# Phase 1 – Step 13

# Async Sync & Refresh with Celery + Redis

## Goal

Make `POST /metadata/sync` and `POST /metadata/refresh` return immediately
regardless of schema size, by running the actual work on a Celery worker
instead of inside the HTTP request.

This step **supersedes** the "Background Jobs" section of
[step-12.md](step-12.md), which deliberately chose FastAPI's in-process
`BackgroundTasks` over a task queue, reasoning "not something to build ahead
of that need." That reasoning was correct at the time; the decision changed
because durability (surviving a process restart mid-job) and running a
worker as its own separate, independently-scalable process are wanted now,
not deferred.

---

# Why This Step Exists

Step 12 fixed the two actual root causes of slow sync/refresh (batched
column fetch, `pg_catalog`-based FK discovery — 90 tables now takes ~5-10s
total instead of 90+ seconds). That's fast enough that `BackgroundTasks`
was arguably already good enough for schemas this size.

But `BackgroundTasks` runs inside the same FastAPI process:

* If the process restarts (deploy, crash, `--reload` picking up a file
  change) mid-job, the job is silently lost — nothing observes that it
  didn't finish.
* It competes with the API for the same process's resources; a slow job
  can't be isolated onto its own worker.
* It can't be scaled independently — you can't run "3 workers, 1 API" with
  `BackgroundTasks`.

Celery + a broker solves all three: jobs survive an API restart (the broker
holds the queued/in-flight task), workers are separate processes that can
scale independently of the API, and Celery has built-in retry/timeout
handling instead of us reimplementing it.

---

# Real World Example

Without Celery:

```
POST /metadata/sync → 202 {job_id} → BackgroundTasks runs sync in-process
   ↓ (API process restarts here)
job silently never completes; job row stuck at "running" forever
```

With Celery:

```
POST /metadata/sync → SyncJob row created → task queued on Redis → 202 {job_id}
   ↓ (API process restarts — doesn't matter, task is on the broker)
Celery worker (separate process) picks up the task, runs it, updates SyncJob
```

---

# Key Concepts

## Broker

Celery needs somewhere to queue tasks. **Redis** is used here: free,
self-hosted (one more service in `docker-compose.yml`, same pattern as
`db`), and simple enough to serve as both the broker *and* the result
backend — no second piece of infrastructure needed. RabbitMQ is the other
common choice; Redis is preferred here for being one dependency instead of
two, at a scale where RabbitMQ's extra durability guarantees aren't needed.

## Durable Job State Lives in Postgres, Not Just Redis

Celery's Redis result backend is TTL-based — results expire and can be
evicted on a Redis restart. That's fine for "did my task finish in the last
few minutes" but not for a queryable job history. So job state is still a
`SyncJob` row in the Copilot's own catalog DB (same idea as step-12's
original plan), correlated to the Celery task via `celery_task_id`. Celery
handles *running* the work reliably; Postgres remains the source of truth
for *what happened*.

## Workers Are a Separate Process

A Celery worker is not part of the FastAPI process — it's launched
separately (`celery -A app.core.celery_app worker`) and imports the same
service code, but runs in its own process (and, in Docker, its own
container). It needs its own database session per task — it cannot reuse a
FastAPI request's session, since it isn't part of that request.

---

# Architecture

```
POST /metadata/sync
    │
    ▼
SyncJob(status=pending) saved to Postgres
    │
    ▼
sync_metadata_task.delay(job_id, connection_id, schema_name) ── queued on Redis
    │
    ▼
202 {job_id} returned to caller immediately
    │
    ┊ (separately, whenever a worker is free)
    ▼
Celery worker picks up task
    │
    ▼
SyncJob(status=running)
    │
    ▼
MetadataSyncService.sync_connection_metadata()   ← unchanged, from step 12
    │
    ▼
SyncJob(status=completed | failed, result_summary)

GET /connections/{id}/jobs/{job_id} → reads SyncJob from Postgres directly
```

---

# Folder Changes

```
app/
├── core/
│   └── celery_app.py         # Celery() instance, configured from settings
├── tasks/
│   ├── __init__.py
│   └── metadata_tasks.py     # sync_metadata_task, refresh_metadata_task
├── models/
│   └── sync_job.py           # SyncJob
├── repositories/
│   └── sync_job_repository.py
├── schemas/
│   └── job_schema.py         # JobAcceptedResponse, JobResponse
├── api/
│   └── jobs.py               # GET /connections/{id}/jobs[/{job_id}]
```

`MetadataSyncService` / `MetadataRefreshService` are not changed — tasks
call them exactly as the synchronous routes did.

---

# Config

New settings (`app/core/config.py`), same pattern as `DATABASE_URL`:

* `CELERY_BROKER_URL` — default `redis://localhost:6379/0`
* `CELERY_RESULT_BACKEND` — default `redis://localhost:6379/0` (same Redis,
  different logical DB index optional but not required at this scale)

`docker-compose.yml` overrides both to `redis://redis:6379/0` for container
networking, matching how `DATABASE_URL` is already overridden for `db`.

---

# API Changes

## Sync / Refresh (contract change — same shape as step-12 planned)

```
POST /connections/{id}/metadata/sync?schema_name=...
POST /connections/{id}/metadata/refresh?schema_name=...
```

Before: `200` with the full result once work finishes.
After: `202` with `{"job_id": ..., "status": "pending"}` immediately.

## New: Job Status

```
GET /connections/{id}/jobs/{job_id}
GET /connections/{id}/jobs
```

Same response shape as step-12 planned — `SyncJob` fields, read from
Postgres.

---

# Explicitly Out of Scope (This Step)

* No task result push (websocket/SSE) — polling only, same as step-12.
* No task retry/backoff tuning beyond Celery's defaults — revisit if a
  specific failure mode shows up in practice.
* No RabbitMQ — Redis covers broker + result backend needs at this scale;
  switching later is a config change (`CELERY_BROKER_URL`), not a rewrite,
  since Celery abstracts the broker behind that one setting.
* No separate Celery Beat / scheduled tasks — this step is only about
  making the existing on-demand sync/refresh endpoints async, not adding
  new scheduled jobs.

---

# Implementation Requirements

### Infrastructure

* `redis` service in `docker-compose.yml`
* `celery`, `redis` (Python client) added as dependencies

### Core

* `app/core/celery_app.py`
* `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` settings

### Jobs

* `SyncJob` model + Alembic migration (id, connection_id, job_type,
  schema_name, status, result_summary, error_message, celery_task_id,
  created_at, started_at, completed_at)
* `SyncJobRepository`
* `app/tasks/metadata_tasks.py` — `sync_metadata_task`, `refresh_metadata_task`,
  each opening its own DB session
* `POST /metadata/sync` / `POST /metadata/refresh` switched to `202` +
  `.delay(...)`
* `GET /connections/{id}/jobs/{job_id}`, `GET /connections/{id}/jobs`

### Running a Worker

* `docker-compose.yml` gets a `worker` service (same image as `api`,
  `command: celery -A app.core.celery_app worker --loglevel=info`)
* README documents running a worker locally without Docker

---

# Deliverables

* `sync`/`refresh` return instantly regardless of schema size.
* A job's progress/result survives an API process restart.
* Adding more worker capacity is a matter of running more worker
  processes/containers, not changing application code.

---

# What We Have Built So Far

Step 1–10: backend foundation through observability (Phase 1 complete).
Step 11: multi-source connector abstraction.
Step 12: batched introspection + `pg_catalog`-based FK discovery.
Step 13: async sync/refresh via Celery + Redis.

---

# Next Step

## Phase 2 – Step 1

### Local LLM Integration (Ollama)

Unchanged from the original roadmap.
