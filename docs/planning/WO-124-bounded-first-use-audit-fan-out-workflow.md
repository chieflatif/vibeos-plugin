---
wo: WO-124
title: Bounded First Use: Audit Fan-Out Workflow
status: Awaiting Evidence
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

`Awaiting Evidence`

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
- [ ] AC-7: Findings and cost/token evidence compared against the subagent-path baseline
- [x] AC-8: Adoption verdict recorded from live evidence: `DEFER_LIVE_WORKFLOW_BUDGET_LIMIT`

## Remaining Limitations

- Current local implementation proves the workflow file is discovered and reaches runtime execution attempts, but it does not prove a completed 12-auditor run.
- Source-derived baseline evidence is not the same as live subagent execution evidence.
- The final bounded attempt hit `error_max_budget_usd` at `total_cost_usd: 2.105614499999999` after the workflow reached real 12-agent fan-out.
- Aggregate local Claude attempt cost captured for WO-124 is `3.7187443499999991` USD estimate, before provider billing reconciliation.
- Claude workflow concurrency can overshoot the requested `--max-budget-usd` cap before the controller stops the run; attempt 7 was capped at `1.50` but reported `2.105614499999999`.
- No public claim may say dynamic workflows are adopted by default until AC-6 through AC-8 are complete.

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
- Findings: Seven bounded Claude invocations were captured. Attempt 1 exposed the first-statement `meta` requirement. Attempt 2 exposed the need to allow the `Workflow` tool. Attempt 3 exposed that only `meta` is exported while the executable body is an async script. Attempt 4 reached the low budget ceiling. Attempt 5 reconfirmed the required `export const meta` shape. Attempt 6 launched all 12 auditors but exposed the `agent(prompt, opts)` signature. Attempt 7 used the corrected signature and reached real fan-out, then hit the budget ceiling before findings/baseline comparison proof completed. This is enough to defer default adoption, not enough to approve it.
- Test status: Focused tests passed; full suite passed; `pre_commit` gate passed.

## Evidence

- [x] Local implementation complete
- [x] Tests pass
- [x] Gates pass
- [x] Bounded live workflow proof captured
- [x] Adoption verdict recorded as `DEFER_LIVE_WORKFLOW_BUDGET_LIMIT`
- [ ] Completed live workflow proof captured

### Proof Commands

```bash
python3 -m pytest tests/test_workflow_audit_sweep.py tests/test_generate_inventory.py
# 9 passed

python3 -m pytest tests
# 222 passed

node --input-type=module --check - < .claude/workflows/vibeos-audit-sweep
# exit 0

claude -p "<bounded /vibeos-audit-sweep prompt>" --model sonnet --output-format json --max-budget-usd 1.50 --allowedTools Workflow,Read,Glob,Grep --no-session-persistence
# returncode 1
# subtype: error_max_budget_usd
# total_cost_usd: 2.105614499999999

python3 plugins/vibeos/scripts/workflow-audit-sweep-evidence.py --project-dir . --live-output docs/evidence/vnext/wo-124-audit-fanout-workflow/claude-workflow-output.json --live-stderr docs/evidence/vnext/wo-124-audit-fanout-workflow/claude-workflow-stderr.txt --out docs/evidence/vnext/wo-124-audit-fanout-workflow/workflow-evidence-report.json
# adoption_verdict: DEFER_LIVE_WORKFLOW_BUDGET_LIMIT

bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos
# Total: 10 | Passed: 6 | Failed: 0 | Skipped: 4
# Result: PASS
```
