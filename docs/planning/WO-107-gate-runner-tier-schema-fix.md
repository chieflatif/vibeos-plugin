# WO-107: Gate-Runner Tier-Schema Fix

## Status

`Complete` — deliverable implemented and real-path verified. Note: the Phase 34 gate floor is **not yet green** (by design — it goes green only at the Phase 34 audit checkpoint after WO-108/109/110 and a file-size refactor). See "Known Out-of-Scope Failures" below.

## Phase

Phase 34: Foundation Repair (everything else is blocked on this)

## Objective

Repair the gate-runner so the `pre_commit` phase executes all 10 gates end-to-end. The runner currently aborts with `AttributeError: 'str' object has no attribute 'get'` because `get_tier_info()` assumes every tier definition is an object, while the live `quality-gate-manifest.json` stores tier definitions as plain strings. Migrate the live manifest tier definitions to the object schema `{"label", "blocking", ...}` (matching the already-correct reference manifest) AND make the runner tolerate legacy string tiers so installed projects that have not migrated keep working.

## Scope

### In Scope
- [x] Fix `get_tier_info()` in `plugins/vibeos/scripts/gate-runner.sh` to handle object tiers, legacy string tiers (blocking inferred from `tier <= 1`), and missing tiers
- [x] Add a small `--print-tier N` testability hook to the runner so tier resolution can be unit-tested deterministically
- [x] Migrate `plugins/vibeos/quality-gate-manifest.json` tier definitions from strings to objects `{"label", "blocking", "description"}`, preserving blocking semantics (tiers 0–1 blocking, 2–3 advisory)
- [x] Confirm `plugins/vibeos/reference/manifests/quality-gate-manifest.json.ref` already uses the object schema; align if any inconsistency exists (verified already object-form; no change needed)
- [x] Add tests to `tests/test_gate_runner.py` covering object-tier, legacy string-tier, and missing-tier resolution, plus a `pre_commit` end-to-end execution test

### Out of Scope
- Any WO-frontmatter work (lands in WO-111+)
- Changing per-gate `blocking` fields or the gate list itself
- Fixture secret quarantine / pytest scoping (WO-108)
- Runtime capability detection (WO-109)
- Hook-manifest sync and WO status reconciliation (WO-110)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-106 commit | Predecessor (vNext foundation) | Implemented Locally |

## Findings

1. The live manifest `tiers` map stores values as description strings (`"0": "Always run — security and environment basics"`), but `get_tier_info()` calls `tier_def.get("blocking", …)` / `tier_def.get("label", …)`, which raises `AttributeError` on a string. Reproduced directly: exit 7, `'str' object has no attribute 'get'`.
2. The reference manifest (`…/reference/manifests/quality-gate-manifest.json.ref`) already uses the object schema `{"label", "blocking", "description"}`. The live manifest is the stale copy; the migration brings it into line.
3. `get_tier_info()` is the **only** consumer of the `tiers` map (verified by grep across scripts/ and hooks/). The blocking decision in the gate loop is tier-driven via this function, so the fix is localized.
4. WO-106's own pre-commit audit recorded this exact failure as a pre-existing blocker outside its scope — it is this WO's scope.

## Acceptance Criteria

- [x] AC-1: Tier definitions in the live manifest are objects `{"label": str, "blocking": bool}`, with tiers 0–1 blocking and 2–3 advisory
- [x] AC-2: `get_tier_info()` resolves object tiers correctly (uses declared `blocking`/`label`) — verified: tier 0→`True|critical`, 2→`False|advisory`
- [x] AC-3: `get_tier_info()` tolerates legacy string tiers (blocking inferred from `tier <= 1`; string used as label) — back-compat for installed projects
- [x] AC-4: `get_tier_info()` returns safe defaults for a missing tier (`blocking = tier <= 1`, label `tier-N`) — verified: tier 9→`False|tier-9`
- [x] AC-5: `pre_commit` executes all 10 gates end-to-end without the AttributeError (Total: 10 with `--continue-on-failure`)
- [x] AC-6: New tests cover object-tier, string-tier, and missing-tier resolution and pass (9/9 in `tests/test_gate_runner.py`)

## Test Strategy

- **Unit tests:** `python3 -m pytest tests/test_gate_runner.py`
- **Real-path verification:** `bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos` — all 10 gates execute (pass or fail on their own merits, but the runner no longer aborts on tier resolution)
- **Tier hook:** `bash plugins/vibeos/scripts/gate-runner.sh --print-tier 0 --manifest <temp> --project-dir . --framework-dir plugins/vibeos` prints `blocking|label`

## Implementation Plan

### Step 1: Tests (TDD)
- Extend `tests/test_gate_runner.py` with object/string/missing tier cases and a pre_commit end-to-end test
- Expected outcome: tests fail before the fix (string-tier crash, `--print-tier` unrecognized)

### Step 2: Runner fix
- Rewrite `get_tier_info()` to branch on `isinstance(tier_def, dict)` vs string vs missing
- Add `--print-tier` flag, argument parsing, and a dispatch in the Main Execution section before `acquire_lock`

### Step 3: Manifest migration
- Convert `quality-gate-manifest.json` `tiers` to object form, preserving labels/descriptions and blocking semantics

### Step 4: Verification
- Run the two proof commands; confirm 10 gates execute and tier tests pass

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Findings: Single-file logic change + manifest data migration + back-compat + tests; localized, low blast radius.
- Test status: Pending at planning time.

### Pre-Implementation Audit
- Status: `complete` (recorded retrospectively)
- Findings: `get_tier_info()` is the sole consumer of the manifest `tiers` map (verified by grep across `scripts/` and `hooks/`), so the fix is contained. The `.ref` manifest already uses the object schema; the live manifest is the stale copy. Test strategy: deterministic unit tests via a new `--print-tier` diagnostic hook plus a `pre_commit` end-to-end assertion. Environment prerequisites (python3, jq, bash 3.2+) confirmed present.
- Anchor status: aligned — foundation-repair WO, no product-surface change.
- Freshness status: N/A (no external dependency decisions).

### Pre-Commit Audit
- Status: `complete`
- Layer-2 auditors run (same-tree, read-only): correctness-auditor, evidence-auditor.
- Correctness findings: 1 HIGH (fail-fast abort at `gate-runner.sh:675` only matched lowercase `"true"`, newly exposed by the migration) — **fixed**; 1 MEDIUM (`blocking: null` silently demoted a tier) — **fixed** via `None`-coercion; 2 LOW (non-integer `--print-tier` traceback, whitespace-only legacy label) — **fixed** (exit 2 on bad input, `.strip()` on labels). All four fixes verified: 9/9 tests pass; fail-fast abort now fires (Total: 1) without `--continue-on-failure`.
- Evidence findings: WO file now records proof; status reconciled across WO file / WO-INDEX / DEVELOPMENT-PLAN; out-of-scope failures enumerated below.
- Required fixes: none outstanding within WO-107 scope.
- Accepted risks: gate-runner.sh remains over the 300-line file-size limit (pre-existing, framework-wide condition) — deferred to a dedicated refactor WO (see Known Out-of-Scope Failures).
- Test status: `python3 -m pytest tests/test_gate_runner.py` → 9 passed.
- Anchor status: aligned. Freshness status: N/A.

### Staging / Completion Audit
- Status: `complete`
- Real path exercised: `gate-runner.sh pre_commit` executes all 10 gates with `--continue-on-failure` (Total: 10, no AttributeError); fail-fast aborts at the first blocking failure without the flag (Total: 1). Tier diagnostic resolves all four live tiers plus a missing tier correctly.
- Repo state: clean and resumable; only WO-107 scope files touched.

## Known Out-of-Scope Failures (pre_commit, with `--continue-on-failure`)

WO-107's AC-5 requires only that the runner **executes** all 10 gates end-to-end without the tier-resolution crash — not that every gate passes. Per the master plan, the Phase 34 gate floor goes fully green only at the Phase 34 audit checkpoint (after WO-108/109/110). The current blocking failures are owned elsewhere:

| Gate | Why it fails | Owner |
|---|---|---|
| `validate-no-secrets.sh` | Embedded test fixture contains an AWS-pattern fake key | WO-108 (fixture secret quarantine) |
| `validate-tests-pass.sh` | "Cannot determine test command" (no `TEST_CMD` / `pytest` scoping) | WO-108 (pytest scoping) |
| `validate-file-size.sh` | `gate-runner.sh` (754 lines) and ~8 other framework scripts exceed the 300-line hard limit | **Unowned — follow-up refactor WO needed** (pre-existing, framework-wide; WO-107 added ~20 lines to an already-447-over file) |
| `validate-code-complexity.sh` | Same oversized framework scripts flagged as god-objects | Tracked with the file-size refactor |

## Evidence

- [x] Implementation complete
- [x] Tests pass (`python3 -m pytest tests/test_gate_runner.py` → 9 passed)
- [x] Real path verified (`pre_commit` runs all 10 gates; fail-fast abort restored)
- [x] Documentation updated (WO file, WO-INDEX.md, DEVELOPMENT-PLAN.md, build log)

### Proof Commands
```bash
# Tier resolution (live manifest):
bash plugins/vibeos/scripts/gate-runner.sh --print-tier 0 --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos
#   → True|critical   (tier 1 → True|important, 2 → False|advisory, 3 → False|informational, 9 → False|tier-9)

# End-to-end gate execution (10 gates, no crash):
bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos
#   → Total: 10 | Passed: 2 | Failed: 5 | Skipped: 3   (failures owned per table above)

# Tests:
python3 -m pytest tests/test_gate_runner.py
#   → 9 passed
```
