---
name: comp
description: Create a compact VibOS Comp enterprise MVP mission brief. Use when the user wants a competition-grade build, rapid but production-quality MVP, enterprise design-partner prototype, battle harness run, or says VibOS Comp/VibeOS Comp.
argument-hint: "[MVP, competition, or enterprise design-partner brief]"
allowed-tools: Read, Write, Glob, Grep, Bash, AskUserQuestion
---

# /vibeos:comp — Enterprise MVP Mission

Create a compact mission brief for VibOS Comp: fast enough for competitions and MVP validation, but with enterprise-grade foundations from the start.

## Operating Principle

Cut product scope before cutting engineering foundations. A Comp MVP can be narrow, but it cannot be sloppy about security, observability, tests, delivery infrastructure, dependency intelligence, or evidence.

## Communication Contract

Follow `docs/USER-COMMUNICATION-CONTRACT.md` when present.

Skill-specific rules:
- Ask at most three essential questions before producing a first mission draft.
- If the user already gave enough context, write the draft immediately and mark assumptions clearly.
- Explain trade-offs in outcome language first.
- Do not generate a full PRD by default.
- Do not begin implementation in this skill.

## Required Inputs

Derive these from `$ARGUMENTS`, the conversation, or existing project docs:
- Mission name and one-sentence promise
- Primary user and buyer/sponsor
- Core workflow
- Primary flow handoffs: entry point, UI action, backend/API call, auth/session context, data or side effect, user feedback, and proof
- System invariants: state, ownership, data integrity, idempotency, recovery, and auditability rules that must never break
- Dependency intelligence: runtime, package manager, high-impact dependencies, current-source evidence, version/lockfile policy, compatibility rule, security audit expectation, and upgrade path
- Delivery infrastructure: CI/CD or local-proof automation, deployment target, environment/secrets model, observability, health/smoke checks, rollback, and runbook basics
- Must-ship scope and explicit non-goals
- Sensitive data, integrations, and compliance signals
- Threat model and likely abuse paths
- Observability needs and operational expectations
- Performance budget and scale assumption
- Acceptance criteria
- Objective fidelity boundaries: what the product must remain true to, and what drift would invalidate the build

If more than three high-impact fields are missing, ask only the three that would most affect architecture or security:
1. Who is the primary user and what outcome must they achieve?
2. What is the one core workflow that must be excellent?
3. Does this handle sensitive data, money, regulated data, company secrets, or third-party integrations?

Infer the rest, label assumptions, and invite correction after the draft exists.

## High-Risk Escalation

Recommend full VibeOS discovery/planning if the mission includes any of these:
- Health, financial, legal, children, safety-critical, or regulated data
- Enterprise multi-tenancy with strict data isolation
- Payments, production credentials, customer data migration, or destructive operations
- External network exposure without clear auth and rate-limiting requirements
- Ambiguous users, scope, or data sensitivity after the three-question pass

Do not block mission creation solely because risk is high. Create the mission draft, then state that full discovery/planning is recommended before implementation.

## Workflow

### Step 1: Load Context

Read any existing context that exists:
- `MISSION.md`
- `project-definition.json`
- `docs/product/PRODUCT-ANCHOR.md`
- `docs/product/PRD.md`
- `docs/ENGINEERING-PRINCIPLES.md`
- `docs/research/RESEARCH-REGISTRY.md`
- `.vibeos/runtime-capabilities.json`
- `.vibeos/reference/comp/ENTERPRISE-MVP-FOUNDATION.md.ref`
- `.vibeos/reference/comp/enterprise-mvp-foundation.json`
- `.vibeos/reference/comp/DEPENDENCY-INTELLIGENCE.md.ref`
- `.vibeos/reference/comp/DELIVERY-INFRASTRUCTURE.md.ref`
- `.vibeos/reference/comp/stack-dependency-currency.json`

Use existing context as source material. Do not overwrite user intent.

### Step 2: Apply Foundation Blueprint

Read `.vibeos/reference/comp/enterprise-mvp-foundation.json` when available. Use it to decide the minimum threshold:
- `local_proof` only when the user explicitly says private/local demo and no real sensitive data
- `design_partner_mvp` by default for VibOS Comp
- `production_ready` when real customers, regulated data, revenue, or operational dependency exists

Carry every applicable foundation requirement into `MISSION.md` as either required, not applicable with rationale, or deferred with user-approved risk. Use stack variants from `.vibeos/reference/comp/stack-*.json` and stack currency packs from `.vibeos/reference/comp/stack-dependency-currency.json` as guidance when the stack is known.

### Step 3: Draft Mission

Write `MISSION.md` at the project root using `.vibeos/reference/product/MISSION.md.ref` as the structure when available. If the template is missing, use the same section structure from this skill.

The mission must include:
- Mission promise
- Users and buyers
- Core workflow
- Flow integrity: user action, UI, backend/API, auth/session, data or side effect, user feedback, and evidence for the primary path
- Objective fidelity: original objective, success proof, and drift boundaries
- System invariants: state, ownership, data integrity, idempotency, recovery, and auditability rules
- Dependency intelligence: current-source evidence, runtime/package-manager compatibility, lockfile/install proof, security audit requirement, and upgrade path
- Delivery infrastructure: CI/CD or local-proof automation, deployment target, environment/secrets model, observability, health/smoke checks, rollback, and runbook basics
- Must-ship scope and explicit non-goals
- Enterprise foundation baseline
- Threat model
- Observability and operations
- Performance budgets
- Acceptance criteria
- Assumptions and open questions
- Downstream handoff to `COMP-PLAN.md`

### Step 4: Foundation Check

Before finishing, verify the draft does not omit:
- Identity and access where relevant
- Data validation and ownership checks
- Secret management and dependency freshness
- Current-source evidence for high-impact dependencies
- Stack currency pack coverage for detected Node/TypeScript, frontend, Python/FastAPI, AI SDK, auth/security, database/ORM, or deployment surfaces
- Runtime and package-manager compatibility for selected versions
- Lockfile-backed install proof or ecosystem-equivalent pinning
- Vulnerability audit output and upgrade-path ownership
- CI/CD or local-proof automation that runs tests, gates, dependency/security checks, and build
- Deployment target, artifact, environment/secrets model, health/smoke checks, observability signals, rollback, and runbook basics
- Unit/integration/contract/smoke or end-to-end testing strategy
- Structured logs, metrics, health checks, and error reporting
- Deployment shape, rollback notes, and runbook basics
- Accessibility/responsiveness/loading/error states for frontend work
- End-to-end primary-flow proof across UI, auth/session, backend/API, data or side effects, and user feedback
- System invariant proof for invalid states, duplicate side effects, authorization/ownership breaks, and recovery paths where relevant
- Evidence requirements for completion claims

If any foundation item is not applicable, say why inside `MISSION.md`. If it is applicable but deferred, mark it as a user decision with risk.

### Step 5: Report

Tell the user:
- `MISSION.md` was created or updated
- the product scope that was intentionally cut
- the foundation items that remain non-negotiable
- the primary user flow that must be proven before the build can be claimed complete
- the system invariants that must never be broken
- the dependency intelligence decisions that need current evidence before implementation
- the delivery infrastructure that must be evidenced before external review
- whether full discovery/planning is recommended before build
- the next step: run `python3 .vibeos/scripts/comp-plan.py --project-dir .` to create `COMP-PLAN.md` and `.vibeos/worktree-scopes.json`

## Completion Criteria

- `MISSION.md` exists.
- No `{{PLACEHOLDER}}` values remain.
- The mission separates product scope cuts from foundation cuts.
- High-risk missions include a full discovery/planning recommendation.
- No implementation work was started.
