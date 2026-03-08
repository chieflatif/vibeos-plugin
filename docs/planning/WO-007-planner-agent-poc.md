# WO-007: Planner Agent (Proof of Concept)

## Status

`Complete`

## Phase

Phase 1: Plugin Foundation

## Objective

Create a basic planner agent that reads DEVELOPMENT-PLAN.md and WO-INDEX.md, determines the next WO, and returns structured output — proving subagent dispatch works within the plugin system.

## Scope

### In Scope
- [x] Create `agents/planner.md` with YAML frontmatter (tools, model, maxTurns)
- [x] Planner reads DEVELOPMENT-PLAN.md, determines next WO, reports structured summary
- [x] Structured output format defined (WO number, phase, scope, readiness, blockers)
- [x] Communication contract embedded in agent instructions

### Out of Scope
- Plan auditor (WO-010)
- Full orchestrator integration (WO-019)
- WO lifecycle management (WO-020)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-001 | Must complete first | Complete |
| WO-TEMPLATE.md | Must exist | Created |

## Acceptance Criteria

- [x] AC-1: Agent file exists with valid YAML frontmatter
- [x] AC-2: Planner instructions specify reading DEVELOPMENT-PLAN.md and WO-INDEX.md
- [x] AC-3: Structured output format defined (WO, phase, scope, readiness, blockers)
- [x] AC-4: Agent frontmatter sets tools (Read, Glob, Grep, Write), model (sonnet), maxTurns (10)
- [x] AC-5: Communication contract embedded in agent instructions

## Implementation Notes

**Agent frontmatter:**
- `tools: Read, Glob, Grep, Write` — needs Write for creating WO drafts
- `model: sonnet` — planning doesn't need Opus
- `maxTurns: 10` — sufficient for reading plan + index + WO file + reporting

**Runtime verification:** Full dispatch testing deferred to WO-007a test fixture. The agent file structure follows confirmed spike findings (SPIKE-RESULTS.md).

## Evidence

- [x] Agent file created at agents/planner.md
- [x] YAML frontmatter: name, description, tools, model, maxTurns
- [x] Structured output format with WO, phase, scope, readiness, blockers sections
- [x] Communication contract in instructions
