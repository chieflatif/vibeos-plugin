# WO-022: /vibeos:wo Skill (WO Management)

## Status

`Complete`

## Phase

Phase 3: Autonomous Build Loop

## Objective

Create a `/vibeos:wo` skill with subcommands for creating, checking status, completing, and auditing individual work orders.

## Scope

### In Scope
- [x] Create `skills/wo/SKILL.md` with subcommand dispatch
- [x] Subcommand `create`: create new WO from template with user input
- [x] Subcommand `status`: show current WO status, progress, blockers
- [x] Subcommand `complete`: mark WO as complete with evidence checklist
- [x] Subcommand `audit`: run plan auditor against a specific WO
- [x] Wrap existing patterns: wo-research, wo-complete, wo-audit from VibeOS-2
- [x] Communication contract enforced on all output

### Out of Scope
- Build orchestration (WO-019-021)
- Full audit cycle (WO-028)
- WO lifecycle automation (WO-020)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-020 | Must complete first | Draft |
| WO-TEMPLATE.md | Must exist | Created |
| WO-AUDIT-FRAMEWORK.md | Must exist | Created |

## Impact Analysis

- **Files created:** skills/wo/SKILL.md
- **Systems affected:** WO management, user interaction with work orders

## Acceptance Criteria

- [x] AC-1: `/vibeos:wo create` creates a new WO file from template
- [x] AC-2: `/vibeos:wo status` shows current WO with progress and blockers
- [x] AC-3: `/vibeos:wo complete` validates evidence and marks WO complete
- [x] AC-4: `/vibeos:wo audit` dispatches plan auditor and returns findings
- [x] AC-5: Created WOs follow WO-TEMPLATE.md structure exactly
- [x] AC-6: Status output uses communication contract language
- [x] AC-7: Complete validates all acceptance criteria have evidence before marking done

## Test Strategy

- **Integration:** Test each subcommand end-to-end
- **Validation:** Verify created WOs match template structure
- **Completeness:** Verify complete subcommand rejects WOs with missing evidence

## Implementation Plan

### Step 1: Create Skill File
- Define skill metadata with subcommand routing
- Parse subcommand from user input

### Step 2: Implement Create Subcommand
- Read WO-TEMPLATE.md
- Prompt user for: title, objective, scope, dependencies
- Generate WO file with next available number
- Add to WO-INDEX.md

### Step 3: Implement Status Subcommand
- Read DEVELOPMENT-PLAN.md and WO-INDEX.md
- Identify current WO and its state
- Report: what's done, what's in progress, what's blocked

### Step 4: Implement Complete Subcommand
- Read WO file
- Check all acceptance criteria have evidence
- Check all evidence items checked
- If complete: update status, update WO-INDEX.md
- If incomplete: report what's missing

### Step 5: Implement Audit Subcommand
- Dispatch plan auditor agent against specified WO
- Return structured findings to user

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Test status: Integration test — test each subcommand
- Risk: Low complexity; mainly wraps existing patterns

## Evidence

- [x] Skill file created
- [x] Create subcommand generates valid WO
- [x] Status subcommand reports accurate state
- [x] Complete subcommand validates evidence
- [x] Audit subcommand dispatches auditor and returns findings
