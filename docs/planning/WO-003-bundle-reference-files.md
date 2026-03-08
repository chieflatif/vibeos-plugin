# WO-003: Bundle Decision Engine & Reference Files

## Status

`Complete`

## Phase

Phase 1: Plugin Foundation

## Objective

Copy the 8 decision engine files and 40+ reference files from VibeOS-2 into the plugin so agents can read them at runtime.

## Scope

### In Scope
- [x] Copy decision-engine/ (8 markdown files)
- [x] Copy reference/ (44 files across subdirectories)
- [x] Update hardcoded origin comments
- [x] Verify file counts match source

### Out of Scope
- Modifying decision tree logic
- Creating new reference files
- Agent implementations (later WOs)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-001 | Must complete first | Complete |
| VibeOS-2 decision-engine/ | Source files | Available |
| VibeOS-2 reference/ | Source files | Available |

## Impact Analysis

- **Files created:** 8 decision engine files, 44 reference files
- **Files modified:** None
- **Systems affected:** Agent decision-making, governance configuration

## Acceptance Criteria

- [x] AC-1: All 8 decision engine files exist in `decision-engine/`
- [x] AC-2: All 44 reference files exist in `reference/` with original subdirectory structure
- [x] AC-3: No hardcoded VibeOS-2 paths in decision-engine/ (reference/ has legitimate upgrade docs)
- [x] AC-4: File counts match source (8 decision engine, 44 reference)

## Implementation Notes

**Reference file subdirectories preserved:**
- claude/ (CLAUDE.md.ref, settings.json.ref, rules/)
- codex/ (AGENTS.md.ref)
- cursor/ (cursorrules.ref)
- governance/ (ADR-TEMPLATE, ARCHITECTURE, DESIGN-DOC-TEMPLATE, etc.)
- hooks/ (post-tool/, pre-tool/, session/, subagent/, user-prompt/)
- manifests/ (pre-commit-config.yaml.ref, quality-gate-manifest.json.ref)
- product/ (ARCHITECTURE-OUTLINE, ASSUMPTIONS-AND-RISKS, PRD, etc.)
- project-configs/ (python-django.json, python-fastapi.json, typescript-node.json)
- skills/ (5 .md.ref files)

**VibeOS-2 references in reference/claude/CLAUDE.md.ref:** These are legitimate upgrade flow documentation, not hardcoded paths. Left as-is.

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Findings: Reference file count is 44 (not "40+" as estimated)
- Test status: File counts verified, grep clean for decision-engine/

## Evidence

- [x] All 8 decision engine files copied
- [x] All 44 reference files copied with directory structure
- [x] Decision engine headers updated from "VibeOS-2" to "VibeOS Plugin"
- [x] File counts match source
