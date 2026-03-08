# WO-002: Bundle Gate Scripts

## Status

`Complete`

## Phase

Phase 1: Plugin Foundation

## Objective

Copy all gate scripts and gate-runner.sh from VibeOS-2 into the plugin's scripts/ directory and adapt gate-runner.sh to resolve script paths from the plugin root rather than hardcoded project paths.

## Scope

### In Scope
- [x] Copy all gate scripts from VibeOS-2 `scripts/` (26 files: 24 .sh, 1 .py, 1 .example.json)
- [x] Copy gate-runner.sh (500+ lines)
- [x] Adapt gate-runner.sh to accept `--framework-dir` or `CLAUDE_PLUGIN_ROOT` env var
- [x] Ensure `${CLAUDE_PLUGIN_ROOT}` resolves correctly when invoked from any project
- [x] Validate all scripts pass `bash -n` syntax check

### Out of Scope
- Modifying gate logic (scripts work as-is)
- Adding new gates
- Creating the gate skill (WO-004)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-001 | Must complete first | Complete |
| VibeOS-2 scripts/ | Source files | Available |

## Impact Analysis

- **Files created:** scripts/gate-runner.sh, 24 gate scripts (.sh), 1 Python gate, 1 example JSON
- **Files modified:** None
- **Systems affected:** Quality gate enforcement for any project using the plugin

## Acceptance Criteria

- [x] AC-1: All 26 source files exist in `scripts/`
- [x] AC-2: `bash -n scripts/*.sh` passes for all shell scripts
- [x] AC-3: Gate-runner supports `--framework-dir` and `--project-dir` flags
- [x] AC-4: Gate-runner resolves script paths via `CLAUDE_PLUGIN_ROOT` → `FRAMEWORK_DIR`
- [x] AC-5: No hardcoded paths to VibeOS-2 remain in any script

## Test Strategy

- **Unit:** `bash -n` syntax validation for every .sh file
- **Integration:** Run gate-runner.sh from a test project directory, confirm it finds and executes gates
- **Verification:** `grep -rn 'VibeOS-2' scripts/` returns no results

## Implementation Notes

**Script count correction (F-04 from planning audit):** Source has 26 files (not 21 as originally planned):
- 24 shell scripts (.sh)
- 1 Python script (detect-stubs-placeholders.py)
- 1 example JSON (architecture-rules.example.json)

**Path resolution changes to gate-runner.sh:**
- `FRAMEWORK_DIR` = where gate scripts live (plugin root, via `CLAUDE_PLUGIN_ROOT` or `--framework-dir`)
- `PROJECT_ROOT` = target project being validated (via `CLAUDE_PROJECT_DIR` or `--project-dir` or cwd)
- Script paths resolve via `FRAMEWORK_DIR`, manifest/lock paths via `PROJECT_ROOT`

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Findings: Script count was 26 not 21 (F-04 accepted, corrected during implementation)
- Test status: bash -n passes, grep clean, python compiles

## Evidence

- [x] All 26 scripts copied
- [x] All .sh files pass `bash -n` syntax check
- [x] Python script passes `python3 -m py_compile`
- [x] JSON validates via `jq`
- [x] `grep -rn 'VibeOS-2' scripts/` returns no results
- [x] gate-runner.sh supports FRAMEWORK_DIR / --framework-dir / --project-dir
