# Phase 1 – Step 4

# Database Schema Discovery

## Goal

The goal of this step is to enable the platform to understand the structure of a connected PostgreSQL database.

At the end of this phase, the system should be able to:

* List all tables in a database
* View columns for a table
* View data types for each column

The platform will understand the schema, but it will not use AI yet.

---

# Why This Step Exists

Imagine a database contains the following tables:

* customers
* orders
* order_items
* products
* payments

Later, a user might ask:

> Which table stores customer information?

Or:

> Generate SQL to find the top 10 customers by revenue.

An AI model cannot answer those questions unless it first understands the database structure.

Before introducing AI, we need to build the foundation that provides context.

The relationship looks like this:

Database
↓
Schema Discovery
↓
Metadata
↓
AI Understanding
↓
User Answers

Without schema discovery, future AI features will have no reliable information about the database.

---

# Key Concepts

## What is Database Metadata?

Metadata is data about data.

Examples:

### Business Data

customers table

| customer_id | name  |
| ----------- | ----- |
| 1           | John  |
| 2           | Alice |

This is actual user data.

---

### Metadata

customers table

| column_name | data_type |
| ----------- | --------- |
| customer_id | integer   |
| name        | varchar   |

This describes the structure of the table.

Metadata tells us:

* Which tables exist
* Which columns exist
* Data types
* Relationships

Schema discovery works entirely with metadata.

---

## What is Database Introspection?

Database introspection means examining the structure of a database without reading its business records.

Examples:

* Discover tables
* Discover columns
* Discover primary keys
* Discover foreign keys

Tools like:

* DBeaver
* pgAdmin
* DataGrip

all perform schema introspection behind the scenes.

We are building the same capability inside our platform.

---

## What is information_schema?

PostgreSQL exposes metadata through special system views.

Two important views are:

### information_schema.tables

Provides:

* Table names
* Schemas
* Table types

Example query:

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public';
```

---

### information_schema.columns

Provides:

* Column names
* Data types
* Nullability

Example query:

```sql
SELECT column_name,
       data_type
FROM information_schema.columns
WHERE table_name = 'customers';
```

These views allow us to understand a database without touching actual business data.

---

# Architecture

Current architecture:

User
↓
API
↓
Service
↓
Repository
↓
Target Database

For schema discovery:

User
↓
Schema API
↓
Schema Service
↓
Schema Repository
↓
information_schema
↓
Metadata Response

Each layer has a specific responsibility.

---

# Folder Changes

Create:

app/

├── api/
│   └── schema.py
│
├── repositories/
│   └── schema_repository.py
│
├── services/
│   └── schema_service.py
│
├── schemas/
│   └── schema_response.py

---

# Repository Responsibilities

The repository communicates directly with PostgreSQL.

Responsibilities:

* Query information_schema.tables
* Query information_schema.columns
* Return raw metadata

Example methods:

* get_tables()
* get_columns(table_name)

The repository should not:

* Build API responses
* Validate requests
* Apply business rules

Its only job is data access.

---

# Service Responsibilities

The service coordinates schema discovery.

Responsibilities:

* Load connection details
* Call repository methods
* Transform raw metadata
* Return response objects

The service should not:

* Execute HTTP requests
* Contain SQL queries

Its job is orchestration.

---

# API Endpoints

## List Tables

GET /connections/{connection_id}/schema/tables

Purpose:

Return all tables from the connected database.

Example Response:

```json
[
  {
    "table_name": "customers"
  },
  {
    "table_name": "orders"
  }
]
```

---

## Get Table Details

GET /connections/{connection_id}/schema/tables/{table_name}

Purpose:

Return column information for a table.

Example Response:

```json
{
  "table_name": "customers",
  "columns": [
    {
      "name": "customer_id",
      "data_type": "integer"
    },
    {
      "name": "email",
      "data_type": "character varying"
    }
  ]
}
```

---

# Response Models

## TableResponse

Fields:

* table_name

---

## ColumnResponse

Fields:

* name
* data_type

---

## TableDetailResponse

Fields:

* table_name
* columns

---

# Implementation Requirements

Implement:

### Repository

* get_tables()
* get_columns(table_name)

### Service

* get_tables(connection_id)
* get_table_details(connection_id, table_name)

### APIs

* GET /connections/{connection_id}/schema/tables
* GET /connections/{connection_id}/schema/tables/{table_name}

### Schemas

* TableResponse
* ColumnResponse
* TableDetailResponse

Use the existing layered architecture.

---

# Deliverables

By the end of this step:

* Database schema discovery is implemented.
* Tables can be listed.
* Columns can be viewed.
* Data types can be viewed.
* Metadata is retrieved from information_schema.
* No AI functionality is introduced yet.

---

# Why We Are Still Not Using AI

A common beginner mistake is:

AI First
↓
Figure Out Context Later

Production systems work the opposite way:

Understand Data
↓
Build Context
↓
Introduce AI

This step builds the context layer.

The next few phases will continue preparing structured metadata so that when we finally introduce an LLM, it has reliable information to work with.

---

# Next Step

## Phase 1 – Step 5

### Schema Metadata Persistence

Current state:

Every request directly queries PostgreSQL metadata.

Next step:

Connected Database
↓
Extract Metadata
↓
Store Metadata Locally
↓
Serve Metadata From Platform

This will prepare the system for searching, indexing, documentation generation, and future AI capabilities.
