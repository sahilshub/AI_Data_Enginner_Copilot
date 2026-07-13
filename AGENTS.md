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
