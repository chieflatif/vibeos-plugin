# Claude Code Handoff: VibeOS vNext Upgrade Audit and Master Plan

Date: 2026-06-10
Repo: `/Users/latifhorst/cursor projects/vibeos-plugin`
Primary runtime for this phase: Claude Code, latest available model
Execution policy: audit and planning only; do not implement upgrade code yet

## Operator Intent

Latif wants VibeOS upgraded around the latest Claude Code capabilities first, then Codex equivalence after the Claude-first design is correct. The two highest-value upgrade areas are:

1. Multi-agent orchestration: agent teams, dynamic workflows, subagents, worktrees, shared task state, and deterministic lane readiness.
2. Loop and command-driven execution: `/loop`, `/batch`, `/run`, `/verify`, headless `claude -p`, hooks, stop/continue/resume behavior, scheduled/night loops, recovery loops, and durable state.

The deliverable from this Claude pass is not a small patch. It is a comprehensive audit, architecture decision, document-pyramid rewrite plan, and detailed development plan that a smaller model can execute afterward.

Critical existing product capability to preserve and strengthen: the upgrade path. Latif has many projects already running VibeOS. In those projects, the desired operator flow is: open the project, tell Claude "update VibeOS" or "upgrade VOS", and have the installed project-local VibeOS runtime cognition engine review the new framework against that project's product anchor, development plan, custom gates, baselines, findings, runtime capabilities, and local constraints. The upgrade should then selectively adopt the parts that fit, preserve project-owned state, surface recommendations for risky or optional changes, and produce a rollbackable evidence report. Do not reduce upgrade to a blind file-copy operation.

## Start Commands

Run from this repo:

```bash
cd "/Users/latifhorst/cursor projects/vibeos-plugin"
claude --version
codex --version
bash plugins/vibeos/scripts/detect-runtime-capabilities.sh --project-dir .
python3 plugins/vibeos/scripts/generate-inventory.py --project-dir .
```

Use the latest available Claude model for the audit. As of the 2026-06-10 Codex handoff, local Claude Code reports `2.1.170`. Official docs say Claude Opus 4.8 is the latest/default frontier Claude Code model for eligible plans and supports high effort; verify live before relying on that claim.

Recommended interactive setup if available:

```text
/model claude-opus-4-8
/effort xhigh
/plan
```

If a newer model or command surface is available in the live Claude session, use the newer verified option and record the evidence.

## Mandatory Source Inputs

Read these first, in order:

1. `AGENTS.md`
2. `CLAUDE.md`
3. `README.md`
4. `docs/planning/DEVELOPMENT-PLAN.md`
5. `docs/planning/WO-INDEX.md`
6. `docs/planning/WO-106-vnext-generated-inventory-and-claim-ledger.md`
7. `docs/evidence/vnext/generated-inventory.json`
8. `/Users/latifhorst/Joan4U/docs/audits/DEVELOPMENT-HARNESS-AUDIT-AND-UPGRADE-BLUEPRINT-2026-06-09.md`
9. `/Users/latifhorst/Joan4U/docs/audits/DEVELOPMENT-HARNESS-AUDIT-EXECUTION-ADDENDUM-2026-06-09.md`
10. `/Users/latifhorst/Joan4U/docs/handoffs/2026-06-09-claude-code-harness-upgrade-kickoff.md`
11. `/Users/latifhorst/latifhorstweb/docs/planning/evidence-matrices/WO-122-vibeos-vnext-reconciliation.md`
12. `/Users/latifhorst/latifhorstweb/docs/planning/evidence-matrices/WO-121-vibeos-development-harness-readiness.md`
13. `/Users/latifhorst/latifhorstweb/docs/planning/work-orders/WO-130-vibeos-post-upgrade-public-amplification.md`

Do not modify `latifhorstweb` or `Joan4U` from this thread. They are read-only source inputs.

## Current Codex Slice Already Landed Locally

Codex added the first proof-foundation slice:

- `plugins/vibeos/scripts/generate-inventory.py`
- `tests/test_generate_inventory.py`
- `docs/planning/WO-106-vnext-generated-inventory-and-claim-ledger.md`
- `docs/evidence/vnext/generated-inventory.json`
- Phase 33 entries in `docs/planning/DEVELOPMENT-PLAN.md` and `docs/planning/WO-INDEX.md`
- Utility-script manifest entry in `plugins/vibeos/quality-gate-manifest.json`

Generated inventory currently reports:

- Claude/Cursor skills: 15
- Codex skills: 13
- Agents: 32
- Same-tree agents: 12
- Hook scripts: 12
- Documented hooks: 9
- Configured hook commands: 12
- Shared runtime scripts: 90
- Gate entries: 55
- Unique gate scripts: 47
- Decision files: 10
- Reference files: 122
- Test modules: 18
- Work orders: 109

The claim ledger intentionally blocks public claims for Codex hook parity, full automatic write-time enforcement across runtimes, and repo-link readiness.

## Current Verification From Codex

Passed:

```bash
bash plugins/vibeos/scripts/detect-runtime-capabilities.sh --project-dir .
python3 -m py_compile plugins/vibeos/scripts/generate-inventory.py tests/test_generate_inventory.py
python3 -m pytest tests/test_generate_inventory.py
python3 -m pytest tests/test_generate_inventory.py tests/test_runtime_capabilities.py tests/test_gate_runner.py
python3 -m pytest tests
jq . plugins/vibeos/quality-gate-manifest.json docs/evidence/vnext/generated-inventory.json >/dev/null
bash -n vibeos-init.sh vibeos-init-codex.sh plugins/vibeos/scripts/generate-inventory.py plugins/vibeos/scripts/gate-runner.sh plugins/vibeos/scripts/detect-runtime-capabilities.sh
git diff --check
```

Known blockers or pre-existing failures:

1. `bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos` fails before executing gates with `AttributeError: 'str' object has no attribute 'get'`. The runner expects tier objects; the manifest stores tier labels as strings.
2. `bash plugins/vibeos/scripts/validate-no-secrets.sh` fails on an existing AWS-looking fake key in `plugins/vibeos/test-fixture/src/app.py`.
3. Plain `python3 -m pytest` collects `plugins/vibeos/test-fixture/tests/test_app.py` and fails because `test_fixture` is not on `PYTHONPATH`. `python3 -m pytest tests` passes.

Treat these as audit findings unless your live investigation proves otherwise.

## Current Official Claude Code Capability Inputs To Refresh

Codex checked these official sources on 2026-06-10. Refresh them in Claude before finalizing the plan:

- Agent teams: https://code.claude.com/docs/en/agent-teams
  - Experimental, disabled by default, enable with `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`.
  - Claude Code v2.1.32+ required.
  - Use for independent Claude Code sessions with shared tasks and peer messaging.
- Dynamic workflows: https://code.claude.com/docs/en/workflows
  - Claude Code v2.1.154+ required.
  - Intended for large audits, migrations, and cross-checked research across many subagents.
- Agents/subagents comparison: https://code.claude.com/docs/en/agents and https://code.claude.com/docs/en/sub-agents
  - Subagents isolate context inside a session and return summaries.
  - Agent teams coordinate independent sessions.
  - Dynamic workflows run scripted fan-out and result checking.
- Skills and bundled commands: https://code.claude.com/docs/en/skills and https://code.claude.com/docs/en/commands
  - Custom commands have merged into skills.
  - Bundled skills include `/code-review`, `/batch`, `/debug`, `/loop`, and `/claude-api`.
  - `/run` and `/verify` exist for launching/verifying apps on Claude Code v2.1.145+.
- Hooks: https://code.claude.com/docs/en/hooks and https://code.claude.com/docs/en/hooks-guide
  - Hook lifecycle includes session, turn, tool, subagent/task, team idle, compaction, config, file, worktree, notification, and related events.
  - Command hooks are the production baseline.
  - Prompt and agent hooks exist; agent hooks are experimental.
- Agent SDK/headless: https://code.claude.com/docs/en/agent-sdk/overview and https://code.claude.com/docs/en/headless
  - SDK and `claude -p` expose Claude Code's agent loop programmatically.
  - Docs state subscription-plan Agent SDK and `claude -p` usage draws from a separate monthly Agent SDK credit starting 2026-06-15; verify if this still matters for the execution plan.
- Monitoring/OTel: https://code.claude.com/docs/en/monitoring-usage
  - Claude Code can export telemetry through OpenTelemetry for usage, cost, and tool activity.

## Mission For Claude

Perform a comprehensive VibeOS vNext upgrade audit and planning pass. The output must be execution-ready for a smaller model, but you should not implement the upgrade yet.

### Phase A: Current-System Audit

Audit this repo's actual current surface:

- Claude/Cursor assets: skills, agents, hooks, settings/reference material, bootstrap behavior.
- Codex assets: `AGENTS.md`, Codex reference skills, Codex bootstrap, capability detection, limitation language.
- Gate runner, quality manifest, hook manifest, secret scan, runtime capability detection, long-run autonomy scripts.
- Current docs: `README.md`, `CLAUDE.md`, `AGENTS.md`, `DEVELOPMENT-PLAN.md`, `WO-INDEX.md`, existing WO files, and proof artifacts.
- Generated inventory and claim ledger from WO-106.
- Existing upgrade path: `plugins/vibeos/skills/upgrade/SKILL.md`, `plugins/vibeos/scripts/plugin-upgrade.sh`, `vibeos-init.sh --upgrade`, `vibeos-init-codex.sh --upgrade`, and the related WO-039/WO-040/WO-055/WO-067/WO-073/WO-094 through WO-105 upgrade-surface references.

Produce findings first, with severity and evidence. Do not overclaim runtime behavior; prove it with command output or official docs.

### Phase B: Joan4U Plan Reconciliation

Reconcile this repo against the Joan4U U1-U7 upgrade targets:

- U1 machine-readable WO/frontmatter contracts
- U2 automated lane-readiness gate
- U3 agent-team batches
- U4 lane/night/recovery loops
- U5 model/effort policy
- U6 drift management
- U7 harness hygiene

For each target, classify:

- already present
- partially present but insufficient
- missing
- should be redesigned for VibeOS product-neutral use
- should stay Claude-only
- should later get Codex equivalence
- should be rejected as unsafe or overclaim-prone

### Phase C: Latest-Claude Capability Architecture

Design the Claude-first vNext architecture around the latest verified Claude Code capabilities:

- Agent teams for coordinated independent sessions.
- Dynamic workflows for large fan-out audits/migrations/research sweeps.
- Custom subagents for context-isolated specialist work.
- Worktree isolation for file-system safety.
- `/loop`, `/batch`, `/run`, `/verify`, `/plan`, `/model`, `/effort`, `/workflows`, `/agents`, `/permissions`, and related commands where appropriate.
- Hook lifecycle modernization, including command hooks as production baseline and careful evaluation of prompt/agent/HTTP hooks.
- Headless `claude -p` and Agent SDK for deterministic lane-readiness, scheduled audit, and recovery execution where justified.
- OTel/cost capture for model/cost/usage evidence.

Make hard distinctions between:

- deterministic enforcement floor
- Claude orchestration ceiling
- experimental features
- production-safe features
- Codex-equivalent or Codex-fallback behavior

### Phase D: Document Pyramid Redesign

Propose a clean document pyramid for this repo. At minimum define, and where appropriate draft outlines for:

- Vision: what VibeOS is becoming.
- Product anchor: the product promise and anti-goals.
- PRD: the user-facing and operator-facing product requirements.
- Architecture: Claude-first runtime architecture, Codex compatibility layer, enforcement floor.
- Infrastructure/runtime manifest: commands, hooks, skills, agents, workflows, scheduler/headless paths, environment assumptions.
- Development plan: phase-by-phase WOs from audit to vNext proof and public readiness.
- Work order schema: machine-readable frontmatter and generated scope/agent/gate behavior.
- Proof package spec: generated inventory, install proof, runtime matrix, gate/hook/secret scan, sample execution trace, limitation statement, tag/release proof, website/media handoff.
- Upgrade path spec: how an installed VibeOS project reviews a new framework release, classifies applicable changes, selectively applies framework-owned changes, preserves project-owned state, creates WOs for project-specific adoption work, and reports rollback evidence.
- Public limitation statement: clear language around Claude vs Codex, hook parity, autonomy limits, and private assets.

Do not casually rewrite docs yet unless Latif explicitly asks for implementation. The deliverable is the planned doc pyramid, recommended files, and exact migration steps.

### Phase E: Comprehensive Development Plan

Create a detailed execution plan suitable for smaller-model implementation:

- numbered phases
- numbered WOs
- dependencies
- file scopes
- acceptance criteria
- exact tests/gates/proof commands
- expected artifacts
- no-touch boundaries
- implementation order
- independent audit checkpoints
- public-readiness gates

The first execution WOs should likely be:

1. Fix gate-runner/manifest tier-schema mismatch.
2. Resolve or quarantine the embedded fixture secret-scan failure.
3. Define the machine-readable WO schema and migration plan.
4. Generate scope/agent/gate configs from WO frontmatter.
5. Build lane-readiness automation.
6. Modernize Claude hooks around current lifecycle events.
7. Add agent-team pilot plan and evidence model.
8. Add dynamic-workflow discovery and bounded first use.
9. Add loop/headless/SDK execution wrappers with ceilings.
10. Add model/effort/cost policy and OTel evidence.
11. Finish drift/hygiene gates.
12. Redesign the upgrade path as a project-local cognition review and selective migration flow.
13. Produce independent vNext audit and public proof package.

Revise this order if your audit finds a stronger dependency path.

### Phase F: Upgrade Path Architecture

Design the vNext upgrade path as a first-class product feature. It must support the existing installed-project workflow:

```text
User in an existing VibeOS-governed project: "Update VibeOS"
Claude/VibeOS in that project:
1. Detect installed VibeOS version, surfaces, project-owned state, customizations, dirty git state, and runtime capabilities.
2. Locate or fetch the newer VibeOS framework source.
3. Generate a before/after inventory and release delta.
4. Evaluate the delta through the project's local cognition engine: product anchor, PRD, architecture, development plan, WO schema, findings registry, baselines, custom gates, hooks, agents, skills, and runtime capability matrix.
5. Classify every candidate change as auto-apply, project-review, optional, blocked, or incompatible.
6. Apply only framework-owned safe changes automatically.
7. Preserve project-owned docs, WOs, baselines, findings, checkpoints, evidence, and custom gates unless the user explicitly approves a migration.
8. Create upgrade WOs for project-specific adoption work.
9. Run gates and audits as a discovery sweep, not as a hidden baseline reset.
10. Write `.vibeos/upgrade-reports/upgrade-[timestamp].md`, upgrade manifest, before/after inventory, recommendation ledger, and rollback snapshot.
```

The audit should decide whether to evolve the current `/vibeos:upgrade` skill, `plugin-upgrade.sh`, bootstrap `--upgrade` modes, and Codex upgrade path into one coherent mechanism or split them into clear layers:

- deterministic migration engine
- Claude cognition/recommendation layer
- project-owned state preservation layer
- rollback/evidence layer
- Codex-compatible fallback layer

Acceptance criteria for the future implementation plan:

- Upgrade never overwrites project-owned state by default.
- Upgrade can selectively adopt new Claude Code capabilities per project rather than enabling every new feature globally.
- Upgrade produces a recommendation ledger explaining why each major change was applied, deferred, blocked, or left optional.
- Upgrade can create new WOs for local adoption gaps, including docs pyramid migrations.
- Upgrade can be smoke-tested in a fixture project with custom gates, local docs, existing findings, and dirty-state protections.
- Upgrade keeps Codex parity/equivalence separate from Claude-first upgrade support.

## Hard Boundaries

- Do not touch `latifhorstweb` or `Joan4U`; read-only only.
- Do not implement runtime changes in this handoff phase unless Latif explicitly changes the instruction.
- Do not claim Claude agent-team or dynamic-workflow readiness without live/version/config proof.
- Do not claim Codex parity. Codex equivalence comes after the Claude-first architecture is defined.
- Do not claim 24-48 hour autonomy without durable proof.
- Do not use old VibeOS5 counts as current facts.
- Do not expose or print secrets.
- Preserve existing uncommitted Codex slice work unless Latif tells you to reset or commit it.

## Required Claude Output

Return a single comprehensive planning package with:

1. Findings-first current-system audit.
2. Latest Claude Code capability matrix with official-source citations and local command evidence.
3. U1-U7 reconciliation table.
4. Claude-first vNext architecture proposal.
5. Codex equivalence/fallback strategy, explicitly deferred after Claude plan.
6. Document pyramid redesign and migration plan.
7. Detailed development plan with WOs, scopes, tests, gates, and proof artifacts.
8. Upgrade path architecture and selective-adoption plan for existing VibeOS projects.
9. Public-readiness proof checklist.
10. Decisions needed from Latif.
11. Exact next action for the smaller execution model.

Verdict language must be precise:

- `planning-only`
- `locally implemented`
- `nonproduction proven`
- `production/runtime approved`
- `public-link ready`

Do not blur these states.
