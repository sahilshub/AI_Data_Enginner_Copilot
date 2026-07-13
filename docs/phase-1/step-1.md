# Phase 1 – Step 1

# Backend Foundation Setup

## Objective

Build the foundational backend structure for the AI Data Engineering Copilot.

At this stage we are NOT implementing:

* AI models
* OpenAI/Ollama integration
* Database connectivity
* Schema extraction
* RAG
* Vector databases

The goal is to create a maintainable backend architecture that future features can build upon.

---

# Business Problem

The final product will eventually allow users to:

* Connect databases
* Explore schemas
* Generate SQL
* Analyze data quality
* Generate documentation

Before implementing those capabilities, we need a clean project structure.

Without proper architecture, future features become difficult to maintain, test, and extend.

---

# Learning Goals

By completing this step, you should understand:

* Why backend applications use layers
* How FastAPI routes work
* The purpose of Services
* The purpose of Schemas
* Request → Response lifecycle
* Basic project organization

---

# Architecture

Current Architecture:

User
→ API Layer
→ Service Layer
→ Response

Future Architecture:

User
→ API Layer
→ Service Layer
→ Repository Layer
→ PostgreSQL

and later:

User
→ API Layer
→ Service Layer
→ AI Layer
→ PostgreSQL
→ Vector Database

---

# Folder Structure

```text
ai-data-copilot/

├── app/
│   ├── api/
│   │   └── health.py
│   │
│   ├── services/
│   │   └── health_service.py
│   │
│   ├── repositories/
│   │   └── __init__.py
│   │
│   ├── models/
│   │   └── __init__.py
│   │
│   ├── schemas/
│   │   └── health_schema.py
│   │
│   ├── core/
│   │   └── __init__.py
│   │
│   └── main.py
│
├── docs/
│   └── phase-1-step-1.md
│
├── tests/
│
├── requirements.txt
│
├── README.md
│
└── .env
```

---

# Layer Responsibilities

## API Layer

Purpose:

* Receive HTTP requests
* Validate requests
* Return responses

Should NOT contain:

* Business logic
* Database logic
* AI logic

Example:

```python
@app.get("/health")
def health():
    return service.get_status()
```

---

## Service Layer

Purpose:

* Business logic
* Application rules
* Feature orchestration

Examples:

* HealthService
* DatabaseService
* SchemaService
* AIService

---

## Repository Layer

Purpose:

* Database communication

Examples:

* DatabaseConnectionRepository
* SchemaRepository

Not used in this step.

---

## Schemas

Purpose:

* Request models
* Response models
* Validation

Example:

```python
class HealthResponse(BaseModel):
    status: str
```

---

## Models

Purpose:

Database table definitions.

Not used in this step.

---

## Core

Purpose:

Shared utilities and configuration.

Future examples:

* settings.py
* security.py
* logging.py

---

# Endpoint Specification

## GET /health

Purpose:

Verify application is running.

Response:

```json
{
  "status": "healthy"
}
```

Status Code:

```text
200 OK
```

---

# Files To Create

## requirements.txt

Dependencies:

* fastapi
* uvicorn
* pydantic

---

## app/schemas/health_schema.py

Contains:

HealthResponse

---

## app/services/health_service.py

Contains:

HealthService

Method:

get_status()

Returns:

HealthResponse

---

## app/api/health.py

Contains:

GET /health endpoint

Uses:

HealthService

---

## app/main.py

Application entrypoint.

Responsibilities:

* Create FastAPI app
* Register routers

---

# Request Flow

GET /health

↓

FastAPI Router

↓

Health Endpoint

↓

HealthService

↓

HealthResponse

↓

JSON Response

---

# Deliverables

By the end of this step:

* Folder structure exists
* FastAPI runs locally
* Health endpoint works
* Service layer exists
* Schema layer exists
* API layer exists

Expected Response:

```json
{
  "status": "healthy"
}
```

---

# Success Criteria

You can explain:

1. Why services exist.
2. Why schemas exist.
3. Why routes should stay thin.
4. What happens when GET /health is called.
5. How this architecture supports future AI features.
