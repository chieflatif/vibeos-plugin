# WO-001: Repo Setup & Plugin Manifest

## Status

`Complete`

## Phase

Phase 1: Plugin Foundation

## Objective

Create the vibeos-plugin repository with proper structure, plugin manifest, and all foundational files so the plugin can be installed into Claude Code.

## Scope

### In Scope
- [x] Git init with README.md, LICENSE (MIT), .gitignore
- [x] `.claude-plugin/plugin.json` manifest with name, version, description
- [x] Directory skeleton: skills/ (8 subdirs), agents/, hooks/, scripts/, decision-engine/, reference/, convergence/, docs/planning/
- [x] CLAUDE.md with project instructions
- [x] Verify `claude --plugin-dir ./vibeos-plugin` loads the plugin

### Out of Scope
- Actual skill, agent, or hook content (later WOs)
- Gate scripts (WO-002)
- Decision engine and reference files (WO-003)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| Claude Code with plugin support | External tool | Verify during implementation |

## Impact Analysis

- **Files created:** .claude-plugin/plugin.json, CLAUDE.md, README.md, LICENSE, .gitignore, directory skeleton
- **Files modified:** None (greenfield)
- **Systems affected:** Plugin install/discovery in Claude Code

## Acceptance Criteria

- [x] AC-1: `claude --plugin-dir ./vibeos-plugin` loads the plugin successfully
- [x] AC-2: Plugin manifest contains name, version, description (directories auto-discovered per spike findings)
- [x] AC-3: All directories exist: skills/ (8 subdirs), agents/, hooks/, scripts/, decision-engine/, reference/, convergence/, docs/planning/
- [x] AC-4: CLAUDE.md contains project architecture, conventions, and source material references
- [x] AC-5: No placeholder content — every file has real, working content

## Test Strategy

- **Verification:** Run `claude --plugin-dir ./vibeos-plugin` and confirm plugin loads
- **Validation:** `jq . .claude-plugin/plugin.json` succeeds (valid JSON)
- **Validation:** All referenced directories and paths exist

## Implementation Plan

### Step 1: Repository Foundation
- Create repo with git init
- Add .gitignore, LICENSE (MIT), README.md
- Create full directory skeleton

### Step 2: Plugin Manifest
- `.claude-plugin/plugin.json` with name, version, description (already created)
- Directories auto-discovered per spike findings — no explicit references needed
- Validate JSON syntax

### Step 3: Project Instructions
- Create CLAUDE.md with architecture overview, conventions, source material references
- Ensure it provides sufficient context for any agent working in this repo

### Step 4: Verification
- Run `claude --plugin-dir ./vibeos-plugin`
- Confirm plugin loads and skills/agents are discoverable
- Validate all directories exist

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Findings: —
- Test status: Verification is manual (plugin install) + JSON validation

### Pre-Implementation Audit
- Status: `pending`
- Findings: —
- Test status: —

### Pre-Commit Audit
- Status: `pending`
- Findings: —
- Test status: —

## Evidence

- [x] Implementation complete
- [x] Plugin loads via `claude --plugin-dir` (exit 0, no errors)
- [x] JSON validates (`jq . .claude-plugin/plugin.json` succeeds)
- [x] All 16 directories exist (verified via directory check)
- [x] Documentation accurate (CLAUDE.md has architecture, conventions, source refs)
