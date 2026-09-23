---
wo: WO-168
title: WorktreeCreate hook works in every repository (2.4.2)
status: In Progress
phase: 50
phase_name: Ambidextrous Lean Release
wo_class: harness
write_scope:
  - plugins/vibeos/hooks/scripts/worktree-scope-setup.sh
  - tests/test_worktree_create_hook.py
  - tests/test_companion_fallback_integration.py
  - plugins/vibeos/.claude-plugin/plugin.json
  - .claude-plugin/marketplace.json
  - docs/planning/WO-168-worktree-create-fix.md
  - docs/planning/WO-INDEX.md
  - docs/planning/DEVELOPMENT-PLAN.md
  - docs/evidence/WO-168/**
no_touch:
  - external-projects/**
required_auditors:
  - correctness-auditor
model_policy: implementation
budget_posture:
  token_ceiling: null
  turn_ceiling: null
  cost_ceiling_usd: null
---

# WO-168: WorktreeCreate hook works in every repository (2.4.2)

## Status

In Progress. Approved by Latif on 22 September 2026 as decision 6(a) of the 3.0 release proposal: "Ship 2.4.2 … now". His verbatim reply was "yes proceed". The approval record is `docs/evidence/ambidextrous-release/phase-2-design/LATIF-DECISION-2026-09-22.md` on branch `claude/vibeos-ambidextrous-release`.

## Objective

Claude Code isolated worktrees (`--worktree`, `EnterWorktree`, `isolation: worktree` subagents, background sessions) must work in every repository on a machine where the VibeOS plugin is installed at user scope, not only in VibeOS projects. The hook must honour the user's `worktree.baseRef` setting.

## Scope

Changes:
- `plugins/vibeos/hooks/scripts/worktree-scope-setup.sh`:
  - remove the project-scope guard for this hook only;
  - resolve the base ref from `worktree.baseRef`;
  - reopen an existing worktree of the same name instead of failing.
- A new spec-first test file.
- Version metadata moves to 2.4.2.

Discovered during verification (anchored here before the fix, test-only): on the 2.4.1 base, the fake Codex in `tests/test_companion_fallback_integration.py` never reads its stdin. The companion script writes the review prompt to it, so every test using that fixture deadlocks locally; one full-suite run hung for 44 minutes. WO-159 (Codex, candidate `d706d13`) diagnosed this and fixed it with one line, `sys.stdin.read()`. 2.4.2 carries that same line so the suite can be verified. The change is identical to WO-159's, so the later merge is a no-op.

Out of scope, recorded for 3.0:
- a `WorktreeRemove` hook;
- the default's 24-hour fetch of the default branch under `"fresh"`;
- `worktree.symlinkDirectories` and `worktree.sparsePaths`;
- Claude Code's worktree marker.

## Phase 0

- **Necessary?** Yes. Claude Code documents that a registered `WorktreeCreate` hook "replaces that default git behavior". It also documents that "if the hook fails or produces no path, worktree creation fails with an error" (https://code.claude.com/docs/en/hooks#worktreecreate). The hook sources `is-vibeos-project.sh` and exits 0 with empty stdout outside projects carrying `.vibeos/config.json` or `project-definition.json` (`worktree-scope-setup.sh:12-17`). Because the plugin is user-scoped (`~/.claude/plugins/installed_plugins.json`), every other repository loses isolated worktrees. Profile installs never write `.vibeos/config.json` (Phase 1 R1 §A.8), so they are affected too.
- **Exists?** Yes. The hook was added by WO-117. The installed plugin copy (`~/.claude/plugins/cache/vibeos/vibeos/2.2.0-0f0aeb5/hooks/scripts/worktree-scope-setup.sh`) differs from this file only in its `FRAMEWORK_VERSION` line.
- **Dependencies:** none new. The hook uses bash, git and jq, all already required.
- **Prior work:** WO-117 created the hook. Its test (`tests/test_team_governance_hooks.py:109-162`) forces `VIBEOS_FORCE_HOOKS=1`, so the non-VibeOS path was never tested.
- **Integrations:**
  - The Claude Code hook contract. The input carries `name` and `cwd` but not the base ref. The path goes on the last non-empty stdout line; other output goes to stderr.
  - `worktree.baseRef` (`"fresh"`, the default, means `origin/<default-branch>` with a fallback to `HEAD`; `"head"` means the current checkout's `HEAD`). It can be set in user, project and local settings, with precedence local > project > user.
  - Latif's `~/.claude/settings.json` sets `"baseRef": "head"`. The hook currently ignores it: `worktree-scope-setup.sh:53-56` always prefers `origin/HEAD`.
  - The default reopens an existing worktree of the same name; the hook fails instead (`:47-49`).

## Acceptance Criteria

1. In a git repository with no VibeOS marker and without `VIBEOS_FORCE_HOOKS`, the hook exits 0. The last stdout line is the absolute path of a new worktree at `.claude/worktrees/<name>` on branch `worktree-<name>`.
2. `worktree.baseRef: "head"` bases the worktree on the current checkout's `HEAD`, including unpushed commits.
3. `"fresh"`, or no setting, bases it on `origin/<default-branch>` when `refs/remotes/origin/HEAD` exists, and otherwise on `HEAD`.
4. Settings precedence is local (`.claude/settings.local.json`) over project (`.claude/settings.json`) over user (`~/.claude/settings.json`). A malformed settings file is ignored.
5. Requesting an existing worktree of the same name prints its path and exits 0.
6. An invalid name, or a `cwd` outside a git repository, exits non-zero with empty stdout.
7. VibeOS behaviour is preserved: `.vibeos/worktree-scopes.json` and gitignored `.worktreeinclude` matches are copied, and the existing WO-117 test passes.
8. The full test suite passes; `bash -n` is clean; WO lint and index validation pass.
9. A cross-vendor review (tier `engineering`, GPT-6 Sol, for a Claude-built change) passes and is recorded under `docs/evidence/WO-168/`.

## Checklist

- [x] C0: Phase 0 complete (above).
- [x] C1: Spec-first tests written and failing for the right reasons (13 of 14 red on the old hook; `docs/evidence/WO-168/red-tests.log`).
- [x] C2: Hook fixed; new and existing tests pass (19 passed; `green-tests.log`).
- [x] C3: Full suite passes: 436 passed, 95 subtests, Python 3.14.6 (`full-suite-run2.log`). `bash -n` and 118 JSON files are clean (`full-suite.log`); that run was aborted at a fixture deadlock, since fixed. WO lint and index pass.
- [ ] C4: Cross-vendor review passes; receipt recorded. (Rounds 1 to 3 and Latif's decision are in the review log; the confirmation review is pending.)
- [ ] C5: Version 2.4.2; PR opened; `vibeos-quality` CI green.
- [ ] C6: Merged to main and tagged `v2.4.2`.
- [ ] C7: The fixed hook mirrored into Latif's installed plugin cache, with the original set aside, and verified by running the hook in a non-VibeOS repository.

## Cross-vendor review log (GPT-6 Sol, engineering tier)

| Round | Candidate | Verdict | Findings and outcome |
|---|---|---|---|
| 1 | `07da733` | FAIL | F1 (high): a symlink to the main checkout was accepted as an existing worktree. F2: multi-line names passed validation. F3: a symlinked `.claude/worktrees` could redirect creation. F4 (low): stdout was not asserted exactly. All four fixed in `cc00379`. |
| 2 | `cc00379` | FAIL | F1 to F4 confirmed fixed. R2-1 (medium): a registered worktree whose `.git` link was missing could be reopened; fixed in `89fdca7` by requiring git to use the directory as a worktree. R2-2 (low, pre-existing in 2.4.1): a copy failure after `git worktree add` leaves a registered worktree. |
| 3 | `89fdca7` | FAIL | R2-1 confirmed fixed. The round-2 attempt to fix R2-2 (copying only missing files, including on reopen) caused R3-1 (a partially copied directory is never finished) and R3-2, a regression: a new worktree kept a stale tracked scope manifest. |
| Latif | — | Decision after three rounds | "OK": restore 2.4.1's copy behaviour (full copy on first creation, nothing on reopen), keep every security fix, record R2-2 as a known limit, run one confirmation review. |

**Known limit (R2-2, low, unchanged from 2.4.1):** if copying a scope manifest or `.worktreeinclude` file fails after `git worktree add`, the hook fails, but the worktree stays registered. A later reopen returns it as it is, without the missing files. That matches Claude Code's default reopen behaviour. The first failure's stderr names the file.

## Test Strategy

`tests/test_worktree_create_hook.py` runs the hook as Claude Code does, with a JSON payload on stdin, in hermetic temporary repositories. It uses a temporary `HOME`, no `VIBEOS_FORCE_HOOKS`, and a bare `origin` with `origin/HEAD` set, so both base-ref modes are observable. The WO-117 test stays unchanged.

## Evidence

`docs/evidence/WO-168/`: test logs and the review receipt.
