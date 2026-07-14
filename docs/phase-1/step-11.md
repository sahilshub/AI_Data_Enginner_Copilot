# Phase 1 – Step 11

# Multi-Source Connector Abstraction

## Goal

Stop hard-coding "target database" to mean "PostgreSQL via psycopg2", without
actually building support for any other source yet.

At the end of this step:

* Every service that talks to a target database goes through one
  `SourceConnector` interface instead of building a SQLAlchemy engine and
  writing raw `information_schema` SQL inline.
* A `PostgresConnector` is the only real implementation — behavior for
  existing connections does not change.
* Adding Snowflake, BigQuery, or anything else later means writing one new
  connector class, not touching every service.

This step exists *before* Phase 2 (LLM integration) on purpose: once schema
context starts feeding prompts, retrofitting a connector abstraction under
five services that already assume Postgres is a much bigger job than doing
it now, while there is still only one source to migrate.

---

# Why This Step Exists

Today, `schema_service.py`, `relationship_service.py`,
`metadata_sync_service.py`, and `metadata_refresh_service.py` each have their
own copy of:

```python
url = f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"
engine = create_engine(url, connect_args={"connect_timeout": 5})
```

`DatabaseConnection` already has a `dialect` column — but nothing reads it.
A user could set `dialect="snowflake"` today and every service would still
silently build a `postgresql+psycopg2://` URL and fail with a confusing
driver/auth error instead of a clear "not supported yet" message.

Worse: BigQuery has no host/port/username/password at all — it authenticates
with a service-account JSON key and a project id. Snowflake's connection
shape (account, warehouse, role) doesn't fit the current columns either.
Neither fits `information_schema`-based FK introspection the way Postgres
does. None of this is a "swap the connection string" problem.

---

# Real World Example

Without an abstraction:

```
schema_service.py       → builds Postgres URL, calls SchemaRepository
relationship_service.py → builds Postgres URL, calls RelationshipRepository
metadata_sync_service.py → builds Postgres URL, calls SchemaRepository
metadata_refresh_service.py → builds Postgres URL, calls both
```

Adding Snowflake means editing all four, each slightly differently, and
hoping nothing was missed.

With an abstraction:

```
schema_service.py       → get_connector(connection) → connector.get_tables()
relationship_service.py → get_connector(connection) → connector.get_foreign_keys()
metadata_sync_service.py → get_connector(connection) → connector.get_tables()/.get_columns()
metadata_refresh_service.py → get_connector(connection) → all three
```

Adding Snowflake means writing `SnowflakeConnector` and registering it in
one factory function. No service changes.

---

# Key Concepts

## Adapter Pattern

Each source (Postgres, Snowflake, BigQuery, ...) gets its own class
implementing the same interface: `test_connection()`, `get_tables()`,
`get_columns()`, `get_foreign_keys()`. Services depend on the interface,
never on a specific source's client library or SQL dialect.

## Factory / Registry

A single function, `get_connector(dialect, ...)`, maps a `dialect` string to
a connector class. Unsupported dialects raise a clear `400` at connector
creation time — not a confusing failure three layers deep during schema
introspection.

## Flexible Credentials

`host`/`port`/`username`/`password`/`database` describe a Postgres (or
Postgres-shaped) connection. They don't describe BigQuery (service account
JSON + project id) or fully describe Snowflake (account identifier,
warehouse, role). Rather than adding source-specific columns later — another
disruptive migration — add one flexible `extra_config` JSON column now, even
though only Postgres uses it today.

---

# Architecture

Current

```
Service → create_engine(postgres_url) → SchemaRepository / RelationshipRepository
```

New

```
Service → get_connector(dialect, credentials) → SourceConnector
                                                     │
                                          ┌──────────┴──────────┐
                                   PostgresConnector      (future) SnowflakeConnector, BigQueryConnector
                                          │
                                SchemaRepository / RelationshipRepository
                                (unchanged — now an implementation detail
                                 of PostgresConnector, not called directly
                                 by services)
```

---

# Folder Changes

```
app/
├── connectors/
│   ├── __init__.py
│   ├── base.py                 # SourceConnector ABC
│   ├── postgres_connector.py   # the only real implementation
│   └── factory.py              # get_connector(dialect, ...) -> SourceConnector
├── models/
│   └── connection.py           # + extra_config (JSON, nullable)
```

`SchemaRepository` and `RelationshipRepository` are not rewritten — they
already take an `Engine` and know nothing about HTTP or credentials.
`PostgresConnector` becomes their only caller.

---

# Connector Interface

```python
class SourceConnector(ABC):
    def test_connection(self) -> tuple[bool, str]: ...
    def get_tables(self, schema_name: str) -> list[dict]: ...
    def get_columns(self, table_name: str, schema_name: str) -> list[dict]: ...
    def get_foreign_keys(self, schema_name: str) -> list[dict]: ...
```

Return shapes match what `SchemaRepository`/`RelationshipRepository`
already produce, so no changes ripple into the schemas layer.

---

# Explicitly Out of Scope (This Step)

* No Snowflake or BigQuery connector is implemented. `get_connector()`
  raises `400` for any dialect other than `postgresql`.
* `ConnectionService.test_connection()` (the pre-save credential ping) is
  left as-is — it already branches lightly on dialect for URL building and
  isn't schema-introspection code. Folding it into the connector interface
  is a follow-up, not required to unblock Phase 2.
* No change to stored data for existing connections. `extra_config`
  defaults to `NULL` and is unused by `PostgresConnector`.

---

# Implementation Requirements

### Core

* `app/connectors/base.py` — `SourceConnector` ABC
* `app/connectors/postgres_connector.py` — wraps `SchemaRepository` +
  `RelationshipRepository.get_foreign_keys_from_target`, owns engine
  creation and credential decryption
* `app/connectors/factory.py` — `get_connector(dialect, host, port,
  username, password, database, extra_config)`, raises `400` for
  unsupported dialects

### Model

* `DatabaseConnection.extra_config` — nullable JSON column
* Alembic migration adding the column
* Reject unsupported `dialect` values at `POST /connections` time
  (`ConnectionService.create_connection`), not just at introspection time

### Services

Refactor to depend on `get_connector()` instead of building engines
directly:

* `schema_service.py`
* `relationship_service.py`
* `metadata_sync_service.py`
* `metadata_refresh_service.py`

---

# Deliverables

* One connector interface, one real implementation (Postgres).
* Every existing route behaves identically — this step changes internal
  structure, not external behavior, for current (Postgres) connections.
* Creating a connection with an unsupported `dialect` now fails fast with a
  clear error instead of a confusing runtime failure later.
* Adding a second source in a future step is scoped to one new file plus a
  factory registration.

---

# What We Have Built So Far

Step 1–10: backend foundation through observability (Phase 1 complete).

Step 11: multi-source connector abstraction — infrastructure groundwork
inserted before Phase 2, so the LLM/agent layers that come next build on a
system that was designed to add sources, not one that has to be
re-architected to allow it.
