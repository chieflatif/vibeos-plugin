---
name: checkpoint
description: Phase boundary audit that runs all gates and all audit agents on the entire codebase, establishes quality baselines, and enforces ratcheting (finding count cannot increase between phases).
argument-hint: "[optional: phase number, e.g. '3']"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, AskUserQuestion
---

# /vibeos:checkpoint — Phase Boundary Audit (Layer 5)

Run all quality gates and all audit agents on the entire codebase at phase boundaries. Establish baselines and enforce quality ratcheting.

## Communication Contract

Follow the full USER-COMMUNICATION-CONTRACT.md (`${CLAUDE_PLUGIN_ROOT}/docs/USER-COMMUNICATION-CONTRACT.md`). Key rules:
- Lead with outcome, follow with mechanism
- Present decisions with consequences
- Introduce every concept on first use with plain English definition

**Skill-specific addenda:**
- Report progress as each gate suite and auditor completes
- Explain any ratchet violations clearly: what regressed, by how much, which files

## Prerequisites

Before starting, verify these exist:
- `project-definition.json`
- `docs/planning/DEVELOPMENT-PLAN.md`
- Source code in the project

If no source code exists, report "No source code to checkpoint" and stop.

## Checkpoint Flow

### Step 1: Determine Phase

If `$ARGUMENTS` specifies a phase number, use that. Otherwise:
1. Read `docs/planning/DEVELOPMENT-PLAN.md`
2. Find the most recently completed phase (all WOs Complete)
3. Use that phase number

### Step 2: Run All Quality Gates

Run the full gate suite on the entire codebase:
```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/gate-runner.sh" pre_commit --project-dir "${CLAUDE_PROJECT_DIR:-.}"
```

Collect results: pass/fail per gate, total pass count.

### Step 3: Run Full Audit Cycle

Dispatch all 5 audit agents following the same protocol as `skills/audit/SKILL.md`:

1. Dispatch all 5 agents (security, architecture, correctness, test, evidence)
2. Collect structured findings from each
3. Apply consensus logic (2+ agents = true positive, 1 = warning)
4. Generate composite findings list

### Step 4: Load Previous Baseline

Check for previous phase baseline:
```
.vibeos/baselines/phase-[N-1]-baseline.json
```

If no previous baseline exists (first checkpoint), skip ratchet comparison.

Baseline schema:
```json
{
  "phase": N,
  "date": "ISO-8601",
  "gates": {
    "total": N,
    "passed": N,
    "failed": N,
    "gate_results": [{"name": "gate-name", "status": "pass|fail"}]
  },
  "findings": {
    "critical": N,
    "high": N,
    "medium": N,
    "low": N,
    "info": N,
    "total": N,
    "true_positives": N,
    "warnings": N
  },
  "auditors": {
    "security": {"status": "complete|failed", "findings": N},
    "architecture": {"status": "complete|failed", "findings": N},
    "correctness": {"status": "complete|failed", "findings": N},
    "test": {"status": "complete|failed", "findings": N},
    "evidence": {"status": "complete|failed", "findings": N}
  }
}
```

### Step 5: Apply Ratchet

Compare current results against previous baseline:

**Ratchet rules:**
- Gate pass count must be >= previous (cannot have more gate failures)
- Critical finding count must be <= previous (cannot introduce critical issues)
- High finding count must be <= previous
- Total finding count must be <= previous (overall quality cannot decrease)

**Ratchet result:**
- **PASS:** All counts improved or stayed the same
- **FAIL:** Any count regressed

If ratchet fails, report which categories regressed:
> "Quality ratchet violation detected:
> - Critical findings: [prev] → [current] (+[delta])
> - [category]: [prev] → [current] (+[delta])
>
> These regressions must be fixed before proceeding to Phase [N+1]."

### Step 6: Store New Baseline

Save current results as the baseline for this phase:
```bash
mkdir -p .vibeos/baselines
```

Write to `.vibeos/baselines/phase-[N]-baseline.json` using the schema above.

### Step 7: Generate Phase Report

Write the report to stdout and save to `.vibeos/baselines/phase-[N]-report.md`:

```
## Phase [N] Checkpoint Report

**Date:** [today]
**Phase:** [N] — [phase name]
**WOs completed:** [list]

### Gate Results

| Gate | Status |
|---|---|
| [gate-name] | PASS/FAIL |

**Total:** [passed]/[total] gates passing

### Audit Findings

| Severity | Count | Consensus | Warnings |
|---|---|---|---|
| Critical | [N] | [N] true positives | [N] warnings |
| High | [N] | [N] true positives | [N] warnings |
| Medium | [N] | [N] true positives | [N] warnings |
| Low | [N] | [N] true positives | [N] warnings |

### Baseline Comparison

| Metric | Previous (Phase [N-1]) | Current (Phase [N]) | Delta | Status |
|---|---|---|---|---|
| Gates passing | [N] | [N] | [+/-N] | PASS/FAIL |
| Critical findings | [N] | [N] | [+/-N] | PASS/FAIL |
| High findings | [N] | [N] | [+/-N] | PASS/FAIL |
| Total findings | [N] | [N] | [+/-N] | PASS/FAIL |

### Ratchet Status: [PASS/FAIL]

### Overall Assessment

[1-3 sentence plain English assessment]

**Recommendation:** [proceed to Phase N+1 / fix regressions first]
```

## Error Handling

- If gate-runner fails: log error, continue with audit agents
- If an audit agent fails: log failure, continue with remaining agents
- If all agents fail: report failure, suggest checking project-definition.json
- If baseline file is corrupted: treat as first checkpoint (no ratchet comparison)
