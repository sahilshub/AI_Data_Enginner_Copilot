# Phase 2 – Step 2

# Schema Context Assembly for Prompts

## Goal

Replace the full-schema-dump context `QAService` sends today with a
bounded, relevant subset — selected using the existing search
infrastructure (Phase 1, Step 7) — so `/ask` works regardless of catalog
size instead of failing once it's large enough.

---

# Why This Step Exists

This wasn't hypothetical — it already happened. Asking a question against
the real 90-table / ~1171-column / 130-relationship test schema produced a
live `413 Request Entity Too Large` from Groq:

```
httpx.HTTPStatusError: Client error '413 Payload Too Large' for url
'https://api.groq.com/openai/v1/chat/completions'
```

`QAService._build_schema_context()` (Step 1) dumps *every* table, every
column, and every relationship for the connection into the prompt, every
time. Groq enforces a stricter hard request-size cap than
Anthropic/OpenAI/Gemini, so it hit the wall first — but the underlying
problem (context size scales linearly with catalog size, unbounded) would
eventually break the others too on a large enough schema. This step fixes
the actual cause, not just Groq's symptom of it.

---

# Real World Example

Before:

```
question: "Which table stores customer information?"
    ↓
context = ALL 90 tables + ALL ~1171 columns + ALL 130 relationships
    ↓
413 Request Entity Too Large
```

After:

```
question: "Which table stores customer information?"
    ↓
keywords: ["customer", "information"]
    ↓
search catalog (pg_trgm-indexed, Step 7) for tables/columns matching those keywords
    ↓
context = only the matched tables (+ their columns, + relationships touching them),
          capped at MAX_TABLES regardless of match count
    ↓
small, relevant prompt → real answer
```

---

# Key Concepts

## Reuse Search, Don't Reinvent Relevance

The catalog is already searchable via `pg_trgm`-indexed `ILIKE` queries
(Step 7) — table names, column names, and relationship endpoints. Rather
than building a second retrieval mechanism, `QAService` extracts keywords
from the question and runs them through the same `SearchRepository`
methods `SearchService` already uses.

## Keyword Extraction Is Naive on Purpose

Splitting the question into words and dropping a small stopword list is
crude — it's not semantic search, doesn't handle synonyms
("customer" vs "client"), and won't always find the *best* tables, just
tables whose name/columns literally contain a matching substring. That's
an acceptable, honest limitation for this step. Semantic/embedding-based
retrieval is real RAG (`Phase 7` in the original roadmap) — pulling it in
now would be solving a problem two phases early with infrastructure
(vector storage, embeddings) that doesn't exist yet.

## A Hard Cap Is the Actual Fix, Keyword Matching Is Just Better Targeting

Even with keyword matching, an unlucky/broad question could still match
many tables. The real guarantee against ever hitting a 413 again is a hard
`MAX_TABLES_IN_CONTEXT` cap (and a final context-length truncation as a
last line of defense) — keyword matching decides *which* tables make the
cut, the cap decides *how many* can ever be included, full stop.

## Honest Fallback, Not Silent Failure

If no keyword matches anything (a vague question, or terminology that
doesn't appear in the schema), the previous behavior would have been "dump
everything" (the 413 bug) or could silently return an empty/wrong context.
Instead: fall back to a bounded, arbitrary slice of tables, and tell the
LLM (via the system prompt) that this is a partial/fallback view — so the
model's own "say so explicitly if you don't have enough information"
instruction (already in Step 1's system prompt) has accurate information
to work with.

---

# Architecture

```
QARequest.question
    │
    ▼
extract_keywords(question)  — naive tokenize + stopword drop
    │
    ▼
for each keyword: SearchRepository.search_tables() / search_columns()
    │
    ▼
union matched tables, capped at MAX_TABLES_IN_CONTEXT
    │
    ▼ (if nothing matched)
fallback: first MAX_TABLES_IN_CONTEXT tables, flagged as partial
    │
    ▼
build context: selected tables' columns + relationships touching them only
    │
    ▼
truncate to MAX_CONTEXT_CHARS (defense in depth)
    │
    ▼
LLMProvider.generate(question, system=context)
```

---

# Explicitly Out of Scope (This Step)

* No semantic/embedding-based retrieval — naive keyword matching against
  the existing search index only. Real RAG is Phase 7.
* No per-provider context-window-aware sizing (e.g. a bigger cap for
  Claude's larger context window than Groq's) — one conservative cap for
  all providers, simplest thing that fixes the actual bug.
* No caching of context per question — rebuilt every call. Not a
  correctness issue, a possible future optimization if `/ask` latency ever
  matters more than it does now.

---

# Implementation Requirements

* `app/services/qa_service.py`:
  * `_extract_keywords(question) -> List[str]` — tokenize, drop stopwords/short tokens.
  * `_select_relevant_tables(connection_id, question) -> (tables, used_fallback: bool)`
    — search-based selection, capped at `MAX_TABLES_IN_CONTEXT`, with the
    bounded fallback when nothing matches.
  * `_build_schema_context()` rewritten to build context only from selected
    tables (+ their columns, + relationships touching them), with a final
    hard truncation to `MAX_CONTEXT_CHARS`.
  * System prompt notes when the fallback path was used.

---

# Deliverables

* `/ask` no longer fails with a 413 (or any size-related error) regardless
  of catalog size — verified against the real 90-table schema that
  triggered the original failure.
* Context sent to the LLM is meaningfully smaller and more relevant than a
  full catalog dump for a targeted question.
* A vague/no-match question still gets *a* bounded answer instead of a
  crash, honestly flagged as partial.

---

# What We Have Built So Far

Phase 1, Steps 1–15: backend foundation through observability, connector
abstraction, performance fixes, async jobs, Nginx reverse proxy.
Phase 2, Step 1: bring-your-own-key LLM provider integration.
Phase 2, Step 2: bounded, search-based schema context assembly for
prompts, fixing a real 413 hit against the live test schema.

---

# Next Step

Text-to-SQL generation (`Phase 5` in the original roadmap) — now that
context assembly is bounded and reasonably relevant, the next real feature
is generating (and, later, safely executing) SQL from the answer rather
than only natural-language responses.
