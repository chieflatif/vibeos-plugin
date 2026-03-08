# WO-018: Doc Writer Agent

## Status

`Draft`

## Phase

Phase 3: Autonomous Build Loop

## Objective

Create a documentation agent that updates project documentation after implementation and records implementation notes and evidence in the WO file.

## Scope

### In Scope
- [ ] Create `agents/doc-writer.md` with appropriate tool access and model
- [ ] Update relevant documentation files after implementation completes
- [ ] Update the WO file with implementation notes (what was built, deviations from plan)
- [ ] Update the WO file with evidence (files created/modified, test results)
- [ ] Update WO-INDEX.md with current status
- [ ] Update DEVELOPMENT-PLAN.md if WO completion affects plan state
- [ ] Keep documentation accurate to what was actually built (not what was planned)

### Out of Scope
- Writing code (WO-016, WO-017)
- Writing tests (WO-014)
- Architecture documentation changes (require separate WO)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-016 | Must complete first | Draft |

## Impact Analysis

- **Files created:** agents/doc-writer.md
- **Systems affected:** Documentation pipeline, WO tracking

## Acceptance Criteria

- [ ] AC-1: WO file updated with implementation notes section
- [ ] AC-2: WO file updated with evidence section (checked items, file paths, test results)
- [ ] AC-3: WO-INDEX.md reflects current WO status
- [ ] AC-4: Documentation matches actual implementation (not planned implementation)
- [ ] AC-5: Deviations from original WO plan documented with rationale
- [ ] AC-6: Agent does not modify source code or test files

## Test Strategy

- **Integration:** Dispatch doc writer after a completed WO, verify documentation updated
- **Accuracy:** Compare doc writer output against actual implementation files
- **Completeness:** Verify all evidence items checked and documented

## Implementation Plan

### Step 1: Create Agent File
- YAML frontmatter: model (haiku or sonnet), tools (Read, Write, Edit, Glob, Grep), maxTurns
- Instructions: read WO, read implementation, update docs
- Focus on accuracy over completeness

### Step 2: Implement Documentation Protocol
- Read WO file for planned scope and acceptance criteria
- Read implementation files to understand what was actually built
- Read test results to document pass/fail status
- Update WO file with implementation notes
- Check off evidence items

### Step 3: Implement Status Updates
- Update WO status field
- Update WO-INDEX.md entry
- Update DEVELOPMENT-PLAN.md if applicable

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Test status: Integration test — verify docs updated after sample WO completion
- Risk: Doc writer must accurately reflect what was built, not hallucinate features

## Evidence

- [ ] Agent file created
- [ ] WO file updated with implementation notes
- [ ] WO-INDEX.md reflects correct status
- [ ] Documentation matches actual implementation
