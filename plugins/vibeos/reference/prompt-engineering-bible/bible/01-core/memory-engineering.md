# Book 22: Memory Engineering

## Purpose
This book defines how agent systems remember, forget, and reuse information over
time.

## Applies To
This book applies to:
- personal assistants
- chatbots with continuity
- agentic applications with user preferences
- orchestrators with session state
- long-lived agents
- memory subsystems and preference stores

## Why It Matters
Memory can make agents feel coherent and useful, but unmanaged memory makes them
creepy, brittle, and wrong. Memory engineering turns memory from a vague feature
into a governed system behavior.

## Core Rule
Memory `MUST NOT` be treated as an unlimited permanent record of everything.
Memory `MUST` be scoped, typed, and governed.

## Core Distinction
Teams `MUST` distinguish between:
- context: what the agent sees now
- memory: what the system retains for future use
- preferences: durable user-specific defaults or habits
- archive: historical records available primarily for retrieval or audit

## Memory Types
Teams `SHOULD` identify which memory types their system supports.

### Session Memory
Short-lived continuity within the current conversation or task.

### Working Memory
Temporary state across steps in an active workflow.

### Preference Memory
Durable defaults about user choices, style, schedules, or recurring habits.

### Long-Term Task Memory
Open commitments, ongoing projects, unresolved follow-ups, or tracked goals.

### Archival Memory
Historical records that are retained but not automatically surfaced.

## Memory Rules
- A system `MUST` define what it remembers.
- It `MUST` define why each memory type exists.
- It `MUST` define how memories are updated, corrected, and forgotten.
- It `MUST NOT` imply memory that the system does not actually maintain.
- It `MUST NOT` store sensitive information casually or indefinitely without
  explicit policy.

## Preference Handling
- Preferences `MUST` be distinguishable from facts.
- Inferred preferences `MUST` be weaker than stated preferences unless confirmed.
- Temporary preferences `MUST NOT` silently become permanent defaults.
- Users `SHOULD` be able to correct or revoke meaningful remembered preferences.

## Recall Rules
- Memory `SHOULD` be recalled when it helps the current task materially.
- Memory `SHOULD NOT` be surfaced merely because it exists.
- Sensitive or stale memory `MUST` be suppressed unless clearly relevant and
  permitted.
- Systems `SHOULD` prefer compact structured memory over replaying raw history.

## Freshness and Decay
- Memory `SHOULD` have freshness expectations or decay rules.
- Stale memory `MUST NOT` be used as if it were current fact.
- Systems `SHOULD` mark uncertain or aging memories so they can be revalidated.

## Correction and Invalidation
- The system `MUST` define how incorrect memories are corrected.
- It `MUST` define how obsolete preferences or commitments are invalidated.
- It `SHOULD` avoid hidden or irreversible memory mutation for consequential
  user-level information.

## Privacy and Consent
- Memory systems `MUST` follow privacy policy and applicable user expectations.
- High-trust domains `SHOULD` make memory behavior visible enough to be
  understandable.
- Teams `MUST NOT` use memory as a backdoor for retaining data that should have
  expired or been excluded.

## Memory Failure Modes
Common memory failures include:
- false memory: the system recalls something that was never stored
- stale memory: the system recalls something outdated as current
- overexposed memory: the system surfaces private or irrelevant history
- ungoverned inference: the system turns a guess into a remembered fact

Systems `SHOULD` explicitly test for these failures.

## Output Expectations
When memory influences an answer, the system `SHOULD` preserve the user's trust
by making memory use feel:
- relevant
- bounded
- useful
- unsurprising

## Anti-Patterns
- "I remember" when there is no memory system
- Treating all remembered information as equally durable
- Surfacing personal history gratuitously
- Converting inferred preferences into hard defaults
- Keeping long-term data with no freshness or deletion policy

## Validation
A compliant memory system should pass checks such as:
1. Distinguishes memory from active context.
2. Knows which memory types exist.
3. Corrects and invalidates memories intentionally.
4. Prevents stale or inferred memory from posing as fact.
5. Respects privacy, relevance, and retention boundaries.

## Adoption Notes
Not every system needs long-term memory. Many excellent agent systems should
start with strong session memory and explicit preference handling before adding
durable memory layers.
