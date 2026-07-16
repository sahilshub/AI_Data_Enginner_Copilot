# Phase 2 – Step 3

# One Active AI Provider for All AI Tasks

## Goal

Replace per-request provider selection (`QARequest.provider_id`, falling
back to "most recently registered" if omitted) with a single explicit
**active** provider — set once, used automatically by every AI-related
feature (today: `/ask`; later: text-to-SQL, documentation generation,
anything else Phase 2+ adds). Multiple providers can still be registered
(so switching doesn't mean re-entering a key), but exactly one is active
at a time.

---

# Why This Step Exists

Step 1 designed `/ask` to accept an optional `provider_id` per request,
falling back to whichever provider was registered most recently if
omitted. That was a reasonable simplification for a single endpoint, but
it doesn't hold up as more AI features get added:

* "Most recently registered" is an implicit, easy-to-forget default —
  registering a second provider for one test silently changes which
  provider *every other* AI feature uses, with no explicit signal that
  happened.
* Per-request `provider_id` only exists on `/ask` today. Once text-to-SQL
  and other AI features arrive, either every endpoint reinvents its own
  "which provider" parameter, or — the better answer — there's one place
  that decision is made and every feature reads it the same way.
* The user's actual intent is simpler than what Step 1 built: one
  provider/model is *the* one in use at any given time, chosen
  deliberately, not inferred from insertion order.

---

# Real World Example

Before:

```
POST /ask {"question": "...", "provider_id": 2}   # explicit, per-call
POST /ask {"question": "..."}                      # implicit: most recent registration
```
Two different callers could get two different providers answering
"the same" endpoint without either realizing why.

After:

```
POST /ai/providers                    → register (first one registered becomes active automatically)
POST /ai/providers                    → register a second one (stays inactive)
PATCH /ai/providers/2/activate         → explicitly switch
POST /ask {"question": "..."}          → always uses whichever is active — no per-call override
```

---

# Key Concepts

## Exactly One Active, Enforced at Two Levels

Application logic (`activate_provider()`) unsets every other provider
before marking one active. A partial unique index
(`CREATE UNIQUE INDEX ... WHERE is_active = true`) enforces the same
invariant at the database level — defense in depth, the same reasoning
`uq_schema_relationship` and similar constraints already use elsewhere in
this project: application logic can have bugs, a DB constraint can't be
bypassed by a bug in one code path.

## First Registration Auto-Activates

Registering the very first provider marks it active automatically —
otherwise `/ask` would 400 with "no active provider" immediately after
the one obvious setup step a new user just did, which is a bad first
experience. Every subsequent registration stays inactive until explicitly
activated.

## Deleting the Active Provider Degrades Gracefully

If the active provider is deleted and other providers remain registered,
the most recently registered of the remaining ones is auto-promoted to
active — AI features keep working rather than silently going dark until
someone notices and re-activates manually. If no providers remain, there's
simply no active provider, and AI features 400 clearly.

## No More Per-Request Override

`QARequest` no longer accepts a `provider_id`. This is a deliberate
simplification, not an oversight — "one model for all AI tasks" means
exactly that; a per-call override would undermine the single source of
truth this step exists to create.

---

# Architecture

```
POST /ai/providers/{id}/activate
    │
    ▼
AIProviderRepository.set_active(id)
    — unsets is_active on every other row for this... (there's only one
      provider table, no per-connection scoping)
    — sets is_active = True on the target row
    (partial unique index backs this up at the DB level)

Any AI feature (QAService today, others later)
    │
    ▼
AIProviderRepository.get_active()
    │
    ▼
get_llm_provider(active.provider, decrypt(active.api_key), active.default_model)
```

---

# Explicitly Out of Scope (This Step)

* No per-connection or per-user active provider — one global active
  provider for the whole app. Multi-tenancy isn't a concern this project
  has yet.
* No history/audit log of past activations — the current active provider
  is queryable, past ones aren't tracked.

---

# Implementation Requirements

* `AIProviderConfig` model — add `is_active` (Boolean, default False).
* Migration: add column + partial unique index enforcing at most one
  active row.
* `AIProviderRepository`:
  * `get_active() -> Optional[AIProviderConfig]`
  * `set_active(provider_id) -> AIProviderConfig` — unsets others, sets target.
  * `count() -> int` (used to detect "is this the first registration").
* `AIProviderService`:
  * `register_provider()` — auto-activate if this is the first ever registered.
  * `activate_provider(provider_id)` — 404 if missing, else `repo.set_active()`.
  * `delete_provider(provider_id)` — if the deleted provider was active and
    others remain, auto-promote the most recently registered remaining one.
* `AIProviderResponse` — add `is_active: bool`.
* New route: `PATCH /ai/providers/{id}/activate`.
* `QARequest` — remove `provider_id`; `QAService.ask()` always resolves via
  `get_active()`, 400s clearly if none is active.

---

# Deliverables

* Exactly one provider is ever active, enforced by both application logic
  and a DB constraint.
* `/ask` (and every future AI feature) automatically uses whichever
  provider is active — no per-call parameter to remember or get wrong.
* Registering a first provider "just works" without an extra activation
  step; switching providers later is one explicit call.

---

# What We Have Built So Far

Phase 1, Steps 1–15: backend foundation through observability, connector
abstraction, performance fixes, async jobs, Nginx reverse proxy.
Phase 2, Step 1: bring-your-own-key LLM provider integration.
Phase 2, Step 2: bounded, search-based schema context assembly for prompts.
Phase 2, Step 3: single active AI provider for all AI tasks, replacing
per-request provider selection.

---

# Next Step

## Phase 2 – Step 4

### Text-to-SQL Generation

Now that context assembly is bounded and there's one unambiguous provider
in use, the next feature is generating actual SQL from a question using
that context — not just a natural-language answer. Safe *execution* of
that generated SQL is a deliberately separate, later step.
