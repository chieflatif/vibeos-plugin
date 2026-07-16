---
wo: WO-151
title: "Profile-Installed Target Support in Plugin Skills"
status: Complete
phase: 41
phase_name: Agent-Team Pilot
wo_class: harness
write_scope:
  - docs/planning/WO-151-profile-target-skill-support.md
  - docs/planning/WO-INDEX.md
  - plugins/vibeos/skills/discover/SKILL.md
  - plugins/vibeos/skills/plan/SKILL.md
  - plugins/vibeos/skills/comp/SKILL.md
  - plugins/vibeos/skills/checkpoint/SKILL.md
  - plugins/vibeos/skills/upgrade/SKILL.md
  - plugins/vibeos/skills/build/SKILL.md
  - plugins/vibeos/skills/wo/SKILL.md
no_touch:
  - /Users/latifhorst/latifhorstweb/**
  - /Users/latifhorst/Joan4U/**
required_auditors:
  - correctness-auditor
  - product-drift-auditor
model_policy: implementation
budget_posture:
  token_ceiling: null
  turn_ceiling: null
  cost_ceiling_usd: null
---

# WO-151: Profile-Installed Target Support in Plugin Skills

## Status

`Complete`

## Phase

Phase 41: Agent-Team Pilot (install-integrity remediation family, alongside WO-147)

## Objective

Make the plugin's skills executable in profile-installed target repos, which deliberately do not carry `.vibeos/decision-engine/`, `.vibeos/reference/`, or `.vibeos/convergence/` (dormant payload). Today the skills hard-reference those target-relative paths, so `/vibeos:plan` and friends dead-end in exactly the repos the new install flow produces — and both obvious workarounds (copy payload in; install in `full` mode) defeat the flow's design and trip the generated active-surface audit.

## Findings

1. `skills/plan/SKILL.md` reads decision trees from `.vibeos/decision-engine/` (lines ~365, 480) and templates from `.vibeos/reference/governance/` (lines ~482, 524+); `skills/discover/SKILL.md` references `.vibeos/decision-engine/` and `.vibeos/reference/` throughout; `skills/comp/SKILL.md` references `.vibeos/reference/comp/`; `skills/checkpoint/SKILL.md` and `skills/plan/SKILL.md` shell out to `.vibeos/convergence/baseline-check.sh`. **Audit round 1 (red-team + correctness, same-tree) added:** `skills/build/SKILL.md` has nine `.vibeos/convergence/` shell-outs (baseline-check create/check/ratchet, state-hash ×2, convergence-check, migrate-baseline) and `skills/wo/SKILL.md` reads `.vibeos/reference/governance/WO-TEMPLATE.md.ref` — the flagship skills a profile-installed user hits first.
1b. **Audit round 1 also found two literal instructions that fail when followed:** (a) the upgrade snippet referenced `vibeos-profile.json`, a file nothing creates — the installer's pinned profile is `.vibeos/project-profile.json`, and a missing `--profile` path crashed with an unhandled traceback (friendly exit-2 error added under WO-150); (b) `"<source>/vibeos"` doesn't exist for the recorded source — install-plan `.source` is the resolved plugin root, so the installer must be invoked as `python3 "$SOURCE/scripts/profile_install.py"`. Both corrected, plus: upgrade Step 7 redirect now flags missing classic-state files as expected for profile repos, the lock-aware merge rule exempts the JSON manifest (no comment injection) and requires the generated header to stay on line 1, and resolution snippets gained the `${CLAUDE_PLUGIN_ROOT}` fallback and a hard resolution-failure error.
2. Profile installs record the absolute framework source path in `.vibeos/install-plan.json` (`.source`), so targets can always resolve framework assets without carrying them.
3. `skills/upgrade/SKILL.md` copies decision-engine/reference/convergence into the target — in a profile-installed repo this plants un-opted-in dormant payload that the active-surface audit correctly fails.
4. `/vibeos:plan` regenerates `AGENTS.md`, `.claude/CLAUDE.md`, and `.claude/quality-gate-manifest.json`, which in profile-installed repos are hash-locked installer files tracked in `.vibeos/install-lock.json`; without guidance the plan step clobbers them and future upgrades surface confusing merge candidates.
5. `gate-runner.sh` skips missing gate scripts (WO-152), so a stack-tuned manifest referencing gates absent from the installed module set passes vacuously; the plan skill must existence-check what it wires in.

## Scope

### In Scope
- [x] A standard **Framework Asset Resolution** convention in the affected skills: project-local `.vibeos/<asset>` (classic installs) → framework source from `.vibeos/install-plan.json` `.source` (accepting repo-root or `plugins/vibeos` forms) → `${CLAUDE_PLUGIN_ROOT}`; never copy dormant payload into a profile-installed target
- [x] Convergence-script command snippets in plan/checkpoint resolve through the same order
- [x] Upgrade skill: profile-installed guard — if `.vibeos/install-lock.json` exists, refuse the copy-payload path and route to `vibeos analyze`/`apply` from the newer source with the pinned profile
- [x] Plan skill: lock-aware output rule — merge into VIBEOS-generated `AGENTS.md`/`.claude/CLAUDE.md`/gate manifest preserving the generated header, existence-check every manifest `script` path, and re-run the active-surface audit before finishing
- [x] Discover skill: same resolution convention for its template reads

### Out of Scope
- Rendering richer generated skills from `profile_install.py` (the thin-wrapper design stands)
- gate-runner behavior (WO-152)
- Convergence script internals

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| Profile-driven install (commit 6e0227b) | Feature under repair | Landed |
| WO-152 | Complements manifest honesty | Complete |

## Acceptance Criteria

- [x] AC-1: Every skill that reads decision-engine/reference/convergence assets (plan, discover, comp, checkpoint, upgrade, **build, wo**) carries the resolution convention and no longer assumes target-local payload — verify with `grep -rn '"\.vibeos/convergence\|\.vibeos/reference/governance/WO-TEMPLATE' plugins/vibeos/skills/` (expect zero unresolved command references)
- [x] AC-2: `grep -rn "cp .*decision-engine\|cp -R .*reference" plugins/vibeos/skills/` shows payload copying only inside the classic-install branch of upgrade, gated behind an explicit install-lock check
- [x] AC-3: Plan skill instructs lock-aware merge + manifest script existence check + active-surface audit re-run for profile-installed targets
- [x] AC-4: No skill instructs creating `.vibeos/reference|decision-engine|convergence` in a profile-installed target
- [x] AC-5: All skill files remain valid (frontmatter intact), no placeholders introduced

## Anchor Alignment

Serves the profile-driven install promise directly: target repos stay free of generic dormant payload while retaining the full planning methodology. Protects the plan-first, audit-enforced workflow in the exact repos the flow creates.

## Research & Freshness

No external dependencies; resolution order verified against `profile_install.py` (`build_plan` writes `source`; `resolve_source` accepts repo root or `plugins/vibeos`).

## Test Strategy

Documentation/instruction WO — deterministic test waiver per WO-TEMPLATE doc-only rule. Verification is by assertion commands: grep checks in AC-2/AC-4, frontmatter lint, and manual read-through of each inserted section.

## Evidence

- AC-1 grep: `grep -rn '".vibeos/convergence' plugins/vibeos/skills/ | grep -v VIBEOS_ASSETS` → empty; wo-skill template read carries the resolution order; resolution sections present in plan, discover, comp, checkpoint, build.
- AC-2 grep: payload `cp` commands exist only in upgrade Step 4, behind an executable `install-lock.json` guard that exits 1 on profile-installed targets.
- Frontmatter lint: `wo-frontmatter-lint.py lint` → PASS (2026-07-16).
- Audit round 1 (red-team + correctness) findings all reconciled: build/wo coverage added, `vibeos-profile.json`→pinned-profile correction, plugin-root installer invocation, Step-7 prerequisite note, JSON-manifest comment-injection exemption, header-on-line-1 rule, CLAUDE_PLUGIN_ROOT fallback + hard resolution error.
