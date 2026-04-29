---
name: vibeos-wo
description: Work Order management for VibeOS in Codex. Use when the user wants to create a WO, inspect WO status, mark a WO complete, audit a WO, or manage an individual unit of work inside the VibeOS plan.
---

# VibeOS Work Orders

Use this skill for Work Order creation, inspection, closeout, and audit.

## Workflow

1. Read:
   - `docs/planning/WO-INDEX.md`
   - `docs/planning/DEVELOPMENT-PLAN.md`
   - `.vibeos/reference/governance/WO-TEMPLATE.md.ref` when creating a new WO
2. Support four common flows:
   - create a new WO
   - show status of a WO
   - validate and close a WO
   - audit a WO before implementation or closeout
3. When closing a WO, run:

```bash
bash ".vibeos/scripts/gate-runner.sh" wo_exit --continue-on-failure
```

4. Keep status truthful. If evidence is partial, use a truthful partial state instead of `Complete`.

## Rules

- No WO without a concrete objective and acceptance criteria.
- For user-facing or Comp work, the WO must identify the primary user-flow step and objective fidelity risk it affects.
- For durable state, auth, data, jobs, webhooks, retries, or external side effects, the WO must identify the system invariants it affects.
- For dependency, runtime, package-manager, SDK, framework, lockfile, or high-impact package changes, the WO must identify current-source evidence, compatibility constraints, audit command, and upgrade-path expectations.
- For CI/CD, deployment, environment/secrets, observability, health/smoke, rollback, runbook, or operational script changes, the WO must identify delivery infrastructure evidence requirements.
- No WO closeout without evidence.
- Explain WO status in plain English first, then include identifiers.
