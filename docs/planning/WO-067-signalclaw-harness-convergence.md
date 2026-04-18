# WO-067: Signal Claw Harness Convergence

## Status

`Complete`

## Phase

Phase 12: Harness Convergence

## Objective

Port the reusable harness improvements proven during Signal Claw setup back into the ViableOS plugin so future installs get the stronger governance spine without inheriting Signal-Claw-specific doctrine.

## Scope

### In Scope
- [x] Audit the plugin against the Signal Claw harness and identify portable upgrades
- [x] Fix canonical path drift for quality-gate manifests and version tracking
- [x] Add missing generic governance assets: audit protocol, agent workflow, file-size, git hygiene, audit discipline, role separation
- [x] Bundle the corresponding generic scripts: file-size, session-commit, dispatch-audit, audit-ratchet, audit aggregation, commit-msg validation
- [x] Update planning/bootstrap guidance so new projects generate the upgraded harness shape

### Out of Scope
- Full framework release packaging and semver bump beyond the existing 2.1.0 line
- Rewriting all historical planning docs to the new canon
- Project-specific Signal Claw product doctrine

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-065 | Release packaging baseline | Complete |
| WO-066 | Stop-hook hardening baseline | Complete |
| `/Users/latifhorst/signalclaw` | Audit source / donor harness | Verified |

## Impact Analysis

- **Files created:** portable governance reference docs, portable enforcement rules, generic harness scripts
- **Files modified:** bootstrap installers, upgrade flow, planning/gate skills, manifest references, plugin metadata, planning docs
- **Systems affected:** bootstrap consistency, upgrade compatibility, downstream project planning outputs, git hygiene, audit infrastructure

## Acceptance Criteria

- [x] AC-1: The plugin ships the generic governance assets now present in the Signal Claw harness
- [x] AC-2: Canonical file paths are consistent for quality-gate manifests and version tracking
- [x] AC-3: Planning guidance points downstream repos at `AGENTS.md`, `CLAUDE.md`, `.claude/CLAUDE.md`, `AUDIT-PROTOCOL.md`, and `AGENT-WORKFLOW.md`
- [x] AC-4: The plugin bundles working generic scripts for file-size enforcement, session-scoped commits, audit dispatch, ratcheting, and commit-msg validation
- [x] AC-5: The plugin repo documents this convergence work as a completed WO

## Test Strategy

- **Syntax validation:** `bash -n` on changed shell scripts
- **Python validation:** `python3 -m py_compile` on new Python helpers
- **Consistency checks:** `jq` validation for changed JSON manifests and targeted `rg` sweeps for canonical path references
- **Real-path verification:** inspect bootstrap output logic and upgrade fallback logic for both `version.json` and legacy `version.txt`

## Implementation Plan

### Step 1: Audit the delta
- Compare Signal Claw's shipped harness assets against the plugin's current framework
- Separate generic improvements from project-specific doctrine

### Step 2: Port the portable spine
- Add missing governance reference docs and always-rules
- Add the generic scripts that make those rules real

### Step 3: Fix framework contract drift
- Normalize quality-gate manifest location to `.claude/quality-gate-manifest.json`
- Normalize version tracking around `version.json` with `version.txt` fallback compatibility

### Step 4: Update generation guidance
- Patch planning and bootstrap-related docs so future projects receive the stronger harness by default

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Findings: The plugin had real contract drift (`quality-gate-manifest` path variants, `version.txt` vs `version.json`) and was missing several now-proven generic harness assets.
- Test status: Validation plan defined before edits.

### Pre-Implementation Audit
- Status: `complete`
- Findings: The right scope is the portable harness spine only; Signal Claw-specific canon stays out of the plugin.
- Test status: Script syntax, JSON validation, and targeted consistency sweeps selected.

### Pre-Commit Audit
- Status: `complete`
- Findings: Added assets are generic, version fallback is backward-compatible, and planning guidance now points at the upgraded downstream shape.
- Test status: Syntax, compile, and path-consistency checks passed.

## Evidence

- [x] Implementation complete
- [x] Tests pass
- [x] Gates pass
- [x] Documentation updated

Verification commands run:
- `bash -n vibeos-init.sh vibeos-init-codex.sh plugins/vibeos/scripts/setup-git-hooks.sh plugins/vibeos/scripts/plugin-upgrade.sh plugins/vibeos/scripts/validate-file-size.sh plugins/vibeos/scripts/session-commit.sh plugins/vibeos/scripts/dispatch-audit.sh plugins/vibeos/scripts/audit-ratchet.sh plugins/vibeos/scripts/validate-commit-msg.sh`
- `python3 -m py_compile plugins/vibeos/scripts/audit_aggregate.py`
- `jq . plugins/vibeos/.claude-plugin/plugin.json`
- `jq . plugins/vibeos/quality-gate-manifest.json`
- `jq . plugins/vibeos/reference/manifests/quality-gate-manifest.json.ref`
- `git diff --check`
- `rg -n "\.vibeos/quality-gate-manifest\.json|scripts/quality-gate-manifest\.json" CLAUDE.md vibeos-init.sh vibeos-init-codex.sh docs/FILE-INVENTORY.md plugins/vibeos/skills plugins/vibeos/reference plugins/vibeos/scripts plugins/vibeos/quality-gate-manifest.json`
