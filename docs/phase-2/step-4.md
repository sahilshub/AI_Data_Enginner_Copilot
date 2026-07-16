# Phase 2 – Step 4

# Tool-Calling Schema Exploration (OpenAI + Groq First)

## Goal

Replace Step 2's static, keyword-matched context dump with real tool-calling:
the LLM decides what to look up (which tables, which columns, which
relationships) by calling tools backed by the existing catalog
(`SearchRepository`/`MetadataRepository`/`RelationshipRepository`), across
as many rounds as it needs, instead of being handed one pre-filtered slice
up front.

Scoped deliberately to **OpenAI and Groq only** for this step — not all
four registered providers. Anthropic and Gemini support is real future
work, not an afterthought, but the interface is built so adding them later
means implementing one method on one class each, not touching
`QAService` or any other provider.

---

# Why This Step Exists

Step 2 fixed the crash (`413` from Groq) but not the underlying limitation:
keyword matching is a guess. If a question's wording doesn't literally
overlap with a table/column name, the model gets an arbitrary fallback
slice, not the right one. Tool-calling lets the model explore
adaptively — check a table, notice a relationship, follow it, ask another
question of the catalog — the same way a person would.

Scoping to OpenAI + Groq specifically (not building all four providers at
once): Groq's API is OpenAI-SDK-compatible (`GroqProvider` already
subclasses `OpenAIProvider` — see Step 1), so implementing tool-calling
once on `OpenAIProvider` gives both providers real tool-calling for free.
Anthropic's `tool_use` and Gemini's function-calling are different wire
formats — real, separate work, better done once there's a working
tool-calling `QAService` to validate the approach against, not before.

---

# Real World Example

```
question: "How would I find all orders placed by customers in a given city?"
    │
    ▼
LLM call #1 (no pre-stuffed context, just tool definitions)
    → model: "call search_tables('order')"
    ▼
QAService executes against SearchRepository → returns matches
    ▼
LLM call #2 (result added to conversation)
    → model: "call get_relationships('orders')"
    ▼
QAService executes against RelationshipRepository → returns FK links to customers
    ▼
LLM call #3
    → model: "call get_table_columns('customers')"
    ▼
QAService executes against MetadataRepository → returns columns incl. city
    ▼
LLM call #4 → model has enough → final answer, no more tool calls
```
Four LLM round-trips, each one informed by the last — not one big guess.

---

# Key Concepts

## Provider-Agnostic Tool Definitions, Per-Provider Wire Translation

Tools are defined once, in one canonical JSON-schema shape (name,
description, parameters) — the same shape OpenAI's function-calling
already expects natively, which is *why* starting with OpenAI/Groq means
no translation layer is needed yet. Anthropic's `input_schema` and
Gemini's `FunctionDeclaration` differ in field names but hold the same
information — when those providers are added, the translation happens
inside their own provider class, `QAService` never sees it.

## `supports_tool_calling`, Not Silent Failure

`LLMProvider` gains `supports_tool_calling: bool = False` (class
attribute) and a `generate_with_tools()` method that raises a clear
`NotImplementedError`-based error by default. `OpenAIProvider` (and by
inheritance `GroqProvider`) override both. If the currently *active*
provider is Anthropic or Gemini, `/ask` fails with a clear 400 — *"this
provider doesn't support tool-calling yet, activate OpenAI or Groq"* — not
a confusing crash three layers down.

## The Tool Executor Is a Callback, Not Provider Knowledge

`LLMProvider.generate_with_tools()` takes a `tool_executor` callback
(`(tool_name, arguments) -> str`) supplied by `QAService`. The provider
class only knows how to run the request/response loop with *some*
tools — it has no idea what `search_tables` actually does. That stays
entirely in `QAService`, wired to the existing repositories.

## A Hard Round Cap, Same Reasoning as Step 2's Table Cap

Nothing guarantees a model converges quickly. `MAX_TOOL_ROUNDS` bounds how
many request/response cycles one `/ask` call can spend — same defense-in-depth
reasoning as Step 2's `MAX_TABLES_IN_CONTEXT`, just capping rounds instead
of tables.

---

# Architecture

```
app/llm/base.py
    LLMProvider.supports_tool_calling: bool = False
    LLMProvider.generate_with_tools(question, system, tools, tool_executor, max_rounds) -> str
        default: raise "tool-calling not supported by this provider"

app/llm/openai_provider.py
    OpenAIProvider.supports_tool_calling = True
    OpenAIProvider.generate_with_tools(...) — real implementation:
        loop: send messages + tools -> if tool_calls in response, run
        tool_executor for each, append results, send again; else return
        final content.

app/llm/groq_provider.py
    (no changes — inherits OpenAIProvider's implementation entirely)

app/services/qa_service.py
    TOOLS = [search_tables, search_columns, get_table_columns, get_relationships, list_tables]
    _execute_tool(name, arguments) -> str
        — dispatches to SearchRepository / MetadataRepository / RelationshipRepository
    ask() — replaces _build_schema_context()/_select_relevant_tables() with
        a call to llm.generate_with_tools(...), 400s clearly if the active
        provider's supports_tool_calling is False.
```

---

# Explicitly Out of Scope (This Step)

* Anthropic and Gemini tool-calling — real future work, not implemented
  here. Activating either as the AI provider makes `/ask` 400 clearly
  rather than silently falling back to something else.
* Streaming tool-calling responses.
* Text-to-SQL generation itself — still the actual next feature after
  this; this step only changes *how the model explores the schema*, not
  what it does with what it learns yet.

---

# Implementation Requirements

* `app/llm/base.py`:
  * `supports_tool_calling: bool = False` class attribute.
  * `generate_with_tools(question, system, tools, tool_executor, max_rounds=8) -> str`
    — default implementation raises a clear "not supported" error.
* `app/llm/openai_provider.py`:
  * `supports_tool_calling = True`.
  * Real `generate_with_tools()` implementing the request/tool-call/result loop
    against OpenAI's Chat Completions tool-calling API.
* `app/services/qa_service.py`:
  * Tool catalog definitions (JSON-schema shape) wrapping
    `SearchRepository`/`MetadataRepository`/`RelationshipRepository`.
  * `_execute_tool(connection_id, name, arguments) -> str` dispatcher.
  * `ask()` rewritten to use `generate_with_tools()`; 400s if
    `not llm.supports_tool_calling`.
  * Retire `_build_schema_context()` / `_select_relevant_tables()` /
    `MAX_TABLES_IN_CONTEXT` / `MAX_CONTEXT_CHARS` from Step 2 — superseded,
    not kept alongside.

---

# Deliverables

* `/ask` with an active OpenAI or Groq provider explores the catalog
  adaptively via tool calls instead of a static keyword-matched dump.
* Activating Anthropic or Gemini and calling `/ask` fails with a clear,
  actionable 400 instead of a confusing error or silent wrong behavior.
* Adding Anthropic/Gemini tool-calling later is scoped to their own
  provider classes — `QAService` and the tool definitions don't change.

---

# What We Have Built So Far

Phase 1, Steps 1–15: backend foundation through observability, connector
abstraction, performance fixes, async jobs, Nginx reverse proxy.
Phase 2, Steps 1–3: bring-your-own-key LLM providers, bounded context
assembly, single active provider.
Phase 2, Step 4: tool-calling schema exploration for OpenAI/Groq,
superseding Step 2's static context approach.

---

# Next Step

Text-to-SQL generation — now that the model can adaptively explore the
real schema via tools, the next feature is generating actual SQL from a
question, not just a natural-language answer.
