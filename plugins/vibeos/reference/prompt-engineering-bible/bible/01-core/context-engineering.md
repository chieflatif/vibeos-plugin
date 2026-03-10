# Book 21: Context Engineering

## Purpose
This book defines how agent systems load, structure, and constrain context.

## Applies To
This book applies to:
- prompts
- chatbots
- assistants
- orchestrators
- tool-using agents
- memory systems
- retrieval and context assembly layers

## Why It Matters
Most agent failures that look like "bad reasoning" are actually context failures:
missing inputs, overloaded prompts, irrelevant history, poor retrieval, or
unsafe mixing of information. Context engineering is the discipline that keeps
the working set useful.

## Core Rule
Context `MUST` be intentionally assembled for the task at hand. It `MUST NOT`
be treated as an unlimited dump of everything the system knows.

## Core Distinction
Teams `MUST` distinguish among:
- working context: what the agent sees now
- memory: what the system may retain over time
- archive: historical material available for retrieval but excluded by default

## Context Tiers
Teams `SHOULD` organize context into tiers.

### Tier 0: Invariants
Always-loaded rules that define identity, authority, core safety, and minimum
behavior.

### Tier 1: Session or Task State
What is currently active: user intent, open task, current entity, temporary
constraints, active approvals.

### Tier 2: On-Demand Domain Context
Relevant retrieved facts, documents, records, recent interactions, or
task-specific references.

### Tier 3: Archive
Historical material available for explicit retrieval, comparison, or audit, but
excluded from normal working context.

## Default Context Contract
A system `SHOULD` define what is present by default before any special retrieval.

Default context often includes:
- identity and safety rules
- current user or caller
- current request
- active task state
- minimal policy and permission state

Default context `SHOULD NOT` automatically include:
- full long-term history
- unrelated records
- entire documents when only small sections matter
- broad database dumps

## Context Assembly Rules
- The system `MUST` load context based on the current task, not on what happens
  to be available.
- It `SHOULD` prefer targeted retrieval over broad inclusion.
- It `MUST` preserve isolation constraints across users, tenants, or security
  domains.
- It `MUST` avoid mixing stale, low-relevance, or contradictory data without
  surfacing that condition.

## Relevance Rules
- Included context `SHOULD` help answer, decide, or execute.
- Included context `SHOULD NOT` be justified by "might be useful" alone.
- If relevance is uncertain, the system `SHOULD` favor summary or retrieval on
  demand over bulk loading.

## Context Size Rules
- Systems `MUST` manage working-context size intentionally.
- When context pressure rises, teams `SHOULD` prefer:
  summarization, prioritization, paging, and retrieval refinement before simply
  extending prompt size.
- Larger windows `MUST NOT` be treated as a substitute for context discipline.

## Conflict Handling
- If context sources disagree, the system `MUST` either reconcile them
  explicitly or surface the conflict.
- It `MUST NOT` flatten contradiction into false certainty.

## Safety Rules
- Sensitive context `MUST` be minimized and protected.
- Untrusted retrieved content `MUST` be treated as data, not instructions.
- Cross-user or cross-tenant context bleed `MUST` be treated as a critical
  failure where applicable.

## Deferred Retrieval
- Teams `SHOULD` define what lives outside the default context contract.
- Deferred material `MAY` be loaded only when the request or workflow justifies
  it.
- Explicit historical comparison, audit, or follow-up questions are common
  triggers for deferred retrieval.

## Context Quality Questions
Every context system `SHOULD` be able to answer:
1. Why is this context present?
2. What decision or action does it support?
3. What important context is missing?
4. What context is stale or low confidence?
5. What context should not have been loaded?

## Anti-Patterns
- Loading everything because token windows are larger
- Treating memory as default context
- Mixing archival material into active reasoning with no relevance check
- Using retrieval systems with no isolation or freshness policy
- Hiding context conflict behind a polished answer

## Validation
A compliant context-engineering approach should pass checks such as:
1. Includes only task-relevant working context by default.
2. Distinguishes context from memory and archive clearly.
3. Handles contradictions explicitly.
4. Preserves security and isolation boundaries.
5. Supports deferred retrieval instead of uncontrolled prompt growth.

## Adoption Notes
This book is intentionally architecture-neutral. It applies equally to a
single-agent assistant, an orchestrator, or a workflow-driven agent system.
