---
wo: WO-123
title: Workflow Governance Policy + Capability Detection
status: Complete
phase: 40
phase_name: Dynamic Workflow Adoption
wo_class: harness
write_scope:
  - docs/planning/WO-123-workflow-governance-policy-capability-detection.md
  - docs/planning/WO-INDEX.md
  - docs/evidence/vnext/generated-inventory.json
  - docs/evidence/vnext/wo-123-workflow-governance/**
  - plugins/vibeos/scripts/runtime-capabilities.py
  - plugins/vibeos/reference/governance/ARCHITECTURE.md.ref
  - plugins/vibeos/reference/governance/RUNTIME-MANIFEST.md.ref
  - plugins/vibeos/skills/audit/SKILL.md
  - plugins/vibeos/skills/build/SKILL.md
  - tests/test_runtime_capabilities.py
  - tests/test_workflow_governance.py
no_touch:
  - /Users/latifhorst/latifhorstweb/**
  - /Users/latifhorst/Joan4U/**
required_auditors:
  - correctness-auditor
  - evidence-auditor
model_policy: implementation
budget_posture:
  token_ceiling: null
  turn_ceiling: 1
  cost_ceiling_usd: 0
loop_goal: workflow governance policy is emitted and consumed before workflow use
loop_ceiling_turns: 1
loop_ceiling_cost_usd: 0
---

# WO-123: Workflow Governance Policy + Capability Detection

## Status

`Complete`

## Phase

Phase 40: Dynamic Workflow Adoption

## Objective

Add a workflow governance policy to VibeOS runtime detection and reference docs, then make build/audit instructions consume that policy before using Claude Code dynamic workflows.

## Source Evidence

- The vNext master plan requires workflow governance before bounded workflow execution.
- Official Claude Code workflow docs checked on 2026-06-14: dynamic workflows require Claude Code `v2.1.154+`, can be saved under `.claude/workflows/`, should be slice-probed before large runs because token usage can be materially higher, and can be disabled via `/config`, `disableWorkflows`, managed settings, or `CLAUDE_CODE_DISABLE_WORKFLOWS=1`.
- Existing `runtime-capabilities.py` already reports `dynamic_workflows`; WO-123 must add the governance policy around that field and make skills consume it.

## Scope

### In Scope
- [x] Update `runtime-capabilities.py` to emit `workflow_governance`
- [x] Use the current documented disable env `CLAUDE_CODE_DISABLE_WORKFLOWS`, while preserving legacy-env compatibility as a conservative disable signal
- [x] Add architecture/runtime-manifest reference policy text
- [x] Update build/audit skills to read `workflow_governance` before selecting workflow dispatch
- [x] Add deterministic tests and evidence fixtures

### Out of Scope
- Creating `.claude/workflows/vibeos-audit-sweep` (WO-124)
- Running a live dynamic workflow
- Claiming workflow adoption verdicts before bounded execution evidence
- Website changes

## Design Notes

The runtime matrix will keep `claude.capabilities.dynamic_workflows` as a capability field and add a top-level `workflow_governance` section. The policy is intentionally conservative:

- saved + reviewed scripts only for recurring use
- slice-first cost probe before broad repo workflows
- no project-governance writes from workflow agents
- disable paths documented
- dynamic workflow availability does not weaken VibeOS gates, hooks, WO contracts, or evidence requirements

## Acceptance Criteria

- [x] AC-1: Runtime matrix includes `workflow_governance`
- [x] AC-2: `CLAUDE_CODE_DISABLE_WORKFLOWS=1` disables `dynamic_workflows`
- [x] AC-3: Policy records saved project workflow directory, slice-first cost probe requirement, no-governance-writes rule, and disable paths
- [x] AC-4: Build and audit skills read/obey workflow governance before workflow use
- [x] AC-5: Architecture/runtime-manifest references document the policy
- [x] AC-6: Generated inventory and WO index reconcile

## Remaining Limitations

- This WO proves policy and detection only. It does not prove that VibeOS workflows outperform subagent dispatch.
- Live workflow execution, token comparison, and adoption verdict are deferred to WO-124.

## Test Strategy

- **Focused tests:** `python3 -m pytest tests/test_runtime_capabilities.py`
- **Index check:** `python3 plugins/vibeos/scripts/wo-frontmatter-lint.py validate-index --project-dir .`
- **Full suite:** `python3 -m pytest tests`
- **Gate proof:** `bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos`

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Findings: Workflow use must be gated by runtime availability and policy, not by capability enthusiasm. Recurring scripts must be reviewed and saved only after a successful bounded run.
- Test status: Complete.

### Closeout Audit
- Status: `complete`
- Findings: Policy/detection slice is complete. Live local detector shows Claude dynamic workflows available and Codex feature probing blocked by a local config parse error, so no Codex workflow capability was overclaimed.
- Test status: `216 passed`.
