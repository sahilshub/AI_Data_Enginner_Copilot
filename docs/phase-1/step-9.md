# Phase 1 – Step 9

# Metadata Refresh & Change Detection

## Goal

Keep stored metadata synchronized with the source database and detect schema changes over time.

At the end of this step, the platform should be able to:

* Refresh metadata on demand
* Detect schema changes
* Identify added tables
* Identify removed tables
* Identify added columns
* Identify removed columns
* Track relationship changes

The platform is evolving from a metadata snapshot system into a metadata management system.

---

# Why This Step Exists

Currently:

Database
↓
Schema Discovery
↓
Metadata Stored

The problem:

Databases constantly evolve.

Example:

Day 1

customers
orders

Day 30

customers
orders
payments

Day 60

customers
orders
payments
subscriptions

Our platform would become outdated unless metadata is refreshed.

---

# Real World Problem

A common issue in data platforms:

Engineer:
"Where is payment data stored?"

Documentation:
"payments table"

Reality:
Table was renamed three months ago.

Metadata synchronization prevents documentation, search results, and future AI responses from becoming stale.

---

# Key Concepts

## Metadata Refresh

Refreshing means:

Source Database
↓
Read Latest Metadata
↓
Compare With Stored Metadata
↓
Update Catalog

The source database remains the source of truth.

---

## Change Detection

Instead of blindly replacing metadata, detect differences.

Examples:

### Table Added

Before:

customers
orders

After:

customers
orders
payments

Detected Change:

ADD TABLE payments

---

### Column Added

Before:

customers

* customer_id
* email

After:

customers

* customer_id
* email
* phone_number

Detected Change:

ADD COLUMN customers.phone_number

---

### Column Removed

Before:

customers.email

After:

Removed

Detected Change:

REMOVE COLUMN customers.email

---

# Why This Matters For AI

Future AI systems depend entirely on metadata quality.

If metadata is outdated:

AI receives incorrect context.

Result:

Wrong documentation
Wrong answers
Wrong SQL generation

Good AI starts with reliable data.

This step improves reliability.

---

# Architecture

Current

Source Database
↓
Metadata Discovery
↓
Metadata Catalog

New

Source Database
↓
Metadata Discovery
↓
Compare
↓
Detect Changes
↓
Update Catalog
↓
Store Change History

---

# Folder Changes

app/

├── models/
│   └── metadata_change.py
│
├── repositories/
│   └── metadata_change_repository.py
│
├── services/
│   └── metadata_refresh_service.py
│
├── api/
│   └── metadata_refresh.py
│
├── schemas/
│   └── metadata_change_schema.py

---

# New Model

## MetadataChange

Stores detected schema changes.

Fields:

* id
* connection_id
* change_type
* object_type
* object_name
* previous_value
* new_value
* detected_at

---

# Change Types

Supported:

* TABLE_ADDED
* TABLE_REMOVED
* COLUMN_ADDED
* COLUMN_REMOVED
* COLUMN_TYPE_CHANGED
* RELATIONSHIP_ADDED
* RELATIONSHIP_REMOVED

---

# Refresh Workflow

Step 1

Load stored metadata.

Step 2

Run fresh schema discovery.

Step 3

Compare old and new metadata.

Step 4

Generate change records.

Step 5

Update metadata catalog.

Step 6

Store change history.

---

# Repository Responsibilities

MetadataChangeRepository

Responsibilities:

* Store detected changes
* Retrieve change history

Methods:

* save_changes()
* get_changes()

---

# Service Responsibilities

MetadataRefreshService

Responsibilities:

* Refresh metadata
* Compare snapshots
* Detect differences
* Persist changes

Methods:

* refresh_metadata()
* detect_changes()

---

# API Endpoints

## Refresh Metadata

POST /connections/{connection_id}/metadata/refresh

Purpose:

Run synchronization and detect changes.

Response:

```json
{
  "message": "Metadata refreshed successfully",
  "changes_detected": 3
}
```

---

## Get Change History

GET /connections/{connection_id}/metadata/changes

Response:

```json
[
  {
    "change_type": "COLUMN_ADDED",
    "object_name": "customers.phone_number"
  }
]
```

---

## Get Latest Refresh Status

GET /connections/{connection_id}/metadata/status

Response:

```json
{
  "last_refresh": "2026-07-14T10:00:00Z",
  "changes_detected": 5
}
```

---

# Data Flow

Refresh Request
↓
Metadata Refresh Service
↓
Schema Discovery
↓
Compare Metadata
↓
Detect Changes
↓
Update Catalog
↓
Store History

---

# Building Toward AI

Today:

Metadata Catalog

Tomorrow:

AI Context Engine

Future workflow:

Schema Changes
↓
Metadata Refresh
↓
Updated Context
↓
AI Receives Latest Information

Without change detection, AI becomes stale.

With change detection, AI remains trustworthy.

---

# Implementation Requirements

Implement:

### Models

* MetadataChange

### Repositories

* MetadataChangeRepository

### Services

* MetadataRefreshService

### APIs

* POST /connections/{connection_id}/metadata/refresh
* GET /connections/{connection_id}/metadata/changes
* GET /connections/{connection_id}/metadata/status

### Database

Create:

* metadata_changes

Add Alembic migration.

---

# Deliverables

By the end of this step:

* Metadata refresh works.
* Schema changes are detected.
* Change history is stored.
* Metadata catalog stays synchronized.
* Foundation for trustworthy AI context is established.

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

Step 9:
Metadata refresh and change detection

The platform now understands schemas and keeps that understanding up to date.
