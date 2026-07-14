# AI Data Engineering Copilot

AI Data Engineering Copilot is a production-inspired AI engineering project designed to help data engineers, analytics engineers, backend developers, and database administrators understand, manage, and interact with complex database systems using natural language.

The platform allows users to connect PostgreSQL databases, automatically discover and understand database schemas, explore tables and relationships, generate SQL queries from natural language, safely execute queries, analyze data quality issues, generate technical documentation, and create migration scripts with AI assistance.

Unlike traditional chatbot-based AI projects, this project focuses on solving real-world data engineering and backend engineering problems. It combines software engineering best practices with modern AI application development techniques, including schema-aware context generation, retrieval-augmented generation (RAG), structured outputs, tool calling, embeddings, vector search, agent orchestration, evaluation frameworks, and production monitoring.

The project is intentionally built in incremental phases, starting with backend foundations and database connectivity before introducing AI capabilities. Each phase focuses on understanding the underlying engineering concepts, architectural decisions, trade-offs, and implementation details rather than relying on AI-generated code alone. This approach ensures a deep understanding of both the software engineering and AI engineering aspects of the system.

---

# Project Vision

This project is NOT a demo.

It is a production-inspired learning project whose purpose is to teach both Software Engineering and AI Engineering from first principles.

The end goal is to build an AI Data Engineering Copilot capable of:

* Connecting to PostgreSQL databases
* Understanding database schemas
* Answering schema questions
* Generating SQL
* Safely executing SQL
* Creating documentation
* Performing data quality analysis
* Generating migration scripts
* Using multiple AI agents

Every implementation should prioritize clarity, maintainability, and learning over speed.

---

# Primary Goal

Do NOT optimize for writing code quickly.

Optimize for teaching.

Before writing code:

1. Explain the problem.
2. Explain why this feature exists.
3. Explain how this feature fits into the overall architecture.
4. Explain alternative approaches.
5. Explain why the chosen approach is preferred.

Only after that should code be generated.

---

# Development Principles

Always follow these principles:

1. Keep business logic out of API routes.
2. Keep database logic out of services.
3. Keep AI logic isolated.
4. Build loosely coupled modules.
5. Prefer composition over large monolithic classes.
6. Explain every architectural decision.

---

# Code Quality

Generated code should be:

* Production-ready
* Readable
* Well documented
* Type hinted
* PEP 8 compliant
* Modular
* Testable

Avoid shortcuts.

Do not generate unnecessary abstractions.

---

# Preferred Technology Stack

Language

* Python 3.12

Backend

* FastAPI

Database

* PostgreSQL

ORM

* SQLAlchemy 2.x

Validation

* Pydantic v2

Migrations

* Alembic

Containerization

* Docker
* Docker Compose

AI

* Ollama
* Any free available models

Embeddings

* Nomic Embed Text

Vector Storage

* pgvector initially

Agent Framework

* LangGraph (later phases only)

Deployment

* AWS (later)

Testing

* pytest

---

# AI Rules

Never introduce AI libraries unless the roadmap explicitly reaches that phase.

Current progression:

Phase 1
Backend foundation

Phase 2
Database connections

Phase 3
Schema discovery

Phase 4
LLM integration

Phase 5
Text-to-SQL

Phase 6
Safe SQL execution

Phase 7
RAG

Phase 8
Documentation generation

Phase 9
Data quality analysis

Phase 10
Migration generation

Phase 11
Multi-agent architecture

Phase 12
Evaluation and monitoring

Never skip phases.

Note: `docs/phase-1/step-N.md` files track granular implementation steps
*within* Phase 1 (backend foundation through metadata search/exploration).
They are a finer-grained log than the macro phases above — do not confuse
"Phase 3" here with "phase-1/step-N"; check the docs folder for the actual
current step before assuming what's implemented.

---

# Project Structure

Follow this structure unless instructed otherwise.

app/
├── api/
├── core/
├── database/
├── models/
├── repositories/
├── schemas/
├── services/
├── ai/
├── prompts/
├── utils/

docs/
tests/

---

# Folder Responsibilities

API

* HTTP endpoints only

Services

* Business logic

Repositories

* Database operations

Schemas

* Request/response validation

Models

* Database entities

Core

* Configuration
* Logging
* Security

AI

* LLM integration
* Prompt orchestration
* Agent implementations

Prompts

* Prompt templates

Utils

* Shared helper functions

Never violate these boundaries.

---

# Dependency Management

* `pyproject.toml` is the source of truth for dependencies (this project uses `uv`).
* Keep `requirements.txt` in sync if it's kept around for Docker/CI — don't let
  new packages get added to one and not the other.
* Never add a dependency (including AI/embedding libraries) ahead of the phase
  that calls for it.

---

# Local Environment & Tooling

* **Docker is available** in this environment. The project's Postgres and API
  containers are managed via [docker-compose.yml](docker-compose.yml):
  * `docker compose up -d db` — start just the Copilot's own Postgres
    (container `aidataenginnercopilot-db-1`, mapped to host port `5434`,
    database `copilot_db`).
  * `docker compose up -d` — start both `db` and `api`.
  * `docker compose down` — stop containers (add `-v` only if you intend to
    also delete the `postgres_data` volume — that's a destructive, confirm-first action).
  * Other unrelated Postgres containers may already be running on the host
    (different projects) — always check `docker ps` and target the right
    container/port before running destructive commands.

* **`SECRET_KEY` is required** (Fernet key encrypting stored target-DB
  passwords, see `app/core/security.py`) — the app fails to start without it,
  there is no insecure default. Generate one per environment; see README.md.

* **Alembic** manages all schema migrations for the Copilot's own catalog DB
  (never for target/external databases — those are only ever introspected,
  never migrated).
  * `alembic upgrade head` — apply all migrations (run this after a fresh
    volume reset / after wiping the `postgres_data` volume).
  * `alembic revision --autogenerate -m "description"` — generate a new
    migration after changing a model in `app/models/`.
  * `alembic downgrade -1` — roll back the most recent migration.
  * Migration scripts live in `alembic/versions/`; review autogenerated
    migrations before applying — autogenerate can miss things like check
    constraints or renamed columns.

---

# Engineering Guardrails (Lessons Learned)

Concrete pitfalls hit during this project, kept here so they aren't repeated:

* **Introspecting Postgres foreign keys via `information_schema`**: joining
  `key_column_usage` (source columns) to `constraint_column_usage` (target
  columns) on `constraint_name` alone is a cross join for composite FKs, and
  duplicate constraint objects (e.g. from inherited/partitioned tables) can
  still produce duplicate rows even with a correct join. Use
  `referential_constraints` + `position_in_unique_constraint` to pair columns
  positionally, and `SELECT DISTINCT` to collapse duplicate constraint
  objects. Test schema-introspection queries against a real database with
  composite keys before trusting them against a simple test schema.
* Any code that reads live database metadata (schema discovery, relationship
  discovery) should be validated against a real, non-trivial target schema —
  toy schemas with only single-column FKs won't surface these issues.
* **Table/relationship identity must include schema, not just name.**
  `schema_tables` always had a `schema_name` column, but `schema_relationships`
  didn't until it was retrofitted — meaning two tables with the same name in
  different schemas on one connection would have their relationships silently
  conflated. Any new metadata entity that identifies a table/column should be
  schema-qualified from the start, not bolted on later once real multi-schema
  data exposes the gap.
* **Stored credentials must be encrypted at rest from the start.** Target-DB
  passwords in `database_connections` were originally plaintext with just a
  code comment flagging it as a known gap — encrypting it later required a
  data migration to re-encrypt existing rows in place. Any new column storing
  a secret should be encrypted before the first row is ever written, not
  after.

---

# Success Criteria

By the end of this project I should understand:

* Backend architecture
* API design
* Database design
* SQLAlchemy
* PostgreSQL
* Docker
* AI application architecture
* Prompt engineering
* Tool calling
* RAG
* Embeddings
* Vector databases
* LangGraph
* Multi-agent systems
* Evaluation
* Monitoring
* Deployment

Every phase should move me measurably closer to these goals.
