---
wo: WO-118
title: Model Policy Table + Lint
status: Complete
phase: 38
phase_name: Model/Effort/Cost Policy
wo_class: harness
write_scope:
  - docs/planning/WO-118-model-policy-table-lint.md
  - docs/planning/WO-INDEX.md
  - docs/evidence/vnext/generated-inventory.json
  - plugins/vibeos/reference/model-policy.json
  - plugins/vibeos/reference/wo-frontmatter.schema.json
  - plugins/vibeos/reference/manifests/quality-gate-manifest.json.ref
  - plugins/vibeos/quality-gate-manifest.json
  - plugins/vibeos/scripts/validate-model-policy.py
  - tests/test_model_policy.py
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

# WO-118: Model Policy Table + Lint

## Status

`Complete`

## Phase

Phase 38: Model/Effort/Cost Policy

## Objective

Add a provider-neutral model/effort policy table and deterministic lint that validates policy tiers, agent model aliases, and WO `model_policy` frontmatter without pinning current provider model IDs.

## Source Evidence

- Current Claude Code CLI docs checked on 2026-06-14: `--model` accepts aliases such as `sonnet`, `opus`, `haiku`, or full names, and `--effort` accepts `low`, `medium`, `high`, `xhigh`, and `max`.
- Current Claude Code settings docs checked on 2026-06-14: `model`, `effortLevel`, `availableModels`, `fallbackModel`, and teammate model settings are configurable surfaces.
- Current Claude Code headless docs checked on 2026-06-14: JSON output includes `total_cost_usd`, which WO-119 will consume for cost capture.

## Scope

### In Scope
- [x] Add `plugins/vibeos/reference/model-policy.json`
- [x] Add `plugins/vibeos/scripts/validate-model-policy.py`
- [x] Validate that policy tiers match `wo-frontmatter.schema.json`
- [x] Validate that agent `model:` aliases are declared in the policy
- [x] Validate WO `model_policy:` values against table tiers or `custom-*`
- [x] Register the lint in the live and reference quality-gate manifests
- [x] Add tests for pass/fail policy behavior and manifest registration

### Out of Scope
- ConfigChange downgrade blocking (`WO-119`)
- Cost report capture (`WO-119`)
- Rewriting every existing agent to tier names
- Codex model-equivalence claims
- Pinning specific latest model IDs
- Website changes

## Acceptance Criteria

- [x] AC-1: `model-policy.json` defines all schema-supported model tiers with `allow_downgrade` flags
- [x] AC-2: Lint passes on the current repo
- [x] AC-3: Lint fails on unknown agent model aliases
- [x] AC-4: Lint fails when policy tiers drift from the WO schema
- [x] AC-5: Custom `custom-*` WO model policies remain allowed
- [x] AC-6: The lint is registered in live and reference gate manifests

## Test Strategy

- **Policy lint:** `python3 plugins/vibeos/scripts/validate-model-policy.py --project-dir .`
- **Unit tests:** `python3 -m pytest tests/test_model_policy.py tests/test_wo_frontmatter_schema.py`
- **Manifest/status checks:** `python3 -m pytest tests/test_status_reconciliation.py tests/test_generate_inventory.py`
- **Full suite:** `python3 -m pytest tests`
- **Gate proof:** `bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos`

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Findings: The policy must use tier names and model aliases, not provider model IDs. Existing agent aliases can remain as compatibility aliases while WOs use model-policy tiers.
- Test status: Pending.

### Pre-Implementation Audit
- Status: `complete`
- Findings: The first safe slice is static policy plus lint only. Runtime downgrade enforcement and cost capture stay in WO-119.
- Test status: Pending.

### Pre-Commit Audit
- Status: `complete`
- Findings: Model policy is provider-neutral and tier-based. Runtime downgrade blocking and cost capture remain reserved for WO-119.
- Test status: Focused tests passed; full suite passed; `wo_entry` gate passed; `pre_commit` gate passed.

## Evidence

- [x] Implementation complete
- [x] Tests pass
- [x] Gates pass
- [x] Documentation updated

### Proof Commands

```bash
jq . plugins/vibeos/reference/model-policy.json >/dev/null
jq . plugins/vibeos/quality-gate-manifest.json >/dev/null
jq . plugins/vibeos/reference/manifests/quality-gate-manifest.json.ref >/dev/null

python3 plugins/vibeos/scripts/validate-model-policy.py --project-dir .
# [validate-model-policy] PASS: model policy, agent aliases, and WO tiers are consistent

python3 -m pytest tests/test_model_policy.py tests/test_wo_frontmatter_schema.py
# 11 passed in 0.03s

python3 -m pytest tests/test_status_reconciliation.py tests/test_generate_inventory.py tests/test_model_policy.py
# 13 passed in 0.28s

bash plugins/vibeos/scripts/gate-runner.sh wo_entry --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos --wo 118
# Total: 4 | Passed: 2 | Failed: 0 | Skipped: 2
# Result: PASS

python3 -m pytest tests
# 180 passed in 35.50s

bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos
# Total: 10 | Passed: 6 | Failed: 0 | Skipped: 4
# Result: PASS
```
