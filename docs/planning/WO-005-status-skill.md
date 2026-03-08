# WO-005: `/vibeos:status` Skill

## Status

`Complete`

## Phase

Phase 1: Plugin Foundation

## Objective

Create the `/vibeos:status` skill that shows a project dashboard — current phase, active WOs, recent audit results, and next recommended action.

## Scope

### In Scope
- [x] Create `skills/status/SKILL.md` with YAML frontmatter
- [x] Read DEVELOPMENT-PLAN.md and WO-INDEX.md
- [x] Report: current phase, active WOs, recent gate/audit results, next action
- [x] Communication contract format

### Out of Scope
- Gate execution (WO-004)
- Build loop status (WO-019)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-001 | Must complete first | Complete |

## Acceptance Criteria

- [x] AC-1: User invokes `/vibeos:status` and sees project overview
- [x] AC-2: Current phase and active WOs correctly identified from plan files
- [x] AC-3: Next recommended action provided with reasoning
- [x] AC-4: Communication contract patterns followed

## Evidence

- [x] Skill file created at skills/status/SKILL.md
- [x] YAML frontmatter: name, description, allowed-tools
- [x] Dashboard template includes phase, active WOs, next action, blockers
- [x] Handles missing governance files (suggests /vibeos:discover)
