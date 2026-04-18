# VibeOS File Inventory

All files the plugin creates in your project, organized by when they appear.

## Discovery Phase (`/vibeos:discover`)

| File | Purpose |
|---|---|
| `.vibeos/config.json` | Plugin configuration, onboarding state, and autonomy preferences |
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
| `docs/planning/AUDIT-PROTOCOL.md` | Audit layers, trigger points, and blocking rules |
| `docs/planning/AGENT-WORKFLOW.md` | Author/auditor role separation and handoff rules |
| `.claude/quality-gate-manifest.json` | Shared gate configuration used by Claude/Cursor hooks, Codex gate runs, and VibeOS git hooks |
| `.claude/hook-manifest.json` | Hook configuration for real-time enforcement |
| Git hooks: `pre-commit`, `commit-msg` | Commit-boundary enforcement installed by VibeOS when the project is a git repo |
| `.claude/rules/always/*.md` | Always-active governance rules |
| `scripts/architecture-rules.json` | Architecture enforcement rules |
| `scripts/*.sh` | Quality gate scripts (copied from plugin) |
| `AGENTS.md` | Shared repo contract |
| `CLAUDE.md` | Thin Claude entry loader |
| `.claude/CLAUDE.md` | Claude-specific runtime instructions |
| `.vibeos/config.json` | Updated with autonomy preference and any temporary autonomous-session override |

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
| Prompt or instruction files | Updated when a WO changes agent behavior, using the prompt-engineer workflow |
| `.vibeos/build-log.md` | Build history with decisions and outcomes |
| `.vibeos/session-state.json` | Tracks the active or most recent autonomous build session |
| `.vibeos/checkpoints/WO-NNN.json` | Build progress checkpoint (enables mid-WO resume) |
| `.vibeos/baselines/midstream-baseline.json` | Updated after convergence cycles |
| `docs/planning/WO-NNN-*.md` | Updated with completion evidence |

## Audit Artifacts

| File | Purpose |
|---|---|
| `.vibeos/audit-reports/` | Individual audit agent reports |
| `.vibeos/consensus/` | Cross-agent consensus results |
| `.vibeos/session-audits/` | Session closeout audit reports |

## Plugin State (`.vibeos/` directory)

The `.vibeos/` directory holds all plugin state. It is safe to add to `.gitignore` if you don't want to track plugin state in version control, though keeping `baselines/` and `findings-registry.json` in git is recommended for team visibility.
