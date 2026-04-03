# WO-059: Scope Discipline & File Budget Guards

## Status

`Complete`

## Phase

Phase 11: Advanced Governance (v2.1)

## Objective

Add two guardrails that prevent work order scope creep and module bloat: a scope discipline gate that limits WO blast radius (max files, areas, test requirements), and a file budget hook that enforces module size limits to keep code composable.

## Context

Joan learned two hard lessons during 200+ WOs:
1. **Scope creep kills quality** — WOs that touch too many files or areas become impossible to audit effectively. `validate-scope-discipline.sh` enforces hard limits.
2. **Large files resist change** — Files over 300 lines become monolithic and hard to test. The file budget hook warns at 250 lines and blocks at 300, forcing decomposition.

Both are configurable via environment variables and can be tuned per-project.

## Joan Sources

- `/Users/latifhorst/Joan/.vibeos/scripts/validate-scope-discipline.sh`
- `/Users/latifhorst/Joan/.claude/hooks/new-line-file-budget.sh`

## Scope

### In Scope

1. **`scripts/validate-scope-discipline.sh`** — WO exit gate:
   - Counts production files changed in current WO
   - Counts new production files created
   - Counts distinct areas (top-level directories) touched
   - Checks test delta exists when code changes exist
   - Configurable via env vars:
     - `MAX_PRODUCTION_FILES` (default: 10)
     - `MAX_NEW_PRODUCTION_FILES` (default: 4)
     - `MAX_AREA_COUNT` (default: 5)
     - `REQUIRE_TEST_DELTA` (default: true)
   - Excludes: test files, docs, config files from production count

2. **`hooks/file-budget.sh`** — PreToolUse hook for Write/Edit:
   - Generalized from Joan's `new-line-file-budget.sh` (no kernel/NWO references)
   - Checks target file line count
   - Warns at configurable threshold (default: 250 lines)
   - Blocks at configurable threshold (default: 300 lines)
   - Excludes: test files, documentation, config files, generated files
   - Session-state aware: reads active WO for context
   - Only enforces for production code files (not scripts, hooks, agents)

3. **Model version validation** — `scripts/validate-model-versions.sh`:
   - Enforce approved AI model deployment names in project code
   - Configurable approved/forbidden model lists via env vars
   - Scans Python, JSON, YAML, shell files in src/, tests/, config directories

4. **Gate manifest entries** — Add to quality-gate-manifest.json:
   - scope-discipline: tier 1, blocking, wo_exit phase
   - model-versions: tier 2, non-blocking, wo_exit phase
   - file-budget: hook-level enforcement (not gate)

### Out of Scope

- Joan-specific kernel file targeting
- NWO session-state checks (generalize to any active WO)

## Acceptance Criteria

1. `validate-scope-discipline.sh` correctly counts files, new files, areas from git diff
2. Scope discipline respects all 4 env var overrides
3. `file-budget.sh` warns at threshold and blocks at limit
4. File budget correctly identifies file type (excludes tests, docs)
5. Both scripts pass `bash -n` syntax validation
6. Gate manifest updated with scope-discipline entry
7. hooks.json updated with file-budget hook
8. All scripts have `FRAMEWORK_VERSION="2.1.0"`

## Dependencies

- WO-056 — session state for context-aware enforcement

## Files Created

- `plugins/vibeos/scripts/validate-scope-discipline.sh`
- `plugins/vibeos/scripts/validate-model-versions.sh`
- `plugins/vibeos/hooks/scripts/file-budget.sh`

## Files Modified

- Quality gate manifest — add scope-discipline entry
- `plugins/vibeos/hooks/hooks.json` — add file-budget hook
