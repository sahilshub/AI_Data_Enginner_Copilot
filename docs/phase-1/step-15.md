# Phase 1 – Step 15

# Reverse Proxy with Nginx

## Goal

Put Nginx in front of the API as the single published entry point, instead
of exposing Uvicorn directly to the host. Learn the basic, actually-necessary
parts of a reverse proxy setup — not TLS, not load balancing, just the core
mechanics of "one door in, correctly forwarded to the right service behind
it."

---

# Why This Step Exists

`docker-compose.yml` currently publishes the `api` service's port 8000
straight to the host — Uvicorn is directly internet-facing (or would be, in
a real deployment). That's not how production systems are built:

* App servers (Uvicorn, Gunicorn, etc.) are built to run application code
  correctly, not to be hardened against arbitrary edge traffic — slow
  clients holding connections open, malformed requests, raw TLS.
  Reverse proxies exist specifically for that edge-facing role.
* A stack with multiple services (`api`, `worker`, `db`, `redis`) benefits
  from one stable public entry point regardless of how the internals are
  arranged — and if `api` is ever scaled to multiple replicas, the proxy
  is also what load-balances across them.
* Without a proxy correctly forwarding client info, this project's own
  structured request logging (Step 10) would be blind to real client
  IPs/hosts the moment anything *does* sit in front of it — so getting the
  forwarded headers right isn't optional polish, it's the actual point.

---

# Real World Example

Without a proxy:

```
Client → api:8000 (Uvicorn directly)
```
Every client talks straight to the app process. No single choke point for
TLS, logging, or future load balancing.

With a proxy:

```
Client → nginx:80 → api:8000 (internal Docker network only)
```
`api` is no longer published to the host at all — only reachable through
`nginx`, which is how this would actually be deployed.

---

# Key Concepts

## Reverse Proxy vs Forward Proxy

A forward proxy sits in front of *clients*, hiding them from the servers
they talk to (e.g. a corporate VPN proxy). A reverse proxy sits in front of
*servers*, hiding them from clients — clients think they're talking
directly to it. Nginx here is a reverse proxy: from the outside, "the app"
*is* Nginx.

## Forwarded Headers (the actual "basic necessary" part)

When Nginx proxies a request to `api`, the connection FastAPI sees comes
from Nginx's IP, not the real client's — and the `Host` header would be
whatever Nginx sends unless told otherwise. Three headers fix this:

* `X-Real-IP` / `X-Forwarded-For` — the real client IP.
* `X-Forwarded-Proto` — whether the original request was `http` or
  `https` (matters once TLS terminates at the proxy — the backend
  otherwise has no way to know the original request was secure).
* `Host` — forwarded as-is so the backend sees the domain the client
  actually requested, not `api:8000`.

This is the part a lot of tutorials skip and just do `proxy_pass` — without
these headers, a reverse proxy technically works but silently corrupts
anything downstream that reads client IP or scheme (logging, rate limiting,
redirects).

## Docker Network Service Discovery

`nginx` reaches `api` the same way `worker` already reaches `redis`/`db` —
by service name over the Compose-created network (`api:8000`), not
`localhost`. No new concept here, same mechanism already in use.

---

# Architecture

```
Host port 80
    │
    ▼
nginx (container, single published port)
    │  proxy_pass to api:8000, with forwarded headers set
    ▼
api (container, port 8000 — no longer published to the host)
```

---

# Folder Changes

```
nginx/
└── nginx.conf         # reverse proxy config

docker-compose.yml      # + nginx service; api's port 8000 no longer published
```

---

# Explicitly Out of Scope (This Step)

* **TLS/HTTPS** — needs a real domain and certificate (or a self-signed
  cert, which teaches the wrong lesson for real deployment). Natural next
  step once there's a domain to attach it to.
* **Load balancing multiple `api` replicas** — no current need with one
  instance; the config here is structured so adding replicas later is a
  config change, not a rewrite.
* **Rate limiting, caching, WAF rules** — real Nginx capabilities, real
  future steps, not part of a *basic necessary* setup.

---

# Implementation Requirements

* `nginx/nginx.conf` — reverse proxy to `api:8000`, setting `Host`,
  `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto`.
* `docker-compose.yml`:
  * New `nginx` service (official `nginx:alpine` image, mounts
    `nginx.conf`), publishes port 80, depends on `api`.
  * `api` service's `ports: ["8000:8000"]` removed — only reachable via
    `nginx` now, matching a real deployment.

---

# Deliverables

* The API is reachable at `http://localhost/` (via Nginx) instead of
  `http://localhost:8000/`.
* `api` is no longer directly reachable from the host — only from other
  containers on the Compose network.
* Request logs show correct forwarding once headers are wired through
  (verifiable by checking `X-Forwarded-For` arrives at the app).

---

# What We Have Built So Far

Phase 1, Steps 1–15: backend foundation through observability, multi-source
connector abstraction, performance/correctness fixes, async job handling,
consolidated metadata refresh, and now a reverse proxy as the app's single
entry point.

---

# Next Step

## Phase 2 – Step 1

### LLM Provider Integration (Bring-Your-Own-Key)

Unchanged — see `docs/phase-2/step-1.md`.
