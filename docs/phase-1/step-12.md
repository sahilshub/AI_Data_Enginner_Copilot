# Phase 1 – Step 12

# Scaling Sync & Refresh for Large Schemas

## Goal

Make `POST /metadata/sync` and `POST /metadata/refresh` cheap for schemas
with hundreds of tables today, and safe for schemas of any size in the
future — without blocking the caller's HTTP request on either.

At the end of this step:

* Column discovery is a single query per schema, not one query per table.
* Sync and refresh run as background jobs the caller can poll, instead of
  holding the HTTP connection open for the full duration of the work.

---

# Why This Step Exists

`metadata_sync_service.sync_connection_metadata()` and
`metadata_refresh_service.detect_changes()` both fetch a table's columns
*inside* a per-table loop — for a 90-table schema that's 90 sequential
round-trips to the target database. This is the actual reason a sync/refresh
against a real schema takes long enough to matter.

Even after fixing that, a sufficiently large schema (thousands of tables, or
a slow/remote target database) will still take real time. A synchronous
HTTP route ties up the caller's connection for that whole duration and risks
a reverse-proxy or client timeout — a problem that gets worse, not better,
as schemas grow. Fixing the query pattern and fixing the blocking-request
problem are two different fixes; this step does both.

---

# Real World Example

Without batching:

```
sync 90 tables
  → get_tables()          [1 query]
  → get_columns("t1")     [1 query]
  → get_columns("t2")     [1 query]
  → ...                   [88 more queries]
```

With batching:

```
sync 90 tables
  → get_tables()              [1 query]
  → get_columns_bulk()        [1 query — all columns, all tables, grouped in Python]
```

Without background jobs, a hypothetical 5,000-table warehouse schema means
the client's HTTP request (and any reverse proxy/load balancer in front of
it) sits open for however long that takes — commonly longer than typical
30–60s proxy timeouts. With background jobs, the request returns
immediately with a job id, and the client polls when it's convenient.

---

# Key Concepts

## Batch Introspection

Query the whole schema's columns once (`information_schema.columns WHERE
table_schema = :schema_name`, no `table_name` filter), then group rows by
`table_name` in Python. Same total data, one round-trip instead of N.

## Background Jobs (in-process, not a task queue)

FastAPI's built-in `BackgroundTasks` runs a function after the response is
sent, in the same process. No new infrastructure (no Celery, no Redis) —
appropriate at this project's scale. The tradeoff: a job is lost if the
process restarts mid-run. That's an acceptable risk for a single-instance
dev/learning deployment; a real task queue is the correct upgrade *if* this
ever needs to survive restarts or run across multiple worker processes —
not something to build ahead of that need.

## Job Status as Data, Not Just a Response

The result of "did the sync finish, and what happened" has to be queryable
after the triggering request is long gone — so it's a stored `SyncJob` row,
not just an HTTP response body.

---

# Architecture

Current

```
POST /metadata/sync → MetadataSyncService (runs fully) → SyncResponse (200)
```

New

```
POST /metadata/sync → SyncJob(status=pending) created → 202 {job_id}
                          │
                          ▼ (BackgroundTasks, after response sent)
                    SyncJob(status=running)
                          │
                    MetadataSyncService (unchanged — now bulk column fetch)
                          │
                    SyncJob(status=completed | failed, result_summary)

GET /connections/{id}/jobs/{job_id} → current SyncJob state
```

---

# Folder Changes

```
app/
├── models/
│   └── sync_job.py              # SyncJob
├── repositories/
│   └── sync_job_repository.py   # create / mark_running / mark_completed / mark_failed / get_by_id
├── services/
│   └── job_runner.py            # background-task functions; open their own DB session
├── schemas/
│   └── job_schema.py            # JobAcceptedResponse, JobResponse
├── api/
│   └── jobs.py                  # GET /connections/{id}/jobs, GET .../jobs/{job_id}
```

`SchemaRepository`/`SourceConnector` gain one method
(`get_columns_bulk(schema_name)`); `MetadataSyncService` and
`MetadataRefreshService` keep their existing responsibilities and are not
restructured — they just call the bulk method instead of looping.

---

# API Changes

## Sync (contract change)

```
POST /connections/{id}/metadata/sync?schema_name=...
```

Before: `200` with `{"message": ..., "tables_synced": N}` once sync finishes.
After: `202` with `{"job_id": ..., "status": "pending"}` immediately.

## Refresh (contract change)

```
POST /connections/{id}/metadata/refresh?schema_name=...
```

Same shift: `202` + `job_id` instead of `200` + result.

## New: Job Status

```
GET /connections/{id}/jobs/{job_id}
```

```json
{
  "id": 12,
  "job_type": "sync",
  "status": "completed",
  "result_summary": {"tables_synced": 90},
  "error_message": null,
  "created_at": "...",
  "started_at": "...",
  "completed_at": "..."
}
```

```
GET /connections/{id}/jobs
```

Recent job history for a connection.

---

# Explicitly Out of Scope (This Step)

* No task queue (Celery/RQ/arq) — noted above as the future upgrade if
  durability across restarts is ever needed.
* No websocket/SSE push for job completion — polling only.
* No change to `discover_relationships` (`POST /relationships/discover`) —
  it's a single already-batched query and isn't part of the sync/refresh
  latency problem.

---

# Implementation Requirements

### Batching

* `SchemaRepository.get_columns_bulk(schema_name) -> Dict[str, List[dict]]`
* `SourceConnector.get_columns_bulk()` (abstract) + `PostgresConnector` impl
* `metadata_sync_service.py` and `metadata_refresh_service.py` updated to
  call it instead of per-table `get_columns()`

### Jobs

* `SyncJob` model + Alembic migration
* `SyncJobRepository`
* `app/services/job_runner.py` — `run_sync_job()`, `run_refresh_job()`,
  each opening its own DB session
* `POST /metadata/sync` / `POST /metadata/refresh` switched to `202` +
  `BackgroundTasks`
* `GET /connections/{id}/jobs/{job_id}`, `GET /connections/{id}/jobs`

---

# Deliverables

* Sync/refresh against a real multi-table schema completes in one
  column round-trip instead of N.
* Callers get an immediate response regardless of schema size and poll for
  completion.
* Existing `MetadataSyncService`/`MetadataRefreshService` business logic is
  unchanged — this step only changes how they're invoked and how their
  result is reported.

---

# What We Have Built So Far

Step 1–10: backend foundation through observability (Phase 1 complete).
Step 11: multi-source connector abstraction.
Step 12: batched introspection + background job handling for sync/refresh.

---

# What's Next

## Phase 2 – Step 1

### Local LLM Integration (Ollama)

This is the beginning of the AI engineering portion of the project.

You will learn:

* What an LLM actually is
* How Ollama works
* Model selection
* Context windows
* Prompt construction
* Local inference

First feature:

Ask:

"Which table stores customer information?"

The LLM will answer using metadata from your platform.

This will be your first end-to-end AI feature.
