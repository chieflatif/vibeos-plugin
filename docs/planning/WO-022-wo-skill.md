# WO-022: /vibeos:wo Skill (WO Management)

## Status

`Draft`

## Phase

Phase 3: Autonomous Build Loop

## Objective

Create a `/vibeos:wo` skill with subcommands for creating, checking status, completing, and auditing individual work orders.

## Scope

### In Scope
- [ ] Create `skills/wo.md` with subcommand dispatch
- [ ] Subcommand `create`: create new WO from template with user input
- [ ] Subcommand `status`: show current WO status, progress, blockers
- [ ] Subcommand `complete`: mark WO as complete with evidence checklist
- [ ] Subcommand `audit`: run plan auditor against a specific WO
- [ ] Wrap existing patterns: wo-research, wo-complete, wo-audit from VibeOS-2
- [ ] Communication contract enforced on all output

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

- **Files created:** skills/wo.md
- **Systems affected:** WO management, user interaction with work orders

## Acceptance Criteria

- [ ] AC-1: `/vibeos:wo create` creates a new WO file from template
- [ ] AC-2: `/vibeos:wo status` shows current WO with progress and blockers
- [ ] AC-3: `/vibeos:wo complete` validates evidence and marks WO complete
- [ ] AC-4: `/vibeos:wo audit` dispatches plan auditor and returns findings
- [ ] AC-5: Created WOs follow WO-TEMPLATE.md structure exactly
- [ ] AC-6: Status output uses communication contract language
- [ ] AC-7: Complete validates all acceptance criteria have evidence before marking done

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

- [ ] Skill file created
- [ ] Create subcommand generates valid WO
- [ ] Status subcommand reports accurate state
- [ ] Complete subcommand validates evidence
- [ ] Audit subcommand dispatches auditor and returns findings
