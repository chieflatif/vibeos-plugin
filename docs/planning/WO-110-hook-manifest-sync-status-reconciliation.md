# WO-110: Hook-Manifest Sync + WO Status Reconciliation

## Status

`Complete` — manifest synced (12 documented == 12 configured), 13 plan statuses reconciled, detector made header-aware (zero mismatches), gate tier confirmed. 4/4 WO tests pass; full suite 132 passed. Phase 34 gate floor still red on out-of-scope gates — see "Known Out-of-Scope Failures".

## Phase

Phase 34: Foundation Repair

## Objective

Close the F-08 status-drift class and bring the hook manifest into sync with the configured hooks:
1. `hook-manifest.json` documents only 9 hooks while `hooks.json` configures 12 command hooks (missing `governance-guard`, `proof-protection`, `file-budget`). Document all 12 so `generate-inventory.py` reports `documented_count == configured_command_count == 12`.
2. `DEVELOPMENT-PLAN.md` carries stale `Draft` statuses for WO-041–WO-053 while `WO-INDEX.md` (and the dated completions) say `Complete` — 13 genuine plan/index mismatches.
3. The mismatch detector in `prereq-check.sh` hardcodes the index status column, so it misreads the Phase-first ("vNext") table format (`| WO | Title | Phase | Status | … |`) and falsely flags WO-106. Make the parser header-aware so it reads the `Status` column correctly across both table formats.
4. Confirm the status-integrity gate runs at the blocking tier at `wo_exit`.

## Scope

### In Scope
- [x] Add `governance-guard`, `proof-protection`, `file-budget` to `plugins/vibeos/hook-manifest.json` (→ 12 documented)
- [x] Update `DEVELOPMENT-PLAN.md` per-WO status for WO-041–WO-053 from `Draft` to `Complete` (authoritative = index + dated completions + WO files)
- [x] Make `prereq-check.sh` plan/index status parsing header-aware (locate the `Status` column per table)
- [x] Confirm `validate-wo-status-integrity.sh` is tier-1 blocking at `wo_exit` in the manifest (already true; verified by test)
- [x] Tests asserting documented==configured==12, zero plan/index mismatches, and the gate tier

### Out of Scope
- Converting WO-INDEX.md to a generated view (WO-113)
- WO frontmatter (WO-111/112)
- The pre_commit gate-floor failures (Phase 34 gate-floor remediation WO)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-109 | Predecessor (Phase 34 order) | Complete |

## Findings

1. `inventory.hooks` → `configured_command_count: 12`, `documented_count: 9`. The 12 configured command hooks are correct; the manifest is missing 3.
2. The detector reports 14 mismatches: 13 genuine (WO-041–053 plan `Draft` vs index `Complete`) and 1 artifact (WO-106, mis-parsed because the vNext table puts `Phase` in the column the detector reads as status).
3. The vNext Stop hook of `type: "prompt"` (Codex-audit reminder) is correctly excluded from `configured_command_count` (counts `type == "command"` only).

## Acceptance Criteria

- [x] AC-1: `hook-manifest.json` documents all 12 configured command hooks with correct names/event types (verified by `test_manifest_documents_all_configured_command_hooks`)
- [x] AC-2: `generate-inventory.py` reports `documented_count == configured_command_count == 12`
- [x] AC-3: `DEVELOPMENT-PLAN.md` and `WO-INDEX.md` agree for WO-041–WO-053 (`Complete`)
- [x] AC-4: The header-aware detector reports zero plan/index mismatches (WO-106 artifact resolved) — `plan/index mismatches: none`
- [x] AC-5: `validate-wo-status-integrity.sh` is tier-1 blocking at `wo_exit` (manifest line 37)
- [x] AC-6: Tests cover manifest/inventory counts, zero mismatches, and the gate tier (4/4 pass)

## Test Strategy

- **Integration:** `tests/test_status_reconciliation.py`
- **Proof:** `python3 plugins/vibeos/scripts/generate-inventory.py --project-dir .`; run `prereq-check.sh` and confirm `plan/index mismatches: none`

## Implementation Plan

1. Write reconciliation tests (TDD red).
2. Add 3 hooks to the manifest; reconcile 13 plan statuses; make the parser header-aware.
3. Regenerate inventory; prove zero mismatches + 12 documented; Layer-2 audit; document.

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Findings: Config/data reconciliation + one parser-robustness fix. Risk: changing the wrong status; mitigated by cross-checking WO files/index dated completions and by header-aware (not positional) column reads.

### Pre-Implementation Audit
- Status: `complete` (recorded retrospectively)
- Findings: Three files touched (hook-manifest.json, DEVELOPMENT-PLAN.md, prereq-check.sh) plus a new test. The status-integrity gate was already tier-1 blocking at wo_exit (no manifest change needed). The 13 plan rows are corroborated as Complete by WO-INDEX.md Backlog tables and dated (2026-03-08) Completed entries. Header-aware parsing is the durable fix for two coexisting index table formats (until WO-113 makes the index generated).
- Anchor status: aligned. Freshness status: N/A.

### Pre-Commit Audit
- Status: `complete`
- Layer-2 auditors (same-tree, read-only): correctness-auditor, evidence-auditor.
- Correctness findings: 0 critical/high/medium; 1 LOW (stale `status_col` fallback could carry across a headerless table) — **fixed** (header reset uses literal defaults plan=3/index=2). The auditor independently confirmed: exactly the 13 right rows changed (status-only, corroborated Complete), the 3 manifest entries match `hooks.json` event/matcher, and the detector produces a *correct* "none" (not a coincidental match), removing the WO-106 false positive without introducing a false negative.
- Evidence findings: WO documented to parity; status reconciled with WO-INDEX. (The evidence auditor's "test files missing" notes were false positives — the test files are untracked in git but present in the working tree; 132 tests pass.)
- Test status: `python3 -m pytest tests/test_status_reconciliation.py` → 4 passed; full suite 132 passed.
- Anchor status: aligned. Freshness status: N/A.

### Staging / Completion Audit
- Status: `complete`
- Real path exercised: `generate-inventory.py` → `documented_count == configured_command_count == 12`; `prereq-check.sh` → `plan/index mismatches: none`; status-integrity gate confirmed tier-1 blocking at wo_exit.
- Repo state: clean, resumable; only WO-110 scope files (+ generated inventory) touched.

## Known Out-of-Scope Failures (pre_commit gate floor)

WO-110 does **not** fix the four blocking gate failures carried from WO-108/109 — unchanged, owned by the Phase 34 gate-floor remediation (authored next, before the Phase 34 checkpoint):

| Gate | Why it fails | Owner |
|---|---|---|
| `validate-file-size.sh` | Framework scripts exceed the 300-line hard limit | Phase 34 gate-floor remediation |
| `validate-code-complexity.sh` | Same oversized framework scripts | Same remediation |
| `detect-stubs-placeholders.py` | False positives on the no-touch fixture stubs + sibling detection-keyword scripts | Same remediation |
| `validate-tests-pass.sh` | Language detection returns `unknown` (no repo-root project marker) | Same remediation |

**Phase 34 checkpoint note:** WO-110 is the last *planned* Phase 34 WO, but the Phase 34 exit criterion (green gate floor end-to-end) is not yet met. A gate-floor remediation WO is required before the Phase 34 audit checkpoint can truthfully pass (per the WO-108 "Phase 34 Planning Gap").

## Evidence

- [x] Implementation complete
- [x] Tests pass (`python3 -m pytest tests/test_status_reconciliation.py` → 4 passed; full suite 132 passed)
- [x] Real path verified (12 documented hooks; zero plan/index mismatches; gate tier confirmed)
- [x] Documentation updated (WO file, WO-INDEX.md, build log)

### Proof Commands
```bash
python3 plugins/vibeos/scripts/generate-inventory.py --project-dir .
#   → inventory.hooks: documented_count=12, configured_command_count=12
echo '{}' | CLAUDE_PROJECT_DIR="$(pwd)" bash plugins/vibeos/hooks/scripts/prereq-check.sh | grep -o "plan/index mismatches: [^;]*"
#   → plan/index mismatches: none
python3 -m pytest tests/test_status_reconciliation.py     # → 4 passed
```
