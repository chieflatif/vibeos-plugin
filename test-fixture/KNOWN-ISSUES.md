# Test Fixture — Known Issues

Each issue is intentionally planted to validate that the corresponding audit layer detects it.

| # | File | Issue | Detection Layer | Gate/Hook |
|---|---|---|---|---|
| 1 | src/app.py:6 | Hardcoded AWS key (`AKIA...`) | Layer 0 | secrets-scan hook (PreToolUse) |
| 2 | src/app.py:14 | SQL injection via f-string | Layer 2 | security auditor (Phase 4) |
| 3 | src/app.py:24 | `raise NotImplementedError` | Layer 0 + Layer 1 | Stop hook + detect-stubs-placeholders |
| 4 | src/app.py:31 | Swallowed error (`except: pass`) | Layer 1 | detect-stubs-placeholders |
| 5 | tests/test_app.py:7 | Vacuous test (`assert True`) | Layer 1 | validate-test-integrity |
| 6 | tests/test_app.py:12 | Fallback-masked test | Layer 2 | test auditor (Phase 4) |
| 7 | tests/test_app.py:19 | Stub test (`pass` body) | Layer 1 | detect-stubs-placeholders |

## Validation Commands

```bash
# Layer 0: Secrets hook (simulated — hook runs on Write/Edit, not on existing files)
grep -n 'AKIA' test-fixture/src/app.py

# Layer 1: Stub detection
python3 scripts/detect-stubs-placeholders.py test-fixture/

# Layer 1: Test integrity
bash scripts/validate-test-integrity.sh

# Layer 2: Security auditor (Phase 4 — manual review until then)
grep -n "f\"SELECT\|f'SELECT" test-fixture/src/app.py
```

## Phase 1 Verifiable Issues

Issues 1, 3, 4, 5, 7 are verifiable in Phase 1 (hooks + gate scripts exist).
Issues 2, 6 are verifiable in Phase 4 (audit agents).
