---
name: vibeos-comp
description: Compact enterprise MVP mission intake for VibOS Comp. Use for competition-grade builds, enterprise design-partner MVPs, rapid production-quality prototypes, battle harness runs, or explicit VibOS Comp/VibeOS Comp requests.
---

# VibeOS Comp

Create `MISSION.md`: a compact mission brief for a narrow but enterprise-grade MVP.

## Principle

Cut product scope before cutting foundations. A Comp MVP can be small, but it must preserve the baseline for security, observability, testing, delivery infrastructure, dependency intelligence, and evidence.

## Workflow

1. Read existing context when present:
   - `MISSION.md`
   - `project-definition.json`
   - `docs/product/PRODUCT-ANCHOR.md`
   - `docs/product/PRD.md`
   - `docs/ENGINEERING-PRINCIPLES.md`
   - `docs/research/RESEARCH-REGISTRY.md`
   - `.vibeos/runtime-capabilities.json`
   - `.vibeos/reference/comp/ENTERPRISE-MVP-FOUNDATION.md.ref`
   - `.vibeos/reference/comp/enterprise-mvp-foundation.json`
   - `.vibeos/reference/comp/stack-dependency-currency.json`
2. Extract or infer:
   - mission name and promise
   - primary user and buyer/sponsor
   - one core workflow
   - primary flow handoffs: entry point, UI action, backend/API call, auth/session context, data or side effect, user feedback, and proof
   - system invariants: state, ownership, data integrity, idempotency, recovery, and auditability rules that must never break
   - dependency intelligence: runtime, package manager, high-impact dependencies, current-source evidence, version/lockfile policy, compatibility rule, security audit expectation, and upgrade path
   - delivery infrastructure: CI/CD or local-proof automation, deployment target, environment/secrets model, observability, health/smoke checks, rollback, and runbook basics
   - must-ship scope and explicit non-goals
   - sensitive data, integrations, and compliance signals
   - threat model and likely abuse paths
   - observability and operations requirements
   - performance budgets
   - acceptance criteria
   - objective fidelity boundaries: what the product must remain true to, and what drift would invalidate the build
3. Ask at most three essential questions before writing a first draft. If enough context exists, write immediately and label assumptions.
4. Apply `.vibeos/reference/comp/enterprise-mvp-foundation.json` when available:
   - default to `design_partner_mvp` for VibOS Comp
   - use `local_proof` only for private local demos with no real sensitive data
   - use `production_ready` when real customers, regulated data, revenue, or operational dependency exists
   - mark every applicable foundation item as required, not applicable with rationale, or deferred with user-approved risk
5. Use stack variants from `.vibeos/reference/comp/stack-*.json` and stack currency packs from `.vibeos/reference/comp/stack-dependency-currency.json` when the stack is known.
6. Write `MISSION.md` using `.vibeos/reference/product/MISSION.md.ref` when available.
7. Verify the mission includes:
   - users and buyers
   - core workflow
   - flow integrity: user action, UI, backend/API, auth/session, data or side effect, user feedback, and evidence for the primary path
   - objective fidelity: original objective, success proof, and drift boundaries
   - system invariants: state, ownership, data integrity, idempotency, recovery, and auditability rules
   - dependency intelligence: current-source evidence, runtime/package-manager compatibility, lockfile/install proof, security audit requirement, and upgrade path
   - delivery infrastructure: CI/CD or local-proof automation, deployment target, environment/secrets model, observability, health/smoke checks, rollback, and runbook basics
   - must-ship scope and non-goals
   - enterprise foundation baseline
   - threat model
   - observability and operations
   - performance budgets
   - acceptance criteria
   - assumptions and downstream handoff to `COMP-PLAN.md`
8. Recommend full VibeOS discovery/planning before implementation when the mission involves regulated data, payments, production credentials, destructive operations, enterprise multi-tenancy, or unclear data sensitivity.

## Rules

- Do not generate a full PRD unless the user asks or risk requires escalation.
- Do not start implementation in this skill.
- Do not leave `{{PLACEHOLDER}}` values in `MISSION.md`.
- If a foundation item is not applicable, state why.
- If a foundation item is deferred, mark it as a user-approved risk with a consequence.
- Preserve shared `.vibeos/` state so Claude/Cursor and Codex can continue from the same mission.
- Next step after mission creation is `python3 .vibeos/scripts/comp-plan.py --project-dir .` to generate `COMP-PLAN.md` and `.vibeos/worktree-scopes.json`.
