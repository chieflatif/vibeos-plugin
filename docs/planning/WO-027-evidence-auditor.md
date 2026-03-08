# WO-027: Evidence Auditor Agent

## Status

`Draft`

## Phase

Phase 4: Fresh-Context Audit Agents

## Objective

Create an evidence auditor agent that validates documentation completeness, evidence bundles, and WO audit framework compliance across all 4 checkpoints.

## Scope

### In Scope
- [ ] Create `agents/evidence-auditor.md` with read-only access
- [ ] Validate all 4 WO-AUDIT-FRAMEWORK.md checkpoints completed for each WO
- [ ] Check evidence items are present and non-empty
- [ ] Verify test status documented (pass/fail counts, not just "tests pass")
- [ ] Verify acceptance criteria have corresponding evidence
- [ ] Check documentation files exist and are non-trivial
- [ ] Validate WO-INDEX.md accuracy against actual WO file statuses
- [ ] Structured findings with completeness percentage per WO

### Out of Scope
- Security audit (WO-023)
- Code correctness (WO-025)
- Fixing documentation gaps (separate WO)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-023 | Must complete first | Draft |
| WO-AUDIT-FRAMEWORK.md | Must exist | Created |

## Impact Analysis

- **Files created:** agents/evidence-auditor.md
- **Systems affected:** Audit pipeline, documentation enforcement

## Acceptance Criteria

- [ ] AC-1: All 4 checkpoints evaluated for each completed WO
- [ ] AC-2: Missing evidence items identified with specific field and WO
- [ ] AC-3: Test status documentation validated (not just "pass" but counts/details)
- [ ] AC-4: WO-INDEX.md cross-referenced against actual WO files
- [ ] AC-5: Completeness percentage calculated per WO and overall
- [ ] AC-6: Structured output with per-WO and aggregate findings

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

- [ ] Agent file created
- [ ] All 4 checkpoints evaluated
- [ ] Missing evidence detected
- [ ] WO-INDEX.md discrepancies detected
- [ ] Completeness percentages calculated
