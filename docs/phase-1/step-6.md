# Phase 1 – Step 6

# Schema Relationship Discovery

## Goal

Enhance schema understanding by discovering and storing relationships between tables.

At the end of this step, the platform should understand:

* Primary Keys
* Foreign Keys
* Table Relationships
* Parent/Child table connections

The system will move from:

"Knowing tables exist"

to

"Understanding how tables are connected."

---

# Why This Step Exists

Currently, our platform knows:

Table: customers

Columns:

* customer_id
* name
* email

and

Table: orders

Columns:

* order_id
* customer_id

But it does not understand that:

orders.customer_id

references

customers.customer_id

Without relationships, the platform only sees isolated tables.

Modern AI systems need relationship information because most business questions span multiple tables.

Example:

Question:

"Show all customers and their orders."

To answer this, the system must understand:

customers
↓
customer_id
↑
customer_id
↓
orders

This understanding comes from relationship discovery.

---

# Key Concepts

## Primary Key

A primary key uniquely identifies a row.

Example:

customers

| customer_id | name  |
| ----------- | ----- |
| 1           | John  |
| 2           | Alice |

customer_id is the primary key.

Rules:

* Unique
* Not Null

---

## Foreign Key

A foreign key references another table.

orders

| order_id | customer_id |
| -------- | ----------- |
| 101      | 1           |
| 102      | 2           |

customer_id points to customers.customer_id.

This creates a relationship.

---

## Table Relationships

Relationships allow databases to represent real-world connections.

Examples:

Customer
↓
Orders

Order
↓
Order Items

Product
↓
Categories

Without relationships:

Data is isolated.

With relationships:

Data becomes connected.

---

## Why This Matters for AI

Future Text-to-SQL systems need to know:

* Which tables can be joined
* How tables should be joined
* Which keys are related

Example:

User:

"List customers and their order totals."

The AI must know:

# customers.customer_id

orders.customer_id

Otherwise it may generate invalid SQL.

Relationship metadata dramatically improves SQL accuracy.

---

# Architecture

Current Metadata

Tables
↓
Columns

New Metadata

Tables
↓
Columns
↓
Primary Keys
↓
Foreign Keys
↓
Relationships

---

# Folder Changes

app/

├── models/
│   └── schema_relationship.py
│
├── repositories/
│   └── relationship_repository.py
│
├── services/
│   └── relationship_service.py
│
├── api/
│   └── relationship.py
│
├── schemas/
│   └── relationship_schema.py

---

# New Model

## SchemaRelationship

Represents a relationship between two tables.

Fields:

* id
* connection_id
* source_table
* source_column
* target_table
* target_column
* relationship_type
* discovered_at

Example:

source_table:
orders

source_column:
customer_id

target_table:
customers

target_column:
customer_id

relationship_type:
foreign_key

---

# Metadata Discovery Sources

Use PostgreSQL metadata views:

* information_schema.table_constraints
* information_schema.key_column_usage
* information_schema.constraint_column_usage

These views expose:

* Primary Keys
* Foreign Keys
* Constraints

---

# Repository Responsibilities

RelationshipRepository

Methods:

* get_primary_keys()
* get_foreign_keys()
* get_relationships()

Responsibilities:

* Query PostgreSQL metadata
* Return relationship information

---

# Service Responsibilities

RelationshipService

Responsibilities:

* Load relationships
* Transform metadata
* Store discovered relationships
* Build response models

Methods:

* discover_relationships()
* get_relationships()

---

# API Endpoints

## Discover Relationships

POST /connections/{connection_id}/relationships/discover

Purpose:

Extract relationship metadata from PostgreSQL.

Response:

```json
{
  "message": "Relationships discovered successfully"
}
```

---

## Get Relationships

GET /connections/{connection_id}/relationships

Example Response:

```json
[
  {
    "source_table": "orders",
    "source_column": "customer_id",
    "target_table": "customers",
    "target_column": "customer_id"
  }
]
```

---

## Get Table Relationships

GET /connections/{connection_id}/relationships/{table_name}

Example:

GET /connections/1/relationships/orders

Response:

```json
[
  {
    "target_table": "customers",
    "relationship_type": "foreign_key"
  }
]
```

---

# Database Changes

Create:

## schema_relationships

Fields:

* id
* connection_id
* source_table
* source_column
* target_table
* target_column
* relationship_type
* created_at

Add Alembic migration.

---

# Data Flow

Relationship Discovery

Target Database
↓
Constraint Metadata
↓
Relationship Repository
↓
Relationship Service
↓
Platform Database

---

Relationship Retrieval

User
↓
API
↓
Relationship Service
↓
Platform Database
↓
Response

---

# Building Toward AI

Before this step:

AI would know:

customers

orders

After this step:

AI knows:

orders.customer_id
→
customers.customer_id

This is a huge improvement.

Many beginner Text-to-SQL systems fail because they only provide:

* Table names
* Column names

and ignore relationships.

Good systems provide:

* Tables
* Columns
* Relationships

which allows much more accurate SQL generation.

---

# Implementation Requirements

Implement:

### Models

* SchemaRelationship

### Repositories

* RelationshipRepository

### Services

* RelationshipService

### APIs

* POST /connections/{connection_id}/relationships/discover
* GET /connections/{connection_id}/relationships
* GET /connections/{connection_id}/relationships/{table_name}

### Database

Create:

* schema_relationships

Add migration.

---

# Deliverables

By the end of this step:

* Primary keys are discovered.
* Foreign keys are discovered.
* Relationships are stored.
* Relationship APIs work.
* Metadata catalog now understands table connections.

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

At this stage, the platform has enough metadata to understand the structure of most databases.

---

# Next Step

## Phase 1 – Step 7

### Schema Search & Exploration

Current:

Users must know exactly which table they want.

Next:

Users can search metadata.

Examples:

* Search tables by name
* Search columns
* Search relationships
* Explore schema quickly

This prepares the metadata catalog for AI-powered retrieval in future phases.
