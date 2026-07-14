# Phase 1 – Step 8

# Schema Documentation Generation

## Goal

Transform technical metadata into human-readable documentation.

At the end of this step, users should be able to generate documentation for:

- Entire databases
- Individual tables
- Table relationships
- Column definitions

The platform is no longer just storing metadata.

It is now converting metadata into knowledge.

---

# Why This Step Exists

Currently our platform knows:

- Tables
- Columns
- Data types
- Relationships

But the information is still presented as raw metadata.

Example:

customers

Columns:

- customer_id
- email
- created_at

This is useful for machines but not very useful for humans.

Engineers often need:

- Database documentation
- Data dictionaries
- Onboarding guides
- Architecture references

Instead of manually writing documentation, we can generate it automatically from metadata.

---

# Real World Example

Most organizations struggle with documentation.

Common problems:

- Documentation becomes outdated
- New tables are undocumented
- Engineers don't know where data lives
- Knowledge exists only in people's heads

Modern platforms solve this by generating documentation from metadata.

Examples:

- DataHub
- Atlan
- Alation
- Collibra

We are building the first version of that capability.

---

# Key Concepts

## Data Dictionary

A data dictionary describes database assets.

Example:

Table: customers

Purpose:
Stores customer account information.

Columns:

- customer_id → unique customer identifier
- email → customer email address
- created_at → account creation timestamp

This is far easier to consume than raw metadata.

---

## Documentation as a Derived Asset

Metadata:

customers
↓
columns
↓
relationships

Documentation:

A human-readable explanation of that metadata.

The documentation is not the source of truth.

The metadata remains the source of truth.

Documentation is generated from metadata.

---

## Why This Matters for AI

Future AI systems need context.

One of the biggest challenges with LLMs is providing meaningful context.

Raw metadata:

customers.customer_id

Generated context:

"The customers table stores customer account information and is linked to orders through customer_id."

Documentation becomes a higher-quality representation of metadata.

Later this documentation can be embedded and used for retrieval.

---

# Architecture

Current

Metadata
↓
Storage
↓
Search

New

Metadata
↓
Documentation Generator
↓
Generated Documentation

---

# Folder Changes

app/

├── services/
│ └── documentation_service.py
│
├── repositories/
│ └── documentation_repository.py
│
├── api/
│ └── documentation.py
│
├── schemas/
│ └── documentation_schema.py

---

# Documentation Types

## Database Overview

Contains:

- Database name
- Number of tables
- Number of columns
- Relationship summary

Example:

Database Overview

Tables: 25

Columns: 312

Relationships: 48

---

## Table Documentation

Contains:

- Table name
- Description
- Column list
- Relationship list

Example:

Table: customers

Columns:

- customer_id (integer)
- email (varchar)
- created_at (timestamp)

Relationships:

- customers → orders

---

## Relationship Documentation

Contains:

- Parent tables
- Child tables
- Join paths

Example:

customers
↓
orders
↓
order_items

---

# Repository Responsibilities

DocumentationRepository

Responsibilities:

- Retrieve metadata
- Retrieve relationships
- Build documentation inputs

Methods:

- get_database_metadata()
- get_table_metadata()
- get_relationship_metadata()

---

# Service Responsibilities

DocumentationService

Responsibilities:

- Generate documentation content
- Format documentation
- Create export-ready output

Methods:

- generate_database_documentation()
- generate_table_documentation()
- generate_relationship_documentation()

---

# API Endpoints

## Generate Database Documentation

GET /documentation/database/{connection_id}

Response:

```json
{
  "database_name": "sales_db",
  "tables": 25,
  "relationships": 48
}
```

---

## Generate Table Documentation

GET /documentation/table/{connection_id}/{table_name}

Response:

```json
{
  "table_name": "customers",
  "columns": [],
  "relationships": []
}
```

---

## Generate Relationship Documentation

GET /documentation/relationships/{connection_id}

Response:

```json
{
  "relationships": []
}
```

---

# Future Export Support

Design the implementation so it can later support:

- Markdown
- HTML
- PDF
- Confluence
- Wiki pages

Do not implement exports yet.

Only generate structured documentation responses.

---

# Data Flow

Metadata Catalog
↓
Documentation Service
↓
Generated Documentation
↓
API Response

---

# Implementation Requirements

Implement:

### Repository

- get_database_metadata()
- get_table_metadata()
- get_relationship_metadata()

### Service

- generate_database_documentation()
- generate_table_documentation()
- generate_relationship_documentation()

### APIs

- GET /documentation/database/{connection_id}
- GET /documentation/table/{connection_id}/{table_name}
- GET /documentation/relationships/{connection_id}

### Schemas

- DatabaseDocumentationResponse
- TableDocumentationResponse
- RelationshipDocumentationResponse

---

# Deliverables

By the end of this step:

- Documentation generation is implemented.
- Table documentation can be generated.
- Relationship documentation can be generated.
- Database overview documentation can be generated.
- Documentation is generated entirely from metadata.

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

Step 8:
Schema documentation generation

The platform now not only understands metadata but can explain it in a human-friendly way.

---

# Next Step

## Phase 1 – Step 9

### Metadata Refresh & Change Detection

Current:

Metadata is stored.

Problem:

Databases change.

New tables appear.
Columns are added.
Relationships change.

Next:

Detect changes automatically and keep metadata synchronized with source databases.
