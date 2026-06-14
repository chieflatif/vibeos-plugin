---
wo: WO-119
title: ConfigChange Downgrade Guard + Cost Capture
status: Complete
phase: 38
phase_name: Model/Effort/Cost Policy
wo_class: harness
write_scope:
  - docs/planning/WO-119-configchange-downgrade-guard-cost-capture.md
  - docs/planning/WO-INDEX.md
  - docs/evidence/vnext/generated-inventory.json
  - plugins/vibeos/hooks/hooks.json
  - plugins/vibeos/hook-manifest.json
  - plugins/vibeos/hooks/scripts/model-policy-guard.sh
  - plugins/vibeos/scripts/capture-headless-cost.py
  - plugins/vibeos/reference/model-policy.json
  - tests/test_model_policy_guard.py
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

# WO-119: ConfigChange Downgrade Guard + Cost Capture

## Status

`Complete`

## Phase

Phase 38: Model/Effort/Cost Policy

## Objective

Add the Claude Code `ConfigChange` downgrade guard and a deterministic headless-cost report helper so active model-policy tiers and future loop evidence can be enforced from source-derived policy instead of prose.

## Source Evidence

- Official Claude Code hook docs checked on 2026-06-14: `ConfigChange` can block configuration changes, but `policy_settings` changes cannot be blocked by hooks.
- Official Claude Code settings docs checked on 2026-06-14: `model`, `effortLevel`, `fallbackModel`, and teammate model settings are configurable surfaces.
- Official Claude Code headless docs checked on 2026-06-14: `--output-format json` exposes `total_cost_usd`, which is the source field for `cost-report.json`.

## Scope

### In Scope
- [x] Register `ConfigChange` to run `plugins/vibeos/hooks/scripts/model-policy-guard.sh`
- [x] Implement the guard against the provider-neutral `plugins/vibeos/reference/model-policy.json`
- [x] Resolve active policy from `ConfigChange` payload or `.vibeos/session-state.json` active WO frontmatter
- [x] Block synthetic frontier-audit downgrades for model alias, fallback model, teammate model, and effort
- [x] Add `plugins/vibeos/scripts/capture-headless-cost.py` to parse headless `total_cost_usd` into `cost-report.json`
- [x] Label cost output `estimate; reconcile against billing`
- [x] Keep hook manifest, generated inventory, and status reconciliation tests current

### Out of Scope
- Claiming Codex hook parity
- Claiming full automatic write-time enforcement across runtimes
- Running live Claude headless loops
- Reconciling parsed cost against provider billing
- Policy-setting enforcement, because Claude Code does not let hooks block `policy_settings`
- Website changes

## Design Notes

`model-policy-guard.sh` is a Claude Code `ConfigChange` command hook. It allows changes when no active policy is discoverable, when the active policy allows downgrades, or when the active policy is custom and not declared in the standard model-policy table. For standard tiers with `allow_downgrade: false`, it checks `model`, `fallbackModel`, `teammateDefaultModel`, and `effortLevel` against the active tier.

The guard records decisions to `.vibeos/hook-events/model-policy-guard.jsonl` for local evidence. This is hook-event evidence, not a cross-runtime enforcement claim.

`capture-headless-cost.py` reads Claude headless JSON from a file or stdin and writes a `cost-report.json` evidence artifact. It does not call Claude and does not produce billing truth.

## Acceptance Criteria

- [x] AC-1: `hooks.json` registers `ConfigChange` with `model-policy-guard.sh`
- [x] AC-2: Hook manifest documents the configured command hook
- [x] AC-3: Synthetic frontier-audit downgrade blocks with exit 2
- [x] AC-4: Compliant frontier-audit alias and effort allow
- [x] AC-5: `policy_settings` source is observed but not blocked
- [x] AC-6: Cost helper writes `cost-report.json` with `total_cost_usd` and the required estimate label
- [x] AC-7: Generated inventory and WO index reconcile

## Test Strategy

- **Focused tests:** `python3 -m pytest tests/test_model_policy_guard.py tests/test_status_reconciliation.py`
- **Cost helper smoke:** `python3 plugins/vibeos/scripts/capture-headless-cost.py --input <headless.json> --evidence-dir <evidence-dir>`
- **Index check:** `python3 plugins/vibeos/scripts/wo-frontmatter-lint.py validate-index --project-dir .`
- **Full suite:** `python3 -m pytest tests`
- **Gate proof:** `bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos`

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Findings: The guard must be Claude-specific and policy-derived. `policy_settings` cannot be represented as blockable enforcement. Cost capture must be local parser proof only.
- Test status: Pending.

### Pre-Implementation Audit
- Status: `complete`
- Findings: A safe slice is possible by limiting runtime enforcement to the ConfigChange hook, using the existing model-policy table, and parsing cost from supplied JSON rather than running headless Claude.
- Test status: Pending.

### Pre-Commit Audit
- Status: `complete`
- Findings: The ConfigChange guard blocks synthetic non-downgrade policy violations and records local hook evidence. The cost helper writes an estimate-only report from headless JSON. No Codex parity or billing-truth claim is made.
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

python3 -m pytest tests/test_model_policy_guard.py tests/test_status_reconciliation.py
# 11 passed in 0.54s

python3 plugins/vibeos/scripts/capture-headless-cost.py --input - --evidence-dir /tmp/vibeos-cost-fixture --generated-at 2026-06-14T00:00:00Z
# [capture-headless-cost] PASS: wrote /tmp/vibeos-cost-fixture/cost-report.json

python3 plugins/vibeos/scripts/wo-frontmatter-lint.py validate-index --project-dir .
# [wo-frontmatter] PASS: WO-INDEX.md generated block is current

python3 plugins/vibeos/scripts/validate-model-policy.py --project-dir .
# [validate-model-policy] PASS: model policy, agent aliases, and WO tiers are consistent

bash plugins/vibeos/scripts/gate-runner.sh wo_entry --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos --wo 119
# Total: 4 | Passed: 2 | Failed: 0 | Skipped: 2
# Result: PASS

python3 -m pytest tests
# 187 passed in 34.75s

bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos
# Total: 10 | Passed: 6 | Failed: 0 | Skipped: 4
# Result: PASS
```
