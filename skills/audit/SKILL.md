---
name: audit
description: Full audit cycle that dispatches all 5 audit agents (security, architecture, correctness, test quality, evidence), applies consensus logic, and produces a composite report with actionable findings. Use when the user says "audit the code", "review everything", "check for security issues", "do a full review", or wants a comprehensive multi-perspective code review.
argument-hint: "[optional: 'security', 'architecture', 'correctness', 'test', 'evidence' to run a single auditor]"
allowed-tools: Read, Write, Glob, Grep, Bash, Agent, AskUserQuestion
---

# /vibeos:audit — Full Audit Cycle

Dispatch all 5 audit agents, merge findings with consensus logic, and produce a composite report.

## Communication Contract

Follow the full USER-COMMUNICATION-CONTRACT.md (`docs/USER-COMMUNICATION-CONTRACT.md`). Key rules:
- Lead with outcome, follow with mechanism
- Present decisions with consequences
- Introduce every concept on first use with plain English definition

**Skill-specific addenda:**
- Report which auditors are being dispatched
- After each auditor completes, summarize its top findings

## Prerequisites

Before starting, verify these exist:
- `project-definition.json`
- Source code to audit (at least one source directory with files)

If no source code exists, report "No source code to audit" and stop.

## Audit Flow

### Step 1: Determine Scope

If `$ARGUMENTS` specifies a single auditor name (`security`, `architecture`, `correctness`, `test`, `evidence`), run only that auditor. Otherwise, run all 5.

Read `project-definition.json` for:
- Source directories
- Test directories
- Stack/framework info
- Compliance targets

### Step 2: Dispatch Audit Agents

Dispatch the selected audit agents. Each runs in an isolated worktree and cannot modify files.

**Agent dispatch list:**

| Agent | File | Model | Purpose |
|---|---|---|---|
| Security | `agents/security-auditor.md` | sonnet | OWASP Top 10, secrets, injection, PII |
| Architecture | `agents/architecture-auditor.md` | sonnet | Layer violations, circular deps, boundaries |
| Correctness | `agents/correctness-auditor.md` | opus | Logic errors, missing error paths, user impact |
| Test Quality | `agents/test-auditor.md` | sonnet | Spec-first, assertion quality, mock density |
| Evidence | `agents/evidence-auditor.md` | sonnet | Documentation completeness, tracking accuracy |

Dispatch agents that can run independently in parallel where possible. Pass each agent:
- The `project-definition.json` path
- Source directory paths
- The current WO file path (if running within a build cycle)

### Step 3: Collect Findings

As each agent completes, extract its structured findings. Normalize each finding to this format:

```
{
  "id": "[agent]-[N]",
  "agent": "[agent name]",
  "category": "[finding category]",
  "severity": "[critical|high|medium|low|info]",
  "file": "[file path]",
  "line": "[line number or range]",
  "description": "[what was found]",
  "recommendation": "[how to fix]",
  "confidence": "[high|medium|low]"
}
```

If an agent fails to complete or returns unparseable output:
1. Log the failure
2. Continue with remaining agents
3. Note the missing auditor in the report

### Step 4: Apply Consensus Logic

Group findings by location (file + line range overlap) and category similarity:

**True Positive (high confidence):** 2 or more agents flag the same location or same issue pattern.
- Merge the descriptions from all flagging agents
- Use the highest severity among them
- List all agents that flagged it

**Warning (review recommended):** Exactly 1 agent flags an issue.
- Keep the finding as-is
- Mark as "single-auditor finding"
- Include the agent's confidence rating

**Clean:** Location checked by multiple agents with no findings.
- Not reported individually
- Contributes to the overall confidence score

### Step 5: Generate Composite Report

Write the report to stdout (displayed to user). Format:

```
## Composite Audit Report

**Date:** [today]
**Scope:** [directories audited]
**Auditors dispatched:** [list of 5 or subset]
**Auditors completed:** [count]/[dispatched]

### Executive Summary

- **True positives (2+ auditors agree):** [count]
- **Warnings (single auditor):** [count]
- **Critical findings:** [count]
- **High findings:** [count]
- **Medium findings:** [count]
- **Low/Info findings:** [count]

### Critical & High Findings (Action Required)

| # | Finding | Severity | Consensus | Agents | File | Recommendation |
|---|---|---|---|---|---|---|
| 1 | [description] | [severity] | [true_positive/warning] | [agent list] | [path:line] | [fix] |

### Medium & Low Findings (Review Recommended)

| # | Finding | Severity | Agent | File | Recommendation |
|---|---|---|---|---|---|
| 1 | [description] | [severity] | [agent] | [path:line] | [fix] |

### Auditor Summary

| Auditor | Status | Findings | Top Issue |
|---|---|---|---|
| Security | [complete/failed] | [count] | [top finding or "clean"] |
| Architecture | [complete/failed] | [count] | [top finding or "clean"] |
| Correctness | [complete/failed] | [count] | [top finding or "clean"] |
| Test Quality | [complete/failed] | [count] | [top finding or "clean"] |
| Evidence | [complete/failed] | [count] | [top finding or "clean"] |

### Overall Assessment

[1-3 sentence plain English assessment of project health]

**Recommendation:** [pass/conditional pass/fail]
- pass: No critical or high findings
- conditional pass: High findings exist but are addressable
- fail: Critical findings that must be fixed before proceeding
```

### Step 6: Save Report (if in build cycle)

If this audit was triggered from `/vibeos:build`, save the report to `.vibeos/audit-reports/[WO-NNN]-[timestamp].md` for the build log to reference.

Create the directory if it doesn't exist:
```bash
mkdir -p .vibeos/audit-reports
```

## Single-Auditor Mode

When `$ARGUMENTS` specifies a single auditor:
- Skip consensus logic (only 1 agent)
- Use that agent's native report format
- Still save the report if in build cycle

## Error Handling

- If an agent exceeds its turn limit: log timeout, continue with others
- If an agent returns no findings: record "clean" for that auditor
- If all agents fail: report the failure and suggest checking `project-definition.json`
- Never fabricate findings — only report what agents actually found
