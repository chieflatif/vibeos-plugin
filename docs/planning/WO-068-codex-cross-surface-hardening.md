# WO-068: Codex Cross-Surface Hardening

## Status

`Complete`

## Phase

Phase 12: Harness Convergence

## Objective

Harden the VibeOS Codex surface so it is truthful, operational, and compatible with the shared governance runtime without pretending Codex has Claude Code's native hook model.

## Scope

### In Scope
- Audit the current Codex bootstrap and reference assets against the shared VibeOS runtime
- Fix the Codex bootstrap version drift
- Wire Codex installs into the shared Git-hook enforcement path where safe
- Make commit-boundary enforcement degrade gracefully before a project has a generated gate manifest
- Update Codex-facing instructions so AGENTS and skills describe the real enforcement model

### Out of Scope
- Recreating Claude Code's prompt-time or stop-time hook surface inside Codex
- A full semver release-packaging pass beyond the existing 2.1.x line
- Project-specific Codex app policy or admin controls outside the VibeOS repo contract

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-065 | v2.1 packaging baseline | Complete |
| WO-067 | Harness convergence baseline | Complete |
| OpenAI Codex official docs | Product constraint evidence | Verified |

## Findings

1. `vibeos-init-codex.sh` still stamps Codex installs as `2.0.0`, creating real version drift against the current 2.1.0 framework line.
2. The shared runtime already ships `setup-git-hooks.sh`, but the Codex bootstrap and Codex-facing docs still describe enforcement as fully manual, so commit-boundary protections are not actually activated for Codex users.
3. The existing Git-hook installer assumes a gate manifest already exists; on a fresh Codex install that can cause pre-commit enforcement to fail before planning has generated `.claude/quality-gate-manifest.json`.

## Acceptance Criteria

- [x] AC-1: Codex installs write the correct framework version metadata for the current 2.1.0 line
- [x] AC-2: Codex installs in git repositories attempt to enable shared commit-boundary enforcement through VibeOS-owned Git hooks
- [x] AC-3: The VibeOS pre-commit hook skips cleanly, with a truthful warning, until a gate manifest exists
- [x] AC-4: Codex-facing AGENTS, skills, and inventory docs describe the real enforcement model: AGENTS + shared gates + Git hooks, not Claude-style runtime hooks
- [x] AC-5: The work is verified on a real temporary git repository install path

## Test Strategy

- Syntax validation for changed shell scripts with `bash -n`
- Temporary-repo bootstrap test for `vibeos-init-codex.sh`
- Git-hook installation test in both default `.git/hooks` and custom `core.hooksPath` layouts
- Commit-path verification showing pre-commit skips cleanly before a manifest exists

## Implementation Plan

### Step 1: Fix the hard mismatch
- Align `vibeos-init-codex.sh` to the current 2.1.0 framework version

### Step 2: Activate real Codex-safe enforcement
- Use VibeOS Git hooks as the commit-boundary substitute for missing Claude runtime hooks
- Make the hook installer safe for fresh Codex installs and custom hook directories

### Step 3: Align the human contract
- Update Codex AGENTS, skills, and inventory docs so users understand what is and is not enforced automatically

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Findings: The Codex surface has a real version mismatch and a real enforcement gap, not just wording drift.
- Test status: Verification plan defined before edits.

### Pre-Implementation Audit
- Status: `complete`
- Findings: The right substitute for Claude hooks in Codex is shared Git hooks plus explicit gate entry points, not a fake runtime-hook abstraction.
- Test status: Temporary git repo install and commit-path checks selected.

### Pre-Commit Audit
- Status: `complete`
- Findings: Codex bootstrap, Git-hook installer, and Codex-facing docs now align on the same enforcement model. The hook installer also fixes an outside-target invocation bug by resolving the target Git directory absolutely.
- Test status: Syntax, diff hygiene, temporary install, commit-path, and custom hook-path checks passed. Full file-size gate remains blocked by pre-existing oversized framework scripts outside this WO.

## Evidence

- [x] Implementation complete
- [x] Tests pass
- [x] Targeted gates pass
- [ ] Full file-size gate passes
- [x] Documentation updated

Verification commands run:
- `bash -n vibeos-init-codex.sh plugins/vibeos/scripts/setup-git-hooks.sh`
- `git diff --check`
- Temporary git repository install: `bash vibeos-init-codex.sh --target "$TMP_REPO"`
- Version assertion: `.vibeos/version.json` reports `2.1.0`
- Hook assertion: `pre-commit` and `commit-msg` installed in the target repo
- Commit assertion: commit before manifest generation succeeds with a truthful `quality-gate-manifest.json not found` pre-commit warning
- Custom hooks assertion: `core.hooksPath=.githooks` installs hooks in the configured directory
- Changed-file size assertion: changed classified files are within their documented budgets
- Full file-size gate: `bash plugins/vibeos/scripts/validate-file-size.sh` currently fails on 16 pre-existing oversized framework scripts that were not modified by WO-068
