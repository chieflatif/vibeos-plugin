# WO-013: Investigator Agent (Phase 0)

## Status

`Complete`

## Phase

Phase 3: Autonomous Build Loop

## Objective

Create an investigator agent that runs before each WO to revalidate assumptions, analyze existing code, and perform a mini-audit, returning validated assumptions, confirmed or revised steps, and risk flags.

## Scope

### In Scope
- [x] Create `agents/investigator.md` with appropriate tool access and model
- [x] Read the target WO and its dependencies
- [x] Analyze existing codebase relevant to the WO scope
- [x] Revalidate assumptions listed in the WO
- [x] Check if dependencies are actually complete (not just marked complete)
- [x] Identify risks not captured in the WO
- [x] Return structured report: validated assumptions, confirmed/revised steps, risk flags
- [x] Flag if WO scope has become stale relative to current codebase state

### Out of Scope
- Modifying WO files (investigator is read-only analysis)
- Full security audit (WO-023)
- Test writing (WO-014)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| Phase 2 complete | Must complete first | Draft |

## Impact Analysis

- **Files created:** agents/investigator.md
- **Systems affected:** Build loop pre-flight, WO lifecycle

## Acceptance Criteria

- [x] AC-1: Agent reads WO file and identifies all assumptions
- [x] AC-2: Agent checks dependency WOs are actually complete (reads evidence, not just status)
- [x] AC-3: Agent analyzes relevant codebase files for conflicts or existing implementations
- [x] AC-4: Structured report returned with: assumptions (validated/invalidated), steps (confirmed/revised), risks (new/changed)
- [x] AC-5: Agent completes within maxTurns limit
- [x] AC-6: If assumptions are invalidated, report includes specific evidence why

## Test Strategy

- **Integration:** Dispatch investigator against a WO with known dependency state
- **Accuracy:** Dispatch against a WO with deliberately stale assumptions, verify detection
- **Structure:** Verify output is parseable structured format

## Implementation Plan

### Step 1: Create Agent File
- YAML frontmatter: model (sonnet), tools (Read, Glob, Grep, Bash read-only), maxTurns
- Instructions: systematic investigation protocol
- Output format specification

### Step 2: Implement Investigation Protocol
- Read target WO, extract assumptions and dependencies
- For each dependency: read WO file, check status and evidence
- For each assumption: search codebase for confirming/conflicting evidence
- Identify files that will be affected by the WO

### Step 3: Implement Risk Analysis
- Check for potential conflicts with other in-progress WOs
- Check for missing prerequisites not listed as dependencies
- Check for scope changes since WO was written

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Test status: Integration test — dispatch against sample WO, verify report quality
- Risk: Investigation quality depends on how well the agent navigates unfamiliar codebases

## Evidence

- [x] Agent file created
- [x] Dispatch succeeds
- [x] Structured report returned with all required sections
- [x] Stale assumption detection verified
- [x] Dependency verification works
