---
wo: WO-117
title: Worktree + Team-Governance Hooks (Dormant)
status: Complete
phase: 37
phase_name: Hook Lifecycle Modernization
wo_class: harness
write_scope:
  - docs/planning/WO-117-worktree-team-governance-hooks.md
  - docs/planning/WO-INDEX.md
  - docs/evidence/vnext/generated-inventory.json
  - plugins/vibeos/hooks/hooks.json
  - plugins/vibeos/hook-manifest.json
  - plugins/vibeos/hooks/scripts/team-governance.sh
  - plugins/vibeos/hooks/scripts/worktree-scope-setup.sh
  - plugins/vibeos/scripts/runtime-capabilities.py
  - tests/test_team_governance_hooks.py
  - tests/test_runtime_capabilities.py
  - tests/test_status_reconciliation.py
no_touch:
  - /Users/latifhorst/latifhorstweb/**
  - /Users/latifhorst/Joan4U/**
required_auditors:
  - correctness-auditor
  - evidence-auditor
model_policy: implementation
budget_posture:
  token_ceiling: null
  turn_ceiling: null
  cost_ceiling_usd: null
---

# WO-117: Worktree + Team-Governance Hooks (Dormant)

## Status

`Complete`

## Phase

Phase 37: Hook Lifecycle Modernization

## Objective

Add the dormant Claude Code agent-team governance hook surface and a WorktreeCreate scope setup hook without making agent teams a default VibeOS path.

## Source Evidence

- Official Claude Code agent-team docs checked on 2026-06-14: agent teams are experimental, disabled by default, require Claude Code 2.1.32+, and are enabled with `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`.
- Official Claude Code hook docs checked on 2026-06-14: `TaskCreated`, `TaskCompleted`, `TeammateIdle`, and `WorktreeCreate` are hook events; the first three can veto with exit code 2; `WorktreeCreate` replaces default git worktree behavior and must output an absolute worktree path.
- Local capability detection before implementation: `bash plugins/vibeos/scripts/detect-runtime-capabilities.sh --project-dir .` reported Claude 2.1.177, subagents available, worktrees available, and agent teams unavailable because the opt-in env var is unset.

## Scope

### In Scope
- [x] Register `TaskCreated`, `TaskCompleted`, and `TeammateIdle` command hooks pointing at a dormant-by-default `team-governance.sh`
- [x] Register `WorktreeCreate` command hook pointing at `worktree-scope-setup.sh`
- [x] Correct the runtime capability detector to use the current documented agent-team opt-in variable
- [x] Add synthetic tests for flag-off allow, flag-on allow, flag-on veto, and real git worktree scope setup
- [x] Keep hook manifest and generated inventory in sync

### Out of Scope
- Enabling agent teams by default
- Claiming agent-team production readiness
- Codex hook parity or Codex agent-team equivalence
- Dynamic workflow adoption
- WorktreeRemove customization
- Public website changes

## Design Notes

`team-governance.sh` is dormant unless `.vibeos/config.json` opts in with:

```json
{"features": {"agent_team_governance": true}}
```

When enabled, `TaskCreated` requires a WO reference and task description. `TaskCompleted` requires a WO reference before closure. `TeammateIdle` records enabled idle events for pilot evidence but does not block by default.

`WorktreeCreate` cannot be a literal no-op because Claude Code treats a configured WorktreeCreate hook as the full worktree creation implementation. The hook therefore creates the git worktree under `.claude/worktrees/<name>`, prints the absolute path on stdout, copies `.vibeos/worktree-scopes.json` into the new checkout when present, and preserves simple `.worktreeinclude` entries when the source file is gitignored.

## Acceptance Criteria

- [x] AC-1: `hooks.json` registers `TaskCreated`, `TaskCompleted`, `TeammateIdle`, and `WorktreeCreate`
- [x] AC-2: `team-governance.sh` exits 0 with the feature flag absent
- [x] AC-3: `team-governance.sh` permits scoped WO-backed tasks and vetoes missing-WO closure when enabled
- [x] AC-4: `worktree-scope-setup.sh` creates a git worktree and copies the scope manifest in a fixture repo
- [x] AC-5: Runtime capability detection uses `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`
- [x] AC-6: Hook manifest, WO index, and generated inventory reconcile with the new hook count

## Test Strategy

- **Hook tests:** `python3 -m pytest tests/test_team_governance_hooks.py`
- **Runtime capability tests:** `python3 -m pytest tests/test_runtime_capabilities.py`
- **Manifest sync:** `python3 -m pytest tests/test_status_reconciliation.py`
- **Full suite:** `python3 -m pytest tests`
- **Gate proof:** `bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos`

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Findings: Current official docs support the events but make two constraints material: agent teams stay experimental and opt-in, and WorktreeCreate hooks replace Claude's default git creation behavior.
- Test status: Pending.

### Pre-Implementation Audit
- Status: `complete`
- Findings: The slice is safe if team governance remains flag-gated and WorktreeCreate preserves git-worktree behavior while adding only VibeOS scope copying.
- Test status: Pending.

### Pre-Commit Audit
- Status: `complete`
- Findings: Team governance is dormant unless opted in. WorktreeCreate is implemented as a default-compatible git worktree creator because configured WorktreeCreate hooks replace Claude's built-in git behavior and must return a path.
- Test status: Focused tests passed; full suite passed; `pre_commit` gate passed.

## Evidence

- [x] Implementation complete
- [x] Tests pass
- [x] Gates pass
- [x] Documentation updated

### Proof Commands

```bash
jq . plugins/vibeos/hooks/hooks.json >/dev/null
jq . plugins/vibeos/hook-manifest.json >/dev/null

bash plugins/vibeos/scripts/detect-runtime-capabilities.sh --project-dir .
# Claude: available version=2.1.177 subagents=available worktrees=available
# Strategy: claude / claude-subagents

CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 python3 - <<'PY'
import importlib.util
from pathlib import Path
m=Path('plugins/vibeos/scripts/runtime-capabilities.py').resolve()
s=importlib.util.spec_from_file_location('runtime_capabilities', m)
mod=importlib.util.module_from_spec(s); s.loader.exec_module(mod)
print(mod.compute_claude_capabilities('2.1.177', '--worktree --agents', '/opt/homebrew/bin/claude', 'test')[0]['agent_teams'])
PY
# experimental_available

python3 -m pytest tests/test_team_governance_hooks.py tests/test_runtime_capabilities.py tests/test_status_reconciliation.py
# 26 passed in 0.50s

python3 -m pytest tests
# 174 passed in 33.45s

bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos
# Total: 10 | Passed: 6 | Failed: 0 | Skipped: 4
# Result: PASS
```
