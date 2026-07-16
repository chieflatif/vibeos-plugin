---
wo: WO-150
title: "Profile Install Name/TOML/Canon Integrity"
status: Complete
phase: 41
phase_name: Agent-Team Pilot
wo_class: harness
write_scope:
  - docs/planning/WO-150-profile-install-name-integrity.md
  - docs/planning/WO-INDEX.md
  - plugins/vibeos/scripts/profile_install.py
  - tests/test_profile_install.py
no_touch:
  - /Users/latifhorst/latifhorstweb/**
  - /Users/latifhorst/Joan4U/**
required_auditors:
  - correctness-auditor
  - test-auditor
model_policy: implementation
budget_posture:
  token_ceiling: null
  turn_ceiling: null
  cost_ceiling_usd: null
---

# WO-150: Profile Install Name/TOML/Canon Integrity

## Status

`Complete`

## Phase

Phase 41: Agent-Team Pilot (install-integrity remediation family, alongside WO-147)

## Objective

Eliminate the reproduced feedback loop where re-running `vibeos analyze` without a pinned profile ingests the generated `AGENTS.md` heading as the project name, which then breaks the active-surface audit on every generated Codex TOML and churns canon detection.

## Findings

Reproduced live on 2026-07-16 against fresh git repos (installer at commit 6e0227b):

1. `detect_project_name()` reads the first `#` heading of PROJECT.md → README.md → AGENTS.md. The installer's own generated `AGENTS.md` heading is `"{name} — VibeOS Project Surface"`, so an unpinned re-analyze adopts that string — em dash included — as the new project name.
2. `render_codex_toml()` embeds the project name via `json.dumps` (default `ensure_ascii=True`), producing `—` inside TOML strings. The generated active-surface audit does a literal substring check (`project not in text`) on the raw file, so every one of the 20 `.codex/agents/*.toml` files fails and `apply` exits 1.
3. `detect_canon()` returns any existing `CANON_CANDIDATES` path, including the generated `AGENTS.md`, changing `profile_hash` and churning ~97 files as replace-generated on re-analyze.
4. **Audit round 1 (red-team + correctness, same-tree) extended the defect class:** (a) the escaping mechanism also breaks for quotes/backslashes in project names — `json.dumps` escapes `"`→`\"` in TOML strings while the generated audit does a raw literal substring check, so `# The "Quoted" Project` as a README heading failed apply with 20 audit findings; the generated audit now accepts the string-escaped form too. (b) `ensure_ascii=False` emitted U+007F (DEL) raw, which TOML rejects — now re-escaped. (c) The first suffix-strip implementation over-matched (`MyVibeOS Project Surface` → "My"; trailing-dash mangling) — now strips only the exact generated form `<name> — VibeOS Project Surface` plus its degenerate bare variants. (d) `is_generated_file` tightened from substring-anywhere-in-line-1 to the exact marker prefixes. (e) A missing `--profile` path crashed with an unhandled `FileNotFoundError`; now a clear exit-2 message.

## Scope

### In Scope
- [x] `first_heading`/`detect_project_name`: skip files carrying the `VIBEOS-GENERATED` header; defensively strip a trailing `— VibeOS Project Surface` suffix
- [x] `render_codex_toml`: emit TOML strings with `ensure_ascii=False` so non-ASCII project names appear literally
- [x] `detect_canon`: exclude VIBEOS-generated files from canon candidates
- [x] Regression tests for all three defects

### Out of Scope
- Changing the audit's substring-check design
- Profile schema changes
- The legacy `vibeos-init.sh` flow

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| Profile-driven install (commit 6e0227b) | Feature under repair | Landed |

## Acceptance Criteria

- [x] AC-1: `detect_project_name` never returns a name sourced from a VIBEOS-generated file; a repo whose only heading source is the generated `AGENTS.md` falls back to the directory-name default
- [x] AC-2: A heading ending in `— VibeOS Project Surface` never becomes the project name even if the generated header is absent
- [x] AC-3: A project name containing an em dash renders literally in `.codex/agents/*.toml` and passes the generated active-surface audit
- [x] AC-4: `detect_canon` excludes VIBEOS-generated files; unpinned re-analyze over a prior install is idempotent on name and canon
- [x] AC-5: `python3 -m pytest tests/test_profile_install.py` and the full suite pass

## Anchor Alignment

Serves the profile-driven install promise: customization first, generated surfaces always project-native, upgrades stable under re-analyze. Protects the plan-first workflow (analyze output must be reviewable and stable, not self-polluting).

## Research & Freshness

No external dependencies. Behavior verified against local source only.

## Accepted Risks (documented, not fixed)

- **A merged generated `AGENTS.md` stays excluded from canon detection.** If a team adopts the generated surface as genuine project canon, `detect_canon` keeps skipping it while the line-1 marker remains. Rationale: the marker means "installer-owned"; a team promoting the file to canon should remove the generated header (at which point the lock machinery treats it as a local customization and canon detection sees it).
- **A user file whose first line starts with the literal marker prefix is skipped for name/canon detection.** Pathological (requires `<!-- VIBEOS-GENERATED` or `# VIBEOS-GENERATED` opening line 1 of a hand-written canon file); fail direction is a safe fallback to directory-name default.

## Test Strategy

Tests written from the defect spec before the fix: (1) generated-AGENTS.md-only repo yields directory-default name; (2) em-dash project name → TOML contains the literal name, audit passes; (3) canon detection ignores generated files; (4) double-analyze idempotency on name/canon.

## Evidence

- Pre-fix failure reproduced: `test_analyze_ignores_generated_agents_md_for_name_and_canon` failed with `'Widget — VibeOS Project Surface' != 'Sync Connector'` before the fix.
- Post-fix: 7 WO-150 regression tests green (generated-file exclusion, suffix precision, empty-heading fallback, re-analyze idempotency, em-dash TOML round-trip + audit pass, quoted-name audit pass, missing-profile exit 2).
- Full suite: `python3 -m pytest tests` → 258 passed (2026-07-16).
- Same-tree audits: correctness-auditor + red-team-auditor + test-auditor ran round 1; every actionable finding fixed in-scope (see Findings 4), residuals documented under Accepted Risks. Red-team verdict on this WO: "clean — fix real, tests discriminating, loop closure verified live."
