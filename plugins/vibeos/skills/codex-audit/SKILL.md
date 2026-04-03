---
name: codex-audit
description: >
  Complementary Audit Protocol — dispatches an independent audit via Codex (GPT-series) as auditor.
  Claude implements, Codex audits. Use at plan approval, WO closure, session end, or on demand.
  Claude must reconcile ALL material findings before closure — zero-technical-debt policy enforced
  (fix now or create a tracked WO, nothing dropped).
  Triggers: "codex audit", "audit with codex", "independent audit", "dual audit",
  "complementary audit", "/vibeos:codex-audit plan|complete|session|manual".
argument-hint: "[plan|complete|session|manual] [--both] [--wo <path>] [--wait|--background] [--explicit]"
user-invocable: true
allowed-tools: Read, Write, Glob, Grep, Bash, Agent, AskUserQuestion
---

# /vibeos:codex-audit — Complementary Audit Protocol

Dispatches an independent audit to Codex. Claude implements; Codex audits. All four audit types
are supported. Reconciliation is mandatory — zero technical debt policy applies.

## Step 1: Resolve Arguments

From `$ARGUMENTS`:
- `plan` → `plan_audit`
- `complete` or `completion` → `completion_audit`
- `session` → `session_audit`
- `manual` or empty → `manual_audit`
- `--both` → dual-audit mode (Claude and Codex both audit, then reconcile)
- `--wo <path>` → pass specified WO file to the broker
- `--wait` → run synchronously (foreground, wait for result)
- `--background` → run asynchronously (print status, exit immediately)
- `--explicit` → bypass significance check, run regardless of thresholds

## Step 2: Gather Context

Run these in parallel before calling the broker:

```bash
# Git state
git diff --shortstat HEAD~1 HEAD 2>/dev/null || git diff --shortstat
git log --oneline -5

# Find most recent WO if none specified
ls docs/planning/ 2>/dev/null | grep -E '^WO-' | sort | tail -3

# Check for existing evidence bundles
ls docs/evidence/ 2>/dev/null | sort | tail -5

# For session audits: recent build log
tail -80 .vibeos/build-log.md 2>/dev/null || true
```

If no `--wo` was passed and you can identify the most relevant WO from context, add `--wo <path>`.

## Step 3: Run Broker

Call the audit broker. For `--both` (dual-audit), auditor=both; otherwise auditor=codex (default).

```bash
bash plugins/vibeos/scripts/codex-audit-broker.sh \
  --type <audit_type> \
  --auditor <codex|both> \
  --executor claude \
  [--wo <wo_file>] \
  [--context "<brief context>"] \
  [--wait|--background] \
  [--explicit]
```

**If broker exits with code 2 (not significant):**
Tell the user in one sentence that the change did not meet the significance threshold, and offer
to run with `--explicit` to bypass it. Do not auto-run.

**If broker exits with code 1 (Codex plugin not found or invocation error):**
Report the failure and offer the built-in VibeOS audit agents as fallback: `/vibeos:audit`

## Step 4: Present Findings

When the broker returns output (foreground) or the result file exists (background):

1. State the verdict upfront — one line.
2. Present all findings ordered by severity: critical → high → medium → low → info.
3. For each finding: state what it is, where (file:line), and what must be done.
4. Show a pillar assessment summary table if the broker provides one.
5. If dual-audit: highlight consensus findings (both agree) vs single-auditor findings.

Do not paraphrase away severity. If Codex says blocked, say blocked.

## Step 5: Reconciliation — Zero Technical Debt

**This step is mandatory before any closure. Nothing is dropped.**

For each finding:

### critical or high
Fix before closure. No exceptions. No operator override except with explicit written justification.
Do not mark the WO, plan, or session closed until fixed.

### medium
Fix now if the fix is bounded and clear.
If it naturally belongs in a forward WO (additive enhancement, not a defect in current work):
- Create or update that WO to include it
- Record the linkage in the audit evidence file: "Finding M-N deferred to WO-XXX"
- Must close within 1-2 work sessions — not indefinitely

### low
Fix now if trivial (estimated under 30 minutes).
Otherwise create a WO entry with explicit linkage to the audit evidence file.

### info
Acknowledge in the evidence bundle.
Fix now if trivial. WO is optional but preferred if recurring.

### Rebuttal
If you disagree with a finding:
- State the rebuttal explicitly: "Finding #N: disagree — [evidence at file:line showing it is not an issue]"
- Do NOT silently ignore it
- If the evidence is ambiguous, escalate to the operator

### Operator override
If the operator explicitly says "override [finding #N]" or "proceed anyway":
- Log the override in the audit evidence file: `OVERRIDE: Finding #N — reason: [operator reason]`
- Note which specific findings were overridden
- Proceed, but do not pretend the findings do not exist

## Step 6: Record Evidence

After reconciliation, write an evidence note to the relevant evidence bundle:

```bash
mkdir -p docs/evidence/<WO_NUMBER>/
```

Record in `docs/evidence/<WO_NUMBER>/codex-audit.md`:

```
## Codex Complementary Audit

**Date:** [today]
**Audit type:** [type]
**Verdict:** [verdict]
**Auditors:** [codex|both]
**Result file:** .vibeos/audit/results/[filename]

### Findings Summary
| Severity | Count |
|---|---|
| Critical | N |
| High | N |
| Medium | N |
| Low | N |
| Info | N |

### Reconciliation Actions
[what was fixed, what WOs were created, any overrides logged]
```

## Auto-Trigger Guidance

Proactively invoke this skill (without being asked) when:

1. **plan_audit**: You just approved or finalized a plan or WO tranche for execution AND the significance check would pass
2. **completion_audit**: You are about to declare a WO complete AND the significance check would pass
3. **session_audit**: A session closeout is about to close AND 3 or more WOs were closed this session

For auto-triggers: always ask the operator to confirm before running dual-audit (`--both`). Single-auditor runs can proceed without asking.

## Error Handling

- Broker exit 2 (not significant): surface to user in one sentence, offer `--explicit`
- Broker exit 1 (invocation error): surface error, offer `/vibeos:audit` fallback
- Empty Codex output: report "audit incomplete", surface what was returned, do not fabricate verdict
- Codex plugin not installed: report it clearly, fall back to `/vibeos:audit`

## Quick Reference

```bash
# Manual audit on demand (Codex audits Claude's work)
bash plugins/vibeos/scripts/codex-audit-broker.sh --type manual_audit --executor claude

# Before executing a WO tranche
bash plugins/vibeos/scripts/codex-audit-broker.sh --type plan_audit --executor claude --wo docs/planning/WO-XXX.md

# After a WO closes
bash plugins/vibeos/scripts/codex-audit-broker.sh --type completion_audit --executor claude --wo docs/planning/WO-XXX.md

# Session end
bash plugins/vibeos/scripts/codex-audit-broker.sh --type session_audit --executor claude

# Dual-audit (both models audit, then reconcile)
bash plugins/vibeos/scripts/codex-audit-broker.sh --type completion_audit --auditor both --executor claude --explicit

# Force-run even if below significance threshold
bash plugins/vibeos/scripts/codex-audit-broker.sh --type manual_audit --executor claude --explicit
```
