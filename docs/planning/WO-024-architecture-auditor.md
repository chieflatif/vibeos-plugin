# WO-024: Architecture Auditor Agent

## Status

`Draft`

## Phase

Phase 4: Fresh-Context Audit Agents

## Objective

Create an architecture auditor agent that checks for layer violations, circular dependencies, contract breakage, and module boundary violations in an isolated, read-only context.

## Scope

### In Scope
- [ ] Create `agents/architecture-auditor.md` with strict isolation
- [ ] Agent config: isolation: worktree, disallowedTools: Write, Edit, Agent, model: sonnet
- [ ] Layer violation detection: imports crossing architectural boundaries
- [ ] Circular dependency detection: modules importing each other
- [ ] Contract breakage: public interfaces changed without updating consumers
- [ ] Module boundary violations: internal details exposed outside module
- [ ] Architecture rules compliance: check against ARCHITECTURE-OUTLINE.md
- [ ] Structured findings with severity and evidence

### Out of Scope
- Security analysis (WO-023)
- Correctness analysis (WO-025)
- Fixing violations (separate WO)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-023 | Must complete first | Draft |

## Impact Analysis

- **Files created:** agents/architecture-auditor.md
- **Systems affected:** Audit pipeline, architecture enforcement

## Acceptance Criteria

- [ ] AC-1: Agent runs in isolated worktree
- [ ] AC-2: Agent cannot use Write, Edit, or Agent tools
- [ ] AC-3: Layer violations detected with source and target module
- [ ] AC-4: Circular dependencies detected with full cycle path
- [ ] AC-5: Findings reference ARCHITECTURE-OUTLINE.md rules violated
- [ ] AC-6: Each finding includes: violation type, severity, files involved, rule reference, recommendation
- [ ] AC-7: Structured output returned to caller

## Test Strategy

- **Integration:** Dispatch against code with known architecture violations
- **Accuracy:** Verify detected violations match actual violations
- **Architecture rules:** Verify agent reads and applies ARCHITECTURE-OUTLINE.md

## Implementation Plan

### Step 1: Create Agent File
- YAML frontmatter: model (sonnet), isolation (worktree), disallowedTools (Write, Edit, Agent), maxTurns
- Instructions: read architecture doc, analyze imports/dependencies, check boundaries

### Step 2: Implement Analysis Protocol
- Phase 1: Read ARCHITECTURE-OUTLINE.md for declared layers and boundaries
- Phase 2: Analyze import graph across all source files
- Phase 3: Check each import against layer rules
- Phase 4: Detect circular dependency cycles
- Phase 5: Check for exposed internals (underscore-prefixed, internal/ directories)

### Step 3: Implement Finding Structure
- Each finding: { violation_type, severity, source_file, target_file, rule_reference, description, recommendation }
- Summary: total violations by type and severity

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Test status: Integration test — dispatch against code with planted violations
- Risk: Import graph analysis complexity varies by language; must handle multiple languages

## Evidence

- [ ] Agent file created with correct isolation config
- [ ] Layer violations detected in test code
- [ ] Circular dependencies detected
- [ ] Findings reference architecture rules
- [ ] Tool restrictions enforced
