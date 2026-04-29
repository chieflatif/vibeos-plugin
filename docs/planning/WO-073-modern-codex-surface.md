# WO-073: Modern Codex Surface

## Status

`Complete`

## Phase

Phase 14: VibOS Comp — Enterprise MVP Battle Harness

## Objective

Upgrade the Codex install surface from sequential Markdown role contracts to the current Codex-native project layout for skills, custom agents, hooks, and controlled multi-agent execution.

## Scope

### In Scope
- [x] Generate `.agents/skills/vibeos-*` from the current Codex skill references
- [x] Generate `.codex/agents/*.toml` custom agent definitions for VibeOS roles
- [x] Install `.codex/hooks.json` for compatible prompt, shell, and edit-time checks where Codex supports them
- [x] Preserve legacy `.codex/agents/*.md` role contracts only as reference material when needed
- [x] Update `vibeos-init-codex.sh`, uninstall, upgrade, and welcome output
- [x] Keep Claude/Cursor assets untouched

### Out of Scope
- Claiming Codex hook parity with Claude Code hooks
- Removing Git commit-boundary hooks
- Provider-specific model account provisioning

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-072 | Runtime capability matrix | Complete |

## Findings

1. Current OpenAI Codex docs describe repo skills under `.agents/skills` and custom subagents under `.codex/agents/*.toml`.
2. Current VibeOS Codex bootstrap installs `.codex/skills` and Markdown role contracts, which undersells and underuses current Codex capabilities.
3. Codex hooks exist but are not equivalent to Claude hook enforcement; the install surface must represent this distinction explicitly.

## Research & Freshness

- Verified on: 2026-04-29.
- Sources to verify during implementation: OpenAI Codex skills, subagents, hooks, and AGENTS.md docs.
- Local prerequisite: `codex features list` should show whether `multi_agent` and `codex_hooks` are available.

## Impact Analysis

- **Files created:** `plugins/vibeos/reference/codex/config.toml.ref`, `plugins/vibeos/reference/codex/hooks.json.ref`, `plugins/vibeos/reference/codex/hooks/*.sh`, `tests/test_codex_bootstrap.py`
- **Files modified:** `vibeos-init-codex.sh`, Codex reference templates, README/install docs, upgrade path
- **Systems affected:** Codex install behavior, Codex build orchestration, Codex audit orchestration

## Acceptance Criteria

- [x] AC-1: Fresh Codex install creates current Codex-native skill and agent layout
- [x] AC-2: Upgrade mode preserves user state and migrates legacy `.codex/skills` safely
- [x] AC-3: Generated TOML agents map VibeOS roles to suitable models, tools, and descriptions
- [x] AC-4: Hook installation is explicit about supported checks and unsupported enforcement gaps
- [x] AC-5: README and AGENTS templates no longer claim Codex has no subagent capability
- [x] AC-6: Claude/Cursor bootstrap output and assets remain unchanged except for shared runtime references

## Test Strategy

- **Syntax tests:** `bash -n vibeos-init-codex.sh`
- **Install fixture:** run Codex bootstrap into a temporary git project and inspect generated files
- **JSON/TOML tests:** parse generated hook config and agent TOML
- **Real-path verification:** run install and uninstall flows against a fixture project
- **Verification command:** `bash vibeos-init-codex.sh --target /tmp/vibeos-codex-fixture --force`

## Implementation Plan

### Step 1: Add Source Templates
- Add Codex-native agent and hook templates under `plugins/vibeos/reference/codex/`
- Expected outcome: install source is explicit and versioned

### Step 2: Update Bootstrap
- Copy new templates, preserve old state, and update uninstall logic
- Expected outcome: new installs get the modern Codex surface

### Step 3: Validate
- Add fixture checks for fresh install, upgrade, and uninstall
- Expected outcome: Codex support is current and truthful

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Findings: Modern Codex repo skills, native subagents, and hooks needed to be represented truthfully.
- Test status: WO scope backed by WO-072 runtime matrix.

### Pre-Implementation Audit
- Status: `complete`
- Findings: Install must preserve legacy skill fallback and not claim Claude hook parity.
- Test status: Source templates and bootstrap path identified.

### Pre-Commit Audit
- Status: `complete`
- Findings: Fresh install generates `.agents/skills`, `.codex/agents`, hook config, hook scripts, and legacy contracts.
- Test status: `tests/test_codex_bootstrap.py` passes.

## Evidence

- [x] Implementation complete
- [x] Tests pass: `python3 -m unittest tests/test_codex_bootstrap.py`
- [x] Fixture install verified: `bash vibeos-init-codex.sh --target "$tmpdir" --force`
- [x] Documentation updated
