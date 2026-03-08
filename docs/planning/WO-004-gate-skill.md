# WO-004: `/vibeos:gate` Skill

## Status

`Complete`

## Phase

Phase 1: Plugin Foundation

## Objective

Create the `/vibeos:gate` skill that runs quality gate scripts and reports results in plain English following the communication contract.

## Scope

### In Scope
- [x] Create `skills/gate/SKILL.md` with YAML frontmatter
- [x] Skill runs `gate-runner.sh` for specified phase
- [x] Results reported in communication contract format (business meaning first)
- [x] Parameters: phase (default: pre_commit), --wo NUMBER (optional)

### Out of Scope
- Modifying gate scripts themselves (WO-002)
- Gate integration into build loop (WO-021)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-002 | Must complete first (gate scripts must exist) | Draft |

## Impact Analysis

- **Files created:** skills/gate/SKILL.md
- **Systems affected:** User can manually trigger quality gates

## Acceptance Criteria

- [x] AC-1: User invokes `/vibeos:gate` and gates execute
- [x] AC-2: Results reported in plain English with business context
- [x] AC-3: Phase parameter changes which gates run
- [x] AC-4: Communication contract patterns followed (what happened, why it matters, next step)

## Test Strategy

- **Verification:** Invoke `/vibeos:gate` in a test project, confirm gates run and report fires
- **Source pattern:** `reference/skills/quality-gate-check.md.ref` from VibeOS-2

## Implementation Plan

### Step 1: Create SKILL.md
- YAML frontmatter with name, description, parameters
- Skill body: run gate-runner.sh, parse results, report in communication contract format

### Step 2: Test Invocation
- Invoke from Claude Code
- Verify output follows communication contract

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Test status: Manual invocation test

## Evidence

- [x] Skill file created at skills/gate/SKILL.md
- [x] YAML frontmatter: name, description, argument-hint, allowed-tools
- [x] Communication contract embedded (what happened, why it matters, what to do next)
