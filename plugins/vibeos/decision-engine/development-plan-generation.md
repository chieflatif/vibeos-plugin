# Development Plan Generation

## Purpose

Generate `docs/planning/DEVELOPMENT-PLAN.md` from the PRD, Product Anchor, Engineering Principles, architecture, and project definition. The plan defines phases and ordered Work Orders. **The agent never asks the user "what do you want to build?"** — it uses this plan to determine the next WO.

## Input

- `docs/product/PRD.md`
- `docs/product/PRODUCT-ANCHOR.md`
- `docs/ENGINEERING-PRINCIPLES.md`
- `docs/research/RESEARCH-REGISTRY.md`
- `project-definition.json` (scope.core_workflows, scope.v1_features, governance_profile.deployment_context)
- `docs/ARCHITECTURE.md` or `docs/product/ARCHITECTURE-OUTLINE.md`
- Existing WO-INDEX (if midstream)

## Phase Structure

### Phase 1: Foundation (Always First)

Scaffold and infrastructure. Work Orders in dependency order:

1. Initial scaffold (monorepo, apps, packages) — WO-001
2. Shared packages (types, utils) — depends on scaffold
3. Database schema and migrations — depends on scaffold
4. Auth infrastructure (OAuth, JWT, session) — if required by product
5. Environment and config baseline — depends on scaffold

Adapt to project: IF single app → simpler Phase 1. IF monorepo → full scaffold first.

### Phase 2..N: Core Workflows

One phase per core workflow from `scope.core_workflows`. Order by:

- Dependencies between workflows (e.g. auth before event creation)
- Critical path for v1 (what unlocks the most value first)

Each phase contains WOs that implement that workflow end-to-end (API, UI, integrations).

### Phase N+1..: V1 Features

Remaining `scope.v1_features` not covered by core workflows. Group by domain or dependency.

### Production Readiness Phases (Conditional on deployment_context)

**IF** `deployment_context IN ["production", "customer-facing", "scale"]` (from governance_profile in project-definition.json):

ADD Phase: Production Readiness (lightweight)
- WO: Security headers (CSP, HSTS, X-Frame-Options)
- WO: Health probes (liveness, readiness)
- WO: Structured logging (request IDs, log levels)
- WO: Input validation (centralized, size limits)

**IF** `deployment_context IN ["customer-facing", "scale"]`:

ADD Phase: Observability & Operations
- WO: Structured logging (request IDs, correlation IDs, log levels)
- WO: Metrics (APM, Prometheus/DataDog, or SLOs)
- WO: Health probes (DB/Redis readiness beyond /health)
- WO: Alerting and runbooks (PagerDuty/Opsgenie or equivalent)

ADD Phase: Resilience & Scale
- WO: Rate limiting (per-user/org, abuse protection)
- WO: Circuit breakers and retries for external calls (Claude, LinkedIn, etc.)
- WO: Caching (CDN, HTTP cache headers, Redis beyond tokens)
- WO: Horizontal scaling (e.g. Socket.io Redis adapter if applicable)

ADD Phase: Security Hardening (beyond production baseline)
- WO: Secrets management (Vault/AWS Secrets Manager vs env vars)
- WO: Audit trail (immutable log of sensitive actions)

Each WO gets a number, dependencies, and status like other WOs. They appear in the plan table and "Next Work Order" flows to them. Prototype projects get no extra phases.

## Work Order Sequencing

- Each WO has explicit Dependencies (other WO numbers).
- Order WOs so dependencies complete before dependents.
- Typical size: one WO = one feature area or one integration (e.g. "LinkedIn OAuth", "Event creation API", "Matchmaking algorithm").

## Output Format

See `reference/governance/DEVELOPMENT-PLAN.md.ref`.

- Phases with ordered WO tables
- Each WO: number, title, dependencies, status
- **Next Work Order** section — the single "what to build next" pointer

## Rules

1. **Align with architecture** — WOs must respect module boundaries from ARCHITECTURE.md
2. **Infer from PRD and Product Anchor** — core_workflows and v1_features map directly to phases and WOs, but the Product Anchor decides what experience and non-negotiables must be preserved
3. **Explicit dependencies** — no implicit ordering; every WO lists what it depends on
4. **Trace every WO back to the anchors** — each WO must explain which product promise, experience principle, and engineering principle it serves
5. **Require freshness where it matters** — if a WO depends on high-impact external behavior, note the required current evidence from `docs/research/RESEARCH-REGISTRY.md`
6. **Update after completion** — when a WO completes: (1) mark Status Complete in plan table, (2) move to WO-INDEX Completed, (3) set Next to next pending WO
7. **Never ask the user** — "What WO do you want to build?" is wrong. Use the plan.
8. **Alignment enforced** — `validate-development-plan-alignment.sh` runs at wo_exit and full_audit. It fails if DEVELOPMENT-PLAN, WO-INDEX, or WO files drift.
