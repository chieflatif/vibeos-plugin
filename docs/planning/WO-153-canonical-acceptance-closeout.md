---
wo: WO-153
title: "Canonical Acceptance Closeout"
status: Complete
phase: 41
phase_name: Agent-Team Pilot
wo_class: harness
write_scope:
  - docs/planning/WO-153-canonical-acceptance-closeout.md
  - docs/planning/WO-INDEX.md
  - docs/planning/DEVELOPMENT-PLAN.md
  - docs/planning/REUSABLE-RELEASE-AMENDMENT-2026-09-16.md
  - docs/planning/WO-132-reusable-release-amendment.md
  - docs/FILE-INVENTORY.md
  - docs/release/2.3.2.md
  - docs/evidence/vnext/generated-inventory.json
  - README.md
  - vibeos-init.sh
  - vibeos-init-codex.sh
  - .claude-plugin/marketplace.json
  - plugins/vibeos/.claude-plugin/plugin.json
  - plugins/vibeos/**
  - plugins/vibeos/scripts/validate-canonical-closeout.py
  - plugins/vibeos/scripts/profile_install.py
  - plugins/vibeos/scripts/plugin-upgrade.sh
  - plugins/vibeos/quality-gate-manifest.json
  - plugins/vibeos/reference/parallel-worktree-execution.md
  - plugins/vibeos/reference/governance/AGENTS.md.ref
  - plugins/vibeos/reference/codex/AGENTS.md.ref
  - plugins/vibeos/skills/build/SKILL.md
  - tests/test_canonical_closeout.py
no_touch:
  - external-projects/**
required_auditors:
  - correctness-auditor
  - red-team-auditor
model_policy: implementation
budget_posture:
  token_ceiling: null
  turn_ceiling: null
  cost_ceiling_usd: null
---

# WO-153: Canonical Acceptance Closeout

## Status

`Complete`

## Finding

An accepted product baseline can pass implementation and acceptance checks while
remaining only in a temporary worktree, topic branch or archive. Existing VibeOS
controls govern implementation isolation and pre-merge quality, but did not make
remote-default promotion plus fresh-clone readback a mandatory acceptance close.

## Objective

Make accepted-state adoption explicit and fail closed. Product source is not the
current reusable baseline until its exact accepted commit is reachable from the
remote default branch and a fresh clone carries the bound manifest and front
doors. Evidence-only acceptance remains distinct and must bind an exact artifact
and digest on the remote default branch.

## Acceptance Criteria

- [x] A product-source manifest fails while its accepted commit exists only on a topic branch.
- [x] The same manifest passes after that commit reaches the remote default branch.
- [x] Evidence-only closeout verifies an exact artifact digest without promoting product source.
- [x] An unpushed manifest, missing front door or mismatched digest fails closed.
- [x] Installed VibeOS project surfaces carry the validator and the shared closeout rule.
- [x] Build and parallel-worktree guidance distinguish implementation completion from canonical adoption.

## Evidence

- Joan incident reproduction: accepted product source remained outside GitHub
  `main` until a separate canonicalization repair and fresh-clone proof.
- `python3 -m pytest tests/test_canonical_closeout.py`
- Full repository suite and pre-commit gate recorded in the release commit.

## Research And Reuse

This control composes Git's existing commit ancestry, remote default branches and
fresh clones. It adds no release service, registry or product runtime. Current
GitHub Actions versions remain a project CI concern, not part of this validator.
