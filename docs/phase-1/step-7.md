# Phase 1 – Step 7

# Schema Search & Exploration

## Goal

Enable users to search, filter, and explore metadata stored in the platform.

At the end of this step, users should be able to:

* Search tables
* Search columns
* Search relationships
* Explore database structures without knowing exact table names

The platform now starts behaving like a lightweight data catalog.

---

# Why This Step Exists

Currently we have:

* Connections
* Tables
* Columns
* Relationships

But the user must already know what they are looking for.

Example:

A database contains:

* customers
* customer_addresses
* customer_preferences
* customer_orders
* customer_payments

A user may not know which table contains address information.

Without search:

User
↓
Manually inspect every table

With search:

User searches "address"
↓
Platform returns relevant tables and columns

---

# Real World Example

Imagine a production database with:

* 800 tables
* 15,000 columns
* Hundreds of relationships

No engineer manually browses metadata.

Modern platforms provide:

* Search
* Filtering
* Discovery
* Navigation

Examples:

* DataHub
* Atlan
* Amundsen
* Collibra

We are implementing the first version of that capability.

---

# Key Concepts

## Metadata Discovery

Metadata discovery means helping users find useful information without already knowing where it exists.

Example:

Search:

email

Results:

customers.email

employees.email

vendors.email

---

## Search Index

Right now our metadata is stored in PostgreSQL.

The first version of search can use:

* ILIKE
* Partial matching
* Simple filtering

Later we may introduce:

* Full-text search
* Embeddings
* Semantic search

But not yet.

---

## Why Search Before AI?

Many beginners jump directly into AI.

However:

# Good AI

Good Context

Search is the first retrieval mechanism.

Before AI retrieves context:

Humans should be able to retrieve context.

If humans cannot find metadata easily, AI will struggle too.

---

# Architecture

Current

Metadata
↓
Storage

New

Metadata
↓
Search Layer
↓
User Exploration

---

# Folder Changes

app/

├── repositories/
│   └── metadata_search_repository.py
│
├── services/
│   └── metadata_search_service.py
│
├── api/
│   └── metadata_search.py
│
├── schemas/
│   └── metadata_search_schema.py

---

# Search Capabilities

## Table Search

Search by:

* Table name
* Partial table name

Example:

Search:

customer

Results:

* customers
* customer_addresses
* customer_orders

---

## Column Search

Search by:

* Column name
* Partial column name

Example:

Search:

email

Results:

* customers.email
* employees.email

---

## Relationship Search

Search relationships involving a table.

Example:

Search:

orders

Results:

orders
↓
customers

orders
↓
payments

orders
↓
order_items

---

# Repository Responsibilities

MetadataSearchRepository

Methods:

* search_tables()
* search_columns()
* search_relationships()

Responsibilities:

* Query stored metadata
* Apply filters
* Return results

---

# Service Responsibilities

MetadataSearchService

Responsibilities:

* Coordinate searches
* Validate search requests
* Format responses

Methods:

* search_metadata()
* search_tables()
* search_columns()
* search_relationships()

---

# API Endpoints

## Search Tables

GET /search/tables?q=customer

Response:

```json
[
  {
    "table_name": "customers"
  },
  {
    "table_name": "customer_addresses"
  }
]
```

---

## Search Columns

GET /search/columns?q=email

Response:

```json
[
  {
    "table_name": "customers",
    "column_name": "email"
  }
]
```

---

## Search Relationships

GET /search/relationships?q=orders

Response:

```json
[
  {
    "source_table": "orders",
    "target_table": "customers"
  }
]
```

---

## Global Metadata Search

GET /search?q=customer

Response:

```json
{
  "tables": [],
  "columns": [],
  "relationships": []
}
```

This endpoint becomes the foundation for future retrieval systems.

---

# Database Changes

No new tables required.

Use:

* schema_tables
* schema_columns
* schema_relationships

created in previous steps.

---

# Data Flow

User Search
↓
API
↓
Search Service
↓
Search Repository
↓
Metadata Catalog
↓
Response

---

# Building Toward AI

Current Search:

Keyword Search

Example:

customer

↓

customers

Future Search:

Semantic Search

Example:

customer information

↓

customers

customer_addresses

customer_preferences

Even though exact words differ.

This step prepares the retrieval layer that later evolves into RAG.

---

# Implementation Requirements

Implement:

### Repository

* search_tables()
* search_columns()
* search_relationships()

### Service

* metadata search orchestration

### APIs

* GET /search/tables
* GET /search/columns
* GET /search/relationships
* GET /search

### Schemas

* SearchRequest
* SearchResponse
* TableSearchResponse
* ColumnSearchResponse
* RelationshipSearchResponse

---

# Deliverables

By the end of this step:

* Metadata search works.
* Users can discover tables.
* Users can discover columns.
* Users can discover relationships.
* Metadata catalog becomes searchable.

---

# What We Have Built So Far

Step 1:
Backend foundation

Step 2:
Configuration and Docker

Step 3:
Database connection management

Step 4:
Schema discovery

Step 5:
Metadata persistence

Step 6:
Relationship discovery

Step 7:
Schema search and exploration

At this point, we have a basic metadata platform similar to the foundation of modern data catalog systems.

---

# Next Step

## Phase 1 – Step 8

### Schema Documentation Generation

Current:

Metadata is stored and searchable.

Next:

Generate human-readable documentation from metadata.

Examples:

* Table descriptions
* Column summaries
* Relationship diagrams
* Database overview pages

This is the first step where the platform starts creating value from metadata rather than simply storing it.
