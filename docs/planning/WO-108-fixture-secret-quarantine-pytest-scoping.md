# WO-108: Fixture Secret Quarantine + Pytest Scoping

## Status

`Complete` — deliverable (secret-quarantine + pytest-scoping) implemented, real-path verified, 8/8 tests pass, audit findings fixed. The Phase 34 gate floor is **not yet green** — see "Known Out-of-Scope Failures" and the "Phase 34 Planning Gap" note below.

## Phase

Phase 34: Foundation Repair

## Objective

Make two pre_commit blockers pass honestly without weakening real detection:
1. The secret scanner (`validate-no-secrets.sh`) flags the intentional fake AWS key inside the self-contained test fixture (`plugins/vibeos/test-fixture/src/app.py`). Add a narrowly-scoped allowlist so the fixture is exempt **while a real-pattern secret anywhere else still fails the scan**.
2. Bare `python3 -m pytest` collects the fixture's sample tests and dies with `ModuleNotFoundError: No module named 'test_fixture'`. Scope pytest to `tests/` so bare `pytest` == `pytest tests`.

The fixture is a global no-touch asset and is never modified or deleted.

## Scope

### In Scope
- [x] Add `plugins/vibeos/scripts/secrets-allowlist.json` listing the fixture path + pattern (+ value pin) intentionally exempt from scanning
- [x] Wire `validate-no-secrets.sh` to consult the allowlist and skip only matching (path + pattern + value-token) hits
- [x] Add `pytest.ini` with `testpaths = tests` so bare pytest collects only the framework suite
- [x] Add tests proving the allowlist exempts the fixture but still detects real secrets elsewhere, and that pytest is scoped

### Out of Scope
- Modifying or deleting the test fixture (global no-touch)
- Gate-runner tier logic (WO-107, complete)
- Runtime capability detection (WO-109)
- The file-size gate failures (separate refactor WO)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-107 (gate floor executes) | Predecessor | Complete |

## Findings

1. `validate-no-secrets.sh` exits 1 on `plugins/vibeos/test-fixture/src/app.py:6` (a fake `AKIA[REDACTED]` key, pattern `aws_access_key_id`) — an intentional fixture fake.
2. Bare `python3 -m pytest` collects 109 framework tests **plus** the fixture's `test_app.py`, which fails import (`from test_fixture.src.app import ...`) → collection error, exit non-zero.
3. `tests/` already collects 109 tests; scoping pytest to `tests/` satisfies the 103+ bar with the fixture excluded.

## Acceptance Criteria

- [x] AC-1: `validate-no-secrets.sh` exits 0 with the fixture intact (allowlisted)
- [x] AC-2: A planted real-pattern secret outside the allowlist still fails the scan (exit 1) — covered by `test_real_secret_outside_allowlist_is_detected`
- [x] AC-3: The allowlist is path+pattern+value scoped (different path, different value, suffix-collision, and same-line non-token all still detected)
- [x] AC-4: `pytest.ini` scopes collection to `tests/`; bare `python3 -m pytest` == `pytest tests` (both **114 passed**)
- [x] AC-5: New tests cover allowlist exemption, outside-allowlist detection, path-scoping, token-pinning, require-value, and pytest scoping (8/8)

## Test Strategy

- **Unit/integration:** `tests/test_no_secrets_allowlist.py`
- **Proof commands:** `bash plugins/vibeos/scripts/validate-no-secrets.sh`; `python3 -m pytest`

## Implementation Plan

1. Write allowlist + scoping tests (TDD red).
2. Add `secrets-allowlist.json`; teach the scanner to skip allowlisted hits.
3. Add `pytest.ini` (`testpaths = tests`).
4. Capture failing→passing trace; run Layer-2 audit; document.

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Test strategy: `tests/test_no_secrets_allowlist.py` (integration via subprocess against the real scanner) — exemption, detection, path/value scoping, pytest scoping.
- Real-path entrypoint: `bash plugins/vibeos/scripts/validate-no-secrets.sh` (the gate as invoked by gate-runner); `pytest.ini` configures bare-pytest collection.
- Findings: Additive allowlist + config; primary risk is over-exemption, mitigated by exact-path + token-value pinning and detection-still-works tests.

### Pre-Implementation Audit
- Status: `complete` (recorded retrospectively)
- Findings: `secrets-allowlist.json` is a new file (no migration risk). The scanner already supports path-arg scanning and a git/filesystem dual mode; allowlist consultation is purely subtractive on hits. `pytest.ini` with `testpaths = tests` is the minimal scoping mechanism; `tests/` already collects 109+ tests so the 103+ bar is met with the fixture excluded. Prerequisites (bash, python3, jq) confirmed present. Fixture is global no-touch — never modified.
- Anchor status: aligned. Freshness status: N/A.

### Pre-Commit Audit
- Status: `complete`
- Layer-2 auditors (same-tree, read-only): correctness-auditor, evidence-auditor.
- Correctness findings: 1 HIGH (`value_contains` matched the whole line, not the secret token → a real key sharing a line with the magic substring at the fixture path would be silently exempted) — **fixed** (now pins to `rx.search(line).group(0)`); 2 MEDIUM (suffix path-matching collision; blanket-exemption when `value_contains` absent) — **fixed** (exact repo-relative match; empty value never exempts); 1 LOW (pinning-strength doc clarity) — **fixed** (allowlist `description` updated). All fixes covered by 3 new regression tests; 8/8 pass; fixture still exempt (scan exit 0).
- Evidence findings: WO file now records proof; status reconciled with WO-INDEX; out-of-scope failures + Phase 34 planning gap enumerated below.
- Accepted risks: none within WO-108 scope.
- Test status: `python3 -m pytest tests/test_no_secrets_allowlist.py` → 8 passed.
- Anchor status: aligned. Freshness status: N/A.

### Staging / Completion Audit
- Status: `complete`
- Real path exercised: `validate-no-secrets.sh` → PASS (exit 0) with fixture intact; bare `python3 -m pytest` == `python3 -m pytest tests` (both 114 passed); within gate-runner the secret gate now reports PASS.
- Repo state: clean, resumable; only WO-108 scope files touched.

## Known Out-of-Scope Failures (pre_commit gate floor, with `--continue-on-failure`)

WO-108 fixes the secret-scan blocker and scopes pytest. Remaining `pre_commit` blocking failures are owned elsewhere:

| Gate | Why it fails | Owner |
|---|---|---|
| `validate-file-size.sh` | `gate-runner.sh` (754 lines) + ~8 framework scripts exceed the 300-line hard limit | Phase 34 gate-floor remediation (see planning gap) |
| `validate-code-complexity.sh` | Same oversized framework scripts flagged as god-objects | Same remediation |
| `detect-stubs-placeholders.py` | Trips on the **intentional** no-touch test-fixture stubs (`NotImplementedError`, `pass`-only, `assert True`) AND on sibling gate scripts that legitimately contain detection keywords (`response-quality-stop.sh`, `e2e-test-runner.sh`, `test-quality-gate.sh`) — all false positives | Same remediation (needs fixture + self-scan exclusion, mirroring this WO's allowlist pattern) |
| `validate-tests-pass.sh` | Language detection returns `unknown` (no `pyproject.toml`/`setup.py`/`requirements.txt` at repo root), so the gate exits "Cannot determine test command" — it runs its own detection rather than reading `pytest.ini` | Same remediation (set `TEST_CMD`, add a project marker, or teach the gate to recognize `pytest.ini`) |

## Phase 34 Planning Gap (discovered)

The master plan's Phase 34 exit criterion is a **green gate floor end-to-end**. The four planned WOs (WO-107–110) do **not** collectively achieve it: after WO-108, the four failures above remain, none owned by WO-109 (runtime capabilities) or WO-110 (hook-manifest + status reconciliation). At least one additional Phase 34 WO is required before the Phase 34 audit checkpoint can truthfully claim a green floor:
- A **framework gate-floor remediation WO**: split/except the oversized framework scripts (file-size + complexity), add fixture + self-scan exclusions to `detect-stubs-placeholders.py`, and make `validate-tests-pass.sh` recognize this Python project.

This gap is recorded here and will be addressed (a remediation WO authored and executed) when this autonomous run reaches the Phase 34 checkpoint, after WO-109 and WO-110.

## Evidence

- [x] Implementation complete
- [x] Tests pass (`python3 -m pytest tests/test_no_secrets_allowlist.py` → 8 passed)
- [x] Real path verified (scan passes with fixture exempt; planted/other secrets still detected; bare pytest scoped to `tests/`)
- [x] Documentation updated (WO file, WO-INDEX.md, build log)

### Proof Commands
```bash
bash plugins/vibeos/scripts/validate-no-secrets.sh        # → PASS: No secrets detected (exit 0)
python3 -m pytest                                          # → 114 passed (fixture no longer collected)
python3 -m pytest tests                                    # → 114 passed (identical)
python3 -m pytest tests/test_no_secrets_allowlist.py       # → 8 passed
```

**Failing→passing trace (proof package):** before WO-108, `validate-no-secrets.sh` exited 1 on `plugins/vibeos/test-fixture/src/app.py:6` (`aws_access_key_id`); after the allowlist it exits 0 while a real-pattern secret anywhere else (or a non-token same-line substring at the fixture path) still exits 1.
