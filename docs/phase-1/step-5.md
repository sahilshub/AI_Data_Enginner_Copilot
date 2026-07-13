# Phase 1 – Step 5

# Schema Metadata Persistence

## Goal

Store discovered schema metadata inside our platform database instead of querying the target database every time.

At the end of this step, the platform should:

* Discover schema metadata from a target database
* Save that metadata locally
* Serve schema information from local storage
* Support metadata refresh when the source database changes

The platform is beginning to behave like a lightweight data catalog.

---

# Why This Step Exists

Currently, every schema request works like this:

User
↓
API
↓
Target Database
↓
information_schema
↓
Response

This works for small projects but becomes problematic as systems grow.

Imagine:

* 100 connected databases
* 500 tables per database
* Multiple users exploring schemas

Every request would trigger metadata queries against the source database.

Problems:

* Increased latency
* Unnecessary database load
* Repeated work
* Poor scalability

Instead, we want:

User
↓
Platform Database
↓
Metadata Response

with periodic refreshes.

---

# How Real Systems Work

Modern data platforms rarely inspect databases on every request.

Examples:

* DataHub
* Atlan
* Amundsen
* Collibra

They ingest metadata and store it locally.

Benefits:

* Faster searches
* Better user experience
* Metadata history
* AI-ready context

We are building the first version of that capability.

---

# Key Concepts

## Metadata Catalog

A metadata catalog is a database that stores information about other databases.

Example:

Target Database:

customers
orders
payments

Platform Database:

connections
schema_tables
schema_columns

The platform stores knowledge about external systems.

---

## Metadata Synchronization

Metadata can change.

Example:

Today:

customers

Tomorrow:

customers
customer_addresses

The platform must eventually refresh metadata.

This step introduces the concept of synchronization.

---

## Source of Truth

The target database remains the source of truth.

The platform stores a cached representation.

Think of it as:

Target Database
↓
Metadata Snapshot
↓
Platform Database

---

# Architecture

Current:

User
↓
Schema Service
↓
Target Database
↓
Metadata

New Architecture:

User
↓
Schema Service
↓
Platform Metadata Store
↓
Metadata Response

Metadata Refresh:

Target Database
↓
Schema Discovery
↓
Platform Metadata Store

---

# New Models

## SchemaTable

Represents a discovered table.

Fields:

* id
* connection_id
* table_name
* schema_name
* discovered_at

---

## SchemaColumn

Represents a discovered column.

Fields:

* id
* table_id
* column_name
* data_type
* is_nullable

---

# Folder Changes

app/

├── models/
│   ├── schema_table.py
│   └── schema_column.py
│
├── repositories/
│   ├── schema_repository.py
│   └── metadata_repository.py
│
├── services/
│   └── metadata_sync_service.py
│
├── api/
│   └── metadata.py

---

# New Responsibilities

## Schema Repository

Responsible for:

* Reading metadata from target databases

Methods:

* get_tables()
* get_columns()

---

## Metadata Repository

Responsible for:

* Storing metadata
* Retrieving metadata
* Updating metadata

Methods:

* save_tables()
* save_columns()
* get_stored_tables()
* get_stored_columns()

---

## Metadata Sync Service

Responsible for:

* Running schema discovery
* Persisting metadata
* Refreshing metadata

Methods:

* sync_connection_metadata()

---

# Database Design

## schema_tables

Stores discovered tables.

Fields:

* id
* connection_id
* table_name
* schema_name
* created_at

---

## schema_columns

Stores discovered columns.

Fields:

* id
* table_id
* column_name
* data_type
* is_nullable
* created_at

---

# API Endpoints

## Sync Metadata

POST /connections/{connection_id}/metadata/sync

Purpose:

Discover schema metadata and store it locally.

Response:

```json
{
  "message": "Metadata synchronized successfully"
}
```

---

## Get Stored Tables

GET /connections/{connection_id}/metadata/tables

Purpose:

Return tables from platform storage.

---

## Get Stored Columns

GET /connections/{connection_id}/metadata/tables/{table_name}

Purpose:

Return columns from platform storage.

---

# Data Flow

Metadata Synchronization

Target Database
↓
information_schema
↓
Schema Repository
↓
Metadata Sync Service
↓
Platform Database

---

Metadata Retrieval

User
↓
API
↓
Metadata Repository
↓
Platform Database
↓
Response

---

# Why This Matters For AI

This step may seem unrelated to AI, but it is actually one of the most important AI preparation steps.

Future AI features need:

* Fast access to schema information
* Searchable metadata
* Structured context

LLMs work best when context is already organized.

Instead of:

AI
↓
Live Database
↓
Metadata Discovery

We want:

AI
↓
Metadata Catalog
↓
Structured Context

Much faster and more reliable.

---

# Implementation Requirements

Implement:

### Models

* SchemaTable
* SchemaColumn

### Repositories

* MetadataRepository

### Services

* MetadataSyncService

### APIs

* POST /connections/{connection_id}/metadata/sync
* GET /connections/{connection_id}/metadata/tables
* GET /connections/{connection_id}/metadata/tables/{table_name}

### Database

Create:

* schema_tables
* schema_columns

Add Alembic migrations.

---

# Deliverables

By the end of this step:

* Metadata can be persisted.
* Metadata can be retrieved locally.
* Metadata synchronization works.
* Schema discovery and metadata storage are separated.
* Foundation for search and AI context is established.

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

At this point, we have built the core of a metadata platform.

---

# Next Step

## Phase 1 – Step 6

### Schema Relationships & Database Understanding

Current metadata:

* Tables
* Columns

Next:

* Primary Keys
* Foreign Keys
* Table Relationships

Goal:

Move from simply storing metadata to actually understanding how tables relate to each other.

This will become critical for future Text-to-SQL generation and schema-aware AI features.
