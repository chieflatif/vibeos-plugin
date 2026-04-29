# VibeOS Plugin — Codex Surface (Experimental)

This file provides Codex with structured instructions for working in this repository. It coexists with `CLAUDE.md` and `.claude/`, which provide the full enforcement surface for Claude Code and Cursor.

## What Codex Gets

- Structured build instructions via `.agents/skills/`, `.codex/agents/`, and legacy role contracts when installed
- Shared quality gate scripts in `.vibeos/scripts/`
- Decision engine and reference materials in `.vibeos/`
- Shared project state: plans, checkpoints, baselines, and logs in `.vibeos/`
- Long-run autonomy state: heartbeat, checkpoint, audit cadence, and closeout validation scripts in `.vibeos/`
- Commit-boundary Git hooks via `.vibeos/scripts/setup-git-hooks.sh` when the repo can install them
- Runtime capability detection via `.vibeos/scripts/detect-runtime-capabilities.sh` when installed

## What Codex Does Not Get

- **No Claude hook parity.** Codex hook support is runtime/version dependent and must be detected locally. Do not assume prompt/edit/stop enforcement behaves like Claude Code hooks.
- **No automatic write-time enforcement guarantee.** Quality gates and architecture rules still run explicitly; Git hooks only block at commit time after they are installed.
- **No unconditional subagent claim.** Current Codex versions can support multi-agent execution, but installed project surfaces may still be legacy role-contract mode. Read `.vibeos/runtime-capabilities.json` before choosing parallel Codex orchestration.

## Core Rules

1. No remediation without a Work Order.
2. No Work Order without an evidence-backed finding.
3. No finding without investigation.

## What To Read First

1. `README.md`
2. `CLAUDE.md` (the full enforcement surface — Codex should understand what it cannot enforce)
3. `plugins/vibeos/reference/codex/AGENTS.md.ref` (template for target projects)
4. `docs/planning/DEVELOPMENT-PLAN.md`

## Current Architecture

- `plugins/vibeos/skills/`, `plugins/vibeos/agents/`, and `plugins/vibeos/hooks/` are the Claude/Cursor source assets (full enforcement).
- `plugins/vibeos/reference/codex/skills/` and `plugins/vibeos/reference/codex/AGENTS.md.ref` are the Codex source assets (instruction-only).
- `vibeos-init.sh` installs the Claude/Cursor surface.
- `vibeos-init-codex.sh` installs the Codex surface.
- Both bootstraps share the `.vibeos/` runtime: scripts, decision engine, references, and convergence logic.

## Working Rule

When editing Codex support, prefer additive changes. Do not break the Claude/Cursor surface. Do not pretend Codex has capabilities it does not have.

Codex's truthful enforcement stack is: `AGENTS.md` + skills for behavior, `.vibeos/scripts/gate-runner.sh` for explicit checks, and Git `pre-commit` / `commit-msg` hooks for commit-boundary blocking.

When planning or auditing VibOS Comp work, treat flow integrity as a first-class requirement: the primary user must be able to move through UI, auth/session, backend/API, data or side effects, and feedback while staying true to the mission objective.

Treat system invariants as first-class too: state, ownership, data integrity, idempotency, recovery, and auditability rules must be explicit, enforced at durable boundaries, and evidenced before completion.

Treat dependency intelligence as first-class: package, framework, SDK, runtime, and transitive dependency decisions need current-source evidence, version/lockfile discipline, compatibility proof, security audit output, and upgrade-path notes before completion.

Treat delivery infrastructure as first-class: CI/CD, deployment, environment/secrets, observability, health/smoke checks, rollback, and runbook evidence must be explicit before external-review or Comp completion claims.

Treat 24-48 hour autonomy as a resumable control-plane problem: record `.vibeos/autonomy/heartbeats/*.json`, keep checkpoints fresh, respect `.vibeos/autonomy/run-lease.json`, use `autonomy-loop.py` for scheduler-safe ticks, classify supervisor resume plans with `autonomy-runner.py`, plan Codex/Claude handoffs with `autonomy-runtime-adapter.py`, detect repeated loop/runtime/provider failures with `autonomy-failure-detector.py`, plan safe responses with `autonomy-recovery-planner.py`, record evidence-backed recovery resolution with `autonomy-recovery-resolution.py`, block recovery loops without matching resolution evidence with `autonomy-scheduler-guard.py`, generate reviewed scheduler profiles with `autonomy-scheduler-profile.py`, smoke-test the chain with `autonomy-smoke.py`, validate cadence with `validate-long-run-autonomy.py`, and never imply that a single Codex context can run forever without durable resume state.

For runtime-specific orchestration claims, first run:

```bash
bash ".vibeos/scripts/detect-runtime-capabilities.sh" --project-dir "."
```

Then read `.vibeos/runtime-capabilities.json`.
