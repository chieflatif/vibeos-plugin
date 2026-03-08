# WO-027: Evidence Auditor Agent

## Status

`Complete`

## Phase

Phase 4: Fresh-Context Audit Agents

## Objective

Create an evidence auditor agent that validates documentation completeness, evidence bundles, and WO audit framework compliance across all 4 checkpoints.

## Scope

### In Scope
- [x] Create `agents/evidence-auditor.md` with read-only access
- [x] Validate all 4 WO-AUDIT-FRAMEWORK.md checkpoints completed for each WO
- [x] Check evidence items are present and non-empty
- [x] Verify test status documented (pass/fail counts, not just "tests pass")
- [x] Verify acceptance criteria have corresponding evidence
- [x] Check documentation files exist and are non-trivial
- [x] Validate WO-INDEX.md accuracy against actual WO file statuses
- [x] Structured findings with completeness percentage per WO

### Out of Scope
- Security audit (WO-023)
- Code correctness (WO-025)
- Fixing documentation gaps (separate WO)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-023 | Must complete first | Complete |
| WO-AUDIT-FRAMEWORK.md | Must exist | Complete |

## Impact Analysis

- **Files created:** agents/evidence-auditor.md
- **Systems affected:** Audit pipeline, documentation enforcement

## Acceptance Criteria

- [x] AC-1: All 4 checkpoints evaluated for each completed WO
- [x] AC-2: Missing evidence items identified with specific field and WO
- [x] AC-3: Test status documentation validated (not just "pass" but counts/details)
- [x] AC-4: WO-INDEX.md cross-referenced against actual WO files
- [x] AC-5: Completeness percentage calculated per WO and overall
- [x] AC-6: Structured output with per-WO and aggregate findings

## Test Strategy

- **Integration:** Dispatch against WOs with varying evidence completeness
- **Cross-reference:** Verify WO-INDEX.md discrepancies detected
- **Completeness:** Verify percentage calculations are accurate

## Implementation Plan

### Step 1: Create Agent File
- YAML frontmatter: model (sonnet), tools (Read, Glob, Grep), maxTurns
- Instructions: evidence audit protocol based on WO-AUDIT-FRAMEWORK.md

### Step 2: Implement Checkpoint Validation
- For each completed WO: check all 4 audit checkpoints
- Planning: plan exists, risks identified
- Implementation: code complete, tests pass
- Post-implementation: review done, quality verified
- Completion: evidence collected, docs updated

### Step 3: Implement Evidence Validation
- For each evidence item: check it exists, is non-empty, is specific
- Flag generic evidence ("tests pass") vs. specific ("14/14 tests pass, 0 failures")
- Cross-reference WO-INDEX.md status against actual WO file status

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Test status: Integration test — dispatch against WOs with varying completeness
- Risk: Low complexity; mainly file reading and cross-referencing

## Evidence

- [x] Agent file created
- [x] All 4 checkpoints evaluated
- [x] Missing evidence detected
- [x] WO-INDEX.md discrepancies detected
- [x] Completeness percentages calculated
