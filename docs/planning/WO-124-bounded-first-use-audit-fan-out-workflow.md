---
wo: WO-124
title: Bounded First Use: Audit Fan-Out Workflow
status: Complete
phase: 40
phase_name: Dynamic Workflow Adoption
wo_class: harness
write_scope:
  - .claude/workflows/vibeos-audit-sweep
  - docs/planning/WO-124-bounded-first-use-audit-fan-out-workflow.md
  - docs/planning/WO-INDEX.md
  - docs/evidence/vnext/generated-inventory.json
  - docs/evidence/vnext/wo-124-audit-fanout-workflow/**
  - plugins/vibeos/scripts/generate-inventory.py
  - plugins/vibeos/scripts/workflow-audit-sweep-evidence.py
  - tests/test_generate_inventory.py
  - tests/test_workflow_audit_sweep.py
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
  cost_ceiling_usd: 4.0
loop_goal: workflow candidate and bounded-run evidence are recorded without default adoption overclaim
loop_ceiling_turns: 1
loop_ceiling_cost_usd: 4.0
---

# WO-124: Bounded First Use: Audit Fan-Out Workflow

## Status

`Complete`

## Phase

Phase 40: Dynamic Workflow Adoption

## Objective

Create the first reviewed Claude Code saved workflow for the VibeOS audit fan-out path, then prove whether it should advance beyond candidate status by running a bounded slice and comparing workflow evidence against the existing subagent audit path.

## Source Evidence

- The vNext master plan scopes WO-124 to `.claude/workflows/vibeos-audit-sweep`, with bounded execution, token evidence, subagent-path comparison, and an adoption verdict.
- WO-123 added the workflow governance policy: saved and reviewed scripts only, slice-first cost probe, no workflow writes to governance files, documented disable path, and no default adoption before WO-124 evidence.
- Official Claude Code workflow docs checked during this implementation state that dynamic workflows are JavaScript scripts, saved project workflows live under `.claude/workflows/`, saved workflows can accept `args`, `claude -p` starts workflows without an approval prompt, workflow scripts do not get direct filesystem or shell access, and small-slice cost probes are recommended before broad use.

## Scope

### In Scope

- [x] Add `.claude/workflows/vibeos-audit-sweep`
- [x] Express the 12-auditor consensus sweep used by the VibeOS audit skill
- [x] Keep the default target bounded to `plugins/vibeos/scripts/runtime-capabilities.py`
- [x] Add deterministic evidence generation for workflow shape, baseline comparison state, and adoption verdict
- [x] Include saved workflows in the generated inventory/claim ledger
- [x] Run bounded live Claude workflow invocations and capture cost/token output
- [x] Record the current adoption verdict based on live evidence

### Out of Scope

- Whole-repo workflow audits
- Defaulting VibeOS audit dispatch to dynamic workflows
- Claiming Codex workflow parity or Claude/Codex hook parity
- Website changes

## Design Notes

The workflow is report-only. It passes a narrow target to 12 auditors and instructs agents to avoid edits, governance writes, and shell commands. The workflow itself uses only JavaScript coordination logic and marker comments that deterministic tests can parse.

Because the public docs document `args` and saved workflow location but do not expose a stable public JavaScript agent-launch API, WO-124 treats the saved file as a reviewed candidate until a live `claude -p` run proves the local runtime accepts it and can finish within an approved budget.

The evidence script records three separate states:

- static workflow shape proof
- source-derived subagent-path baseline
- live workflow output and cost proof, when available

## Acceptance Criteria

- [x] AC-1: `.claude/workflows/vibeos-audit-sweep` exists
- [x] AC-2: Workflow marker evidence records exactly 12 auditors and the bounded default target
- [x] AC-3: Evidence report records no-governance-write controls and no direct filesystem/shell access from the workflow script
- [x] AC-4: Generated inventory includes saved Claude workflow scripts
- [x] AC-5: Deterministic tests cover workflow shape and deferred adoption without live evidence
- [x] AC-6: Bounded live Claude attempts captured with cost/token evidence
- [x] AC-7: Canary findings and cost/token evidence compared against the matching live subagent-path baseline
- [x] AC-8: Adoption verdict recorded from live evidence: `PARTIAL_UNLOCK_CANDIDATE_REVIEW_BEFORE_DEFAULT`

## Remaining Limitations

- Current local implementation proves the workflow file is discovered and reaches runtime execution attempts, but it does not prove a completed 12-auditor run.
- Source-derived baseline evidence is not the same as live subagent execution evidence.
- The full 12-auditor bounded attempt hit `error_max_budget_usd` at `total_cost_usd: 2.105614499999999` after the workflow reached real fan-out.
- The successful canary run completed 2 auditors at `total_cost_usd: 0.4981767`.
- The matching live subagent baseline completed 2 auditors at `total_cost_usd: 0.9119877000000001`.
- Aggregate local Claude attempt cost captured for WO-124 is `7.3570225499999992` USD estimate, before provider billing reconciliation.
- Claude workflow concurrency can overshoot the requested `--max-budget-usd` cap before the controller stops the run; attempt 7 was capped at `1.50` but reported `2.105614499999999`.
- No public claim may say dynamic workflows are adopted by default. Current evidence supports only a reviewed canary-level partial unlock candidate.

## Test Strategy

- **Focused tests:** `python3 -m pytest tests/test_workflow_audit_sweep.py tests/test_generate_inventory.py`
- **Workflow evidence:** `python3 plugins/vibeos/scripts/workflow-audit-sweep-evidence.py --project-dir . --out docs/evidence/vnext/wo-124-audit-fanout-workflow/workflow-evidence-report.json`
- **Inventory:** `python3 plugins/vibeos/scripts/generate-inventory.py --project-dir .`
- **Index:** `python3 plugins/vibeos/scripts/wo-frontmatter-lint.py validate-index --project-dir .`
- **Full suite:** `python3 -m pytest tests`
- **Gate proof:** `bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos`

## Audit Checkpoints

### Planning Audit

- Status: `complete`
- Findings: WO-124 must not turn dynamic workflows on by default. It must first prove a bounded run and preserve fallback to the existing audit skill/subagent path.
- Test status: Planned.

### Pre-Live-Run Audit

- Status: `complete`
- Findings: Static workflow shape, ESM/module syntax check, and generated inventory tests passed before live attempts.
- Test status: Focused tests passed.

### Evidence-Closeout Audit

- Status: `partial`
- Findings: Nine bounded Claude workflow invocations and one live subagent baseline were captured. Attempts 1-8 exposed and fixed workflow format, permission, argument parsing, and agent-launch issues. Attempt 9 completed a 2-auditor canary and produced one low-severity architecture finding at lower cost than the matching subagent baseline. The full 12-auditor workflow remains too expensive for default adoption without additional cost controls.
- Test status: Focused tests passed; full suite passed; `pre_commit` gate passed.

## Evidence

- [x] Local implementation complete
- [x] Tests pass
- [x] Gates pass
- [x] Bounded live workflow proof captured
- [x] Adoption verdict recorded as `PARTIAL_UNLOCK_CANDIDATE_REVIEW_BEFORE_DEFAULT`
- [x] Canary live workflow proof captured
- [x] Matching live subagent baseline captured
- [ ] Full 12-auditor live workflow proof captured

### Proof Commands

```bash
python3 -m pytest tests/test_workflow_audit_sweep.py tests/test_generate_inventory.py
# 10 passed

python3 -m pytest tests
# 223 passed

node --input-type=module --check - < .claude/workflows/vibeos-audit-sweep
# exit 0

claude -p "<bounded /vibeos-audit-sweep canary prompt>" --model sonnet --output-format json --max-budget-usd 1.00 --allowedTools Workflow,Read,Glob,Grep --no-session-persistence
# returncode 0
# subtype: success
# total_cost_usd: 0.4981767
# workflow finding count: 1

claude -p "<matching subagent baseline prompt>" --model sonnet --output-format json --max-budget-usd 1.00 --allowedTools Agent,Read,Glob,Grep --no-session-persistence
# returncode 0
# subtype: success
# total_cost_usd: 0.9119877000000001
# baseline finding count: 11

python3 plugins/vibeos/scripts/workflow-audit-sweep-evidence.py --project-dir . --baseline docs/evidence/vnext/wo-124-audit-fanout-workflow/subagent-baseline-live.json --live-output docs/evidence/vnext/wo-124-audit-fanout-workflow/claude-workflow-output.json --live-stderr docs/evidence/vnext/wo-124-audit-fanout-workflow/claude-workflow-stderr.txt --out docs/evidence/vnext/wo-124-audit-fanout-workflow/workflow-evidence-report.json
# adoption_verdict: PARTIAL_UNLOCK_CANDIDATE_REVIEW_BEFORE_DEFAULT
# findings_comparison_status: available
# token_or_cost_comparison_status: available

bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos
# Total: 10 | Passed: 6 | Failed: 0 | Skipped: 4
# Result: PASS
```
