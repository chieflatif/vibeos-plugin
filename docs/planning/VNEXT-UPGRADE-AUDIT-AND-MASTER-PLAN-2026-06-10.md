# VibeOS vNext Upgrade Audit and Master Plan

- **Date:** 2026-06-10
- **Author runtime:** Claude Code 2.1.170 (interactive session; Codex CLI 0.125.0 also present)
- **Execution policy honored:** audit and planning only — no runtime code changed by this pass
- **Overall verdict:** `planning-only` (this document); WO-106 slice remains `locally implemented`; no component of vNext is `nonproduction proven`, `production/runtime approved`, or `public-link ready`

This document is the single comprehensive planning package requested by the 2026-06-10 handoff. It is written to be execution-ready for a smaller model. Every claim is tagged with evidence (live command output, file:line, or official doc URL).

---

## 0. Operator Vision Statement (captured 2026-06-10, post-audit)

Latif's articulation of the harness's purpose, recorded verbatim-in-spirit as the source text for `docs/product/VISION.md` and `PRODUCT-ANCHOR.md` (WO-134). This is the anchor the cognition layers evaluate against.

**Primary goal:** enable technical and non-technical builders to leverage agentic development to its maximum — producing high-quality, secure, *eloquent* software (simple, clear, clean) in the most cost-effective way.

**The four token-economy pillars** (every architectural decision in this plan must serve at least one):

1. **Anti-drift.** Even with the current system, drift still occurs across 100+ vibe-coded projects (a recent project required deleting ~700 documents — pure token waste). Countermeasures: the document pyramid (thesis → product anchor → PRD → technical spec → dependencies → architecture → plan), file-size limits, persistent clarity/eloquence reminders, and the specialized auditor fleet. Build the map first; then execute without drift, without unnecessary work.
2. **Reuse.** Stop rebuilding the same things. Identify reusable components inside the operator's own repos; ingest skills, agents, packages, frameworks, and whole subsystems from external marketplaces (GitHub etc.) — **securely**, via a sandboxed analysis environment that standardizes and normalizes third-party code before it enters a project. Enterprise variant: an internal reusable-component marketplace the harness knows how to search and ingest from.
3. **Audit-driven error prevention.** The specialized auditors (technical, architectural, security, drift) are non-negotiable; spec-driven and test-driven development are absolute musts.
4. **Maximum autonomy.** The operator spends time up front building the map, then the system runs for a very long time on its own: multi-agent orchestration, self-prompting loops, a model router using the right model per task, and **session-limit awareness** — when a 5-hour (or weekly) limit approaches or hits, the system schedules its own resumption for when capacity returns instead of dying overnight.

How this vision maps onto the plan: anti-drift → Sections 6 (pyramid) + Phase 42 (drift gates) + existing baselines/ratcheting; reuse → **new Phase 46** (Section 7) + Decision D-9/D-10; audit-driven prevention → preserved fleet (F-11) + Phases 36/45; autonomy → Phases 37–41 + **new WO-139** (limit-aware scheduling). Model router → Phase 38. Hooks/loops underleveraged → Phases 37/39 close exactly that gap.

### Core principle hierarchy (proposed 2026-06-10; ratified by Latif → becomes PRODUCT-ANCHOR.md core)

**The promise (above the principles):** anyone — technical or not — can build serious software by building the map and letting the system execute it. Accessibility is the promise; the five principles below are how the promise stays true.

| Principle | Meaning | Subdomains | Primary enforcement in the harness |
|---|---|---|---|
| **1. Eloquence** | The software itself is simple, clear, clean | Minimalism (no stubs/TODOs/dead weight), clarity (naming, structure), composability (file-size budgets, module boundaries), architectural coherence (every line traces to the architecture) | file-budget hook, architecture auditor + enforce-architecture gate, no-stubs detector, code-quality gates |
| **2. Efficiency** | Build it once, with the right resources, and nothing extra | Token economy, reuse-before-build (Phase 46), right model per task (Phase 38 router), autonomy over babysitting (Phases 39–41), no unnecessary work or documents (WO-128 doc budget) | cost capture, model-policy lint, reuse registry/indexer, loop ceilings, hygiene/prune gates |
| **3. Security** | Secure by default, never bolted on | Secure coding (OWASP/PII/tenant-isolation gates), secrets discipline (scan hook + gate), supply-chain admission control (WO-142 sandbox), least-privilege agents (read-only auditors, scope guards), compliance targets as constraints | security auditor, secrets-scan hook, ingestion sandbox gate, worktree scope/bash guards |
| **4. Fidelity** *(the one the original triad was missing — anti-drift, named)* | What gets built is what was anchored; the map governs execution | Document pyramid as single source of truth, scope discipline, product-direction lint, ratcheting baselines, flow integrity (the user journey survives) | product-drift + flow auditors, anchor-term lint, baseline ratchet, scope guards, WO frontmatter contracts |
| **5. Provability** *(also missing from the triad — the existing house culture, named)* | No claim without evidence; the system can prove what it says | Evidence-first cascade (investigate → evidence → WO → implement), spec-driven tests written before code, audits at every boundary, claim ledger + verdict language, generated inventories over hand-counts | tester-before-implementation, audit fleet + consensus, claim ledger, proof packages, gate evidence bundles |

Tension rule for the anchor: when principles conflict, the order of precedence is **Security > Fidelity > Provability > Eloquence > Efficiency** — it is never acceptable to save tokens by skipping an audit, and never acceptable to ship elegant code that drifted from the anchor. Efficiency is the goal-state reward of honoring the other four, not a license to shortcut them.

### Lean-governance doctrine (resolving the Efficiency↔Provability tension)

Operator-observed failure mode across active projects: governance itself burns tokens — evidence prose, uniform audit depth, hand-maintained tracking docs. The precedence rule says provability wins when they conflict; the doctrine below makes them conflict far less often by attacking *how* provability is produced, not *whether*:

1. **Captured, not authored.** The cheapest evidence is a byproduct: exit codes, command output, diffs, hashes, JSON packets written by hooks and scripts at zero model cost. Model-authored narrative about what happened is the most expensive and least trustworthy form of evidence. Default: machines capture, models only fill small judgment fields in structured forms. (Mechanisms: WO-116 gate-result capture, lane packets, generated inventory, cost reports — all already in plan; evidence templates become JSON/checklist forms, not freeform markdown.)
2. **Proportional, not uniform.** Audit depth scales with blast radius via `wo_class` (U1): a docs-only WO gets one evidence-auditor pass; a mutation-path/auth WO gets the full panel. Uniform 12-auditor sweeps are reserved for phase checkpoints. Differential auditing wherever a baseline exists: auditors receive the diff and its contracts, not the whole repo. (Mechanisms: WO-111 governance-tier semantics, WO-127 auditor-artifact gate keyed to class, existing state-hash/baselines for diff scoping.)
3. **Generated, not duplicated.** Every hand-maintained second copy of state is future drift plus reconciliation tokens (the 14 plan/index mismatches in F-08 are this tax). WO frontmatter becomes the single source; WO-INDEX and status views are generated from it. (Mechanisms: WO-112/113 generators; doc budget in WO-128 catches new duplication.)

Governance work also routes to the cheapest adequate model tier (Phase 38 `drafting` tier) — provability rarely needs frontier reasoning to *record*, only to *judge*.

---

## 1. Findings-First Current-System Audit

All findings reproduced live on 2026-06-10 unless noted.

### F-01 (HIGH) — Gate runner cannot execute any gates: tier-schema mismatch

`bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos` reaches "Running 10 gate(s)..." then dies with `AttributeError: 'str' object has no attribute 'get'`.

Root cause: `gate-runner.sh:316-320` (`get_tier_info`) does `tiers.get(str(tier), {})` then `tier_def.get("blocking", ...)` — it expects tier **objects** (`{"label": ..., "blocking": true}`). The manifest's `tiers` map (`plugins/vibeos/quality-gate-manifest.json`) stores plain **string labels**: `"1": "Blocking — code quality, architecture, scope discipline"`. Calling `.get()` on that string raises.

Impact: the deterministic enforcement floor is **non-functional for live gate execution** in this repo. Everything that depends on `gate-runner.sh` (build skill step 7, checkpoint, upgrade discovery sweep, lane-readiness plans) is blocked. This is the single highest-priority fix.

### F-02 (HIGH) — Runtime capability detection falsely reports Claude subagents unavailable

Live: `detect-runtime-capabilities.sh` reports `Claude: available version=2.1.170 subagents=unavailable` and `Strategy: sequential / single-context` — in a session where subagents demonstrably work (this audit dispatched four).

Root cause: `plugins/vibeos/scripts/runtime-capabilities.py` runs `claude agents`, which in non-TTY contexts exits non-zero with the message *"use 'claude agents --json' for a machine-readable listing"*. The script records the error and never retries with `--json`; `active_count` stays `None`, so `subagents` is reported `unavailable`. There is also no detection for agent teams (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`) or dynamic workflows.

Impact: every orchestration decision keyed off `.vibeos/runtime-capabilities.json` silently degrades to sequential single-context execution. This poisons the build skill's parallel-audit dispatch and any future lane/team decisions. Must be fixed before any orchestration upgrade is meaningful.

### F-03 (HIGH) — The upgrade path's cognition layer is specification-only

The `/vibeos:upgrade` skill (`plugins/vibeos/skills/upgrade/SKILL.md`) documents an 11-step flow including CLAUDE.md/settings reconciliation (lines ~169-195), decision-engine re-evaluation (~197-239), discovery-sweep gates (~241-261), full audit dispatch (~271-293), upgrade-report generation (~296-402), and rollback (~427-437). What is actually **implemented as executable mechanism** is: version detection, pre-upgrade snapshot, hardcoded-list file copy, and version tracking (`vibeos-init.sh`, `vibeos-init-codex.sh`, `plugin-upgrade.sh`). The reconciliation, delta classification, recommendation ledger, and upgrade-WO creation exist only as skill prose that depends on model diligence with no deterministic backing, no fixtures, and no tests.

Additional defects inside this surface:
- Snapshot location is inconsistent: SKILL.md uses `.vibeos/upgrade-snapshots/`, `plugin-upgrade.sh` uses `.vibeos/upgrade-backup/`.
- There is **no machine-readable manifest of framework-owned files**; preservation is inverse-inferred from hardcoded arrays (`plugin-upgrade.sh:47-57`).
- No before/after inventory or delta classification exists anywhere in the flow.
- The Codex upgrade path shares `.vibeos/` runtime but has no report, no recommendations, no WO creation — fully divergent.

Impact: the operator's most-valued flow ("open project, say 'update VibeOS'") currently behaves closer to a blind file-copy with good intentions than the cognition-led selective migration the product promises. This is the core product gap vNext must close (Section 8).

### F-04 (MEDIUM) — Secret scan fails on embedded test fixture

`bash plugins/vibeos/scripts/validate-no-secrets.sh` → FAIL on `plugins/vibeos/test-fixture/src/app.py:6` (a deliberately fake AWS-style access key, `AKIA…`, planted by WO-007a as test material; key value intentionally not reproduced here — this repo's own secrets-scan hook blocks files containing the literal pattern, which it correctly did to the first draft of this document). The scanner has no fixture allowlist, so the gate floor can never go green. Needs an explicit, narrowly-scoped allowlist or fixture quarantine — not deletion of the fixture, which other tests depend on.

### F-05 (MEDIUM) — Bare `pytest` fails on fixture collection

`python3 -m pytest` collects `plugins/vibeos/test-fixture/tests/test_app.py` → `ModuleNotFoundError: No module named 'test_fixture'`. `python3 -m pytest tests` passes (103 passed, 7.91s, live). Missing pytest configuration (`testpaths = tests` or `norecursedirs`) means the documented "run the tests" command lies depending on invocation.

### F-06 (MEDIUM) — Hook manifest out of sync with configured hooks

`plugins/vibeos/hooks/hooks.json` registers 12 hook commands; `plugins/vibeos/hook-manifest.json` documents 9. Missing from the manifest: **governance-guard**, **proof-protection**, **file-budget**. Also a name mismatch: manifest says `response-quality-stop-review`, the script is `response-quality-stop.sh`. The generated inventory (WO-106) already exposes the 12-vs-9 gap publicly; it must be reconciled before any proof package.

### F-07 (MEDIUM) — Hook surface uses 4 of ~30 available lifecycle events

VibeOS hooks bind only `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `Stop`. Current Claude Code supports ~30 events (Section 2). Concretely missing enforcement value: `PostToolUse`/`PostToolUseFailure` (verify gate/test outcomes after execution), `SubagentStop` (validate auditor return packets), `ConfigChange` (block silent model downgrades — U5 dependency), `SessionEnd`/`PreCompact` (durable state flush for long runs), `TaskCreated`/`TaskCompleted`/`TeammateIdle` (agent-team governance — U3 dependency), `WorktreeCreate`/`WorktreeRemove` (scope setup/teardown).

### F-08 (MEDIUM) — Plan/index status drift

Session-start recovery reports 14 plan-vs-index mismatches (WO-041/042/043 plan=Draft index=Complete, +11 more). `validate-wo-status-integrity.sh` exists but evidently is not enforced at a blocking boundary, or its findings were never remediated. This is exactly the F9-class hygiene problem the Joan4U blueprint warns about.

### F-09 (LOW) — No machine-readable WO contracts

All 109 WO files express scope, auditors, and acceptance criteria in prose. No frontmatter, no generated scope-guard config, no generated agent configs. `worktree-scopes.schema.json` exists (`plugins/vibeos/reference/worktree-scopes.schema.json`) but is hand-fed, not WO-derived. This is U1, fully missing.

### F-10 (INFO) — Zero adoption of native Claude Code orchestration primitives

Repo-wide grep: no references to `/loop`, `/batch`, `/run`, `/verify`, headless `claude -p`, agent teams, dynamic workflows, the Agent SDK, or OTel-for-self. Long-run autonomy is a bespoke (and well-built) Python control plane (`autonomy-*.py`, 10+ scripts: heartbeat, lease, supervisor, runner, failure detector, recovery planner/resolution, scheduler guard/profile, smoke). This is a strength to preserve as the deterministic floor — but it predates and duplicates native capabilities that should become the execution layer above it.

### F-11 (INFO) — Strengths to preserve (explicitly not findings)

- Convergence control (`state-hash`, `convergence-check`, finding-level baselines with SHA-256 fingerprints, regression detection in `findings-lifecycle.sh`) is genuinely good and product-neutral — it is the seed of U6.
- The agent fleet (20 base + 12 same-tree) has correct read-only auditor discipline (`disallowedTools: Write, Edit, Agent`, worktree isolation) and per-agent `model` frontmatter.
- WO-106's generated inventory + claim ledger is the right proof-foundation pattern; it already blocks the three known overclaims.
- The autonomy control plane's resume/lease/recovery semantics map almost one-to-one onto what U4's loops need underneath them.
- The secrets-scan PreToolUse hook demonstrably blocks live writes containing secret patterns (proven during the authoring of this document).

---

## 2. Latest Claude Code Capability Matrix

Local evidence: `claude --version` → **2.1.170**; `codex --version` → **codex-cli 0.125.0** (both live, 2026-06-10). All doc citations fetched live on 2026-06-10.

| Capability | Status | Version req. | Enablement | Key facts (verified) | VibeOS classification |
|---|---|---|---|---|---|
| **Subagents** | Production | GA | none | Own context, results return to caller; per-agent `model`, `tools`, `disallowedTools`, `isolation: worktree`. Works live in this session. | Production floor — already used; fix F-02 detection |
| **Agent teams** | **Experimental, off by default** | v2.1.32+ | `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` (env or settings.json) | Lead + named teammates, shared task list w/ file locking, peer messaging, plan-approval mode, subagent definitions reusable as teammates. Limitations: no session resumption of in-process teammates, task status can lag, one team per lead, no nested teams, lead fixed, permissions inherited at spawn. Hooks `TaskCreated`/`TaskCompleted`/`TeammateIdle` can veto with exit 2. Token cost scales linearly per teammate. ([docs](https://code.claude.com/docs/en/agent-teams)) | Pilot-only, version-pinned, manual fallback documented; never a default path until Anthropic de-experimentalizes |
| **Dynamic workflows** | Production (paid plans) | v2.1.154+ | On by default; Pro needs `/config` toggle; disable via `disableWorkflows` / `CLAUDE_CODE_DISABLE_WORKFLOWS=1` | Script-driven fan-out (dozens–hundreds of agents), `ultracode` keyword/effort, 16 concurrent agents max, 1,000 agents/run cap, same-session resume, per-run approval prompt, subagents run `acceptEdits` + inherit allowlist, `/workflows` progress view, saveable as commands under `.claude/workflows/`. ([docs](https://code.claude.com/docs/en/workflows)) | Production-safe with governance: bounded first use, saved+reviewed scripts only, budget logging |
| **Hooks lifecycle** | Production (agent-type hooks experimental) | current | settings/plugin hooks.json | ~30 events verified, including `PostToolUse`, `PostToolUseFailure`, `PostToolBatch`, `SubagentStart`/`SubagentStop` (Stop can block), `TaskCreated`/`TaskCompleted`/`TeammateIdle` (block w/ exit 2), `ConfigChange` (blocks config change), `PermissionRequest`/`PermissionDenied`, `FileChanged`, `WorktreeCreate`(blocking)/`WorktreeRemove`, `PreCompact`(blocking)/`PostCompact`, `SessionEnd`, `Setup`, `UserPromptExpansion`, `InstructionsLoaded`, `CwdChanged`, `Elicitation`. Handler types: `command`, `http`, `mcp_tool`, `prompt` = production; `agent` = experimental. ([docs](https://code.claude.com/docs/en/hooks)) | Command hooks = production baseline (unchanged policy); prompt/agent/http hooks deferred |
| **Skills / commands merge** | Production | current | — | Custom commands merged into skills; `.claude/commands/deploy.md` ≡ `.claude/skills/deploy/SKILL.md`. Bundled skills include `/code-review`, `/batch`, `/debug`, `/loop`, `/deep-research`, `/claude-api`. `/run`, `/verify`, `/run-skill-generator` require **v2.1.145+** (verified in docs). ([docs](https://code.claude.com/docs/en/skills)) | Adopt: `/loop` for recurring checks; `/run`+`/verify` inside build verification; `/batch` evaluated in WO |
| **Headless `claude -p`** | Production | current | — | `--bare` recommended for scripts (skips hooks/skills/plugins/CLAUDE.md discovery; API-key auth only); `--output-format json` returns `total_cost_usd` + per-model cost; `--json-schema` for structured output; `--continue`/`--resume "$session_id"`; stdin capped 10MB (v2.1.128+); background tasks killed ~5s after result (v2.1.163+). **Confirmed in official docs:** "Starting June 15, 2026, Agent SDK and `claude -p` usage on subscription plans will draw from a new monthly Agent SDK credit, separate from your interactive usage limits." ([docs](https://code.claude.com/docs/en/headless)) | Production substrate for lane-readiness, night loop, recovery loop. Operator must claim the SDK credit before first scheduled run (Decision D-3) |
| **OpenTelemetry** | Production | current | `CLAUDE_CODE_ENABLE_TELEMETRY=1`, `OTEL_METRICS_EXPORTER=otlp|prometheus|console`, `OTEL_LOGS_EXPORTER`, `OTEL_EXPORTER_OTLP_ENDPOINT` | Metrics include `claude_code.cost.usage`, `claude_code.api_request`, `claude_code.commit.count`, `claude_code.active_time.total`, `claude_code.hook` etc.; traces in beta. ([docs](https://code.claude.com/docs/en/monitoring-usage)) | Optional evidence layer; simpler `total_cost_usd` capture from headless JSON is the v1 cost mechanism |
| **Model** | — | — | — | This audit session itself ran on a model newer than Opus 4.8 (Fable 5 per session environment). The handoff's "Opus 4.8 is latest/default" claim is **plausibly already stale** — model policy must use capability tiers and live verification, never hardcoded IDs (feeds U5 design). | Policy: tier names + verify-at-runtime, no pinned model IDs in framework files |

**Local proof commands recorded:** `claude --version`, `codex --version`, `detect-runtime-capabilities.sh` (exposed F-02), `generate-inventory.py` (PASS, regenerated artifact), `gate-runner.sh pre_commit` (reproduced F-01), `validate-no-secrets.sh` (reproduced F-04), `python3 -m pytest` vs `python3 -m pytest tests` (reproduced F-05; 103 passed).

---

## 3. U1–U7 Reconciliation Table

Classifications per the handoff's taxonomy. "Present" assessments are against this repo's actual code, not its docs.

| Target | What Joan4U specifies | VibeOS current state | Classification | vNext disposition |
|---|---|---|---|---|
| **U1** Machine-readable WO contracts | YAML frontmatter: `wo_class`, `write_scope`, `required_auditors`, `model_policy`, `budget_posture`; generators feed scope-guard, agent configs, auditor gates | **Missing** (F-09). Prose-only WOs; `worktree-scopes.schema.json` exists but hand-fed | Missing → **redesign product-neutral** | Phase 35. Operator-definable `wo_class` enum (not Joan's hardcoded classes); generators emit `.vibeos/worktree-scopes.json` + agent allow/deny + auditor-gate keys; cross-validating lint |
| **U2** Automated lane-readiness gate | Scratch-worktree rebase → `wo_exit` → JSON return-packet schema check → ACCEPT/DEFER with reasons; re-validate scope against actual diff | **Missing.** Convergence/baseline scripts are adjacent but nothing validates a lane pre-merge | Missing → **build fresh** | Phase 36. Headless-optional: pure bash core, `claude -p --bare` only for defect summarization. Blocked on F-01 fix (wo_exit must run) |
| **U3** Agent-team batches | Experimental pilot: env-gated teams, TaskCompleted/TeammateIdle/SubagentStop governance, stall detection, evidence vs manual baseline | **Missing.** No teams references anywhere | Missing → **Claude-only, experimental pilot, capability-detected** | Phase 41, deliberately after deterministic floor (mirrors Joan HX-7 sequencing). Never default; manual dispatch stays the documented fallback. No Codex equivalent claimed — Codex equivalence explicitly deferred |
| **U4** Lane/night/recovery loops | Three bounded loop types with frontmatter ceilings (`loop_goal`, `loop_ceiling_turns`, `loop_ceiling_cost_usd`), Stop-hook goal verification, June-15 SDK credit awareness | **Partially present, different substrate.** `autonomy-*.py` control plane already implements heartbeat/lease/supervisor/recovery/scheduler-guard — i.e., the durable-state half of night+recovery loops. No native `/loop`, no headless wrappers, no per-WO ceilings | Partially present → **redesign as integration**: native execution layer over the existing deterministic control plane | Phase 39. Do NOT rewrite the autonomy control plane; wrap it. `claude -p --bare` night tick → `autonomy-loop.py`; ceilings in WO frontmatter (U1); `total_cost_usd` captured per tick |
| **U5** Model/effort policy | `model-policy.json` routing table, ConfigChange hook blocks audit-role downgrades, manifest lint, per-lane cost capture | **Missing as policy.** Agents have ad-hoc `model:` frontmatter (sonnet/opus split) but no table, no lint, no enforcement, no cost capture | Missing → **redesign provider-aware** (per WO-122: avoid Claude-only assumptions; Codex maps via existing model/effort transpilation in `vibeos-init-codex.sh`) | Phase 38. Tier names (`frontier-audit`, `implementation`, `drafting`), runtime-resolved; never hardcoded model IDs (see Section 2 model row) |
| **U6** Drift management | Auditor-artifact gate, waiver-expiry gate, product-direction lint, cross-plane scenario test, executed-vs-declared gate-count assertion | **Partially present.** Strong: finding-level baselines, ratcheting, regression detection, product-drift-auditor agent, `validate-development-plan-alignment.sh`. Missing: waiver expiry, auditor-artifact gate keyed to wo_class, executed-vs-declared count assertion, configurable anchor-term lint | Partially present → **extend product-neutral** | Phase 42. Anchor terms configurable per project (`.vibeos/config.json`), not hardcoded product names. F-08 (status drift) fixed earlier in Phase 34 |
| **U7** Harness hygiene | Archive retired scripts, retention policy for checkpoints/exhaust, anti-sprawl rule for harness WOs | **Partially present.** Generated inventory (WO-106) is the U7 seed; no retention policy, no archive structure; status drift exists (F-08) | Partially present → **extend** | Phase 42. `hygiene-policy.json` + prune script with mandatory dry-run; smaller problem here than Joan4U (no 8,600-dir exhaust yet) — right time to install the policy |

**Rejected as unsafe/overclaim-prone** (consistent with the claim ledger): Codex hook parity in any form; "24–48h autonomy" as a public capability claim without durable-run proof; agent teams as a production default; any count claims not regenerated from `generate-inventory.py`.

---

## 4. Claude-First vNext Architecture Proposal

Five layers, with a hard line between deterministic floor and model-driven ceiling. Principle inherited from Joan4U and kept non-negotiable: **every blocking control lives on the deterministic floor; Claude-native features are acceleration, never the only guard.**

```
L4  Evidence & Cost        total_cost_usd capture, OTel (optional), claim ledger,
                           generated inventory, proof packages
L3  Scheduled/Headless     claude -p --bare wrappers: lane-readiness, night loop,
                           recovery tick — all over the existing autonomy control plane
L2  Orchestration ceiling  subagents (production) → dynamic workflows (governed)
                           → agent teams (experimental pilot, env-gated)
L1  Session enforcement    modernized command hooks (~12 events used, up from 4)
L0  Deterministic floor    bash/python gates, gate-runner, git hooks, baselines,
                           convergence, findings lifecycle, autonomy control plane,
                           WO frontmatter generators, framework-ownership manifest
```

### Hard distinctions

| Bucket | Contents |
|---|---|
| **Deterministic enforcement floor** (runtime-independent) | gate-runner + manifest (post F-01 fix), secret scan, baselines/ratcheting, findings lifecycle, lane-readiness core, WO-frontmatter generators + lints, framework-manifest/delta engine, autonomy control plane, git hooks |
| **Claude orchestration ceiling** (production-safe) | subagent dispatch (current build loop), dynamic workflows under governance (approval prompt, saved scripts, slice-first cost probing), `/loop` for recurring local checks, `/run`+`/verify` in build verification, headless `claude -p --bare` for scripted lanes |
| **Experimental** (env-gated, version-pinned, fallback documented, never load-bearing) | agent teams (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`), agent-type hooks |
| **Codex-equivalent / fallback** (deferred — Section 5) | instruction-layer skills, shared L0, git commit-boundary hooks, explicit gate runs |

### Hook modernization design (Phase 37)

Keep all 12 existing command hooks. Add, as command hooks:

| Event | New hook | Enforces |
|---|---|---|
| `PostToolUse` (Bash matcher) | `gate-result-capture.sh` | Record gate/test outcomes to session state; close the "claimed pass vs actual pass" gap |
| `SubagentStop` | `validate-agent-return.sh` | Auditor/implementation return-packet shape (the `.ref` for this already exists: `reference/hooks/subagent/validate-audit-result.sh.ref`) |
| `ConfigChange` | `model-policy-guard.sh` | Block mid-run model downgrades for audit-class work (U5) |
| `SessionEnd`, `PreCompact` | `state-flush.sh` | Flush heartbeat/checkpoint state before compaction/exit (long-run durability) |
| `TaskCreated`, `TaskCompleted`, `TeammateIdle` | `team-governance.sh` (dormant) | Installed but inert until teams pilot enables them; exit-2 veto wired to lane-readiness |
| `WorktreeCreate` | `worktree-scope-setup.sh` | Materialize WO scope file into new worktrees automatically |

### Loop architecture (Phase 39) — wrap, don't rewrite

The autonomy control plane already owns durable state, leases, failure detection, and recovery resolution. vNext adds native execution shells:

1. **Lane loop** — in-session continuation bounded by WO frontmatter (`loop_ceiling_turns`, `loop_ceiling_cost_usd`); existing Stop hook (`response-quality-stop.sh`) extends to verify the declared `loop_goal` before accepting terminal state; `STALLED_AT_CEILING` is a first-class WO status.
2. **Night loop** — scheduled `claude -p --bare` (or plain cron→bash where no cognition is needed) that runs one `autonomy-loop.py` tick, then full_audit gates + drift sweep + waiver expiry; writes cost from `--output-format json`.`total_cost_usd` into the evidence bundle; runtime ceiling and `autonomy-scheduler-guard.py` blocking preserved exactly as-is.
3. **Recovery loop** — `autonomy-recovery-planner.py` plans stay plan-only; the new wrapper may execute exactly one `--resume`-based retry against the saved checkpoint, then escalates. `autonomy-scheduler-guard.py` blocking semantics unchanged.

No unbounded loops anywhere; every loop declares ceilings in U1 frontmatter. The 2026-06-15 Agent SDK credit (verified, Section 2) must be claimed before the first scheduled headless run — Decision D-3.

### Workflow adoption (Phase 40)

Bounded first use: re-express the `/vibeos:audit` fan-out (12 auditors + consensus) as a saved, reviewed workflow under `.claude/workflows/`, run on a small slice first, compare findings + tokens against the subagent path, and keep whichever wins per evidence. Workflows never gain Write access to project-owned governance docs (subagents in workflows run `acceptEdits` — scope-guard hooks remain the control).

---

## 5. Codex Equivalence / Fallback Strategy (explicitly deferred)

No Codex equivalence work occurs until the Claude-first architecture (Phases 34–43) is implemented and audited. Until then the standing posture is the current truthful one (`AGENTS.md`): instruction-layer skills + shared `.vibeos/` floor + explicit gate runs + commit-boundary git hooks; no hook parity, no write-time enforcement guarantee, no unconditional subagent claim.

Deferred design principles (recorded now so the Claude design doesn't paint Codex into a corner):

1. **Everything blocking already lives in L0**, which Codex shares byte-for-byte. Claude work in Phases 35–42 must keep new blocking controls in L0 (frontmatter lints, lane-readiness, waiver expiry, delta engine) so Codex inherits them for free.
2. Codex equivalence then reduces to: (a) regenerate Codex skills from the same WO/loop specs, (b) map model-policy tiers through the existing transpiler mapping in `vibeos-init-codex.sh`, (c) wire Codex headless lanes into the same `autonomy-runtime-adapter.py` handoff plans (which already model Codex/Claude handoffs), (d) re-detect capabilities per `runtime-capabilities.py` and degrade explicitly.
3. The claim ledger's `posture.codex_hook_parity = blocked_overclaim` stays in force permanently unless Codex ships a true hook lifecycle and we prove it.

A single future phase ("Codex Equivalence", placed after Phase 45) gets planned only after the independent vNext audit passes.

---

## 6. Document Pyramid Redesign and Migration Plan

Current state: the repo has no VISION/PRODUCT-ANCHOR/PRD of its own (ironically — it ships templates for them in `reference/product/`). `CLAUDE.md` carries architecture + constraints + conventions in one file; `README.md` carries product narrative; planning docs carry everything else.

### Target pyramid (all under `docs/` unless noted)

| # | Document | Purpose | Status |
|---|---|---|---|
| 1 | `docs/product/VISION.md` | What VibeOS is becoming: the governed development operating layer for AI-assisted work (language anchored to WO-121's "underweighted story") | New |
| 2 | `docs/product/PRODUCT-ANCHOR.md` | Product promise + anti-goals (anti-goals include: blind file-copy upgrades, unbounded autonomy claims, runtime-parity claims) | New |
| 3 | `docs/product/PRD.md` | Operator-facing requirements: voice-led routing, build loop, audits, Comp, long-run autonomy, **upgrade path as first-class feature** | New |
| 4 | `docs/architecture/ARCHITECTURE.md` | The L0–L4 layer model (Section 4), Claude-first runtime, Codex compatibility layer, enforcement-floor invariants | New — supersedes the architecture section of CLAUDE.md (CLAUDE.md keeps a pointer + agent operating rules only) |
| 5 | `docs/architecture/RUNTIME-MANIFEST.md` | Commands, hooks (all events used), skills, agents, workflows, scheduler/headless paths, env assumptions, capability requirements per feature — generated sections from `generate-inventory.py` extended output | New, partially generated |
| 6 | `docs/planning/DEVELOPMENT-PLAN.md` | Existing, extended with Phases 34–45 (Section 7) | Extend |
| 7 | `docs/planning/WO-SCHEMA.md` | The machine-readable frontmatter contract (U1): fields, enums, generator behavior, lint rules | New (Phase 35 deliverable) |
| 8 | `docs/proof/PROOF-PACKAGE-SPEC.md` | The 8-item package: generated inventory, install proof, runtime matrix, gate/hook/secret-scan proof (incl. one failing→passing trace), sample execution trace, limitation statement, tag/release proof, website/media handoff | New (mirrors WO-121/WO-130 requirements exactly) |
| 9 | `docs/architecture/UPGRADE-PATH-SPEC.md` | The five-layer upgrade architecture (Section 8), classification taxonomy, report formats, fixture test plan | New (Phase 43 anchor doc) |
| 10 | `docs/PUBLIC-LIMITATIONS.md` | Public-safe language: Claude vs Codex, hook parity absence, autonomy bounds, private-asset boundaries — single source the website quotes | New |

### Migration steps (executed in Phase 44, not now)

1. Author 1–3 (product docs) from this plan + WO-121's preserved story; Latif approves the anchor before anything else moves.
2. Extract architecture content out of `CLAUDE.md` into 4; reduce CLAUDE.md to operating rules + pointers (keeps agent-context cost down — also what official skills-vs-CLAUDE.md guidance recommends).
3. Generate 5's inventory sections from an extended `generate-inventory.py` (`--emit-runtime-manifest`).
4. Author 7 from the implemented U1 schema (not before — the schema gets validated by generators+lints first; spec follows implementation evidence).
5. Author 8, 9, 10; update README to point at 10 instead of inlining limitation language.
6. Add a docs-pyramid lint to `full_audit` (each doc exists, cross-links resolve, no stale counts vs generated inventory).

No doc in `latifhorstweb` or `Joan4U` is touched at any point.

---

## 7. Detailed Development Plan (Phases 34–45)

Numbering continues from WO-106. Every WO below gets a full `docs/planning/WO-NNN-*.md` file at execution time using the existing template; this table is the authoritative scope/ordering. Global no-touch boundaries for ALL WOs: `latifhorstweb/`, `Joan4U/`, `docs/evidence/vnext/generated-inventory.json` only changes via the generator, no edits to `tests/` by implementation lanes (existing hook enforces), never delete the test fixture.

**Revised dependency path vs the handoff's suggested order:** the handoff's items 1–2 stand; this plan promotes **runtime-capability detection repair** into the same phase (it gates every orchestration decision and is a 1-file fix), and inserts the **document pyramid** before the upgrade-path redesign completes its dogfood loop — but keeps upgrade-path implementation (Phase 43) ahead of full doc migration (Phase 44) since the upgrade engine's deterministic layers don't need the docs, only its cognition layer's *own-project* evaluation does, and the anchor docs land via WO-134 in time for Phase 45's audit.

### Phase 34 — Foundation Repair (everything else is blocked on this)

| WO | Title | Scope (files) | Acceptance criteria | Proof commands |
|---|---|---|---|---|
| **WO-107** | Gate-runner tier-schema fix | `plugins/vibeos/scripts/gate-runner.sh` (get_tier_info), `plugins/vibeos/quality-gate-manifest.json`, `plugins/vibeos/reference/manifests/quality-gate-manifest.json.ref`, `tests/test_gate_runner.py` | Tier defs become objects `{"label": str, "blocking": bool}` (manifest migration) AND runner tolerates legacy string tiers (back-compat for installed projects; blocking inferred from `tier <= 1`); pre_commit executes all 10 gates end-to-end; new tests cover object-tier, string-tier, missing-tier | `bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos` executes gates; `python3 -m pytest tests/test_gate_runner.py` |
| **WO-108** | Fixture secret quarantine + pytest scoping | `plugins/vibeos/scripts/validate-no-secrets.sh`, new allowlist (e.g. `plugins/vibeos/scripts/secrets-allowlist.json` listing the fixture path+pattern), `pytest.ini` or `pyproject.toml` (`testpaths = tests`), fixture unchanged | Secret scan passes with the fixture intact and STILL fails on a planted real-pattern secret outside the allowlist (failing→passing trace captured for proof package); bare `python3 -m pytest` == `pytest tests` (103+ pass) | `bash plugins/vibeos/scripts/validate-no-secrets.sh`; `python3 -m pytest` |
| **WO-109** | Runtime capability detection repair + extension | `plugins/vibeos/scripts/runtime-capabilities.py`, `tests/test_runtime_capabilities.py` | `claude agents` non-TTY failure retries with `--json`; subagents report `available` on 2.1.170; new fields: `agent_teams` (env var + version ≥2.1.32 → `experimental_available`), `dynamic_workflows` (version ≥2.1.154 + not disabled), `headless` (claude binary present), each with evidence strings; strategy recomputed | `bash plugins/vibeos/scripts/detect-runtime-capabilities.sh --project-dir .` shows `subagents=available`; pytest module |
| **WO-110** | Hook-manifest sync + WO status reconciliation | `plugins/vibeos/hook-manifest.json`, `docs/planning/DEVELOPMENT-PLAN.md`, WO-041…043 + 11 mismatched WO files, `validate-wo-status-integrity.sh` tier | Manifest documents all 12 hooks with correct names; `generate-inventory.py` shows documented_count == configured_command_count == 12; zero plan/index mismatches; status-integrity gate moved to blocking tier at wo_exit | `python3 plugins/vibeos/scripts/generate-inventory.py --project-dir .`; status-integrity gate run |

**Audit checkpoint 34:** independent same-tree audit (correctness + evidence auditors) on the Phase 34 diff; gate floor must run fully green for the first time — this green run is itself a proof-package artifact.

### Phase 35 — Machine-Readable WO Contracts (U1)

| WO | Title | Scope | Acceptance criteria |
|---|---|---|---|
| **WO-111** | WO frontmatter schema + template | `docs/planning/WO-SCHEMA.md`, `plugins/vibeos/reference/governance/WO-TEMPLATE.md.ref`, JSON Schema at `plugins/vibeos/reference/wo-frontmatter.schema.json` | Fields: `wo`, `wo_class` (operator-extensible enum), `write_scope` (globs), `required_auditors`, `model_policy` (tier name), `budget_posture`, optional `loop_goal`/`loop_ceiling_turns`/`loop_ceiling_cost_usd`, `no_touch` (globs). **`wo_class` carries governance-tier semantics (lean-governance rule 2): each class defines auditor-panel size, evidence-form depth, and whether differential audit suffices — docs-only ≠ mutation-path.** Schema validates known-good/known-bad fixtures |
| **WO-112** | Frontmatter generators | new `plugins/vibeos/scripts/wo-contracts.py` (+ tests) | From one WO file: emits `.vibeos/worktree-scopes.json` entry (validating against existing `worktree-scopes.schema.json`), agent allow/deny material, and the auditor-requirement key consumed by the Phase 42 auditor-artifact gate. Identical allow/deny output proven by schema self-tests |
| **WO-113** | Migration + drift lint + generated WO-INDEX | one historical WO back-filled as fixture; WO-107+ all carry frontmatter; new lint gate `validate-wo-frontmatter.sh` registered in manifest (advisory → blocking after backfill); **WO-INDEX.md becomes a generated view from WO frontmatter (lean-governance rule 3)** — hand-edits to the index are detected and rejected by the lint, which structurally eliminates the F-08 plan/index drift class | Lint cross-validates frontmatter vs prose scope; gate-runner runs it in `wo_entry`; regenerating the index twice is idempotent; a deliberate hand-edit to the generated index fails the lint fixture |

### Phase 36 — Lane-Readiness Automation (U2) *(depends: 34, 35)*

| WO | Title | Scope | Acceptance criteria |
|---|---|---|---|
| **WO-114** | Lane return-packet schema | `plugins/vibeos/reference/lane-packet.schema.json`, doc section in WO-SCHEMA.md | Fields per Joan U2: `wo_number`, `lane_status`, `gate_results[]`, `defects[]`, `evidence_bundle_path`; schema-checked fixtures |
| **WO-115** | `check-lane-readiness.sh` | new script + tests; integrates `gate-runner.sh wo_exit` | Scratch worktree → rebase lane branch → run wo_exit → validate packet → re-validate `write_scope` against actual rebase diff (anti-spoofing) → ACCEPT/DEFER with reasons; rebase failure → clean abort + DEFER. Three synthetic fixtures: clean→ACCEPT, scope-violation→DEFER, rebase-conflict→DEFER |

### Phase 37 — Hook Lifecycle Modernization *(depends: 34)*

| WO | Title | Scope | Acceptance criteria |
|---|---|---|---|
| **WO-116** | PostToolUse + SubagentStop + SessionEnd/PreCompact hooks | `plugins/vibeos/hooks/hooks.json`, new scripts `gate-result-capture.sh`, `validate-agent-return.sh` (from existing `.ref`), `state-flush.sh`; `hook-manifest.json` | Each hook has a synthetic fire test (JSON-on-stdin harness, pattern already used by hook scripts); exit-code semantics documented; manifest in sync (gate from WO-110 keeps it honest) |
| **WO-117** | Worktree + team-governance hooks (dormant) | `worktree-scope-setup.sh` on `WorktreeCreate`; `team-governance.sh` on `TaskCreated`/`TaskCompleted`/`TeammateIdle` behind a `.vibeos/config.json` feature flag, default off | Hooks no-op (exit 0) when flag off; veto correctly with exit 2 in synthetic tests when on |

### Phase 38 — Model/Effort/Cost Policy (U5) *(depends: 34, 35)*

| WO | Title | Scope | Acceptance criteria |
|---|---|---|---|
| **WO-118** | Model policy table + lint | new `plugins/vibeos/reference/model-policy.json` (tier names → resolution rules, `allow_downgrade` flags), lint script comparing agent frontmatter + WO `model_policy` against table | Policy uses tier names, resolved at runtime against detected models; lint fails on mismatch; registered in manifest |
| **WO-119** | ConfigChange downgrade guard + cost capture | `model-policy-guard.sh` (ConfigChange hook), cost-capture helper that parses headless `--output-format json` `total_cost_usd` into `cost-report.json` in evidence bundles | Guard blocks audit-class downgrade in synthetic test; cost report labeled "estimate; reconcile against billing" |

### Phase 39 — Loop & Headless Execution (U4) *(depends: 34, 35, 37, 38)*

| WO | Title | Scope | Acceptance criteria |
|---|---|---|---|
| **WO-120** | Lane-loop ceilings + goal-verified stop | extend `response-quality-stop.sh` (or sibling Stop hook) to check `loop_goal` from active WO frontmatter; `STALLED_AT_CEILING` status in build skill + session state | Fixture WO with ceiling 2 stops at 2 and records the status; goal-claim verified against gate evidence, not assistant text alone |
| **WO-121** | Night-loop headless wrapper | new `plugins/vibeos/scripts/night-loop.sh`: `claude -p --bare` (allowlisted tools) → one `autonomy-loop.py` tick → full_audit gates → drift sweep → waiver check → evidence + cost write; respects `autonomy-scheduler-guard.py` and run lease | Dry-run mode default; ceiling on runtime; cost in evidence; refuses to run if scheduler guard blocks. **Pre-req: Decision D-3 (SDK credit) resolved** |
| **WO-122** | Recovery-loop execution shell | wrapper allowing exactly one `--resume` retry from checkpoint per recovery plan, then escalate; `autonomy-recovery-resolution.py` evidence binding unchanged | Known-bad fixture: second failure escalates, does not loop; resolution evidence required to unblock (existing semantics preserved, proven by existing tests still passing) |
| **WO-139** | Session-limit-aware self-rescheduling | new `plugins/vibeos/scripts/limit-aware-scheduler.py` + a `Notification`-event hook + integration with `autonomy-failure-detector.py` (which already classifies provider/session-limit failures), `autonomy-scheduler-profile.py`, and run lease | **Design invariant (operator-mandated):** once the limit hits, ALL Claude API calls are dead — so every component that detects, schedules, and resumes MUST be pure bash/python/cron with zero Claude dependency; Claude is only ever the *payload* of the resumed tick, never the scheduler. **(a) Proactive — primary path:** Claude Code surfaces "approaching your 5-hour session limit" warnings as notifications, and the hook lifecycle has a `Notification` event — spike task 1 is capturing that hook's payload live to confirm limit warnings flow through it AND that it carries (or lets us derive) the reset time. **Operator simplification (2026-06-10): since the limit notification tells us when the window resets, the only mandatory pre-death action is writing the cron entry for that reset time — heavy wind-down is unnecessary because checkpoints and heartbeats are already continuous; the session can keep working until the very end and the resumed tick picks up from the last checkpoint as designed. One dispatch rule applies post-warning: do not START new large dispatches (multi-agent audit sweeps, parallel lanes, workflows) inside the warning window — finish or checkpoint current work instead; the threshold for "large" keys off `wo_class`/governance tier.** Secondary proactive signals to spike: usage-command output parsing, OTel `claude_code.cost.usage`, elapsed-session-time heuristic (a 5h limit is partially predictable from session start time — cheap fallback ceiling). **(b) Reactive — guaranteed fallback:** on a `rate_limit`-class failure from a headless tick (`claude -p` emits `system/api_retry` events with `error: rate_limit`), the non-Claude wrapper parses/records the reset window, writes a one-shot scheduler entry (cron/launchd via the existing reviewed-profile mechanism), marks loop state `PAUSED_FOR_LIMIT` — never busy-polls a dead API. If the reset time cannot be parsed, schedule conservative fixed-interval re-probes (e.g., hourly) from cron, with the probe itself being a cheap non-Claude liveness check before any real tick spends tokens. Fixtures: simulated limit notification → wind-down + schedule written pre-death; simulated hard limit error → schedule written post-death; resumed tick honors lease and recovery-resolution semantics |

### Phase 40 — Dynamic Workflow Adoption *(depends: 34; parallel-safe with 39)*

| WO | Title | Scope | Acceptance criteria |
|---|---|---|---|
| **WO-123** | Workflow governance policy + capability detection | policy section in ARCHITECTURE/RUNTIME-MANIFEST docs; `runtime-capabilities.py` field (from WO-109) consumed by build/audit skills | Policy: saved+reviewed scripts only for recurring use; slice-first cost probe; no project-governance writes; disable path documented |
| **WO-124** | Bounded first use: audit fan-out workflow | `.claude/workflows/vibeos-audit-sweep` script expressing the 12-auditor consensus sweep | Run on a bounded slice; findings + token evidence compared against the subagent-path baseline; adoption verdict recorded with evidence (either outcome is a valid result) |

### Phase 41 — Agent-Team Pilot (U3) *(depends: 36, 37; experimental)*

| WO | Title | Scope | Acceptance criteria |
|---|---|---|---|
| **WO-125** | Pilot plan + evidence model | pilot design doc; version pin recorded; manual fallback documented; team-governance hooks (WO-117) flag on for pilot only | Go/no-go criteria defined BEFORE the pilot: stall-detection latency target, pre-merge defects caught, coordinator labor vs sequential baseline |
| **WO-126** | Pilot execution: parallel WO lanes as team | 2–3 disjoint-scope WOs run as named teammates with shared task list; TaskCompleted veto wired to lane-readiness (WO-115) | Evidence bundle: task-list state, hook fire logs, lane packets, cost; verdict stated in the five-level language; teams remain non-default regardless of outcome |

### Phase 42 — Drift & Hygiene Completion (U6/U7) *(depends: 35)*

| WO | Title | Scope | Acceptance criteria |
|---|---|---|---|
| **WO-127** | Auditor-artifact + waiver-expiry + executed-vs-declared gates | `validate-audit-completeness.sh` extension keyed to `required_auditors`; new waiver-expiry scan (frontmatter + `WAIVER until YYYY-MM-DD` prose pattern); gate-runner asserts executed gate count == manifest phase count (Joan NF-1-class defense) | Known-good/known-bad fixtures per gate; registered in manifest at wo_exit |
| **WO-128** | Product-direction lint + hygiene policy + doc budget | configurable `anchor_terms`/`retired_terms` in `.vibeos/config.json`; `check-product-direction-drift` script; `hygiene-policy.json` + `prune-observation-exhaust.sh` (dry-run mandatory); **doc-sprawl budget**: per-project ceiling on governed-doc count + orphan-doc detection (docs not reachable from the pyramid index), surfaced as advisory findings (motivated by the operator's 700-deleted-documents drift incident — doc sprawl is token waste with the same shape as code sprawl, and `file-budget.sh` already proves the budget-hook pattern) | Advisory tier until the doc pyramid lands, then blocking; prune never deletes without `--execute` + git-backed archive; orphan detection has known-good/known-bad fixtures |

### Phase 43 — Upgrade Path vNext *(depends: 34–38, 42; the product centerpiece — full architecture in Section 8)*

| WO | Title | Scope | Acceptance criteria |
|---|---|---|---|
| **WO-129** | Framework-ownership manifest | new generated `plugins/vibeos/framework-manifest.json` (every shipped file: path, hash, ownership=framework, merge-strategy ∈ {overwrite, smart-merge, never}); generator added alongside `generate-inventory.py` | Manifest regenerates deterministically; install/bootstrap consumes it instead of hardcoded arrays; snapshot location unified to `.vibeos/upgrade-snapshots/` |
| **WO-130** | Deterministic delta engine | new `plugins/vibeos/scripts/upgrade-delta.py`: before/after inventory diff, per-file classification candidates (added/changed/removed × ownership × merge-strategy), dirty-git refusal, version detection | Fixture old-install vs new-framework produces a complete machine-readable delta; never writes during analysis |
| **WO-131** | Cognition review layer (Claude) | rewrite `plugins/vibeos/skills/upgrade/SKILL.md` to consume the delta artifact and evaluate against the project's anchor/PRD/plan/gates/baselines/capability matrix; classify each change auto-apply / project-review / optional / blocked / incompatible; recommendation-ledger format | Skill steps are each backed by a deterministic artifact (no prose-only steps remain); ledger explains every non-auto-apply decision |
| **WO-132** | Apply + preserve + rollback engine | apply only auto-apply class; project-owned registry honored (from WO-129 manifest inversion + project-owned globs); upgrade-WO creation for project-review items; `.vibeos/upgrade-reports/upgrade-[ts].md` + manifest + ledger + rollback snapshot; rollback command restores byte-for-byte | Rollback proven on fixture; project-owned files untouched by default in all fixture runs |
| **WO-133** | Upgrade fixture smoke test | fixture project with custom gates, local docs, existing findings, dirty-state cases | Smoke covers: clean upgrade, dirty-git refusal, custom-gate preservation, blocked-change surfacing, rollback; wired into `full_audit` |

### Phase 44 — Document Pyramid Migration *(content per Section 6)*

| WO | Title | Scope |
|---|---|---|
| **WO-134** | Product docs (VISION, PRODUCT-ANCHOR, PRD) — **requires Latif approval of anchor text** | `docs/product/` |
| **WO-135** | Architecture + runtime manifest + limitations + proof-package spec + upgrade spec; CLAUDE.md slimmed; docs-pyramid lint gate | `docs/architecture/`, `docs/proof/`, `docs/PUBLIC-LIMITATIONS.md`, `CLAUDE.md`, `README.md` |

### Phase 45 — Independent vNext Audit & Public Proof Package *(depends: all)*

| WO | Title | Scope | Acceptance criteria |
|---|---|---|---|
| **WO-136** | Independent audit | full audit cycle + Codex external audit (`/vibeos:codex-audit`) over Phases 34–44; zero-debt remediation | All fixable findings fixed (house policy); ratchet baselines updated at checkpoint |
| **WO-137** | Proof package assembly | per `PROOF-PACKAGE-SPEC.md`: regenerated inventory; temp-repo install proof (Claude + Codex surfaces); runtime matrix; gate/hook/secret-scan proof incl. one failing→passing trace; real sample execution trace (one true WO through the loop); limitation statement; clean tag | Every item present in `docs/evidence/vnext/`; claim ledger flips `posture.repo_link_readiness` only when ALL items exist |
| **WO-138** | Public-readiness gate + website handoff | readiness checklist run (Section 9); handoff doc for `latifhorstweb` WO-130 consumption (written HERE, consumed THERE — no cross-repo writes) | Verdict recorded in the five-level language |

### Phase 46 — Reuse & Secure Ingestion *(new track from the 2026-06-10 vision statement; default position after 45, re-prioritizable per Decision D-9)*

The token-economy pillar the current plan did not cover: stop rebuilding what already exists. Two sources of reuse — the operator's own repos, and external marketplaces (GitHub repos, skill/agent marketplaces). The external path is a **supply-chain attack surface by definition** (untrusted code entering governed projects), so the deterministic floor owns admission control, and nothing ingested skips the same gates that govern written code. The Joan4U third-party skill/agent ingestion mechanism is prior art to be extracted product-neutral, not rebuilt.

| WO | Title | Scope | Acceptance criteria |
|---|---|---|---|
| **WO-140** | Reusable-object registry + spec | `docs/architecture/REUSE-REGISTRY-SPEC.md`; registry format `.vibeos/reuse-registry.json` (object types: package, component, skill, agent, framework, subsystem; each with provenance, version, license, ingestion-evidence pointer, trust tier) | Generalizes the packages-directory concept; registry is generated/validated, not hand-edited; trust tiers: `internal`, `vetted-external`, `quarantined` |
| **WO-141** | Own-repo reuse scanner | new scanner (subagent-driven discovery + deterministic indexer) that inventories the operator's existing repos for reusable components and writes registry candidates | Run against 2–3 of Latif's real repos as fixtures; candidates carry file refs + extraction notes; zero writes to scanned repos |
| **WO-142** | Secure ingestion sandbox | Docker-based (local-first; VPS deferred per D-10) analysis pipeline: clone into a network-egress-disabled container → license check → secret scan → dependency/SBOM inventory → malware/supply-chain heuristics (install scripts, obfuscation, typosquat signals) → static review by security-auditor agent → normalization report | A known-good and a deliberately-bad fixture repo: good → `vetted-external` with evidence bundle; bad → `quarantined` with findings. Ingested code NEVER executes outside the sandbox before admission; admission verdict is a deterministic gate, not model judgment alone |
| **WO-143** | Marketplace indexer + project-setup integration | extend `/vibeos:discover` and `/vibeos:plan` with a "what already exists?" step that fires specifically during the **technical-architecture and technical-dependency sections of planning**; build or adopt a marketplace indexer (evaluate existing sources first: GitHub search API, agentskills/plugin marketplaces, package registries — build a scraper only where no API exists) that maintains a **fast local index cache** (`.vibeos/reuse-index/`) of frameworks, packages, skills, agents, and reusable objects, so candidate lookup during planning is a sub-second local query, not a live crawl; Joan4U ingestion mechanism extracted product-neutral | Index refresh is a scheduled/explicit operation, never inline during planning; plan output distinguishes build-vs-reuse decisions with evidence (candidate, source, license, trust tier); every reuse decision creates an ingestion WO routed through WO-142; scraping respects source terms-of-service and rate limits, recorded per source |
| **WO-144** | Enterprise internal-marketplace mode | registry federation: a project can point at an organization-internal registry (git repo or file share) as a `vetted` source with its own trust policy | Fixture internal marketplace consumed end-to-end; documented in PRD as the enterprise story |

**Implementation order:** 34 → 35 → {36, 37, 38 in parallel-safe lanes (disjoint files)} → 39 (incl. WO-139) → 40 → 41 → 42 → 43 → 44 → 45 → 46. Phase 41 (teams) intentionally lands after deterministic-floor hardening, mirroring Joan4U's HX sequencing rationale. Phase 42 can start any time after 35 if lane capacity exists. Phase 46 is sequenced after the proof package by default so vNext public readiness doesn't balloon, but it is independent of 43–45 and can be pulled forward into a parallel lane if D-9 says so.

**Independent audit checkpoints:** end of 34 (gate floor green), end of 38 (policy floor), end of 43 (upgrade path — also Codex-audited), Phase 45 (full).

---

## 8. Upgrade Path Architecture (the product centerpiece)

Decision: **split into five explicit layers** (not evolve the current monolith), because the audit proved the monolith conflates a working copy engine with an unimplemented cognition spec (F-03). The existing `/vibeos:upgrade` skill name, voice trigger ("update VibeOS" / "upgrade VOS"), and operator experience are preserved; the internals are rebuilt.

```
User: "update VibeOS"
        │
        ▼
┌─ L-A Deterministic migration engine (bash/python — WO-129/130/132)
│   detect installed version/surfaces/customizations/dirty git
│   locate/fetch new framework source
│   generate before/after inventory + classified delta (framework-manifest driven)
│   REFUSES to proceed on dirty git without explicit override
│
├─ L-B Claude cognition/recommendation layer (skill — WO-131)
│   evaluates delta against: product anchor, PRD, architecture, development plan,
│   WO schema, findings registry, baselines, custom gates, hooks/agents/skills,
│   runtime capability matrix
│   classifies: auto-apply | project-review | optional | blocked | incompatible
│   per-project selective adoption: new Claude capabilities (teams, workflows,
│   loops) adopt per-project via capability matrix + config flags, never globally
│
├─ L-C Project-owned preservation layer (manifest-driven — WO-129/132)
│   project-owned registry: docs/, .vibeos/config.json, baselines, findings,
│   checkpoints, evidence, custom gates, session/autonomy state
│   NEVER overwritten by default; migrations only with explicit user approval
│
├─ L-D Rollback/evidence layer (WO-132)
│   .vibeos/upgrade-reports/upgrade-[ts].md, upgrade manifest, before/after
│   inventory, recommendation ledger, rollback snapshot (byte-for-byte restore)
│   creates upgrade WOs for project-review adoption gaps (incl. doc-pyramid
│   migrations); runs gates+audits as discovery sweep, never baseline reset
│
└─ L-E Codex-compatible fallback layer (deferred design, shared L-A/C/D)
    deterministic layers run identically under Codex; L-B is replaced by a
    recommendations file the operator reviews; no parity claims
```

Acceptance criteria (verbatim adoption of the handoff's six, all testable via WO-133's fixture): never overwrites project-owned state by default; selective per-project capability adoption; recommendation ledger explains every applied/deferred/blocked/optional decision; creates WOs for local adoption gaps; smoke-tested against a fixture with custom gates, local docs, findings, and dirty-state protections; Codex parity kept separate from Claude-first upgrade support.

---

## 9. Public-Readiness Proof Checklist

Gate before any repo link or stronger public claim (synthesis of WO-121/WO-122/WO-130 requirements — all currently **unmet**):

1. ☐ Canonical repo decision: named repo, verified remote URL, intended public/private posture, clean worktree
2. ☐ Clean commit/tag representing the upgrade state (`git.public_tag_status` currently `not_selected` in the generated inventory)
3. ☐ Generated inventory regenerated at that tag; README/site claims match it exactly (stale counts — 11 capabilities / 13 agents / 30 scripts / 8 trees / 67 references — remain forbidden)
4. ☐ Fresh temp-repo install proof for Claude/Cursor AND Codex surfaces, limitations included
5. ☐ Runtime capability matrix regenerated post-WO-109 (the current one contains the F-02 false negative — it is itself an inaccuracy and unusable as proof)
6. ☐ Gate proof: green gate run, hook install output, secret scan pass, one failing→passing gate trace
7. ☐ Real sample execution trace: one genuine WO through plan→lanes→implementation→audit→evidence→handoff
8. ☐ Public-safe limitation statement (`docs/PUBLIC-LIMITATIONS.md`) + approved media asset (media is `latifhorstweb` WO-130's side)

Blocked-claim list stays in force throughout: production-ready autonomous development; Codex hook parity; full automatic write-time enforcement; 24–48h autonomy as general capability; TDD-improvement percentages; repo link before tag/install/proof.

---

## 10. Decisions Needed From Latif

| # | Decision | Status (2026-06-10) | Blocks |
|---|---|---|---|
| D-1 | Approve this master plan + Phases 34–46 as the governing plan | **APPROVED** — appended to DEVELOPMENT-PLAN.md and WO-INDEX.md | — |
| D-2 | Commit the uncommitted Codex slice (WO-106 et al.) + this plan document | **APPROVED — committed** | — |
| D-3 | Claim the Agent SDK monthly credit before 2026-06-15 (verified: headless/`claude -p` on subscription plans draws from it after that date) | **OPEN — operator action only**; deadline 2026-06-15 | WO-121 (night loop), any scheduled headless work |
| D-4 | Agent-team pilot (experimental, env-gated, never default) | **APPROVED**, scoped exactly to WO-125/126 | — |
| D-5 | Dynamic-workflows governed adoption per WO-123/124 | **APPROVED** | — |
| D-6 | Model policy shape: capability tiers resolved at runtime vs pinned model IDs | Standing recommendation: **tiers** (no objection raised; WO-118 proceeds on tiers) | — |
| D-7 | Product-anchor document approval for `docs/product/` | **OPEN** — core principles ratified 2026-06-10 (Eloquence, Efficiency, Security, Fidelity, Provability; precedence Security > Fidelity > Provability > Eloquence > Efficiency; lean-governance doctrine); full WO-134 draft still requires review | Phase 44 |
| D-8 | Canonical public repo + tag selection | **OPEN** — defer to Phase 45 entry | WO-137/138 |
| D-9 | Priority of Phase 46: after proof package (default) or pulled forward | **OPEN** — default stands (after 45); pull WO-140/141 forward if reuse pain outweighs drift pain | Phase 46 timing only |
| D-10 | Ingestion sandbox substrate | Standing recommendation: **local Docker** (no standing cost, no remote attack surface); VPS only if enterprise-shared vetting emerges | WO-142 detail only |

---

## 11. Exact Next Action for the Execution Model

1. ~~Wait for D-1/D-2~~ **Done 2026-06-10:** plan approved, slice + plan committed, Phases 34–46 appended to `DEVELOPMENT-PLAN.md` and `WO-INDEX.md`.
2. **Execute WO-107 first** (gate-runner tier fix). Author the WO file from the Section 7 row (with frontmatter once WO-111 lands; prose template until then). Single-file logic change + manifest migration + back-compat + tests. Verify with:
   ```bash
   bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure \
     --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos
   python3 -m pytest tests/test_gate_runner.py
   ```
3. Then WO-108 → WO-109 → WO-110 in order; run the Phase 34 audit checkpoint; do not begin Phase 35 until the gate floor runs green end-to-end.

Verdict-language reminder for all future status reporting: `planning-only` → `locally implemented` → `nonproduction proven` → `production/runtime approved` → `public-link ready`. Nothing in Phases 34–45 may claim a level it has not evidenced.
