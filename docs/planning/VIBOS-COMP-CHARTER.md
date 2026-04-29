# VibOS Comp Charter

## Purpose

VibOS Comp is the enterprise MVP delivery harness for VibeOS.

Its job is to let a non-specialist move fast with AI agents while still producing software that a serious design partner, CTO, security reviewer, or senior engineer can inspect without dismissing it as a fragile prototype.

## Product Promise

Given a product idea or competition prompt, VibOS Comp produces a working enterprise MVP foundation:

- focused product scope
- coherent frontend, backend, data, and integration architecture
- proven primary user flow across UI, auth/session, backend, data, feedback, and evidence
- explicit system invariants for state, ownership, data integrity, idempotency, recovery, and auditability
- real authentication and authorization posture where needed
- secure configuration, dependency hygiene, and current-source dependency intelligence
- CI/CD, deployment, observability, smoke checks, rollback, and runbook evidence
- observable runtime behavior
- useful tests and real-path verification
- deployable environment shape
- adversarial audit evidence
- a compact scorecard showing what is proven, partial, or still risky

## Operating Principle

An MVP should be small in feature scope, not small in engineering standards.

VibOS Comp cuts product scope aggressively. It does not cut the foundation needed to keep building: architecture boundaries, security baseline, observability, tests, deployment posture, data integrity, dependency intelligence, and evidence.

It also does not let individual pieces pass while the human journey fails. The mission, Work Orders, implementation, tests, audits, and scorecard must keep the primary user flow and original objective visible.

It does not let happy-path functionality pass while the underlying system can enter invalid states. Invariants are part of the product contract, not optional engineering polish.

It does not let stale model memory choose the stack. Dependency decisions need current-source evidence, runtime/package-manager compatibility, lockfile discipline, security audit output, and an upgrade path.

It does not let delivery infrastructure stay invisible. CI/CD, deployment, environment/secrets, observability, smoke checks, rollback, and runbooks are part of the product foundation, not cleanup after the demo.

## Optimization Targets

| Target | Meaning |
|---|---|
| Functionality | Core workflows work through real user or system paths, not only through mocked units |
| Flow Integrity | The primary user can complete the promised workflow end to end across UI, auth/session, backend, data or side effects, and feedback |
| Objective Fidelity | The integrated product stays true to the original objective and does not drift into an easier but different product |
| System Invariants | State, ownership, side-effect, recovery, and auditability rules are explicit, enforced, and regression-tested |
| Architecture | Modules, contracts, data flow, and ownership boundaries are explicit and enforceable |
| Security | Auth, authorization, secrets, input validation, tenancy, PII, and OWASP risks are handled proportionally |
| Dependency Intelligence | Dependency versions, SDK choices, lockfiles, compatibility, audit output, and upgrade paths are backed by current evidence |
| Delivery Infrastructure | CI/CD, deployment, environment/secrets, observability, smoke checks, rollback, and runbooks are explicit and evidenced |
| Observability | Operators can see health, failures, requests, jobs, and important state transitions |
| Performance | The system has explicit latency, bundle, query, memory, or throughput budgets where relevant |
| Operability | The app can be configured, run, deployed, rolled back, and debugged |
| Evidence | Completion claims map to tests, gates, audits, logs, screenshots, or command output |
| Speed | Parallel agents are used where ownership is clear and integration risk is controlled |

## AI Failure Modes To Design Against

| Failure Mode | VibOS Comp Control |
|---|---|
| Stale package or API choices | Dependency intelligence evidence, live version validation, compatibility proof, lockfiles, and audit output before stack decisions |
| Demo-only happy paths | Real-path smoke tests and integration checks before completion |
| Mock-heavy tests | Test quality audits and real execution evidence |
| Weak backend behind polished UI | Contract validation, data model checks, and backend route verification |
| Disconnected user flow | Flow auditor, flow-integrity gate, critical-path E2E evidence, and scorecard dimension |
| Invalid hidden state | System invariant auditor, invariant gate, negative/retry tests, and scorecard dimension |
| Missing auth or authorization boundaries | Security baseline and auth-boundary gates |
| Secrets in code or docs | Secrets scans at tool, gate, and commit boundaries where available |
| Unobservable failures | Observability acceptance criteria for logs, health, errors, and correlation IDs |
| Architecture drift | Architecture rules, forbidden imports, file budgets, and module boundary checks |
| Dependency sprawl | Dependency justification, current-source evidence, compatibility checks, and freshness gates |
| Invisible delivery gaps | Delivery infrastructure auditor, delivery gate, CI/CD evidence, smoke/health proof, rollback/runbook evidence |
| Hidden production gaps | Dev-mode fallback checks and truthful partial states |
| Agent file conflicts | Worktree scopes, branch ownership, shared-path contracts, and integration captain review |
| False completion claims | Scorecard evidence requirements and evidence auditor checks |

## Competition Control Plane

VibOS Comp adds a thin high-performance layer over VibeOS:

1. **Mission Control** converts a prompt into a compact enterprise MVP brief.
2. **Foundation Architect** selects the smallest credible architecture and baseline controls.
3. **Swarm Planner** splits work into scoped branches, worktrees, roles, and merge order.
4. **Worktree Factory** prepares isolated execution territory for parallel agents.
5. **Quality Gauntlet** runs deterministic checks for tests, security, observability, architecture, dependency intelligence, dependencies, performance, and operability.
6. **Flow Auditor** validates the user journey and objective fidelity across integrated layers.
7. **System Invariant Auditor** validates state safety, ownership, idempotency, recovery, and change-safety guarantees.
8. **Dependency Intelligence Auditor** validates current-source evidence, lockfiles, compatibility, audit output, and upgrade paths.
9. **Delivery Infrastructure Auditor** validates CI/CD, deployment, observability, smoke checks, rollback, and runbook evidence.
10. **Red Team Arena** attacks the result before completion.
11. **Integration Captain** merges parallel work, resolves shared files, and proves coherence.
12. **Scorecard** records what was built, what passed, what failed, and what remains risky.

## Minimal Artifacts

VibOS Comp replaces broad paperwork with a compact evidence spine:

- `MISSION.md` — objective, non-goals, architecture sketch, threat model, acceptance criteria
- `COMP-PLAN.md` — swarm split, worktrees, file ownership, dependencies, merge order
- `FLOW-INTEGRITY.md` or equivalent evidence — primary user path, layer handoffs, and proof
- `SYSTEM-INVARIANTS.md` or equivalent evidence — rules that must never break and proof they are enforced
- `DEPENDENCY-INTELLIGENCE.md` or equivalent evidence — dependency versions, current sources, compatibility, audit output, and upgrade path
- `DELIVERY-INFRASTRUCTURE.md` or equivalent evidence — CI/CD, deployment, environment/secrets, observability, smoke checks, rollback, and runbook proof
- `SCORECARD.md` — tests, gates, audits, performance, security, observability, evidence

Full PRDs, design docs, and long-form governance remain available for high-risk systems, but they are not the default path for rapid enterprise MVP delivery.
