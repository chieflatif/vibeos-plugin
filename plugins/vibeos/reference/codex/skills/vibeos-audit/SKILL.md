---
name: vibeos-audit
description: VibeOS audit flow for Codex. Use when the user asks for a code audit, quality review, governance review, architecture review, security review, or wants a full audit cycle before or after implementation work.
---

# VibeOS Audit

Use this skill for focused or full audits of the current project state.

## Workflow

1. Read `docs/USER-COMMUNICATION-CONTRACT.md`, `project-definition.json`, and the relevant planning or anchor docs.
2. Decide whether the request is:
   - focused audit of one change area
   - WO-level audit
   - full project audit
3. Refresh runtime capabilities:

```bash
bash ".vibeos/scripts/detect-runtime-capabilities.sh" --project-dir "."
```

4. Run the matching shared gates with `.vibeos/scripts/gate-runner.sh`.
5. Use available Codex-native agents or `.codex/agent-contracts/*auditor*.md` role contracts according to `.vibeos/runtime-capabilities.json`, then execute the audit phases with severity discipline. Include Flow Auditor review when the change touches user journeys, frontend/backend handoffs, auth/session continuity, data side effects, or objective fidelity. Include System Invariant Auditor review when the change touches state transitions, ownership, data integrity, retries, duplicate side effects, background jobs, webhooks, or recovery. Include Dependency Intelligence Auditor review when the change touches manifests, lockfiles, package managers, runtimes, SDKs, frameworks, auth/security/database/payment/AI packages, deployment libraries, or public-interface packages. Include Delivery Infrastructure Auditor review when the change touches CI/CD, deployment, environment/secrets, observability, smoke/health checks, rollback, runbooks, or operational scripts.
6. Report findings in severity order, with business impact first and concrete fixes second.
7. If there are no findings, say that plainly and note residual risk or verification gaps.

## Rules

- Findings come first; summaries come second.
- Do not overstate confidence when the evidence is incomplete.
- Keep accepted risks, deferred work, and blockers explicit.
