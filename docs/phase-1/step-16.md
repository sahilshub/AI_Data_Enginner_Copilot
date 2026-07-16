# Phase 1 – Step 16

# Docker Hardening

## Goal

Fix five real problems found by actually reading the Docker setup, not
assuming it was fine because it worked: secrets baked into the image,
plaintext credentials committed to `docker-compose.yml`, no health checks,
unwanted host port exposure, and a missing `.dockerignore`.

---

# Why This Step Exists

None of this was hypothetical — each was confirmed by reading the actual
`Dockerfile`/`docker-compose.yml`:

1. **`Dockerfile` bakes `.env` into the image** (`COPY .env .env`) — the
   real `SECRET_KEY` and DB credentials end up permanently in an image
   layer, extractable from any copy of the image (`docker save`, a pushed
   registry image, even `docker history`). It's also redundant:
   `docker-compose.yml` already injects `.env` at runtime via `env_file:`.
2. **Plaintext credentials directly in `docker-compose.yml`** —
   `POSTGRES_PASSWORD=postgres`, and `postgres:postgres` repeated inline in
   `DATABASE_URL` for both `api` and `worker`. This file is committed to
   git — every clone of this repo has the DB password regardless of what's
   actually in (gitignored) `.env`.
3. **No health checks** — `depends_on: [db, redis]` only waits for the
   container *process* to start, not for Postgres/Redis to actually be
   ready to accept connections. A real, common Compose race condition.
4. **`db` (5434) and `redis` (6379) are published directly to the host** —
   this defeats Step 15's entire point (Nginx as the one controlled entry
   point). Anyone reaching the host's network can connect straight to
   Postgres — with the trivial `postgres`/`postgres` credentials — or
   Redis, bypassing the app and proxy entirely.
5. **No `.dockerignore`** — not a leak today (the Dockerfile only `COPY`s
   specific paths), but there's nothing stopping a future broad `COPY . .`
   from accidentally including `.env`, `.git`, or `.venv` in an image.

---

# Key Concepts

## Runtime Injection, Not Build-Time Baking

A container image should be reusable across environments (dev/staging/
prod) without containing any environment's actual secrets. Secrets belong
in environment variables injected when the container *starts* (Compose's
`env_file:`/`environment:`, or a real secrets manager in production), never
`COPY`'d into the image at build time.

## Compose's Own `.env` Substitution vs a Service's `env_file:`

These are two different mechanisms that are easy to conflate:
* `env_file:` on a service injects that file's variables as environment
  variables *inside that container* at runtime.
* A `.env` file in the same directory as `docker-compose.yml` is read by
  **Compose itself** to substitute `${VAR}` placeholders *within the
  compose file*, before it ever builds/runs anything.

Using the second mechanism for `POSTGRES_PASSWORD` etc. means
`docker-compose.yml` itself never contains a literal secret — just a
placeholder — so the file committed to git is safe regardless of what
real value `.env` (gitignored) holds locally.

## `depends_on: condition: service_healthy`, Not Just `depends_on`

Plain `depends_on` only sequences container *start order*. Pairing it with
a `healthcheck:` on the depended-on service and
`condition: service_healthy` on the dependent makes Compose actually wait
for readiness — e.g. `api` won't start until `pg_isready` succeeds against
`db`, not just until the `db` process has been launched.

## Internal-Only Services Don't Need Host Ports

A service only needs a `ports:` mapping if something *outside* the Compose
network needs to reach it directly. `db` and `redis` are only ever
addressed by other containers (`api`, `worker`) via the Compose network's
service-name DNS (`db:5432`, `redis:6379`) — removing their host port
mappings doesn't break anything internal, it only closes an unnecessary
external attack surface. (For occasional manual inspection, `docker exec`
into the container, or temporarily add the port mapping back for that
session — not as the permanent default.)

---

# Explicitly Out of Scope (This Step)

* A real secrets manager (Vault, AWS Secrets Manager, Docker Swarm/K8s
  secrets) — appropriate for an actual production deployment, not a local
  learning-project Compose setup. Compose's own `.env` substitution is the
  right-sized fix here.
* TLS between Nginx and `api` (internal, Compose-network-only traffic) —
  external TLS termination at Nginx was already out of scope in Step 15
  and stays that way.

---

# Implementation Requirements

* `Dockerfile`: remove `COPY .env .env`.
* `docker-compose.yml`:
  * Replace literal `postgres`/`postgres` credentials with
    `${POSTGRES_USER}`/`${POSTGRES_PASSWORD}`/`${POSTGRES_DB}` substitution.
  * Add `healthcheck:` to `db` (`pg_isready`), `redis` (`redis-cli ping`),
    `api` (curl `/health`).
  * Change `api`/`worker`/`nginx`'s `depends_on` to
    `condition: service_healthy` for `db`/`redis` where applicable.
  * Remove `ports:` from `db` and `redis`.
* `.dockerignore`: exclude `.venv`, `.git`, `__pycache__`, `.env`, and
  similar.
* `Dockerfile`: install `curl` (needed for the new `api` healthcheck — not
  present in the current `apt-get install` list).

---

# Deliverables

* Building a fresh image and inspecting it shows no `.env` contents inside.
* `docker-compose.yml` contains no literal secret values.
* `docker compose ps` shows healthy status for `db`/`redis`/`api` once
  each is actually ready, not just started.
* `db` and `redis` are unreachable from the host; only `nginx` (port 80)
  is.
* The app continues to work exactly as before through Nginx — this step
  changes operational safety, not behavior.

---

# What We Have Built So Far

Phase 1, Steps 1–16: backend foundation through observability, connector
abstraction, performance fixes, async jobs, Nginx reverse proxy, and now
Docker hardening.
Phase 2, Steps 1–4: bring-your-own-key LLM providers, bounded context
assembly, single active provider, tool-calling schema exploration.
