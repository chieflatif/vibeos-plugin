---
wo: WO-109
title: Runtime Capability Detection Repair + Extension
status: Complete
phase: 34
phase_name: Foundation Repair
wo_class: harness
write_scope:
  - docs/planning/WO-109-runtime-capability-detection-repair.md
  - docs/planning/WO-INDEX.md
  - plugins/vibeos/scripts/runtime-capabilities.py
  - plugins/vibeos/scripts/detect-runtime-capabilities.sh
  - tests/test_runtime_capabilities.py
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

# WO-109: Runtime Capability Detection Repair + Extension

## Status

`Complete` — detection repaired and extended, real-path verified (`subagents=available`, strategy `claude / claude-subagents`), 16/16 tests pass, audit findings fixed. Phase 34 gate floor remains red on out-of-scope gates — see "Known Out-of-Scope Failures".

## Phase

Phase 34: Foundation Repair

## Objective

Repair Claude subagent detection and extend the runtime capability matrix. Today `detect_claude()` derives `subagents` from `claude agents` CLI active-count, which fails or returns nothing in a non-TTY context, so the matrix reports `subagents=unavailable` on Claude 2.1.170 and the orchestration strategy collapses to `sequential / single-context`. Make subagent availability version-gated (authoritative), retry `claude agents` with `--json` on non-TTY failure, and add three new capability fields — `agent_teams`, `dynamic_workflows`, `headless` — each with an evidence string. Recompute the strategy from the corrected capabilities.

## Scope

### In Scope
- [x] `claude agents` non-TTY failure retries with `claude agents --json` (tolerant JSON parser)
- [x] `subagents` reported `available` on 2.1.170 (version-gated, not dependent on CLI active-count)
- [x] New `agent_teams`: env-var opt-in + version ≥ 2.1.32 → `experimental_available`, else `unavailable`
- [x] New `dynamic_workflows`: version ≥ 2.1.154 AND not disabled → `available`
- [x] New `headless`: claude binary present → `available`
- [x] Each new capability carries an evidence string (`capability_evidence`)
- [x] Strategy recomputed from corrected capabilities (`claude / claude-subagents` when subagents available)
- [x] Tests in `tests/test_runtime_capabilities.py` for version gating, the new fields, and JSON-retry parsing

### Out of Scope
- Codex capability detection changes (unchanged)
- The file-size posture of `runtime-capabilities.py` (Phase 34 gate-floor remediation WO)
- Hook-manifest / status reconciliation (WO-110)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-108 | Predecessor (Phase 34 order) | Complete |

## Findings

1. `detect_runtime-capabilities.sh --project-dir .` reports `Claude: ... subagents=unavailable` on version 2.1.170 → strategy `sequential / single-context`, which suppresses subagent orchestration even though subagents are available.
2. Root cause: `capabilities.subagents = status(bool(active_count))` where `active_count` comes from parsing `claude agents` stdout, which is empty/failing in non-TTY runs.

## Acceptance Criteria

- [x] AC-1: `version_ge` compares dotted-int versions numerically (`2.1.170 >= 2.1.32`) — `test_version_ge_compares_dotted_ints_numerically`, `test_version_ge_tolerates_suffixed_versions`
- [x] AC-2: `compute_claude_capabilities` reports `subagents=available` for 2.1.170 — `test_subagents_available_on_2_1_170`
- [x] AC-3: `agent_teams=experimental_available` only with env opt-in AND version ≥ 2.1.32 — `test_agent_teams_experimental_requires_env_and_version`
- [x] AC-4: `dynamic_workflows` version-gated at 2.1.154 and honors the disable env — `test_dynamic_workflows_version_gated_and_disable_respected`
- [x] AC-5: `headless=available` when the claude binary is present — `test_headless_available_when_binary_present`
- [x] AC-6: `claude agents` non-TTY failure retries with `--json`; tolerant parser — `test_parse_claude_agents_json_*`; live evidence string shows the retry fired
- [x] AC-7: Strategy recomputes to `claude / claude-subagents` — `test_recommend_strategy_falls_back_to_claude` + real-path output
- [x] AC-8: `detect-runtime-capabilities.sh --project-dir .` shows `subagents=available`; 16/16 tests pass

## Test Strategy

- **Unit:** `python3 -m pytest tests/test_runtime_capabilities.py` (pure helpers: `version_ge`, `compute_claude_capabilities`, `parse_claude_agents_json`)
- **Real-path:** `bash plugins/vibeos/scripts/detect-runtime-capabilities.sh --project-dir .` → `subagents=available`, strategy `claude / claude-subagents`

## Implementation Plan

1. Write version-gating + new-field + JSON-retry tests (TDD red).
2. Add `version_tuple`/`version_ge`, `parse_claude_agents_json`, extract pure `compute_claude_capabilities`, wire the `--json` retry into `detect_claude`.
3. Verify real-path output; run Layer-2 audit; document.

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Test strategy: pure unit tests in `tests/test_runtime_capabilities.py` (mock env/path, no claude binary required).
- Real-path entrypoint: `detect-runtime-capabilities.sh` → `runtime-capabilities.py` (writes `.vibeos/runtime-capabilities.json`).
- Findings: Single-file logic change + tests. Risk: version thresholds and env-var names; mitigated by named module constants, evidence strings, and unit tests.

### Pre-Implementation Audit
- Status: `complete` (recorded retrospectively)
- Findings: `runtime-capabilities.py` is the only file touched. Subagent detection moved from `claude agents` active-count (empty in non-TTY) to a version gate (authoritative). New capabilities extracted into a pure, testable `compute_claude_capabilities`. No external deps; python3 prerequisite present. No downstream consumer reads the removed `agents.active_count` for capability derivation (verified by the correctness auditor).
- Anchor status: aligned. Freshness status: thresholds are version constants; revisit on Claude Code releases.

### Pre-Commit Audit
- Status: `complete`
- Layer-2 auditors (same-tree, read-only): correctness-auditor, evidence-auditor.
- Correctness findings: 0 critical/high; 1 MEDIUM (`version_tuple` truncated on suffixed versions like `2.1.170-beta`) — **fixed** (per-chunk leading-digit parse) + regression test `test_version_ge_tolerates_suffixed_versions`; 2 LOW (hardcoded thresholds documented as named constants; cosmetic `.get` default) — accepted. No contract break for downstream JSON consumers (they read only `strategy.*`).
- Evidence findings: WO documented to parity; status reconciled with WO-INDEX; out-of-scope failures enumerated below.
- Test status: `python3 -m pytest tests/test_runtime_capabilities.py` → 16 passed.
- Anchor status: aligned. Freshness status: N/A.

### Staging / Completion Audit
- Status: `complete`
- Real path exercised: `bash plugins/vibeos/scripts/detect-runtime-capabilities.sh --project-dir .` → `Claude: ... subagents=available`, `Strategy: claude / claude-subagents` (was `subagents=unavailable` / `sequential / single-context`). Generated matrix `claude.capabilities` includes `agent_teams`, `dynamic_workflows`, `headless` with `capability_evidence` for each; subagents evidence confirms the `--json` retry fired.
- Repo state: clean, resumable; only WO-109 scope files touched.

## Known Out-of-Scope Failures (pre_commit gate floor)

WO-109 does **not** fix the four blocking gate failures carried from WO-108 — they are unchanged and owned by the Phase 34 gate-floor remediation:

| Gate | Why it fails | Owner |
|---|---|---|
| `validate-file-size.sh` | Framework scripts exceed the 300-line hard limit | Phase 34 gate-floor remediation |
| `validate-code-complexity.sh` | Same oversized framework scripts | Same remediation |
| `detect-stubs-placeholders.py` | False positives on the no-touch fixture stubs + sibling detection-keyword scripts | Same remediation |
| `validate-tests-pass.sh` | Language detection returns `unknown` (no repo-root project marker) | Same remediation |

See the "Phase 34 Planning Gap" note in WO-108 for context. The remediation WO will be authored after WO-110, before the Phase 34 audit checkpoint.

## Evidence

- [x] Implementation complete
- [x] Tests pass (`python3 -m pytest tests/test_runtime_capabilities.py` → 16 passed)
- [x] Real path verified (`subagents=available`, strategy `claude / claude-subagents`)
- [x] Documentation updated (WO file, WO-INDEX.md, build log)

### Proof Commands
```bash
bash plugins/vibeos/scripts/detect-runtime-capabilities.sh --project-dir .
#   → Claude: available version=2.1.170 subagents=available worktrees=available
#   → Strategy: claude / claude-subagents
python3 -m pytest tests/test_runtime_capabilities.py
#   → 16 passed
```
