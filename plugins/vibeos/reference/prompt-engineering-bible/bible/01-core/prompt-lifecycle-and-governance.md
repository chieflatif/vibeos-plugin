# Book 25: Prompt Lifecycle and Governance

## Purpose
This book defines how prompt artifacts, agent contracts, and related behavioral
assets are owned, versioned, tracked, and changed over time.

## Applies To
This book applies to:
- canonical prompts
- agent contracts
- prompt templates
- output schemas
- safety invariants
- evaluation matrices
- generated prompt assets derived from canonical sources

## Why It Matters
Behavior drift is one of the fastest ways to lose trust in an AI system.
Governance turns prompt behavior from hidden folklore into an auditable product
surface.

## Core Rule
Any artifact that materially changes agent behavior `MUST` be governed as a
versioned system asset.

## Required Metadata
Each canonical behavioral artifact `MUST` have:
- canonical source location
- version
- change date or last-updated date
- owner

Each consequential artifact `SHOULD` also have:
- dependent systems
- validation status
- last validated date
- change rationale

## Ownership Rules
- Every consequential artifact `MUST` have a human owner or owning team.
- Ownership `MUST NOT` be ambiguous.
- Profile-level extensions `SHOULD` name both profile owner and shared-core
  dependencies where relevant.

## Versioning Rules
- Semantic versioning `SHOULD` be used for canonical prompt and contract assets.
- Patch versions `SHOULD` be used for clarification or non-behavioral edits.
- Minor versions `SHOULD` be used for additive behavioral changes or contract
  expansion.
- Major versions `SHOULD` be used for breaking changes in semantics, authority,
  output structure, or safety posture.

## Canonical Source Rules
- Every behavioral artifact `MUST` have one canonical source of truth.
- Generated runtime prompts `MUST` be traceable back to canonical source assets.
- Teams `MUST NOT` treat copied inline prompt text across multiple systems as
  separate authorities unless deliberately versioned that way.

## Drift Prevention
- Teams `SHOULD` compare deployed or generated prompts against canonical source
  representations.
- Suspected drift `SHOULD` be treated as real until resolved.
- If canonical authority is unclear, prompt changes `SHOULD` pause until the
  source of truth is re-established.

## Change Control
Before changing a consequential behavioral artifact, teams `SHOULD` capture:
- why the change is needed
- what behavior is expected to improve or change
- what risks the change introduces
- what tests or baselines must be rerun

After a change:
- affected evaluations `SHOULD` be rerun
- regressions `SHOULD` be reviewed explicitly
- release status `SHOULD` be updated if the artifact is production-facing

## Registry Guidance
Teams `SHOULD` maintain a registry for canonical behavioral assets.

A useful registry entry `SHOULD` include:
- artifact name
- canonical path
- owner
- version
- dependent systems
- validation status
- last validated date
- integrity or drift reference

## Prompt-as-Product Rule
- Prompts and agent contracts `MUST NOT` be treated as disposable prose.
- A prompt change `MUST` be considered a product change when it affects
  authority, routing, output, safety, tool use, or user expectations.
- Teams `SHOULD` review consequential prompt changes with the same seriousness as
  code changes that affect behavior.

## Governance for This Framework Itself
This framework `MUST` follow its own governance principles.

That means:
- the books themselves `MUST` have versioning and ownership
- the project `SHOULD` document when guidance is universal versus profile-level
- examples `MUST NOT` silently redefine doctrine
- migration guidance `SHOULD` exist for major changes

## Required Release Questions
Before adopting a changed behavioral artifact, the team `SHOULD` be able to
answer:
1. What changed?
2. Why did it change?
3. Who approved it?
4. What tests were rerun?
5. Did any baseline behavior change?
6. Is any downstream system affected?

## Anti-Patterns
- Prompt text copied across repos with no owner
- Runtime prompt changes that never flow back to source control
- Version numbers with no meaningful change policy
- Major behavior changes hidden inside wording cleanups
- Shipping examples that are more authoritative than the stated standard

## Validation
This book is complete when a team can:
1. identify the canonical source of each behavioral artifact
2. name its owner
3. explain its current version
4. detect drift
5. review and ship changes intentionally

## Adoption Notes
Small teams can start with lightweight governance: file ownership, version
metadata, and a simple registry. Larger systems should add stronger drift
detection, approval flow, and release evidence over time.
