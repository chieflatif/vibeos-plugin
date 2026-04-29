# WO-072: Runtime Capability Matrix

## Status

`Complete`

## Phase

Phase 14: VibOS Comp — Enterprise MVP Battle Harness

## Objective

Create a deterministic runtime capability matrix so VibOS Comp knows what Claude Code, Codex CLI, Codex app, hooks, agents, skills, models, and worktree features are actually available before selecting an orchestration strategy.

## Scope

### In Scope
- [x] Add a local capability detection command for Codex and Claude surfaces
- [x] Record tool versions, feature flags, hook support, multi-agent support, model defaults, worktree support, and known enforcement gaps
- [x] Write results to `.vibeos/runtime-capabilities.json`
- [x] Add a human-readable capability summary for build/audit workflows
- [x] Update Codex and Claude instructions to consume the matrix before claiming support

### Out of Scope
- Installing or upgrading user tools automatically
- Provider billing, pricing, or credential management
- Replacing VibeOS gates or Work Orders

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-068 | Codex cross-surface hardening baseline | Complete |
| WO-071 | Current v2.2 metadata baseline | Complete |

## Findings

1. Local repo instructions still describe Codex as having no subagent spawning or runtime hooks, while current Codex documentation and local feature flags show multi-agent and hook capability now exist.
2. Claude Code and Codex have different enforcement boundaries. Capability selection must be runtime-aware instead of encoded as static documentation.
3. Enterprise MVP builds need orchestration to fail closed when critical capabilities are missing or stale.

## Research & Freshness

- Verified on: 2026-04-29.
- Local evidence: `codex --version`, `codex features list`, `claude --version`, `claude agents`.
- External sources to keep current: OpenAI Codex subagents, hooks, skills, models docs; Claude Code subagents and agent teams docs.

## Impact Analysis

- **Files created:** `plugins/vibeos/scripts/runtime-capabilities.py`, `plugins/vibeos/scripts/detect-runtime-capabilities.sh`, `tests/test_runtime_capabilities.py`, `.vibeos/runtime-capabilities.json` at runtime
- **Files modified:** Codex/Claude surface instructions, build/audit skills, bootstrap gitignore setup, quality manifest, README, development plan, WO index, file inventory
- **Systems affected:** runtime selection, build routing, audit routing, install truthfulness

## Acceptance Criteria

- [x] AC-1: Command detects Codex CLI version and relevant feature flags when Codex is installed
- [x] AC-2: Command detects Claude Code version and registered VibeOS agents when Claude is installed
- [x] AC-3: Output distinguishes available, unavailable, experimental, and unknown capabilities
- [x] AC-4: Output records enforcement limitations separately from feature availability
- [x] AC-5: Build and audit workflows read the matrix before choosing sequential, subagent, worktree, or app-based orchestration; Comp workflows depend on this artifact in WO-073+
- [x] AC-6: Tests cover parser behavior, feature stages, agent extraction, and strategy fallback

## Test Strategy

- **Unit tests:** parse fixture outputs for Codex and Claude capability commands
- **Integration tests:** run the detector on the local machine when tools are available
- **Real-path verification:** generate `.vibeos/runtime-capabilities.json` in this repo and inspect selected strategy
- **Verification command:** `bash .vibeos/scripts/detect-runtime-capabilities.sh --project-dir .`

## Implementation Plan

### Step 1: Add Detector
- Implement a Bash-compatible detector with JSON output
- Expected outcome: stable capability file without network dependency

### Step 2: Wire Consumers
- Update Comp, build, audit, and Codex instructions to use the matrix
- Expected outcome: orchestration claims match actual runtime support

### Step 3: Verify
- Add fixtures and local real-path checks
- Expected outcome: missing or stale runtime capability is visible before build execution

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Findings: Runtime capability selection must be explicit because Codex and Claude support differ by local version, feature flags, and installed project surface.
- Test status: Parser/unit and real-path verification selected.

### Pre-Implementation Audit
- Status: `complete`
- Findings: Bash wrapper plus Python parser keeps the user-facing command simple while making output parsing testable.
- Test status: Unit, syntax, JSON, and local detector run selected.

### Pre-Commit Audit
- Status: `complete`
- Findings: Detector writes generated local state, keeps limitations separate from feature availability, and does not claim Codex/Claude enforcement parity.
- Test status: Targeted unit tests, syntax checks, JSON validation, and real-path detector run passed.

## Evidence

- [x] Implementation complete
- [x] Tests pass
- [x] Real-path capability generation verified
- [x] Documentation updated

Verification commands run:
- `python3 -m unittest tests.test_runtime_capabilities`
- `python3 -m unittest discover -s tests`
- `bash -n vibeos-init.sh vibeos-init-codex.sh plugins/vibeos/scripts/detect-runtime-capabilities.sh plugins/vibeos/scripts/plugin-upgrade.sh`
- `python3 -m py_compile plugins/vibeos/scripts/runtime-capabilities.py plugins/vibeos/scripts/evidence-recall.py tests/test_runtime_capabilities.py tests/test_evidence_recall.py`
- `for f in plugins/vibeos/quality-gate-manifest.json plugins/vibeos/.claude-plugin/plugin.json .claude-plugin/marketplace.json plugins/vibeos/hook-manifest.json; do python3 -m json.tool "$f" >/dev/null || exit 1; done`
- `bash plugins/vibeos/scripts/detect-runtime-capabilities.sh --project-dir .`
