---
wo: WO-147
title: "Plugin Install Integrity Remediation (stale + broken marketplace cache)"
status: Draft
phase: 41
phase_name: Agent-Team Pilot
wo_class: harness
write_scope:
  - docs/planning/WO-147-plugin-install-integrity-remediation.md
  - docs/planning/WO-INDEX.md
  - docs/evidence/vnext/wo-147-plugin-install-integrity/**
  - docs/evidence/vnext/generated-inventory.json
  - plugins/vibeos/scripts/validate-plugin-package.sh
  - plugins/vibeos/quality-gate-manifest.json
  - plugins/vibeos/.claude-plugin/plugin.json
  - plugins/vibeos/agents/system-invariant-auditor.md
  - .claude-plugin/marketplace.json
  - tests/test_plugin_package_integrity.py
no_touch:
  - /Users/latifhorst/latifhorstweb/**
  - /Users/latifhorst/Joan4U/**
required_auditors:
  - correctness-auditor
  - evidence-auditor
model_policy: implementation
budget_posture:
  token_ceiling: null
  turn_ceiling: null
  cost_ceiling_usd: null
---

# WO-147: Plugin Install Integrity Remediation

## Status

`Draft` — proposed remediation awaiting Latif's approval (new validator gate + release/install change = "you propose, I approve").

## Phase

Discovered during Phase 41 (Agent-Team Pilot). The durable packaging-validator portion is adjacent to Phase 43 (WO-129 framework-ownership manifest, WO-133 upgrade fixture smoke test) and must be reconciled with them — see *Relationship to Phase 43*.

## Objective

Make the **runtime plugin equal the dev tree**. Today every Claude Code session on this machine loads a stale, internally-broken cached package, so none of the local 2.2.0 vNext enforcement actually runs. Fix the install and add a deterministic packaging-completeness gate so a broken release cannot ship or load silently again.

## Source Evidence

Full diagnostic: [install-gap-evidence.json](../evidence/vnext/wo-147-plugin-install-integrity/install-gap-evidence.json). Surfaced by the WO-126 agent-team pilot (Terminal arm threw non-blocking hook errors on nearly every tool call).

**Install scope:** `vibeos@vibeos` is enabled at **user scope** in `~/.claude/settings.json` and installed once at `~/.claude/plugins/cache/`. It is **system-wide** — every repository and session on this machine loads the one shared engine. Per-repo state (`.vibeos/`, `docs/planning/`, WO files) is separate; the engine is global, the work is per-project.

**Three defects:**

1. **Broken release (critical, installed).** The installed 1.0.5 `hooks.json` references 5 scripts — `governance-guard.sh`, `proof-protection.sh`, `file-budget.sh`, `worktree-bash-guard.sh`, `worktree-scope-guard.sh` — that are **not in the package**. Every `PreToolUse` fires them and hits `No such file or directory` (non-blocking). The enforcement hooks are inert at runtime. The desktop app loads the same install but does not surface the non-blocking errors.

2. **Stale release (critical, installed).** 1.0.5 is `FRAMEWORK_VERSION 1.0.0` and predates all of vNext (Phases 34–46, WO-107..146). It does not register the team-governance hooks (WO-117) at all and ships none of the vNext scripts. The local dev tree is 2.2.0 and complete.

3. **Local source not install-ready (high, dev tree).** `claude plugin validate plugins/vibeos` **fails**: `plugins/vibeos/agents/system-invariant-auditor.md` has YAML frontmatter that fails to parse (the `description:` value contains a colon-space — `"…system invariants: rules…"` — which YAML reads as a nested mapping). The agent loads with **empty metadata** at runtime. This must be repaired before either update path, or the published/loaded 2.2.0 plugin ships a broken invariant-auditor. (`marketplace.json` itself validates ✔.)

**The publish gap (why a plain update won't reach 2.2.0):** `origin` is the marketplace source `chieflatif/vibeos-plugin`. The installed commit `21236f92` is **47 commits** behind local HEAD; the vNext work sits on branch `codex/vibeos-vnext-continuation`, and local `main` is itself 5 commits ahead of `origin/main`. **GitHub's main does not have 2.2.0** (catalog last refreshed 2026-03-11). So `claude plugin update vibeos@vibeos` today pulls the old GitHub version — the new engine exists only on this laptop.

**Correction this WO records:** WO-126's `D-TEAM-1` concluded "this Claude Code build does not emit team-lifecycle hook events." That is **not proven** — the installed 1.0.5 never registered those events or shipped `team-governance.sh`, so the local team-governance wiring was never loaded. Whether the runtime emits team events remains an **open question** answerable only after the current-source plugin is installed and a team arm is re-run.

## Scope

### In Scope
- [ ] Record the install-vs-dev-tree gap as evidence (done: `install-gap-evidence.json`)
- [ ] **Make the source install-ready:** fix the `system-invariant-auditor` frontmatter (defect 3) so `claude plugin validate plugins/vibeos` passes
- [ ] **Immediate fix:** make `vibeos@vibeos` resolve to current 2.2.0 source — via a local-dev marketplace pointing at this repo (preferred for ongoing dogfooding) and/or a clean repackage+reinstall. Operator-executed step (restart required); this WO documents the exact procedure (Path A / Path B above) and verifies the result.
- [ ] **Durable defense:** `validate-plugin-package.sh` — a deterministic gate asserting that (a) every script referenced by `hooks.json` exists in the package, (b) `plugin.json` version and `FRAMEWORK_VERSION` are consistent and not behind the dev tree, (c) no dangling hook command paths.
- [ ] Register the gate in `quality-gate-manifest.json` (release/packaging tier)
- [ ] Known-good / known-bad fixtures for the gate
- [ ] Post-fix verification: a fresh session loads 2.2.0 hooks with **zero** hook errors; `.vibeos/team-governance/` can be created when team events fire

### Out of Scope
- The full Phase 43 upgrade engine (framework-ownership manifest, delta engine, apply/rollback) — this WO is the narrow install-integrity remediation only
- Re-running the WO-126 team arm (separate follow-up once the plugin is fixed)
- Enabling agent teams by default; any production-readiness / parity / autonomy claim
- Website changes

## Proposed Fix Design

**Prerequisite for both paths:** fix defect 3 (quote the `system-invariant-auditor` description) so `claude plugin validate plugins/vibeos` passes.

**Path A — Publish then update (release path):**
1. Fix the frontmatter; confirm `claude plugin validate plugins/vibeos` passes.
2. Merge the vNext branch to `main`; push to `chieflatif/vibeos-plugin`.
3. `claude plugin tag` — cuts a `{name}--v{version}` tag, validating `plugin.json` and the marketplace entry agree.
4. `claude plugin marketplace update vibeos` → `claude plugin update vibeos@vibeos` → restart to apply.
- Result: 2.2.0 installed system-wide, reproducible, installable by anyone. Best for a real release.

**Path B — Local-dev marketplace (dogfooding path, fastest):**
1. Fix the frontmatter.
2. `claude plugin marketplace add "/Users/latifhorst/cursor projects/vibeos-plugin"` (marketplace.json `source: ./plugins/vibeos` → the 2.2.0 plugin).
3. Install/enable vibeos from the local marketplace; disable/uninstall the stale GitHub-sourced install so they don't collide; restart.
- Result: runtime == local working tree (2.2.0), live. Best while actively building vNext.

Both are **system-wide** once enabled in user settings, and applying an install change **requires restarting Claude Code** — so these steps are operator-run, not agent-run. Verify success: a fresh session shows no `No such file or directory` hook errors and `governance-guard`/`file-budget`/`proof-protection` resolve.

**Built-in guards to lean on:** `claude plugin validate <path>` (caught defect 3) and `claude plugin tag` (version/marketplace agreement at release).

**Durable defense (prevent recurrence):** `validate-plugin-package.sh`
- Input: a plugin package root (default `plugins/vibeos`).
- Checks the gap the built-ins don't: parse `hooks/hooks.json`; for every `command` referencing `${CLAUDE_PLUGIN_ROOT}/.../*.sh`, assert the file exists in the package; assert `plugin.json.version` and `FRAMEWORK_VERSION` agree with the repo's declared version; flag any event registered with a missing handler.
- Exit: 0 = complete; 1 = dangling reference or version skew; 2 = config error.

## Relationship to Phase 43

WO-129 (framework-ownership manifest) and WO-133 (upgrade fixture smoke test) are the broad, generated defenses for this whole class. WO-147 is the **narrow, urgent** fix: it unblocks all current dogfooding now and installs the minimal hook-reference/version check. When Phase 43 lands, `validate-plugin-package.sh` should be folded into / superseded by the framework-ownership manifest rather than duplicated.

## Acceptance Criteria
- [ ] AC-1: Evidence documents the stale + broken install with exact missing-script list
- [ ] AC-2: `system-invariant-auditor` frontmatter fixed; `claude plugin validate plugins/vibeos` passes
- [ ] AC-3: After the fix, a fresh Claude Code session loads the 2.2.0 plugin with zero hook errors
- [ ] AC-4: `validate-plugin-package.sh` fails the known-bad fixture (dangling hook ref and/or version skew) and passes the known-good
- [ ] AC-5: Gate registered in `quality-gate-manifest.json`; inventory reconciled
- [ ] AC-6: D-TEAM-1's open question is restated (runtime team-event emission untested) so the team arm can be re-run cleanly

## Test Strategy
- **Focused:** `python3 -m pytest tests/test_plugin_package_integrity.py`
- **Gate:** `bash plugins/vibeos/scripts/validate-plugin-package.sh --package plugins/vibeos`
- **Index:** `python3 plugins/vibeos/scripts/wo-frontmatter-lint.py validate-index --project-dir .`
- **Full suite + pre_commit gate** before completion.

## Remaining Limitations
- The immediate reinstall is an operator action outside the repo (`~/.claude/plugins`); this WO documents and verifies it but cannot perform it via repo writes alone.
- This WO does not test whether the runtime emits team-lifecycle hook events; that requires a re-run of the WO-126 team arm against the fixed install.
