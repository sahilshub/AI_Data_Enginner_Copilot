# Phase 1 – Step 14

# Consolidate Metadata Write Endpoints into One Refresh

## Goal

Replace three overlapping ways to update the catalog with one: `POST
/connections/{id}/metadata/refresh` becomes the only trigger endpoint for
bringing the catalog up to date. `POST /metadata/sync` and `POST
/relationships/discover` are removed as callable endpoints — their
underlying services aren't deleted, `refresh` already calls both.

---

# Why This Step Exists

Three endpoints existed for updating the catalog, each added in a
different step without revisiting the others:

| Endpoint | Tables/columns | Relationships | Change detection |
|---|---|---|---|
| `POST /metadata/sync` (Step 4-5) | ✅ | ❌ | ❌ |
| `POST /relationships/discover` (Step 6) | ❌ | ✅ | ❌ |
| `POST /metadata/refresh` (Step 9, async in Step 13) | ✅ | ✅ | ✅ |

`refresh` is a strict superset of the other two combined, plus diffing. It
also works correctly as the *first* call for a brand-new connection — its
"before" snapshot is just empty, so everything discovered correctly shows
up as `TABLE_ADDED`/`RELATIONSHIP_ADDED` and gets persisted regardless.
There was never a scenario where `sync` or `discover` could do something
`refresh` couldn't.

The original reason to keep relationship discovery separate — it used to
cost ~40 seconds via the old `information_schema`-based query, so skipping
it might matter — mostly disappeared after Step 12's `pg_catalog` rewrite
(~4 seconds now against the real 90-table test schema). The cost argument
that justified three endpoints no longer holds at the same weight.

Leftover overlapping endpoints aren't just untidy — they're a real
usability problem for whatever calls this API next. Phase 2's Q&A layer
will need one unambiguous way to say "make sure the context is fresh"
without a caller having to first learn there are three partially-redundant
options and guess which one is "enough."

---

# What Changes

* `POST /connections/{id}/metadata/sync` — **removed**.
* `POST /connections/{id}/relationships/discover` — **removed**.
* `POST /connections/{id}/metadata/refresh` — gains one optional param:
  `include_relationships: bool = True`. Set to `false` for the narrow case
  of wanting schema-only (skip FK re-discovery).
* `MetadataSyncService.sync_connection_metadata()` and
  `RelationshipService.discover_relationships()` are **not deleted** —
  `MetadataRefreshService` still calls them internally exactly as before.
* All `GET` endpoints (`/metadata/tables`, `/relationships`, etc.) are
  unchanged — this only affects the write/trigger side.

This is a breaking API change with no migration path offered — there are
no external consumers of this API today, so a clean removal is preferred
over carrying two deprecated-but-working endpoints indefinitely.

---

# Explicitly Out of Scope (This Step)

* No change to the underlying sync/relationship-discovery logic itself.
* No versioning scheme (e.g. `/v1/`, `/v2/`) introduced to soften the
  breaking change — not warranted for a project with no external callers.

---

# Implementation Requirements

* `app/services/metadata_refresh_service.py` — `refresh_metadata()` and
  `detect_changes()` accept `include_relationships: bool = True`; skip
  relationship diffing/discovery when `False`.
* `app/tasks/metadata_tasks.py` — `refresh_metadata_task` threads the flag
  through to the service.
* `app/api/metadata_refresh.py` — `POST /refresh` exposes
  `include_relationships` as a query param.
* `app/api/metadata.py` — remove the `POST /sync` route (keep the `GET`
  routes and the `MetadataSyncService` import they still need).
* `app/api/relationship.py` — remove the `POST /discover` route (keep the
  `GET` routes).

---

# Deliverables

* One write endpoint (`refresh`) instead of three overlapping ones.
* `sync`/`discover` still work as internal services, just not as directly
  callable routes.
* `refresh` remains correct as both the first-ever catalog population and
  every subsequent update.

---

# What We Have Built So Far

Phase 1, Steps 1–14: backend foundation through observability, multi-source
connector abstraction, performance/correctness fixes, async job handling,
search performance, connector caching, and now a single consolidated
metadata-refresh endpoint.

---

# Next Step

## Phase 2 – Step 1

### LLM Provider Integration (Bring-Your-Own-Key)

Unchanged — see `docs/phase-2/step-1.md`.
