# VibeOS File Inventory

All files the plugin creates in your project, organized by when they appear.

## Discovery Phase (`/vibeos:discover`)

| File | Purpose |
|---|---|
| `.vibeos/config.json` | Plugin configuration and onboarding state |
| `project-definition.json` | Machine-readable project definition with confidence levels |
| `docs/product/PROJECT-IDEA.md` | Raw user intent capture (greenfield only) |
| `docs/product/PRODUCT-BRIEF.md` | One-page product summary (greenfield only) |
| `docs/product/PRD.md` | Requirements, user stories, acceptance criteria |
| `docs/product/PRODUCT-ANCHOR.md` | Core promise, experience principles, and anti-goals |
| `docs/TECHNICAL-SPEC.md` | Stack, modules, security posture |
| `docs/ENGINEERING-PRINCIPLES.md` | Build standards, anti-shortcut rules, freshness policy |
| `docs/research/RESEARCH-REGISTRY.md` | Current evidence for high-impact technical decisions |
| `docs/decisions/DEVIATIONS.md` | Explicit compromise log with review dates |
| `docs/product/ARCHITECTURE-OUTLINE.md` | System components, data flow, module map |
| `docs/product/ASSUMPTIONS-AND-RISKS.md` | Open questions and risks (greenfield only) |

## Planning Phase (`/vibeos:plan`)

| File | Purpose |
|---|---|
| `docs/planning/DEVELOPMENT-PLAN.md` | Phased work orders with dependencies |
| `docs/planning/WO-INDEX.md` | Work order tracking index |
| `docs/planning/WO-NNN-*.md` | Individual work order specifications |
| `scripts/quality-gate-manifest.json` | Gate configuration (which checks run, blocking vs advisory) |
| `.claude/hook-manifest.json` | Hook configuration for real-time enforcement |
| `scripts/architecture-rules.json` | Architecture enforcement rules |
| `scripts/*.sh` | Quality gate scripts (copied from plugin) |
| `CLAUDE.md` | Agent instructions for your project |
| `.vibeos/config.json` | Updated with autonomy preference |

### Midstream-Specific (existing codebases)

| File | Purpose |
|---|---|
| `.vibeos/findings-registry.json` | Audit findings with dispositions |
| `.vibeos/baselines/midstream-baseline.json` | Quality baseline (existing issues tracked, only new issues flagged) |
| `docs/planning/midstream-report.md` | Guided audit summary |
| `ACCEPTED-RISKS.md` | Findings explicitly accepted with justification |
| `REMEDIATION-ROADMAP.md` | Deferred fix timeline |

## Build Phase (`/vibeos:build`)

| File | Purpose |
|---|---|
| Source code files | Implementation per work order spec |
| Test files | Tests written from spec (TDD — tests first, then code) |
| `.vibeos/build-log.md` | Build history with decisions and outcomes |
| `.vibeos/checkpoints/WO-NNN.json` | Build progress checkpoint (enables mid-WO resume) |
| `.vibeos/baselines/midstream-baseline.json` | Updated after convergence cycles |
| `docs/planning/WO-NNN-*.md` | Updated with completion evidence |

## Audit Artifacts

| File | Purpose |
|---|---|
| `.vibeos/audit-reports/` | Individual audit agent reports |
| `.vibeos/consensus/` | Cross-agent consensus results |

## Plugin State (`.vibeos/` directory)

The `.vibeos/` directory holds all plugin state. It is safe to add to `.gitignore` if you don't want to track plugin state in version control, though keeping `baselines/` and `findings-registry.json` in git is recommended for team visibility.
