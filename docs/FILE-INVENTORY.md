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
| `MISSION.md` | Compact VibOS Comp enterprise MVP mission brief when Comp mode is used |

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
| `.agents/skills/*` | Repo-scoped Codex skill instructions installed by the Codex bootstrap |
| `.codex/skills/*` | Legacy Codex skill mirror for older Codex surfaces |
| `.codex/agents/*.toml` | Codex-native VibeOS subagent definitions generated from canonical role contracts |
| `.codex/agent-contracts/*.md` | Legacy Markdown VibeOS role contracts for reference and fallback |
| `.codex/config.toml` | Codex project feature and agent concurrency settings |
| `.codex/hooks.json` and `.codex/hooks/*` | Codex-compatible governance, secret-scan, and worktree guard hooks |
| `.claude/rules/always/*.md` | Always-active governance rules |
| `scripts/architecture-rules.json` | Architecture enforcement rules |
| `scripts/*` | Quality gate and utility scripts (copied from plugin) |
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
| `.vibeos/autonomy/heartbeats/*.json` | Long-run autonomy heartbeat evidence for 24-48 hour resumable runs |
| `.vibeos/autonomy/run-lease.json` | Active long-run autonomy run lease preventing concurrent drivers |
| `.vibeos/autonomy/last-lease.json` | Last acquired/released lease evidence |
| `.vibeos/autonomy/lease-conflict.json` | Latest blocked concurrent autonomy driver attempt |
| `.vibeos/autonomy/loop-state.json` | Latest scheduler-safe long-run loop tick state |
| `.vibeos/autonomy/loop-history.jsonl` | Append-only scheduler-safe loop tick history for stuck-loop detection |
| `.vibeos/autonomy/resume-plan.json` | Deterministic supervisor decision and command plan for the next long-run loop |
| `.vibeos/autonomy/runner-report.json` | Classification and execution report for the latest long-run resume plan |
| `.vibeos/autonomy/runtime-adapter-plan.json` | Planned or executed Codex/Claude runtime handoff command |
| `.vibeos/autonomy/runtime-adapter-history.jsonl` | Append-only Codex/Claude runtime adapter history for repeated failure detection |
| `.vibeos/autonomy/failure-report.json` | Long-run autonomy failure detector report for loops, runner blocks, lease conflicts, and provider/session limits |
| `.vibeos/autonomy/recovery-plan.json` | Plan-only recovery actions for detected autonomy failure classes |
| `.vibeos/autonomy/recovery-resolution.json` | Evidence-backed resolution state for recovery-plan actions |
| `.vibeos/autonomy/recovery-resolution-history.jsonl` | Append-only history of recorded recovery resolutions |
| `.vibeos/autonomy/scheduler-guard-report.json` | Pre-tick scheduler guard report for unresolved recovery actions |
| `.vibeos/autonomy/scheduler-profile.json` | Generated scheduler profile manifest for shell, cron, launchd, or GitHub Actions |
| `.vibeos/autonomy/scheduler/*` | Generated scheduler profile files for reviewed manual installation |
| `.vibeos/autonomy/smoke-report.json` | Disposable autonomy smoke-test report |
| `.vibeos/autonomy/supervisor-state.json` | Latest long-run supervisor decision summary |
| `.vibeos/runtime-capabilities.json` | Generated local matrix of Codex, Claude, hook, agent, and orchestration capabilities |
| `.vibeos/cache/evidence-recall-index.json` | Generated local index for source-cited evidence recall |
| `.vibeos/reference/comp/*` | VibOS Comp mission, foundation, flow, invariant, dependency intelligence, delivery infrastructure, scorecard, and evidence references |
| `.vibeos/baselines/midstream-baseline.json` | Updated after convergence cycles |
| `docs/planning/WO-NNN-*.md` | Updated with completion evidence |

## Audit Artifacts

| File | Purpose |
|---|---|
| `.vibeos/audit-reports/` | Individual audit agent reports |
| `.vibeos/consensus/` | Cross-agent consensus results |
| `.vibeos/session-audits/` | Session closeout audit reports |
| `.vibeos/autonomy/` | Long-run autonomy heartbeat and closeout evidence |

## Plugin State (`.vibeos/` directory)

The `.vibeos/` directory holds all plugin state. It is safe to add generated runtime state such as `.vibeos/cache/` to `.gitignore`. Keeping `baselines/` and `findings-registry.json` in git is recommended for team visibility.
