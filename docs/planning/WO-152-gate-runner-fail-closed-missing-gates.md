---
wo: WO-152
title: "Gate-Runner Fail-Closed on Missing Blocking Gates"
status: Complete
phase: 41
phase_name: Agent-Team Pilot
wo_class: harness
write_scope:
  - docs/planning/WO-152-gate-runner-fail-closed-missing-gates.md
  - docs/planning/WO-INDEX.md
  - plugins/vibeos/scripts/gate-runner.sh
  - plugins/vibeos/scripts/validate-file-size.sh
  - plugins/vibeos/scripts/validate-commit-msg.sh
  - .vibeos/scripts/validate-commit-msg.sh
  - tests/test_gate_runner.py
no_touch:
  - <separate-website-project>/**
  - <separate-product-project>/**
required_auditors:
  - correctness-auditor
  - red-team-auditor
model_policy: implementation
budget_posture:
  token_ceiling: null
  turn_ceiling: null
  cost_ceiling_usd: null
---

# WO-152: Gate-Runner Fail-Closed on Missing Blocking Gates

## Status

`Complete`

## Phase

Phase 41: Agent-Team Pilot (install-integrity remediation family, alongside WO-147)

## Objective

Stop `gate-runner.sh` from silently passing when a blocking-tier gate's script does not exist. Today `run_single_gate` emits `SKIP|<gate>|script_not_found|0` and the caller counts every SKIP as benign, so a manifest referencing uninstalled gates produces a green run that checked nothing — a false-green corruption vector in exactly the repos where the manifest and installed module set can diverge (profile installs, partial upgrades).

## Findings

1. `run_single_gate` (gate-runner.sh ~line 410): missing script → warn + `SKIP` + return 0.
2. Result loop SKIP branch (~line 601): all SKIPs increment `skipped` only; `blocking_failures` untouched; runner exits 0.
3. Legitimate skip semantics exist and must be preserved: gates skip-by-design by printing a `SKIP:` marker and exiting 0 (verified in `run_single_gate` — the result header's third field is `script_not_found` for missing scripts vs the numeric exit code for marker-skips, so the two are cleanly distinguishable).
4. **Discovered during TDD (worse than documented):** `warn` writes to stdout, and `run_single_gate`'s stdout is the parsed result contract — so for a missing script the WARN line displaced the `SKIP|...` header, the status fell through the result `case` unmatched, and the gate was silently *uncounted* (not even reported as SKIP). Fixed by redirecting that warn to stderr.
5. **Discovered during TDD (pre-existing, reproduced on unmodified HEAD):** the result-header extraction `printf ... | awk 'NR==1 {print; exit}'` takes SIGPIPE under `set -euo pipefail` once a gate's output exceeds the pipe buffer, aborting the entire phase mid-run (observed: `pre_commit` died at gate 4/10). Fixed with pure-bash string extraction and a guarded display pipe.
6. **Audit round 1 (red-team + correctness, same-tree) extended the same defect class:** (a) the marker-skip match `printf "$output" | grep -q 'SKIP:'` races SIGPIPE the same way — a marker-skip with large output was misclassified **PASS** (status inflation); replaced with a pure-bash substring match. (b) `validate-file-size.sh`'s exception-marker checks (`head | grep -q`, `grep -oE | head -1`) hit the identical race, making valid FILE-SIZE-EXCEPTION markers flakily report as HARD BREACH (root cause of the intermittent `tests/test_gate_floor.py` failure — `grep -q`/`head -1` exit on first match while the writer is still writing; timing-dependent); replaced with pure-bash `case`/`[[ =~ ]]` matching, verified deterministic over repeated runs. (c) Nonstandard manifest `blocking` values (`1`, `"yes"`) printed verbatim from `get_tier_info` and failed the shell's `true|True` comparison, silently demoting author-intended-blocking tiers — normalized to canonical `true`/`false` with unrecognized strings failing closed. (d) A defensive `*)` branch now counts unparseable result headers as failures instead of silently dropping them. (e) The display pipe's residual broken-pipe stderr noise is silenced.
7. **Fourth instance, caught live at commit time:** `validate-commit-msg.sh`'s subject extraction (`printf | awk 'NF>0 {print; exit}'`) hit the same SIGPIPE race on a longer commit body — the commit-msg hook died with exit 141 and **no output**, silently blocking the commit. Fixed with pure-bash extraction (both the plugin source and this repo's installed `.vibeos/` copy). Also found there: the emoji check used `grep -P`, which BSD grep lacks — a silent no-op on macOS since installation; replaced with python3, and the trailer check's grep pipe replaced with a line-anchored bash loop. Verified: long-body message passes 5/5 deterministically; missing-trailer and emoji messages now correctly fail.

## Scope

### In Scope
- [x] SKIP branch distinguishes reason `script_not_found`: for blocking tiers it counts as FAIL (increments `failed` and `blocking_failures`, prints `FAIL [BLOCKING] (script not found: <path>)`); non-blocking tiers keep SKIP with the existing warning
- [x] Marker-based skips (`SKIP:` output + exit 0) unchanged for all tiers
- [x] `run_single_gate` result contract kept clean: warnings go to stderr, stdout carries only the parseable result
- [x] Result-header extraction made SIGPIPE-safe (pure bash, no awk/cut pipes on large output; display pipe guarded)
- [x] Missing blocking script aborts the run without `--continue-on-failure`, consistent with FAIL behavior
- [x] Regression tests covering blocking-missing, non-blocking-missing, and marker-skip

### Out of Scope
- Manifest schema changes
- Baseline (`known_baselines`) logic
- Gate script inventory

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-107 | Gate-runner tier schema | Complete |
| WO-146 | Tests-pass recursion guard | Complete |

## Acceptance Criteria

- [x] AC-1: A blocking-tier gate whose script is missing causes exit 1 and appears as FAIL with a `script not found` reason
- [x] AC-2: A non-blocking-tier gate whose script is missing still reports SKIP and does not affect exit code
- [x] AC-3: A gate that skips via the `SKIP:` output marker (exit 0) still reports SKIP for all tiers
- [x] AC-4: `python3 -m pytest tests/test_gate_runner.py` and the full suite pass
- [x] AC-5: `bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos` still passes (no regression on the real manifest)

## Anchor Alignment

Serves the zero-corruption principle: a green gate run must mean the gates ran. Directly closes a red-team finding class (status inflation via vacuous manifests).

## Accepted Risks (documented, not fixed)

- **Empty phase exits 0.** A phase that resolves to zero gates passes. Rationale: an empty phase is an explicit manifest-author state, distinct from a configured gate whose script is missing; failing it would break legitimately gate-free phases. Mitigation lives in the plan skill's manifest-honesty rule (existence-check every wired script).
- **`includes:` dedup can re-tier an inherited gate.** An outer phase redefining an included blocking gate at tier 2 neutralizes fail-closed for that gate. Rationale: last-occurrence-wins dedup is the documented override mechanism; the redefinition is explicit manifest content, reviewable in diffs.
- **JSON abort omits the aborting gate from `gates[]`.** Consistent with the pre-existing FAIL-branch abort; the summary (`failed`, `blocking_failures`, `result: FAIL`) still carries the outcome. Changing the JSON shape is out of scope.

## Research & Freshness

No external dependencies. Bash 3.2 compatibility preserved (no bash-4 constructs introduced).

## Test Strategy

Tests written from spec before the fix: synthetic manifest with (a) blocking gate pointing at a nonexistent script → runner exits 1, output contains FAIL and `script not found`; (b) tier-2 gate pointing at a nonexistent script → exit 0, output contains SKIP; (c) gate script that prints `SKIP:` and exits 0 → SKIP, exit 0.

## Evidence

- Pre-fix failure reproduced: missing blocking script → exit 0, `Result: PASS`, gate entirely uncounted (`Total: 1 | Passed: 0 | Failed: 0 | Skipped: 0`) — confirmed by test-auditor's empirical HEAD-code run.
- Post-fix: 9 WO-152 regression tests green (blocking-missing text+JSON, non-blocking-missing, marker-skip both tiers, marker-skip large output, large-output survival, abort path, nonstandard blocking normalization, tier resolution canonicalization).
- `validate-file-size.sh` marker race: pre-fix flaky HARD BREACH on valid markers (reproduced under pipefail trace); post-fix 5/5 deterministic PASS runs.
- AC-5 real-manifest proof: `gate-runner.sh pre_commit --continue-on-failure` on this repo → `Total: 10 | Passed: 6 | Failed: 0 | Skipped: 4 | Result: PASS`; full suite 258 passed (2026-07-16).
